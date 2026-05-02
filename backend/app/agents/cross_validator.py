"""交叉验证Agent - 使用DeepSeek模型验证合同与发票的一致性"""
import json
import logging
from typing import Dict, Any, List

from app.agents.base import BaseAgent, AgentError
from app.services.ai_service import ai_service, AIServiceError

logger = logging.getLogger(__name__)


class CrossValidator(BaseAgent):
    """交叉验证Agent，验证合同与发票的匹配性、一致性和合规性"""

    def __init__(self):
        super().__init__(name="cross_validator", agent_type="cross_validator")

    async def _execute(
        self,
        contract_info: Dict[str, Any] = None,
        invoice_list: List[Dict[str, Any]] = None,
        config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        contract_info = contract_info or {}
        invoice_list = invoice_list or []
        config = config or {}

        await self._report_progress(10.0, "验证合同-发票信息匹配...")

        # 基础规则验证（不依赖AI）
        issues = []
        issues.extend(self._check_amount_consistency(contract_info, invoice_list))
        issues.extend(self._check_party_match(contract_info, invoice_list))
        issues.extend(self._check_duplicates(invoice_list))
        issues.extend(self._check_item_coverage(contract_info, invoice_list))

        # 计算覆盖率
        coverage = self._calculate_coverage(contract_info, invoice_list)

        await self._report_progress(50.0, f"基础验证完成, 发现 {len(issues)} 个问题")

        # 尝试AI深度分析
        ai_validated = False
        try:
            if not contract_info.get("_fallback") and invoice_list:
                await self._report_progress(60.0, "正在进行AI深度分析...")
                ai_result = await ai_service.analyze_contract_compliance(
                    contract_info, invoice_list
                )
                if ai_result:
                    ai_issues = self._filter_actionable_issues(ai_result.get("issues", []))
                    issues.extend(ai_issues)
                    ai_validated = True
                    logger.info(f"AI交叉验证完成, 额外发现 {len(ai_issues)} 个问题")
        except AIServiceError as e:
            logger.warning(f"AI交叉验证失败，使用基础验证结果: {e}")

        await self._report_progress(90.0, f"交叉验证完成, 共 {len(issues)} 个问题")

        return {
            "compliance_status": self._determine_status(issues),
            "overall_score": self._calculate_score(issues, coverage),
            "issues": issues,
            "ai_validated": ai_validated,
            "summary": {
                "contract_amount": contract_info.get("total_amount", 0) or 0,
                "total_invoice_amount": sum(
                    inv.get("total_amount", 0) or 0 for inv in invoice_list
                ),
                "coverage_rate": coverage,
                "issue_count": len(issues),
                "duplicate_invoices": sum(1 for inv in invoice_list if inv.get("is_duplicate")),
            },
        }

    @staticmethod
    def _filter_actionable_issues(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤AI输出中被误放进issues的合规说明。"""
        positive_words = ["一致", "匹配", "合规", "正常", "无异常", "未发现问题"]
        negative_words = ["不一致", "不匹配", "缺失", "异常", "风险", "错误", "无法", "超过", "为空"]
        actionable = []
        for issue in issues or []:
            text = f"{issue.get('title', '')} {issue.get('description', '')}"
            is_positive = any(word in text for word in positive_words)
            is_negative = any(word in text for word in negative_words)
            if is_positive and not is_negative:
                continue
            actionable.append(issue)
        return actionable

    def _check_amount_consistency(
        self, contract: Dict, invoices: List[Dict]
    ) -> List[Dict]:
        """检查金额一致性"""
        issues = []
        contract_amount = contract.get("total_amount") or 0
        if not contract_amount:
            return issues

        total_invoice = sum(inv.get("total_amount", 0) or 0 for inv in invoices)
        if total_invoice <= 0:
            return issues

        diff = abs(contract_amount - total_invoice)
        diff_pct = diff / contract_amount

        if diff_pct > 0.2:
            issues.append({
                "type": "amount_mismatch",
                "severity": "high",
                "title": "金额严重不符",
                "description": f"合同金额 {contract_amount:.2f} 与发票总额 {total_invoice:.2f} 差异 {diff_pct:.1%}",
                "recommendation": "请核实是否存在未上传的发票或合同金额有误",
            })
        elif diff_pct > 0.05:
            issues.append({
                "type": "amount_mismatch",
                "severity": "medium",
                "title": "金额存在差异",
                "description": f"合同金额 {contract_amount:.2f} 与发票总额 {total_invoice:.2f} 差异 {diff:.2f}",
                "recommendation": "建议核实差异原因，确认是否部分交货",
            })

        return issues

    def _check_party_match(
        self, contract: Dict, invoices: List[Dict]
    ) -> List[Dict]:
        """检查买卖双方信息匹配"""
        issues = []
        contract_buyer = (contract.get("buyer_name") or "").strip()
        contract_seller = (contract.get("seller_name") or "").strip()

        if not contract_buyer and not contract_seller:
            return issues

        for inv in invoices:
            inv_buyer = (inv.get("buyer_name") or "").strip()
            inv_seller = (inv.get("seller_name") or "").strip()
            inv_num = inv.get("invoice_number", "unknown")

            if contract_buyer and inv_buyer and contract_buyer != inv_buyer:
                issues.append({
                    "type": "party_mismatch",
                    "severity": "high",
                    "title": "买方信息不匹配",
                    "description": f"发票 {inv_num} 买方'{inv_buyer}'与合同买方'{contract_buyer}'不一致",
                    "recommendation": "请核实是否为关联公司或开票错误",
                })

            if contract_seller and inv_seller and contract_seller != inv_seller:
                issues.append({
                    "type": "party_mismatch",
                    "severity": "high",
                    "title": "卖方信息不匹配",
                    "description": f"发票 {inv_num} 卖方'{inv_seller}'与合同卖方'{contract_seller}'不一致",
                    "recommendation": "请核实供应商信息",
                })

        return issues

    def _check_duplicates(self, invoices: List[Dict]) -> List[Dict]:
        """汇总重复发票问题"""
        duplicates = [inv for inv in invoices if inv.get("is_duplicate")]
        if not duplicates:
            return []

        return [{
            "type": "duplicate",
            "severity": "medium",
            "title": "发现重复发票",
            "description": f"发现 {len(duplicates)} 张重复发票: " + ", ".join(
                d.get("invoice_number", "unknown") for d in duplicates
            ),
            "recommendation": "请核实是否为重复报销，如是请作废重复发票",
        }]

    def _check_item_coverage(
        self, contract: Dict, invoices: List[Dict]
    ) -> List[Dict]:
        """检查商品清单匹配"""
        issues = []
        contract_items = contract.get("product_list") or []
        if not contract_items:
            return issues

        invoice_items = []
        for inv in invoices:
            items = inv.get("product_list") or []
            invoice_items.extend(items)

        contract_names = {str(item.get("name", "") or "") for item in contract_items if item.get("name")}
        invoice_names = {str(item.get("name", "") or "") for item in invoice_items if item.get("name")}

        missing = contract_names - invoice_names
        missing = {m for m in missing if m}  # 过滤空值
        if missing:
            issues.append({
                "type": "item_missing",
                "severity": "medium",
                "title": "商品未在发票中找到",
                "description": f"合同商品未在发票中匹配: {', '.join(sorted(missing))}",
                "recommendation": "请确认是否所有商品都已开票",
            })

        extra = invoice_names - contract_names
        extra = {e for e in extra if e}  # 过滤空值
        if extra:
            issues.append({
                "type": "item_extra",
                "severity": "low",
                "title": "发票包含合同外商品",
                "description": f"发票商品不在合同中: {', '.join(sorted(extra))}",
                "recommendation": "请确认是否为关联采购或开票错误",
            })

        return issues

    def _calculate_coverage(
        self, contract: Dict, invoices: List[Dict]
    ) -> float:
        """计算发票覆盖率"""
        contract_amount = contract.get("total_amount") or 0
        if not contract_amount:
            return 100.0

        total_invoice = sum(inv.get("total_amount", 0) or 0 for inv in invoices)
        if total_invoice <= 0:
            return 0.0

        return min(total_invoice / contract_amount * 100, 100.0)

    def _determine_status(self, issues: List[Dict]) -> str:
        has_high = any(i.get("severity") == "high" for i in issues)
        has_medium = any(i.get("severity") == "medium" for i in issues)
        if has_high:
            return "不合规"
        if has_medium:
            return "部分合规"
        return "合规"

    def _calculate_score(self, issues: List[Dict], coverage: float) -> float:
        """计算综合评分"""
        score = 1.0
        for issue in issues:
            sev = issue.get("severity", "low")
            if sev == "high":
                score -= 0.15
            elif sev == "medium":
                score -= 0.05
            else:
                score -= 0.01
        score *= min(coverage / 100.0, 1.0)
        return max(score, 0.0)
