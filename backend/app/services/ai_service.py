"""
AI服务模块 - 集成百度云OCR和DeepSeek API
百度云OCR负责文字提取，DeepSeek负责结构化分析和推理
"""
import asyncio
import logging
import json
import aiohttp
from typing import Dict, Any, List, Optional
from PIL import Image
import base64
import os
import tempfile
import re
import subprocess

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI服务异常"""
    pass


class PDFExtractor:
    """PDF页面提取器，将PDF转换为图片"""

    @staticmethod
    def pdf_to_image(pdf_path: str, output_path: str = None, page: int = 0) -> Optional[str]:
        """将PDF指定页面转换为图片"""
        try:
            from pypdf import PdfReader

            reader = PdfReader(pdf_path)
            if page >= len(reader.pages):
                logger.warning(f"PDF页面超出范围: {page} >= {len(reader.pages)}")
                return None

            # 获取指定页面
            pdf_page = reader.pages[page]

            # 转换为图片
            from pypdf import PdfRenderer

            renderer = PdfRenderer()
            renderer.render_page(pdf_page)

            # 使用Pillow保存
            if output_path is None:
                output_path = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name

            renderer.render_to_image().save(output_path)
            logger.info(f"PDF转换为图片成功: {pdf_path} -> {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"PDF转换失败: {pdf_path}, {e}")
            return None


class BaseAIClient:
    """AI客户端基类"""

    def __init__(self, api_key: str, api_base: str, model: str):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _make_request(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """发送API请求"""
        raise NotImplementedError("子类必须实现此方法")


class BaiduOCRClient:
    """百度云OCR客户端 - 传统AK/SK认证方式"""

    def __init__(self, api_key: str, secret_key: str, api_base: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.api_base = api_base
        self.session: Optional[aiohttp.ClientSession] = None
        self._access_token: Optional[str] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _get_access_token(self) -> str:
        """获取access_token"""
        if self._access_token:
            return self._access_token

        if not self.session:
            raise AIServiceError("会话未初始化")

        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }

        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise AIServiceError(f"获取access_token失败: {response.status} - {error_text}")

                result = await response.json()
                token = result.get("access_token")
                if not token:
                    raise AIServiceError(f"获取access_token失败: {result}")

                self._access_token = token
                logger.info("成功获取百度OCR access_token")
                return token

        except asyncio.TimeoutError:
            raise AIServiceError("获取access_token超时")
        except aiohttp.ClientError as e:
            raise AIServiceError(f"获取access_token请求错误: {e}")

    async def recognize_text(self, image_path: str, use_high_accuracy: bool = False) -> str:
        """使用百度OCR识别图片文字"""
        if not self.session:
            raise AIServiceError("会话未初始化")

        # 处理图片
        try:
            file_ext = os.path.splitext(image_path)[1].lower()
            temp_path = None

            if file_ext == '.pdf':
                # PDF文件需要先转换为图片，使用pdftoppm
                import subprocess
                temp_png = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_png.close()
                result = subprocess.run(
                    ['pdftoppm', '-png', '-singlefile', '-r', '150', image_path, temp_png.name.replace('.png', '')],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    os.unlink(temp_png.name)
                    raise AIServiceError(f"PDF转换失败: {result.stderr}")
                temp_path = temp_png.name

            if temp_path is None:
                temp_path = image_path

            with Image.open(temp_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    img.save(temp_file, format='JPEG', quality=95)
                    temp_path = temp_file.name

            with open(temp_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            os.unlink(temp_path)

        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError(f"图片处理失败: {e}")

        # 获取token并调用接口
        access_token = await self._get_access_token()
        endpoint = "accurate_basic" if use_high_accuracy else "general_basic"
        url = f"{self.api_base}/{endpoint}?access_token={access_token}"

        try:
            async with self.session.post(
                url,
                data={"image": base64_image},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"百度OCR请求失败: {response.status} - {error_text}")
                    raise AIServiceError(f"百度OCR请求失败: {response.status}")

                result = await response.json()

                # 提取文字
                if "words_result" in result:
                    return "\n".join(item.get("words", "") for item in result["words_result"])
                else:
                    logger.warning(f"百度OCR返回格式异常: {result}")
                    return ""

        except asyncio.TimeoutError:
            raise AIServiceError("百度OCR请求超时")
        except aiohttp.ClientError as e:
            raise AIServiceError(f"百度OCR请求错误: {e}")

    async def recognize_vat_invoice(self, image_path: str) -> Dict[str, Any]:
        """识别增值税发票，返回结构化结果"""
        if not self.session:
            raise AIServiceError("会话未初始化")

        temp_path = None
        try:
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext == '.pdf':
                # PDF文件需要先转换为图片，使用pdftoppm
                import subprocess
                temp_png = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                temp_png.close()
                result = subprocess.run(
                    ['pdftoppm', '-png', '-singlefile', '-r', '150', image_path, temp_png.name.replace('.png', '')],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    os.unlink(temp_png.name)
                    raise AIServiceError(f"PDF转换失败: {result.stderr}")
                temp_path = temp_png.name

            with Image.open(temp_path if temp_path else image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    img.save(temp_file, format='JPEG', quality=95)
                    temp_path = temp_file.name

            with open(temp_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            os.unlink(temp_path)
            temp_path = None  # 已删除，避免重复删除

        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError(f"图片处理失败: {e}")

        # 获取token并调用接口
        access_token = await self._get_access_token()
        url = f"{self.api_base}/vat_invoice?access_token={access_token}"

        try:
            async with self.session.post(
                url,
                data={"image": base64_image},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"百度增值税发票OCR请求失败: {response.status} - {error_text}")
                    raise AIServiceError(f"百度增值税发票OCR请求失败: {response.status}")

                return await response.json()

        except asyncio.TimeoutError:
            raise AIServiceError("百度增值税发票OCR请求超时")
        except aiohttp.ClientError as e:
            raise AIServiceError(f"百度增值税发票OCR请求错误: {e}")


class DeepSeekClient(BaseAIClient):
    """DeepSeek客户端"""

    async def _make_request(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """发送DeepSeek API请求"""
        if not self.session:
            raise AIServiceError("会话未初始化")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 4000),
            "stream": False
        }

        try:
            async with self.session.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"DeepSeek API请求失败: {response.status} - {error_text}")
                    raise AIServiceError(f"DeepSeek API请求失败: {response.status}")

                result = await response.json()
                return result

        except asyncio.TimeoutError:
            raise AIServiceError("DeepSeek API请求超时")
        except aiohttp.ClientError as e:
            raise AIServiceError(f"DeepSeek API请求错误: {e}")


class AIService:
    """AI服务主类"""

    def __init__(self):
        self.baidu_client: Optional[BaiduOCRClient] = None
        self.deepseek_client: Optional[DeepSeekClient] = None
        self._initialize_clients()

    def _initialize_clients(self):
        """初始化AI客户端"""
        if settings.baidu_ocr_api_key and settings.baidu_ocr_secret_key:
            self.baidu_client = BaiduOCRClient(
                api_key=settings.baidu_ocr_api_key,
                secret_key=settings.baidu_ocr_secret_key,
                api_base=settings.baidu_ocr_api_base
            )
            logger.info("百度OCR客户端初始化成功")
        else:
            logger.warning("百度OCR API密钥未配置")

        if settings.deepseek_api_key:
            self.deepseek_client = DeepSeekClient(
                api_key=settings.deepseek_api_key,
                api_base=settings.deepseek_api_base,
                model=settings.deepseek_model
            )
            logger.info(f"DeepSeek客户端初始化成功，模型: {settings.deepseek_model}")
        else:
            logger.warning("DeepSeek API密钥未配置")

    async def extract_contract_info(self, image_path: str) -> Dict[str, Any]:
        """从合同图片中提取信息：百度OCR文字提取 + DeepSeek结构化"""
        logger.info(f"开始提取合同信息: {image_path}")

        try:
            if not self.baidu_client:
                raise AIServiceError("百度OCR客户端未初始化")

            # Step 1: 百度OCR提取原始文字
            raw_text = await self._recognize_contract_text(image_path)

            if not raw_text.strip():
                logger.warning(f"合同图片 {image_path} 未提取到文字")

            logger.info(f"百度OCR提取文字长度: {len(raw_text)}")

            # Step 2: DeepSeek从文字中提取结构化信息
            if not self.deepseek_client:
                raise AIServiceError("DeepSeek客户端未初始化")

            prompt = f"""
