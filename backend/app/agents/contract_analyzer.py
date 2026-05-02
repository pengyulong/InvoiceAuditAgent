"""合同分析Agent - 使用百度OCR+DeepSeek提取合同关键信息"""
import json
import logging
from typing import Dict, Any, List

from app.agents.base import BaseAgent, AgentError
from app.services.ai_service import ai_service, AIServiceError

logger = logging.getLogger(__name__)


class ContractAnalyzer(BaseAgent):
    """合同分析Agent，从合同图片中提取结构化信息"""

    def __init__(self):
        super().__init__(name="contract_analyzer", agent_type="contract_analyzer")

    async def _execute(
        self,
        contract_files: List[str] = None,
        config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        contract_files = contract_files or []

        if not contract_files:
            raise AgentError("没有合同文件可分析")

        all_results = []
        total = len(contract_files)

        for i, file_path in enumerate(contract_files):
            await self._report_progress(
                (i / total) * 100,
                f"分析合同 {i + 1}/{total}: {file_path}",
            )

            try:
                result = await ai_service.extract_contract_info(file_path)
                result["source_file"] = file_path
                all_results.append(result)
                logger.info(f"合同分析完成: {file_path}, 置信度={result.get('confidence_score', 0)}")
            except AIServiceError as e:
                logger.warning(f"AI合同分析失败: {file_path}, {e}")
                all_results.append(self._fallback_extract(file_path))

        merged = self._merge_results(all_results)
        await self._report_progress(100.0, f"合同分析完成, 置信度={merged.get('confidence_score', 0):.2f}")
        return merged

    def _merge_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个合同分析结果"""
        if not results:
            return {}

        if len(results) == 1:
            return results[0]

        # 取置信度最高的结果
        best = max(results, key=lambda r: r.get("confidence_score", 0) or 0)

        # 合并商品清单
        all_items = []
        seen = set()
        for r in results:
            for item in r.get("product_list", []) or []:
                key = item.get("name", "")
                if key and key not in seen:
                    seen.add(key)
                    all_items.append(item)

        best["product_list"] = all_items
        return best

    def _fallback_extract(self, file_path: str) -> Dict[str, Any]:
        """AI不可用时的降级方案"""
        return {
            "contract_number": None,
            "buyer_name": None,
            "seller_name": None,
            "contract_date": None,
            "total_amount": None,
            "tax_rate": None,
            "payment_terms": None,
            "delivery_terms": None,
            "product_list": [],
            "confidence_score": 0.0,
            "source_file": file_path,
            "_fallback": True,
        }
