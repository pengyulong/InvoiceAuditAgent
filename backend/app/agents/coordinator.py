"""协调器Agent - 文件分类、任务编排和状态管理"""
import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.agents.base import BaseAgent, AgentError
from app.agents.contract_analyzer import ContractAnalyzer
from app.agents.invoice_analyzer import InvoiceAnalyzer
from app.agents.cross_validator import CrossValidator
from app.services.ai_service import ai_service, AIServiceError

logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """协调器Agent，负责整个审计流程的编排"""

    def __init__(self):
        super().__init__(name="coordinator", agent_type="coordinator")
        self.contract_analyzer = ContractAnalyzer()
        self.invoice_analyzer = InvoiceAnalyzer()
        self.cross_validator = CrossValidator()

    async def _execute(
        self,
        task_id: str = "",
        upload_dir: str = "uploads",
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """执行完整的审计工作流"""
        config = config or {}
        task_dir = Path(upload_dir) / task_id

        # Step 1: 文件解析和分类 (0-10%)
        await self._report_progress(5.0, "正在解析上传文件...")
        file_info = await self._classify_files(task_dir)

        contracts = file_info.get("contracts", [])
        invoices = file_info.get("invoices", [])
        await self._report_progress(10.0, f"文件分类完成: {len(contracts)}合同, {len(invoices)}发票")

        # Step 2: 并行分析合同和发票 (10-60%)
        contract_result = None
        invoice_results = []

        if contracts:
            await self._report_progress(15.0, "开始分析合同...")
            try:
                self.contract_analyzer.set_progress_callback(self._sub_agent_progress(15, 35))
                contract_result = await self.contract_analyzer.run(
                    contract_files=contracts, config=config
                )
            except AgentError as e:
                logger.warning(f"合同分析失败: {e}")
                contract_result = self._get_basic_contract_info(contracts)

        if invoices:
            await self._report_progress(35.0, f"开始分析 {len(invoices)} 张发票...")
            try:
                self.invoice_analyzer.set_progress_callback(self._sub_agent_progress(35, 60))
                invoice_results = await self.invoice_analyzer.run(
                    invoice_files=invoices, config=config
                )
            except AgentError as e:
                logger.warning(f"发票分析失败: {e}")

        await self._report_progress(60.0, "合同和发票分析完成")

        # Step 3: 交叉验证 (60-85%)
        await self._report_progress(65.0, "开始交叉验证...")
        validation_result = None

        if contract_result and invoice_results:
            try:
                self.cross_validator.set_progress_callback(self._sub_agent_progress(65, 85))
                validation_result = await self.cross_validator.run(
                    contract_info=contract_result,
                    invoice_list=invoice_results,
                    config=config,
                )
            except AgentError as e:
                logger.warning(f"交叉验证失败: {e}")
                validation_result = self._basic_validation(contract_result, invoice_results)
        else:
            validation_result = self._basic_validation(contract_result, invoice_results)

        await self._report_progress(85.0, "交叉验证完成")

        # Step 4: 汇总结果 (85-95%)
        await self._report_progress(90.0, "正在汇总审计结果...")
        report = self._build_report(task_id, contract_result, invoice_results, validation_result)

        await self._report_progress(95.0, "审计报告生成完成")

        return {
            "task_id": task_id,
            "contract_info": contract_result or {},
            "invoice_list": invoice_results if isinstance(invoice_results, list) else [],
            "validation_result": validation_result or {},
            "summary": report.get("summary", {}),
            "issues": report.get("issues", []),
            "comparisons": report.get("comparisons", []),
        }

    async def _classify_files(self, task_dir: Path) -> Dict[str, List[str]]:
        """分类文件为合同和发票"""
        result = {"contracts": [], "invoices": [], "other": []}

        if not task_dir.exists():
            logger.warning(f"任务目录不存在: {task_dir}")
            return result

        # 检查解压目录
        extracted_dir = task_dir / "extracted"
        search_dir = extracted_dir if extracted_dir.exists() else task_dir

        for file_path in search_dir.rglob("*"):
            if not file_path.is_file():
                continue
            # 跳过macOS资源分支文件和系统隐藏文件
            parts = file_path.parts
            if any(p.startswith("__MACOSX") for p in parts):
                continue
            if file_path.name.startswith("._"):
                continue
            fpath = str(file_path)
            fname = file_path.name.lower()

            if any(kw in fname for kw in ["合同", "contract", "协议", "agreement", "ht"]):
                result["contracts"].append(fpath)
            elif any(kw in fname for kw in ["发票", "invoice", "票据", "receipt", "fp"]):
                result["invoices"].append(fpath)
            elif file_path.suffix.lower() in [".pdf", ".jpg", ".jpeg", ".png"]:
                # 无法从文件名判断，默认作为发票，后续会通过回退机制分配合同
                result["invoices"].append(fpath)

        # 如果没有明确的合同文件，将第一个文件作为合同
        if not result["contracts"] and result["invoices"]:
            result["contracts"] = [result["invoices"].pop(0)]
            logger.info("未找到明确合同文件，将第一个文件作为合同")

        return result

    def _sub_agent_progress(self, base: float, ceiling: float):
        """生成子Agent的进度回调，映射到总体进度范围"""
        async def callback(name: str, progress: float, message: str):
            mapped = base + (progress / 100.0) * (ceiling - base)
            await self._report_progress(mapped, f"[{name}] {message}")
        return callback

    def _get_basic_contract_info(self, contracts: List[str]) -> Dict[str, Any]:
        """获取基础合同信息（AI不可用时的降级方案）"""
        return {
            "contract_number": "未知",
            "buyer_name": "未识别",
            "seller_name": "未识别",
            "total_amount": 0,
            "tax_rate": 0,
            "contract_date": "",
            "product_list": [],
            "confidence_score": 0.0,
            "source_files": contracts,
            "_fallback": True,
        }

    def _basic_validation(
        self, contract_info: Optional[Dict], invoice_list: List[Dict]
    ) -> Dict[str, Any]:
        """基础验证（AI不可用时的降级方案）"""
        if not contract_info:
            return {"compliance_status": "未知", "issues": [], "summary": {}}

        contract_amount = contract_info.get("total_amount", 0) or 0
        total_invoice = sum(
            inv.get("total_amount", 0) or 0
            for inv in (invoice_list if isinstance(invoice_list, list) else [])
        )

        issues = []
        if contract_amount > 0 and total_invoice > 0:
            diff = abs(contract_amount - total_invoice)
            if diff / contract_amount > 0.1:
                issues.append({
                    "type": "amount_mismatch",
                    "severity": "medium",
                    "title": "金额差异较大",
                    "description": f"合同金额 {contract_amount} 与发票总额 {total_invoice} 差异 {diff:.2f}",
                    "recommendation": "建议核实发票是否完整",
                })

        return {
            "compliance_status": "需人工复核",
            "overall_score": 0.5,
            "issues": issues,
            "summary": {
                "contract_amount": contract_amount,
                "total_invoice_amount": total_invoice,
                "coverage_rate": min(total_invoice / contract_amount * 100, 100) if contract_amount > 0 else 0,
                "issue_count": len(issues),
                "duplicate_invoices": 0,
            },
        }

    def _build_report(
        self,
        task_id: str,
        contract_info: Optional[Dict],
        invoice_list: List[Dict],
        validation_result: Optional[Dict],
    ) -> Dict[str, Any]:
        """构建审计报告"""
        contract_amount = (contract_info or {}).get("total_amount", 0) or 0
        total_invoice = sum(
            inv.get("total_amount", 0) or 0
            for inv in (invoice_list if isinstance(invoice_list, list) else [])
        )
        summary = (validation_result or {}).get("summary", {})
        issues = (validation_result or {}).get("issues", [])
        invoice_count = len(invoice_list) if isinstance(invoice_list, list) else 0

        return {
            "task_id": task_id,
            "summary": {
                "status": self._determine_status(issues),
                "contract_amount": contract_amount,
                "invoice_total": total_invoice,
                "coverage": summary.get("coverage_rate", 100) / 100,
                "issue_count": len(issues),
                "processing_time": 0,
                "confidence_score": (contract_info or {}).get("confidence_score", 0) or 0.5,
            },
            "issues": issues,
            "comparisons": summary.get("comparisons", []),
        }

    @staticmethod
    def _determine_status(issues: List[Dict]) -> str:
        has_high = any(i.get("severity") == "high" for i in issues)
        has_medium = any(i.get("severity") == "medium" for i in issues)
        if has_high:
            return "fail"
        if has_medium:
            return "warning"
        return "pass"