请根据以下合同OCR识别的全文，提取结构化信息并以JSON格式返回。
注意：
1. OCR文本可能包含多页内容，页码标记如“第 1 页”仅用于定位，不是合同正文。
2. 合同总金额可能写作“合同价款”“含税总价”“总金额”“费用合计”“人民币”等，请提取含税总金额；如果出现大小写金额，以大写金额优先核对。
3. 商品/服务清单可能在附件、报价表或后续页，请尽量提取服务名称、数量、单价、总价。
4. 只在全文确实没有对应信息时才返回null或0。

OCR识别的文字：
---
{raw_text}
---

请提取以下字段并以JSON格式返回：
{{
    "contract_number": "合同编号（如无可填null）",
    "buyer_name": "买方名称",
    "seller_name": "卖方名称",
    "contract_date": "合同签订日期",
    "total_amount": "合同总金额（数字，如无可填0）",
    "tax_rate": "税率（如无可填null）",
    "payment_terms": "付款条件（如无可填null）",
    "delivery_terms": "交货条件（如无可填null）",
    "product_list": [
        {{
            "name": "商品名称",
            "specification": "规格型号",
            "quantity": "数量",
            "unit_price": "单价",
            "total_price": "总价"
        }}
    ],
    "confidence_score": "提取信息的置信度（0-1之间的数字）"
}}

