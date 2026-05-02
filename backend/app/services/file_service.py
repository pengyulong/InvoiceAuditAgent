import os
import uuid
# import python_magic  # 暂时移除以避免依赖问题
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class FileService:
    """文件处理服务"""

    def __init__(self):
        self.supported_image_types = {
            'application/pdf': 'PDF',
            'image/jpeg': 'JPEG',
            'image/jpg': 'JPG',
            'image/png': 'PNG'
        }

    async def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """
        分析文件并返回基本信息

        Args:
            file_path: 文件路径

        Returns:
            文件信息字典
        """
        try:
            file_info = {
                "id": str(uuid.uuid4()),
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "path": str(file_path),
                "type": await self._get_file_type(file_path),
                "category": await self._categorize_file(file_path),
                "created_at": file_path.stat().st_ctime,
                "modified_at": file_path.stat().st_mtime
            }

            # 如果是图像文件，尝试获取更多元数据
            if file_info["category"] in ["contract", "invoice"]:
                file_info.update(await self._get_image_metadata(file_path))

            return file_info

        except Exception as e:
            logger.error(f"分析文件失败: {file_path}, error: {e}")
            raise

    async def _get_file_type(self, file_path: Path) -> str:
        """获取文件MIME类型（优先通过文件头magic bytes检测）"""
        try:
            extension = file_path.suffix.lower()

            # 通过文件头magic bytes验证
            with open(file_path, "rb") as f:
                header = f.read(8)

            # PDF: %PDF-
            if header[:5] == b"%PDF-":
                return "application/pdf"
            # PNG: 89 50 4E 47
            if header[:4] == b"\x89PNG":
                return "image/png"
            # JPEG: FF D8 FF
            if header[:3] == b"\xff\xd8\xff":
                return "image/jpeg"
            # ZIP/PK: 50 4B 03 04
            if header[:4] == b"PK\x03\x04":
                return "application/zip"

            # 回退到扩展名判断
            ext_map = {
                ".pdf": "application/pdf",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".zip": "application/zip",
            }
            return ext_map.get(extension, "application/octet-stream")
        except Exception as e:
            logger.warning(f"无法获取文件类型: {file_path}, error: {e}")
            return "application/octet-stream"

    async def _categorize_file(self, file_path: Path) -> str:
        """
        根据文件名、类型和内容对文件进行分类

        Returns:
            'contract', 'invoice', 'other'
        """
        file_name = file_path.name.lower()
        file_type = await self._get_file_type(file_path)

        # 根据文件名推断合同
        if any(keyword in file_name for keyword in ['合同', 'contract', '协议', 'agreement', 'ht']):
            return 'contract'
        # 根据文件名推断发票
        if any(keyword in file_name for keyword in ['发票', 'invoice', '票据', 'receipt', 'fp', '收据']):
            return 'invoice'

        # 文件名无法判断时，尝试内容识别
        if file_type in self.supported_image_types:
            content_category = await self._categorize_by_content(file_path, file_type)
            if content_category:
                return content_category
            # 内容也无法判断，默认作为发票
            return 'invoice'

        return 'other'

    async def _categorize_by_content(self, file_path: Path, file_type: str) -> Optional[str]:
        """通过内容识别文件类型（第一页OCR关键词匹配）"""
        try:
            text = ""
            if file_type == 'application/pdf':
                # 使用pypdf提取第一页文字
                from pypdf import PdfReader
                reader = PdfReader(str(file_path))
                if len(reader.pages) > 0:
                    text = reader.pages[0].extract_text() or ""
            # 对于图片文件暂不进行OCR（耗时较长，交给审计流程处理）
            # 留作后续优化点：集成快速OCR

            if not text or not text.strip():
                return None

            text_lower = text.lower()

            # 合同关键词：甲方乙方、条款、协议等
            contract_keywords = ['甲方', '乙方', '合同', '条款', '协议', '签署', '签订', '甲 方', '乙 方']
            invoice_keywords = ['发票', '发票代码', '发票号码', '价税合计', '销售方', '购买方', '开票日期']

            contract_score = sum(1 for kw in contract_keywords if kw in text)
            invoice_score = sum(1 for kw in invoice_keywords if kw in text)

            if contract_score > invoice_score and contract_score >= 2:
                logger.info(f"内容识别为合同: {file_path.name} (合同分={contract_score}, 发票分={invoice_score})")
                return 'contract'
            elif invoice_score > contract_score and invoice_score >= 2:
                logger.info(f"内容识别为发票: {file_path.name} (合同分={contract_score}, 发票分={invoice_score})")
                return 'invoice'

            return None

        except Exception as e:
            logger.debug(f"内容识别失败: {file_path.name}, {e}")
            return None

    async def _get_image_metadata(self, file_path: Path) -> Dict[str, Any]:
        """获取图像文件的元数据"""
        try:
            file_type = await self._get_file_type(file_path)

            metadata = {}

            if file_type == 'application/pdf':
                metadata = await self._get_pdf_metadata(file_path)
            elif file_type.startswith('image/'):
                metadata = await self._get_image_basic_metadata(file_path)
            elif file_type == 'text/plain':
                # 处理文本文件
                metadata = await self._get_text_metadata(file_path)
            elif file_type == 'application/zip':
                # 处理ZIP文件
                metadata = {
                    "format": "ZIP",
                    "entries": "unknown"
                }

            return metadata

        except Exception as e:
            logger.warning(f"获取图像元数据失败: {file_path}, error: {e}")
            return {}

    async def _get_pdf_metadata(self, file_path: Path) -> Dict[str, Any]:
        """获取PDF文件的元数据"""
        try:
            # 这里可以使用PyPDF2或其他PDF库来获取更多元数据
            # 目前返回基本信息
            return {
                "pages": "unknown",  # 需要PDF库支持
                "format": "PDF",
                "readable": True
            }
        except Exception:
            return {}

    async def _get_text_metadata(self, file_path: Path) -> Dict[str, Any]:
        """获取文本文件的元数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "format": "TEXT",
                "size": len(content),
                "lines": len(content.split('\n')),
                "readable": True
            }
        except Exception as e:
            logger.warning(f"读取文本文件失败: {file_path}, error: {e}")
            return {
                "format": "TEXT",
                "readable": False
            }

    async def _get_image_basic_metadata(self, file_path: Path) -> Dict[str, Any]:
        """获取图像文件的基本元数据"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                return {
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "size": img.size  # (width, height)
                }
        except Exception:
            return {}

    def is_supported_file(self, file_path: Path) -> bool:
        """检查文件类型是否支持"""
        return file_path.suffix.lower() in ['.pdf', '.jpg', '.jpeg', '.png', '.zip']

    def validate_file_size(self, file_size: int) -> bool:
        """验证文件大小是否在限制范围内"""
        return file_size <= settings.max_file_size

    async def save_uploaded_file(self, file_content: bytes, filename: str, category: str = "general") -> str:
        """
        保存上传的文件

        Args:
            file_content: 文件内容
            filename: 文件名
            category: 文件分类

        Returns:
            保存的文件路径
        """
        try:
            # 生成唯一文件名
            file_id = str(uuid.uuid4())
            file_extension = Path(filename).suffix
            safe_filename = f"{file_id}{file_extension}"

            # 创建目标目录
            target_dir = Path(settings.upload_dir) / category
            target_dir.mkdir(parents=True, exist_ok=True)

            # 保存文件
            file_path = target_dir / safe_filename
            with open(file_path, "wb") as f:
                f.write(file_content)

            logger.info(f"文件保存成功: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"保存文件失败: {filename}, error: {e}")
            raise

    async def delete_file(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            是否删除成功
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"文件删除成功: {file_path}")
                return True
            else:
                logger.warning(f"文件不存在: {file_path}")
                return False
        except Exception as e:
            logger.error(f"删除文件失败: {file_path}, error: {e}")
            return False

    def get_file_size_mb(self, file_path: Path) -> float:
        """获取文件大小（MB）"""
        try:
            size_bytes = file_path.stat().st_size
            return size_bytes / (1024 * 1024)
        except Exception:
            return 0.0