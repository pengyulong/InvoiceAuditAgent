from typing import Dict, Any, List
from sqlalchemy.orm import Session
from loguru import logger

from app.services.ai_service import AIService
from app.services.websocket_service import websocket_manager
from app.services.file_service import FileService
from app.agents.contract_analyzer import ContractAnalyzer
from app.agents.invoice_analyzer import InvoiceAnalyzer
from app.agents.cross_validator import CrossValidator
from app.models.audit import AuditTask, AuditStatus
from app.core.database import get_db

class CoordinatorAgent:
    """
    协调器Agent - 负责整个审计流程的协调和管理
    """

    def __init__(self):
        self.ai_service = AIService()
        self.contract_analyzer = ContractAnalyzer()
        self.invoice_analyzer = InvoiceAnalyzer()
        self.cross_validator = CrossValidator()
        self.file_service = FileService()

    async def coordinate_audit(self, task_id: str, audit_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        协调查计流程
        """
        db = next(get_db())

        try:
            # 获取审计任务
            task = db.query(AuditTask).filter(AuditTask.id == task_id).first()
            if not task:
                raise ValueError(f"审计任务不存在: {task_id}")

            logger.info(f"开始协调查计任务: {task_id}")

            # 阶段1: 准备和文件分类
            await self._update_progress(task_id, "准备文件", 5, "正在分类和验证文件...")
            files = self._classify_files(task_id)

            if not files.get("contracts") and not files.get("invoices"):
                raise ValueError("未找到有效的合同或发票文件")

            await self._update_progress(task_id, "文件准备完成", 10, f"发现 {len(files.get('contracts', []))} 份合同，{len(files.get('invoices', []))} 份发票")

            # 阶段2: 并行分析合同和发票
            contract_results = []
            invoice_results = []

            # 分析合同
            if files.get("contracts"):
                await self._update_progress(task_id, "分析合同", 20, "正在使用AI分析合同内容...")
                contract_results = await self.contract_analyzer.analyze_contracts(
                    files["contracts"], task_id
                )
                await self._update_progress(task_id, "合同分析完成", 40, f"成功分析 {len(contract_results)} 份合同")

            # 分析发票
            if files.get("invoices"):
                await self._update_progress(task_id, "分析发票", 50, "正在使用AI分析发票内容...")
                invoice_results = await self.invoice_analyzer.analyze_invoices(
                    files["invoices"], task_id
                )
                await self._update_progress(task_id, "发票分析完成", 70, f"成功分析 {len(invoice_results)} 份发票")

            # 阶段3: 交叉验证
            await self._update_progress(task_id, "交叉验证", 75, "正在进行合同与发票的交叉验证...")
            validation_results = await self.cross_validator.validate(
                contract_results, invoice_results, task_id
            )

            # 阶段4: 生成综合报告
            await self._update_progress(task_id, "生成报告", 90, "正在生成审计报告...")
            report = await self._generate_audit_report(
                task_id, contract_results, invoice_results, validation_results
            )

            # 更新任务状态
            task.status = AuditStatus.COMPLETED
            task.progress_percentage = 100.0
            task.current_step = "审计完成"
            task.processed_files = len(files.get("contracts", [])) + len(files.get("invoices", []))
            db.commit()

            await self._update_progress(task_id, "审计完成", 100, "审计流程已完成")

            # 发送完成通知
            await websocket_manager.send_audit_completed(task_id, report)

            logger.info(f"审计任务完成: {task_id}")
            return {
                "task_id": task_id,
                "status": "completed",
                "report": report,
                "statistics": {
                    "contracts_analyzed": len(contract_results),
                    "invoices_analyzed": len(invoice_results),
                    "issues_found": len(validation_results.get("issues", [])),
                    "total_files": task.processed_files
                }
            }

        except Exception as e:
            # 更新任务状态为失败
            if task:
                task.status = AuditStatus.FAILED
                task.error_message = str(e)
                db.commit()

            logger.error(f"审计任务失败: {task_id}, 错误: {e}")
            await websocket_manager.send_error(task_id, f"审计过程发生错误: {str(e)}")

            raise

        finally:
            db.close()

    def _classify_files(self, task_id: str) -> Dict[str, List[str]]:
        """
        分类文件：合同和发票
        """
        files = self.file_service.get_task_files(task_id)

        contracts = []
        invoices = []

        for file_info in files:
            file_type = file_info.get("file_type", "")
            file_path = file_info.get("file_path", "")

            if file_type == "contract":
                contracts.append(file_path)
            elif file_type == "invoice":
                invoices.append(file_path)

        return {
            "contracts": contracts,
            "invoices": invoices
        }

    async def _update_progress(self, task_id: str, step: str, progress: int, message: str):
        """
        更新审计进度
        """
        db = next(get_db())
        try:
            task = db.query(AuditTask).filter(AuditTask.id == task_id).first()
            if task:
                task.current_step = step
                task.progress_percentage = progress
                db.commit()

            # 发送WebSocket通知
            await websocket_manager.send_progress(task_id, {
                "step": step,
                "progress": progress,
                "message": message
            })

        finally:
            db.close()

    async def _generate_audit_report(
        self,
        task_id: str,
        contract_results: List[Dict],
        invoice_results: List[Dict],
        validation_results: Dict
    ) -> Dict[str, Any]:
        """
        生成审计报告
        """
        # 统计信息
        total_contracts = len(contract_results)
        total_invoices = len(invoice_results)

        # 计算合同总金额
        contract_total_amount = sum(
            result.get("extracted_data", {}).get("total_amount", 0)
            for result in contract_results
        )

        # 计算发票总金额
        invoice_total_amount = sum(
            result.get("extracted_data", {}).get("total_amount", 0)
            for result in invoice_results
        )

        # 获取问题统计
        issues = validation_results.get("issues", [])
        high_issues = [issue for issue in issues if issue.get("severity") == "high"]
        medium_issues = [issue for issue in issues if issue.get("severity") == "medium"]
        low_issues = [issue for issue in issues if issue.get("severity") == "low"]

        # 确定审计结论
        overall_status = validation_results.get("overall_status", "需人工复核")
        match_score = validation_results.get("match_score", 0)

        # 生成报告
        report = {
            "task_id": task_id,
            "audit_summary": {
                "overall_status": overall_status,
                "match_score": match_score,
                "contract_total_amount": contract_total_amount,
                "invoice_total_amount": invoice_total_amount,
                "amount_difference": abs(contract_total_amount - invoice_total_amount),
                "total_contracts": total_contracts,
                "total_invoices": total_invoices
            },
            "issues_summary": {
                "total_issues": len(issues),
                "high_priority": len(high_issues),
                "medium_priority": len(medium_issues),
                "low_priority": len(low_issues)
            },
            "contracts": contract_results,
            "invoices": invoice_results,
            "validation_results": validation_results,
            "recommendations": self._generate_recommendations(validation_results, issues),
            "generated_at": str(__import__('datetime').datetime.now())
        }

        return report

    def _generate_recommendations(self, validation_results: Dict, issues: List[Dict]) -> List[str]:
        """
        生成审计建议
        """
        recommendations = []

        if not issues:
            recommendations.append("未发现明显问题，合同与发票匹配良好。")
            return recommendations

        # 根据问题类型生成建议
        high_issues = [issue for issue in issues if issue.get("severity") == "high"]
        medium_issues = [issue for issue in issues if issue.get("severity") == "medium"]

        if high_issues:
            recommendations.append("发现高优先级问题，建议立即进行人工复核。")

        if medium_issues:
            recommendations.append("发现中优先级问题，建议在规定时间内完成复核。")

        # 金额差异建议
        validation_summary = validation_results.get("summary", "")
        if "金额" in validation_summary:
            recommendations.append("发现金额差异，请仔细核对合同与发票的金额明细。")

        # 匹配度建议
        match_score = validation_results.get("match_score", 0)
        if match_score < 80:
            recommendations.append("整体匹配度较低，建议进行全面人工审核。")
        elif match_score < 95:
            recommendations.append("存在部分不匹配项，建议重点复核相关内容。")

        # 重复发票建议
        for issue in issues:
            if "重复" in issue.get("description", ""):
                recommendations.append("发现重复发票，请确认是否存在重复报销。")
                break

        return recommendations