如果某个字段无法识别，请设置为null。返回格式必须是有效的JSON。
"""

            async with self.deepseek_client:
                result = await self.deepseek_client._make_request([
                    {"role": "user", "content": prompt}
                ], max_tokens=3000)

                content = result["choices"][0]["message"]["content"]
                return self._parse_json_response(content)

        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"合同信息提取失败: {e}")
            raise AIServiceError(f"合同信息提取失败: {e}")

    async def _recognize_contract_text(self, file_path: str) -> str:
        if os.path.splitext(file_path)[1].lower() != ".pdf":
            async with self.baidu_client:
                return await self.baidu_client.recognize_text(file_path, use_high_accuracy=True)

        page_count = self._get_pdf_page_count(file_path)
        page_limit = min(page_count or 1, settings.max_contract_ocr_pages)
        logger.info(f"合同PDF页数: {page_count}, OCR页数: {page_limit}")

        texts = []
        with tempfile.TemporaryDirectory() as temp_dir:
            async with self.baidu_client:
                for page_no in range(1, page_limit + 1):
                    output_prefix = os.path.join(temp_dir, f"contract_page_{page_no}")
                    result = subprocess.run(
                        [
                            "pdftoppm",
                            "-png",
                            "-singlefile",
                            "-f",
                            str(page_no),
                            "-l",
                            str(page_no),
                            "-r",
                            "150",
                            file_path,
                            output_prefix,
                        ],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode != 0:
                        logger.warning(f"合同第 {page_no} 页转换失败: {result.stderr}")
                        continue

                    image_path = f"{output_prefix}.png"
                    if not os.path.exists(image_path):
                        logger.warning(f"合同第 {page_no} 页转换后图片不存在: {image_path}")
                        continue

                    try:
                        page_text = await self.baidu_client.recognize_text(image_path, use_high_accuracy=True)
                    except AIServiceError as e:
                        logger.warning(f"合同第 {page_no} 页OCR失败: {e}")
                        continue

                    if page_text.strip():
                        texts.append(f"【第 {page_no} 页】\n{page_text.strip()}")

        return "\n\n".join(texts)

    @staticmethod
    def _get_pdf_page_count(file_path: str) -> int:
        try:
            result = subprocess.run(
                ["pdfinfo", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return 1
            match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.MULTILINE)
            return int(match.group(1)) if match else 1
        except Exception as e:
            logger.warning(f"读取PDF页数失败: {file_path}, {e}")
            return 1

    async def extract_invoice_info(self, image_path: str) -> Dict[str, Any]:
        """从发票图片中提取信息：优先百度增值税发票OCR，失败则通用OCR+DeepSeek结构化"""
        logger.info(f"开始提取发票信息: {image_path}")

        try:
            if not self.baidu_client:
                raise AIServiceError("百度OCR客户端未初始化")

            # Step 1: 尝试百度增值税发票专用接口
            vat_result = None
            async with self.baidu_client:
                vat_result = await self.baidu_client.recognize_vat_invoice(image_path)

            # 检查增值税发票识别结果
            if vat_result and "words_result" in str(vat_result):
                # 增值税发票专用解析
                parsed = self._parse_vat_invoice_result(vat_result)
                if parsed and parsed.get("invoice_number"):
                    logger.info("使用百度增值税发票专用接口识别成功")
                    return parsed

            # Step 2: 通用文字识别 + DeepSeek结构化
            async with self.baidu_client:
                raw_text = await self.baidu_client.recognize_text(image_path, use_high_accuracy=True)

            if not raw_text.strip():
                logger.warning(f"发票图片 {image_path} 未提取到文字")

            logger.info(f"百度OCR提取文字长度: {len(raw_text)}")

            if not self.deepseek_client:
                raise AIServiceError("DeepSeek客户端未初始化")

            prompt = f"""
