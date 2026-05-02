"""发票分析Agent - 使用千问VL模型批量提取发票信息并进行重复检测"""
import json
import logging
from typing import Dict, Any, List

from app.agents.base import BaseAgent, AgentError
from app.services.ai_service import ai_service, AIServiceError

logger = logging.getLogger(__name__)


class InvoiceAnalyzer(BaseAgent):
    """发票分析Agent，批量提取发票信息并检测重复"""

    def __init__(self):
        super().__init__(name="invoice_analyzer", agent_type="invoice_analyzer")

    async def _execute(
        self,
        invoice_files: List[str] = None,
        config: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        invoice_files = invoice_files or []
        config = config or {}

        if not invoice_files:
            raise AgentError("没有发票文件可分析")

        results = []
        total = len(invoice_files)

        for i, file_path in enumerate(invoice_files):
            progress = (i / total) * 80  # 留20%给重复检测
            await self._report_progress(
                progress,
                f"分析发票 {i + 1}/{total}",
            )

            try:
                result = await ai_service.extract_invoice_info(file_path)
                result["source_file"] = file_path
                result["status"] = "normal"
                result["is_duplicate"] = False
                results.append(result)
            except AIServiceError as e:
                logger.warning(f"AI发票分析失败: {file_path}, {e}")
                results.append(self._fallback_extract(file_path))

        # 重复检测
        await self._report_progress(85.0, "正在进行重复发票检测...")
        results = self._detect_duplicates(results)

        # 计算统计
        await self._report_progress(95.0, f"发票分析完成: {len(results)}张")
        return results

    def _detect_duplicates(self, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测重复发票"""
        seen_numbers: Dict[str, int] = {}  # invoice_number -> first index
        seen_content: Dict[str, int] = {}  # content hash -> first index

        for i, inv in enumerate(invoices):
            inv_num = inv.get("invoice_number")
            if inv_num:
                if inv_num in seen_numbers:
                    inv["is_duplicate"] = True
                    inv["duplicate_of"] = seen_numbers[inv_num]
                    inv["status"] = "duplicate"
                    logger.info(f"发现重复发票(号码): {inv_num}")
                else:
                    seen_numbers[inv_num] = i

            # 基于内容的模糊匹配
            content_key = self._content_key(inv)
            if content_key and not inv.get("is_duplicate"):
                if content_key in seen_content:
                    inv["is_duplicate"] = True
                    inv["duplicate_of"] = seen_content[content_key]
                    inv["status"] = "duplicate"
                    logger.info(f"发现重复发票(内容): {inv.get('invoice_number', 'unknown')}")
                else:
                    seen_content[content_key] = i

        return invoices

    def _content_key(self, invoice: Dict[str, Any]) -> str:
        """生成发票内容指纹"""
        parts = [
            str(invoice.get("total_amount", "")),
            str(invoice.get("seller_name", "")),
            str(invoice.get("buyer_name", "")),
            str(invoice.get("invoice_date", "")),
        ]
        return "|".join(p for p in parts if p)

    def _fallback_extract(self, file_path: str) -> Dict[str, Any]:
        return {
            "invoice_number": None,
            "invoice_code": None,
            "invoice_date": None,
            "seller_name": None,
            "seller_tax_id": None,
            "buyer_name": None,
            "buyer_tax_id": None,
            "total_amount": None,
            "tax_amount": None,
            "amount_without_tax": None,
            "tax_rate": None,
            "product_list": [],
            "confidence_score": 0.0,
            "status": "error",
            "is_duplicate": False,
            "source_file": file_path,
            "_fallback": True,
        }
