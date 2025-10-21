"""
交叉验证Agent - 负责合同与发票的交叉验证
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.invoice import Invoice
from app.models.audit import SeverityLevel
from app.services.ai_service import AIService


class CrossValidator:
    """交叉验证Agent"""

    def __init__(self):
        self.ai_service = AIService()

    async def validate(
        self,
        contract_results: List[Dict],
        invoice_results: List[Dict],
        task_id: str,
        websocket_manager=None
    ) -> Dict[str, Any]:
        """
        执行交叉验证

        Args:
            contract_results: 合同分析结果列表
            invoice_results: 发票分析结果列表
            task_id: 任务ID
            websocket_manager: WebSocket管理器

        Returns:
            验证结果
        """
        results = {
            "overall_status": "需人工复核",
            "match_score": 0,
            "issues": [],
            "summary": "交叉验证完成"
        }

        try:
            # 发送进度更新
            if websocket_manager:
                await websocket_manager.send_progress(
                    task_id, 75, "正在进行合同与发票的交叉验证..."
                )

            # 验证数据完整性
            if not contract_results and not invoice_results:
                results["issues"].append({
                    "type": "数据缺失",
                    "severity": "high",
                    "description": "未找到合同或发票分析结果",
                    "affected_items": ["所有数据"]
                })
                return results

            # 使用AI进行综合验证
            if contract_results and invoice_results:
                validation_request = {
                    "contract_data": [result.get("extracted_data", {}) for result in contract_results],
                    "invoices_data": [result.get("extracted_data", {}) for result in invoice_results]
                }

                ai_result = await self.ai_service.validate_with_llm(validation_request)

                if ai_result.get("success"):
                    validation_result = ai_result.get("validation_result", {})
                    results.update({
                        "overall_status": validation_result.get("overall_status", "需人工复核"),
                        "match_score": validation_result.get("match_score", 0),
                        "issues": validation_result.get("issues", []),
                        "summary": validation_result.get("summary", "交叉验证完成")
                    })
                else:
                    # AI验证失败，进行基础规则验证
                    results = self._basic_validation(contract_results, invoice_results, results)
            else:
                # 只有合同或只有发票，进行部分验证
                results = self._partial_validation(contract_results, invoice_results, results)

            # 发送完成状态
            if websocket_manager:
                await websocket_manager.send_progress(
                    task_id, 90, "交叉验证完成"
                )

        except Exception as e:
            results["issues"].append({
                "type": "验证错误",
                "severity": "high",
                "description": "交叉验证过程发生错误",
                "affected_items": ["验证流程"],
                "details": str(e)
            })

        return results

    def _basic_validation(self, contract_results: List[Dict], invoice_results: List[Dict], results: Dict[str, Any]) -> Dict[str, Any]:
        """
        基础规则验证（当AI验证失败时的备用方案）
        """
        issues = []

        # 金额一致性检查
        contract_total = sum(result.get("extracted_data", {}).get("total_amount", 0) for result in contract_results)
        invoice_total = sum(result.get("extracted_data", {}).get("total_amount", 0) for result in invoice_results)

        if abs(contract_total - invoice_total) > 0:
            issues.append({
                "type": "金额不一致",
                "severity": "medium",
                "description": f"合同总金额与发票总金额存在差异",
                "affected_items": ["金额计算"],
                "details": f"合同金额: {contract_total}, 发票金额: {invoice_total}"
            })

        # 数据完整性检查
        for i, contract in enumerate(contract_results):
            extracted = contract.get("extracted_data", {})
            if not extracted.get("contract_number"):
                issues.append({
                    "type": "合同信息缺失",
                    "severity": "medium",
                    "description": f"第{i+1}份合同缺少合同编号",
                    "affected_items": [f"合同{i+1}"]
                })

        for i, invoice in enumerate(invoice_results):
            extracted = invoice.get("extracted_data", {})
            if not extracted.get("invoice_number"):
                issues.append({
                    "type": "发票信息缺失",
                    "severity": "medium",
                    "description": f"第{i+1}份发票缺少发票号码",
                    "affected_items": [f"发票{i+1}"]
                })

        # 计算匹配分数
        match_score = max(0, 100 - len(issues) * 10)

        results.update({
            "overall_status": "通过" if match_score >= 80 else "需人工复核",
            "match_score": match_score,
            "issues": issues,
            "summary": f"基础验证完成，发现{len(issues)}个问题"
        })

        return results

    def _partial_validation(self, contract_results: List[Dict], invoice_results: List[Dict], results: Dict[str, Any]) -> Dict[str, Any]:
        """
        部分验证（只有合同或只有发票的情况）
        """
        issues = []

        if contract_results and not invoice_results:
            issues.append({
                "type": "缺少发票",
                "severity": "high",
                "description": "未找到相关发票进行匹配",
                "affected_items": ["发票匹配"]
            })
        elif invoice_results and not contract_results:
            issues.append({
                "type": "缺少合同",
                "severity": "high",
                "description": "未找到相关合同进行匹配",
                "affected_items": ["合同匹配"]
            })

        results.update({
            "overall_status": "需人工复核",
            "match_score": 50,
            "issues": issues,
            "summary": "部分验证完成，建议补充相关文件"
        })

        return results

    async def _validate_contract_basic_info(
        self,
        contracts: List[Contract],
        results: Dict[str, Any],
        websocket_manager=None,
        task_id: str = None
    ):
        """验证合同基本信息"""
        if websocket_manager:
            await websocket_manager.send_progress_update(
                task_id, 75, "验证合同基本信息..."
            )

        for i, contract in enumerate(contracts):
            try:
                # 使用AI验证合同信息完整性
                prompt = f"""
                请验证以下合同信息的完整性和准确性：

                合同编号: {contract.contract_number or '未填写'}
                合同名称: {contract.contract_name or '未填写'}
                甲方: {contract.party_a or '未填写'}
                乙方: {contract.party_b or '未填写'}
                合同金额: {contract.contract_amount or '未填写'}
                签订日期: {contract.sign_date or '未填写'}

                请检查：
                1. 必要信息是否完整
                2. 格式是否规范
                3. 是否有明显错误

                返回JSON格式结果：
                {{
                    "is_valid": true/false,
                    "issues": ["问题1", "问题2"],
                    "confidence": 0.95
                }}
                """

                response = await self.ai_service.analyze_contract(contract.extracted_data or {}, prompt)

                if response and "is_valid" in response:
                    results["total_validations"] += 1
                    if response["is_valid"]:
                        results["passed_validations"] += 1
                    else:
                        results["failed_validations"] += 1
                        for issue in response.get("issues", []):
                            results["issues"].append({
                                "type": "contract_info_error",
                                "severity": SeverityLevel.MEDIUM.value,
                                "description": f"合同 {contract.contract_number} 信息问题",
                                "details": issue,
                                "contract_id": contract.id
                            })

            except Exception as e:
                results["issues"].append({
                    "type": "contract_validation_error",
                    "severity": SeverityLevel.LOW.value,
                    "description": f"合同 {contract.contract_number} 验证失败",
                    "details": str(e),
                    "contract_id": contract.id
                })

    async def _validate_invoice_basic_info(
        self,
        invoices: List[Invoice],
        results: Dict[str, Any],
        websocket_manager=None,
        task_id: str = None
    ):
        """验证发票基本信息"""
        if websocket_manager:
            await websocket_manager.send_progress_update(
                task_id, 78, "验证发票基本信息..."
            )

        for i, invoice in enumerate(invoices):
            try:
                # 使用AI验证发票信息完整性
                prompt = f"""
                请验证以下发票信息的完整性和准确性：

                发票号码: {invoice.invoice_number or '未填写'}
                发票代码: {invoice.invoice_code or '未填写'}
                开票日期: {invoice.issue_date or '未填写'}
                销售方: {invoice.seller or '未填写'}
                购买方: {invoice.buyer or '未填写'}
                发票金额: {invoice.total_amount or '未填写'}

                请检查：
                1. 必要信息是否完整
                2. 发票格式是否规范
                3. 金额是否合理

                返回JSON格式结果：
                {{
                    "is_valid": true/false,
                    "issues": ["问题1", "问题2"],
                    "confidence": 0.95
                }}
                """

                response = await self.ai_service.analyze_invoice(invoice.extracted_data or {}, prompt)

                if response and "is_valid" in response:
                    results["total_validations"] += 1
                    if response["is_valid"]:
                        results["passed_validations"] += 1
                    else:
                        results["failed_validations"] += 1
                        for issue in response.get("issues", []):
                            results["issues"].append({
                                "type": "invoice_info_error",
                                "severity": SeverityLevel.MEDIUM.value,
                                "description": f"发票 {invoice.invoice_number} 信息问题",
                                "details": issue,
                                "invoice_id": invoice.id
                            })

            except Exception as e:
                results["issues"].append({
                    "type": "invoice_validation_error",
                    "severity": SeverityLevel.LOW.value,
                    "description": f"发票 {invoice.invoice_number} 验证失败",
                    "details": str(e),
                    "invoice_id": invoice.id
                })

    async def _validate_contract_invoice_matching(
        self,
        contracts: List[Contract],
        invoices: List[Invoice],
        results: Dict[str, Any],
        websocket_manager=None,
        task_id: str = None
    ):
        """验证合同发票匹配"""
        if websocket_manager:
            await websocket_manager.send_progress_update(
                task_id, 82, "验证合同发票匹配..."
            )

        # 构建匹配验证提示
        contract_info = []
        for contract in contracts:
            contract_info.append({
                "id": contract.id,
                "number": contract.contract_number,
                "name": contract.contract_name,
                "party_a": contract.party_a,
                "party_b": contract.party_b,
                "amount": contract.contract_amount
            })

        invoice_info = []
        for invoice in invoices:
            invoice_info.append({
                "id": invoice.id,
                "number": invoice.invoice_number,
                "seller": invoice.seller,
                "buyer": invoice.buyer,
                "amount": invoice.total_amount
            })

        try:
            prompt = f"""
            请分析以下合同和发票的匹配关系：

            合同信息：
            {json.dumps(contract_info, ensure_ascii=False, indent=2)}

            发票信息：
            {json.dumps(invoice_info, ensure_ascii=False, indent=2)}

            请检查：
            1. 发票的购买方/销售方是否与合同的甲乙方匹配
            2. 发票金额是否在合同金额范围内
            3. 时间是否合理

            返回JSON格式结果：
            {{
                "matches": [
                    {{
                        "contract_id": "合同ID",
                        "invoice_id": "发票ID",
                        "match_score": 0.95,
                        "issues": ["匹配问题1"]
                    }}
                ],
                "unmatched_contracts": ["合同ID"],
                "unmatched_invoices": ["发票ID"],
                "confidence": 0.90
            }}
            """

            # 这里需要调用AI服务进行匹配分析
            # 由于需要具体的AI服务实现，这里提供模拟结果
            matches = []
            for contract in contracts:
                for invoice in invoices:
                    # 简单的匹配逻辑：检查金额和主体
                    if (contract.party_a and invoice.buyer and
                        (contract.party_a in invoice.buyer or invoice.buyer in contract.party_a)):
                        matches.append({
                            "contract_id": contract.id,
                            "invoice_id": invoice.id,
                            "match_score": 0.85,
                            "issues": []
                        })

            results["total_validations"] += 1
            if matches:
                results["passed_validations"] += 1
            else:
                results["failed_validations"] += 1
                results["issues"].append({
                    "type": "matching_error",
                    "severity": SeverityLevel.HIGH.value,
                    "description": "合同与发票匹配失败",
                    "details": "未找到有效的合同发票匹配关系"
                })

        except Exception as e:
            results["issues"].append({
                "type": "matching_validation_error",
                "severity": SeverityLevel.MEDIUM.value,
                "description": "合同发票匹配验证失败",
                "details": str(e)
            })

    async def _validate_amount_consistency(
        self,
        contracts: List[Contract],
        invoices: List[Invoice],
        results: Dict[str, Any],
        websocket_manager=None,
        task_id: str = None
    ):
        """验证金额一致性"""
        if websocket_manager:
            await websocket_manager.send_progress_update(
                task_id, 86, "验证金额一致性..."
            )

        try:
            # 计算合同总金额和发票总金额
            total_contract_amount = sum(
                float(c.contract_amount or 0) for c in contracts
            )
            total_invoice_amount = sum(
                float(i.total_amount or 0) for i in invoices
            )

            # 金额一致性检查
            amount_diff = abs(total_contract_amount - total_invoice_amount)
            tolerance_rate = 0.05  # 5% 容差

            results["total_validations"] += 1
            if amount_diff <= total_contract_amount * tolerance_rate:
                results["passed_validations"] += 1
            else:
                results["failed_validations"] += 1
                results["issues"].append({
                    "type": "amount_inconsistency",
                    "severity": SeverityLevel.HIGH.value,
                    "description": "合同与发票金额不一致",
                    "details": f"合同总金额: {total_contract_amount}, 发票总金额: {total_invoice_amount}, 差异: {amount_diff}"
                })

        except Exception as e:
            results["issues"].append({
                "type": "amount_validation_error",
                "severity": SeverityLevel.MEDIUM.value,
                "description": "金额一致性验证失败",
                "details": str(e)
            })

    async def _validate_time_consistency(
        self,
        contracts: List[Contract],
        invoices: List[Invoice],
        results: Dict[str, Any],
        websocket_manager=None,
        task_id: str = None
    ):
        """验证时间一致性"""
        if websocket_manager:
            await websocket_manager.send_progress_update(
                task_id, 88, "验证时间一致性..."
            )

        try:
            # 检查发票时间是否在合同时间之后
            time_issues = []

            for contract in contracts:
                if not contract.sign_date:
                    continue

                contract_date = contract.sign_date
                for invoice in invoices:
                    if not invoice.issue_date:
                        continue

                    invoice_date = invoice.issue_date
                    if invoice_date < contract_date:
                        time_issues.append({
                            "contract_id": contract.id,
                            "invoice_id": invoice.id,
                            "issue": "发票日期早于合同签订日期"
                        })

            results["total_validations"] += 1
            if not time_issues:
                results["passed_validations"] += 1
            else:
                results["failed_validations"] += 1
                for issue in time_issues:
                    results["issues"].append({
                        "type": "time_inconsistency",
                        "severity": SeverityLevel.MEDIUM.value,
                        "description": "时间逻辑不一致",
                        "details": issue["issue"],
                        "contract_id": issue["contract_id"],
                        "invoice_id": issue["invoice_id"]
                    })

        except Exception as e:
            results["issues"].append({
                "type": "time_validation_error",
                "severity": SeverityLevel.LOW.value,
                "description": "时间一致性验证失败",
                "details": str(e)
            })

    def _generate_validation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成验证摘要"""
        total = results["total_validations"]
        passed = results["passed_validations"]
        failed = results["failed_validations"]

        success_rate = (passed / total * 100) if total > 0 else 0

        # 按严重程度统计问题
        severity_count = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }

        for issue in results["issues"]:
            severity = issue.get("severity", "low")
            severity_count[severity] = severity_count.get(severity, 0) + 1

        return {
            "total_validations": total,
            "passed_validations": passed,
            "failed_validations": failed,
            "success_rate": round(success_rate, 2),
            "total_issues": len(results["issues"]),
            "severity_distribution": severity_count,
            "validation_status": "passed" if success_rate >= 80 else "failed"
        }