请根据以下发票图片OCR识别的文字，提取结构化信息并以JSON格式返回。

OCR识别的文字：
---
{raw_text}
---

请提取以下字段并以JSON格式返回：
{{
    "invoice_number": "发票号码",
    "invoice_date": "开票日期",
    "seller_name": "销售方名称",
    "seller_tax_id": "销售方纳税人识别号",
    "buyer_name": "购买方名称",
    "buyer_tax_id": "购买方纳税人识别号",
    "total_amount": "价税合计（数字）",
    "tax_amount": "税额（数字）",
    "amount_without_tax": "不含税金额（数字）",
    "tax_rate": "税率",
    "product_list": [
        {{
            "name": "商品名称",
            "specification": "规格型号",
            "unit": "单位",
            "quantity": "数量",
            "unit_price": "单价",
            "amount": "金额",
            "tax_rate": "税率",
            "tax_amount": "税额"
        }}
    ],
    "confidence_score": "提取信息的置信度（0-1之间的数字）"
}}

如果某个字段无法识别，请设置为null。返回格式必须是有效的JSON。
"""

            async with self.deepseek_client:
                result = await self.deepseek_client._make_request([
                    {"role": "user", "content": prompt}
                ], max_tokens=2000)

                content = result["choices"][0]["message"]["content"]
                return self._parse_json_response(content)

        except AIServiceError:
            raise
        except Exception as e:
            logger.error(f"发票信息提取失败: {e}")
            raise AIServiceError(f"发票信息提取失败: {e}")

    def _parse_vat_invoice_result(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析百度增值税发票识别结果"""
        try:
            if "words_result" not in result:
                return None

            wr = result["words_result"]
            return {
                "invoice_number": wr.get("invoice_num", {}).get("words", ""),
                "invoice_date": wr.get("invoice_date", {}).get("words", ""),
                "seller_name": wr.get("seller_name", {}).get("words", ""),
                "seller_tax_id": wr.get("seller_tax_id", {}).get("words", ""),
                "buyer_name": wr.get("buyer_name", {}).get("words", ""),
                "buyer_tax_id": wr.get("buyer_tax_id", {}).get("words", ""),
                "total_amount": self._parse_amount(wr.get("total_amount", {}).get("words", "0")),
                "tax_amount": self._parse_amount(wr.get("tax_amount", {}).get("words", "0")),
                "amount_without_tax": self._parse_amount(wr.get("total_ex_tax", {}).get("words", "0")),
                "tax_rate": self._parse_rate(wr.get("tax_rate", {}).get("words", "")),
                "confidence_score": 0.9,
                "_source": "vat_invoice_api"
            }
        except Exception as e:
            logger.warning(f"增值税发票解析失败: {e}")
            return None

    def _parse_amount(self, text: str) -> float:
        """解析金额字符串"""
        if not text:
            return 0.0
        text = text.replace(",", "").replace("¥", "").replace("￥", "").strip()
        try:
            return float(text)
        except ValueError:
            return 0.0

    def _parse_rate(self, text: str) -> Optional[float]:
        """解析税率字符串"""
        if not text:
            return None
        text = text.strip()
        if text.endswith("%"):
            try:
                return float(text.replace("%", "")) / 100
            except ValueError:
                return None
        try:
            rate = float(text)
            return rate if rate < 1 else rate / 100
        except ValueError:
            return None

    async def analyze_contract_compliance(self, contract_info: Dict[str, Any], invoice_info_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析合同合规性"""
        logger.info("开始分析合同合规性")

        prompt = f"""
请分析以下合同和发票信息的合规性，找出可能的问题和差异：

合同信息：
{json.dumps(contract_info, ensure_ascii=False, indent=2)}

发票列表：
{json.dumps(invoice_info_list, ensure_ascii=False, indent=2)}

请分析以下方面：
1. 发票是否与合同匹配（合同编号、买卖方信息）
2. 发票总金额是否超过合同金额
3. 商品清单是否与合同一致
4. 税率是否正确
5. 是否存在重复发票
6. 其他潜在问题

请以JSON格式返回分析结果：
{{
    "compliance_status": "合规/不合规/部分合规",
    "overall_score": "总体评分（0-1之间的数字）",
    "issues": [
        {{
            "type": "问题类型",
            "severity": "严重程度（high/medium/low）",
            "title": "问题标题",
            "description": "详细描述",
            "affected_invoices": ["受影响的发票号码"]
        }}
    ],
    "summary": {{
        "contract_amount": "合同金额",
        "total_invoice_amount": "发票总金额",
        "coverage_rate": "覆盖率",
        "issue_count": "问题数量",
        "duplicate_invoices": "重复发票数量"
    }}
}}
"""

        try:
            if self.deepseek_client:
                async with self.deepseek_client:
                    result = await self.deepseek_client._make_request([
                        {"role": "user", "content": prompt}
                    ])

                    content = result["choices"][0]["message"]["content"]
                    return self._parse_json_response(content)
            else:
                raise AIServiceError("DeepSeek客户端未初始化")

        except Exception as e:
            logger.error(f"合同合规性分析失败: {e}")
            raise AIServiceError(f"合同合规性分析失败: {e}")

    async def generate_audit_report(self, audit_data: Dict[str, Any]) -> str:
        """生成审计报告"""
        logger.info("开始生成审计报告")

        prompt = f"""
基于以下审计数据，生成一份详细的审计报告：

{json.dumps(audit_data, ensure_ascii=False, indent=2)}

报告应包含以下部分：
1. 执行摘要
2. 审计范围和方法
3. 合同信息分析
4. 发票信息分析
5. 问题和发现
6. 风险评估
7. 建议和改进措施
8. 结论

请使用专业、正式的语言，确保报告结构清晰、内容详实。
"""

        try:
            if self.deepseek_client:
                async with self.deepseek_client:
                    result = await self.deepseek_client._make_request([
                        {"role": "user", "content": prompt}
                    ])

                    return result["choices"][0]["message"]["content"]
            else:
                raise AIServiceError("DeepSeek客户端未初始化")

        except Exception as e:
            logger.error(f"审计报告生成失败: {e}")
            raise AIServiceError(f"审计报告生成失败: {e}")

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")
                    raise AIServiceError(f"AI返回的JSON格式无效: {e}")
            else:
                logger.error(f"响应中未找到JSON格式: {response}")
                raise AIServiceError("AI返回的内容中未找到有效的JSON格式")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            "baidu_ocr_available": False,
            "deepseek_available": False,
            "total_clients": 0
        }

        # 检查百度OCR
        if self.baidu_client and settings.baidu_ocr_api_key:
            try:
                async with self.baidu_client:
                    await self.baidu_client._get_access_token()
                status["baidu_ocr_available"] = True
                logger.info("百度OCR API连接正常")
            except Exception as e:
                logger.error(f"百度OCR API连接失败: {e}")

        # 检查DeepSeek
        if self.deepseek_client and settings.deepseek_api_key:
            try:
                async with self.deepseek_client:
                    await self.deepseek_client._make_request([
                        {"role": "user", "content": "测试"}
                    ], max_tokens=10)
                status["deepseek_available"] = True
                logger.info("DeepSeek API连接正常")
            except Exception as e:
                logger.error(f"DeepSeek API连接失败: {e}")

        status["total_clients"] = sum([
            status["baidu_ocr_available"],
            status["deepseek_available"]
        ])

        return status


# 创建全局AI服务实例
ai_service = AIService()
