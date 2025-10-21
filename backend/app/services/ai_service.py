import httpx
import base64
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

from app.core.config import settings

class AIService:
    """
    AI模型服务封装类
    """

    def __init__(self):
        self.qwen_client = httpx.AsyncClient(
            base_url=settings.QWEN_API_BASE,
            headers={"Authorization": f"Bearer {settings.QWEN_API_KEY}"}
        )
        self.deepseek_client = httpx.AsyncClient(
            base_url=settings.DEEPSEEK_API_BASE,
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"}
        )

    async def analyze_contract_image(self, image_path: str) -> Dict[str, Any]:
        """
        使用qwen3-vl分析合同图像
        """
        try:
            # 读取并编码图像
            image_data = self._encode_image(image_path)

            # 构建分析prompt
            prompt = self._get_contract_analysis_prompt()

            response = await self.qwen_client.post(
                "/chat/completions",
                json={
                    "model": settings.QWEN_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                timeout=60.0
            )

            response.raise_for_status()
            result = response.json()

            # 解析AI响应
            content = result["choices"][0]["message"]["content"]
            parsed_result = self._parse_contract_response(content)

            return {
                "success": True,
                "extracted_data": parsed_result,
                "raw_response": content,
                "confidence": self._calculate_confidence(parsed_result)
            }

        except Exception as e:
            logger.error(f"合同图像分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_data": {}
            }

    async def analyze_invoice_image(self, image_path: str) -> Dict[str, Any]:
        """
        使用qwen3-vl分析发票图像
        """
        try:
            # 读取并编码图像
            image_data = self._encode_image(image_path)

            # 构建分析prompt
            prompt = self._get_invoice_analysis_prompt()

            response = await self.qwen_client.post(
                "/chat/completions",
                json={
                    "model": settings.QWEN_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                timeout=60.0
            )

            response.raise_for_status()
            result = response.json()

            # 解析AI响应
            content = result["choices"][0]["message"]["content"]
            parsed_result = self._parse_invoice_response(content)

            return {
                "success": True,
                "extracted_data": parsed_result,
                "raw_response": content,
                "confidence": self._calculate_confidence(parsed_result)
            }

        except Exception as e:
            logger.error(f"发票图像分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "extracted_data": {}
            }

    async def validate_with_llm(self, validation_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用DeepSeek进行逻辑验证
        """
        try:
            prompt = self._get_validation_prompt(validation_request)

            response = await self.deepseek_client.post(
                "/chat/completions",
                json={
                    "model": settings.DEEPSEEK_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1500
                },
                timeout=60.0
            )

            response.raise_for_status()
            result = response.json()

            content = result["choices"][0]["message"]["content"]
            parsed_result = self._parse_validation_response(content)

            return {
                "success": True,
                "validation_result": parsed_result,
                "raw_response": content
            }

        except Exception as e:
            logger.error(f"LLM验证失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "validation_result": {}
            }

    def _encode_image(self, image_path: str) -> str:
        """
        将图像文件编码为base64
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _get_contract_analysis_prompt(self) -> str:
        """
        获取合同分析的prompt
        """
        return """
请分析这份合同图像，提取以下关键信息并以JSON格式返回：

{
    "contract_number": "合同编号",
    "buyer_name": "买方名称",
    "seller_name": "卖方名称",
    "total_amount": 合同总金额(数字),
    "tax_rate": 税率(数字，如0.13表示13%),
    "contract_date": "合同日期(YYYY-MM-DD)",
    "items": [
        {
            "item_name": "商品名称",
            "specification": "规格型号",
            "quantity": 数量(数字),
            "unit_price": 单价(数字),
            "total_price": 总价(数字)
        }
    ]
}

注意：
1. 如果某个字段无法识别，请用null表示
2. 金额和数量字段请返回数字类型
3. 日期格式请使用YYYY-MM-DD
4. 请确保JSON格式正确
"""

    def _get_invoice_analysis_prompt(self) -> str:
        """
        获取发票分析的prompt
        """
        return """
请分析这张发票图像，提取以下关键信息并以JSON格式返回：

{
    "invoice_code": "发票代码",
    "invoice_number": "发票号码",
    "buyer_name": "买方名称",
    "seller_name": "卖方名称",
    "total_amount": 发票总金额(数字),
    "tax_amount": 税额(数字),
    "invoice_date": "发票日期(YYYY-MM-DD)",
    "items": [
        {
            "item_name": "商品名称",
            "specification": "规格型号",
            "quantity": 数量(数字),
            "unit_price": 单价(数字),
            "total_price": 金额(数字),
            "tax_rate": 税率(数字)"
        }
    ]
}

注意：
1. 如果某个字段无法识别，请用null表示
2. 金额和数量字段请返回数字类型
3. 日期格式请使用YYYY-MM-DD
4. 请确保JSON格式正确
"""

    def _get_validation_prompt(self, validation_request: Dict[str, Any]) -> str:
        """
        获取验证逻辑的prompt
        """
        contract_data = validation_request.get("contract_data", {})
        invoices_data = validation_request.get("invoices_data", [])

        prompt = f"""
请验证以下合同和发票数据的一致性，返回验证结果：

合同信息：
{json.dumps(contract_data, ensure_ascii=False, indent=2)}

发票信息：
{json.dumps(invoices_data, ensure_ascii=False, indent=2)}

请从以下几个方面进行验证：
1. 合同编号匹配
2. 买卖双方信息一致性
3. 商品清单匹配度
4. 金额一致性检查
5. 税率一致性检查

请返回JSON格式的验证结果：
{{
    "overall_status": "通过/不通过/需人工复核",
    "match_score": 匹配分数(0-100),
    "issues": [
        {{
            "type": "错误类型",
            "severity": "high/medium/low",
            "description": "问题描述",
            "affected_items": ["受影响的项目"]
        }}
    ],
    "summary": "验证摘要"
}}
"""

        return prompt

    def _parse_contract_response(self, content: str) -> Dict[str, Any]:
        """
        解析合同分析响应
        """
        try:
            # 尝试直接解析JSON
            if content.strip().startswith('{'):
                return json.loads(content)

            # 如果不是纯JSON，尝试提取JSON部分
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)

            # 如果无法解析，返回空字典
            logger.warning(f"无法解析合同分析响应: {content}")
            return {}

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return {}

    def _parse_invoice_response(self, content: str) -> Dict[str, Any]:
        """
        解析发票分析响应
        """
        try:
            # 尝试直接解析JSON
            if content.strip().startswith('{'):
                return json.loads(content)

            # 如果不是纯JSON，尝试提取JSON部分
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)

            # 如果无法解析，返回空字典
            logger.warning(f"无法解析发票分析响应: {content}")
            return {}

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return {}

    def _parse_validation_response(self, content: str) -> Dict[str, Any]:
        """
        解析验证响应
        """
        try:
            # 尝试直接解析JSON
            if content.strip().startswith('{'):
                return json.loads(content)

            # 如果不是纯JSON，尝试提取JSON部分
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                return json.loads(json_str)

            # 如果无法解析，返回默认结果
            logger.warning(f"无法解析验证响应: {content}")
            return {
                "overall_status": "需人工复核",
                "match_score": 0,
                "issues": [],
                "summary": "AI验证结果解析失败，需要人工复核"
            }

        except json.JSONDecodeError as e:
            logger.error(f"验证响应JSON解析错误: {e}")
            return {
                "overall_status": "需人工复核",
                "match_score": 0,
                "issues": [],
                "summary": "验证结果解析失败"
            }

    def _calculate_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """
        计算提取结果的置信度
        """
        if not extracted_data:
            return 0.0

        # 统计非空字段数量
        total_fields = 0
        non_null_fields = 0

        key_fields = ["contract_number", "buyer_name", "seller_name", "total_amount"]

        for field in key_fields:
            total_fields += 1
            if field in extracted_data and extracted_data[field] is not None:
                non_null_fields += 1

        # 计算基础置信度
        if total_fields == 0:
            return 0.0

        base_confidence = (non_null_fields / total_fields) * 100

        # 如果有商品信息，额外加分
        if "items" in extracted_data and extracted_data["items"]:
            base_confidence = min(base_confidence + 10, 100)

        return round(base_confidence, 2)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.qwen_client.aclose()
        await self.deepseek_client.aclose()