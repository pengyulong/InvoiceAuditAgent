import os
import uuid
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.contract import Contract
from app.models.invoice import Invoice

class FileService:
    """
    文件处理服务
    """

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)

    async def save_uploaded_file(
        self,
        file: UploadFile,
        task_id: str,
        subfolder: str = ""
    ) -> str:
        """
        保存上传的文件
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"💾 开始保存文件: filename={file.filename}, task_id={task_id}")

        # 创建任务目录
        task_dir = self.upload_dir / task_id
        if subfolder:
            task_dir = task_dir / subfolder
        task_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 任务目录创建成功: {task_dir}")

        # 生成唯一文件名
        file_ext = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = task_dir / unique_filename
        logger.info(f"📝 文件路径: {file_path}")

        # 保存文件
        try:
            logger.info("📖 开始读取文件内容...")
            content = await file.read()
            logger.info(f"✅ 文件内容读取完成: {len(content)} bytes")

            logger.info("💽 开始写入文件...")
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            logger.info(f"✅ 文件保存成功: {file_path}")

        except Exception as e:
            logger.error(f"❌ 文件保存失败: {str(e)}")
            raise

        return str(file_path)

    async def extract_zip_file(self, zip_path: str, task_id: str) -> List[Dict[str, Any]]:
        """
        解压ZIP文件并返回文件列表
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"📦 开始解压ZIP文件: zip_path={zip_path}, task_id={task_id}")
        extracted_files = []
        task_dir = self.upload_dir / task_id

        try:
            logger.info("🔍 检查ZIP文件...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.infolist()
                logger.info(f"📋 ZIP文件包含 {len(file_list)} 个条目")

                for i, file_info in enumerate(file_list):
                    logger.info(f"📄 处理文件 {i+1}/{len(file_list)}: {file_info.filename}")

                    if file_info.is_dir():
                        logger.info(f"📁 跳过目录: {file_info.filename}")
                        continue

                    # 跳过隐藏文件和系统文件
                    if file_info.filename.startswith(('.', '__MACOSX/')):
                        logger.info(f"🚫 跳过系统文件: {file_info.filename}")
                        continue

                    # 检查文件类型
                    file_ext = Path(file_info.filename).suffix.lower()
                    if file_ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
                        logger.info(f"🚫 跳过不支持的文件类型: {file_info.filename} ({file_ext})")
                        continue

                    # 解压文件
                    logger.info(f"📤 解压文件: {file_info.filename}")
                    extracted_path = zip_ref.extract(file_info.filename, task_dir)
                    logger.info(f"✅ 文件解压成功: {extracted_path}")

                    # 确定文件类型
                    file_type = self._determine_file_type(file_info.filename)
                    logger.info(f"📋 文件类型识别: {file_info.filename} -> {file_type}")

                    extracted_files.append({
                        "file_name": os.path.basename(file_info.filename),
                        "file_path": extracted_path,
                        "file_size": file_info.file_size,
                        "file_type": file_type,
                        "file_ext": file_ext
                    })

            # 删除ZIP文件
            logger.info("🗑️ 删除ZIP文件...")
            os.remove(zip_path)
            logger.info(f"✅ ZIP文件删除成功: {zip_path}")

            logger.info(f"🎉 文件解压完成: 提取了 {len(extracted_files)} 个有效文件")
            return extracted_files

        except Exception as e:
            logger.error(f"❌ ZIP文件解压失败: {str(e)}")
            raise

    def _determine_file_type(self, filename: str) -> str:
        """
        根据文件名智能确定文件类型（合同或发票）
        """
        filename_lower = filename.lower()

        # 发票关键词（更全面和精确）
        invoice_keywords = [
            '发票', 'invoice', '票据', 'bill',
            '增值税发票', '专用发票', '普通发票', '电子发票',
            '采购发票', '销售发票', '服务发票', '货物发票',
            'tax invoice', 'vat invoice', 'receipt'
        ]

        # 合同关键词
        contract_keywords = [
            '合同', '协议', 'contract', 'agreement',
            '采购合同', '销售合同', '服务合同', '供货合同',
            '合作协议', '供货协议', '采购协议', '框架协议',
            '采购订单', '订购单', '订单', 'order'
        ]

        # 计算匹配分数
        invoice_score = 0
        contract_score = 0

        # 检查发票关键词
        for keyword in invoice_keywords:
            if keyword in filename_lower:
                # 发票特征词权重更高
                if '发票' in keyword or 'invoice' in keyword:
                    invoice_score += 3
                else:
                    invoice_score += 2

        # 检查合同关键词
        for keyword in contract_keywords:
            if keyword in filename_lower:
                # 合同特征词权重
                if '合同' in keyword or 'contract' in keyword:
                    contract_score += 3
                else:
                    contract_score += 2

        # 特殊模式识别
        # 识别发票编号模式（如：AP00013863_3582357）
        import re
        invoice_pattern = r'(ap|inv|fp)\d{6,}_\d{3,}'
        if re.search(invoice_pattern, filename_lower):
            invoice_score += 5

        # 识别合同编号模式（如：CT20230001）
        contract_pattern = r'(ct|cont|agr)\d{6,}'
        if re.search(contract_pattern, filename_lower):
            contract_score += 4

        # 决策逻辑
        if invoice_score > contract_score:
            return 'invoice'
        elif contract_score > invoice_score:
            return 'contract'
        else:
            # 如果分数相同，进行更细致的分析
            # 检查文件名中是否包含金额相关信息
            amount_indicators = ['金额', 'amount', '总价', 'price']
            for indicator in amount_indicators:
                if indicator in filename_lower:
                    # 如果有金额信息但前面没有明确类型，倾向于发票
                    if invoice_score == 0 and contract_score == 0:
                        return 'invoice'

            # 检查文件名长度和复杂度
            # 发票文件名通常较长且包含编号信息
            if len(filename) > 20 and any(char.isdigit() for char in filename):
                return 'invoice'

            # 默认情况下，如果无法确定，返回'contract'
            return 'contract'

    def get_task_files(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取任务下的所有文件
        """
        task_dir = self.upload_dir / task_id
        files = []

        if not task_dir.exists():
            return files

        for root, dirs, filenames in os.walk(task_dir):
            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.is_file():
                    file_type = self._determine_file_type(filename)
                    files.append({
                        "file_name": filename,
                        "file_path": str(file_path),
                        "file_size": file_path.stat().st_size,
                        "file_type": file_type,
                        "relative_path": str(file_path.relative_to(task_dir))
                    })

        return files

    def delete_task_files(self, task_id: str):
        """
        删除任务相关的所有文件
        """
        task_dir = self.upload_dir / task_id
        if task_dir.exists():
            shutil.rmtree(task_dir)

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        验证文件是否有效
        """
        path = Path(file_path)

        if not path.exists():
            return {"valid": False, "error": "文件不存在"}

        if not path.is_file():
            return {"valid": False, "error": "不是有效的文件"}

        # 检查文件大小
        file_size = path.stat().st_size
        if file_size > settings.MAX_FILE_SIZE:
            return {
                "valid": False,
                "error": f"文件大小超过限制 ({settings.MAX_FILE_SIZE} bytes)"
            }

        # 检查文件扩展名
        file_ext = path.suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            return {
                "valid": False,
                "error": f"不支持的文件类型: {file_ext}"
            }

        return {
            "valid": True,
            "file_size": file_size,
            "file_ext": file_ext
        }

    async def save_extracted_files_to_db(
        self,
        task_id: str,
        extracted_files: List[Dict[str, Any]],
        db: Session
    ):
        """
        将解压的文件信息保存到数据库
        """
        for file_info in extracted_files:
            file_type = file_info["file_type"]

            if file_type == "contract":
                contract = Contract(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    file_name=file_info["file_name"],
                    file_path=file_info["file_path"],
                    file_size=file_info["file_size"]
                )
                db.add(contract)

            elif file_type == "invoice":
                invoice = Invoice(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    file_name=file_info["file_name"],
                    file_path=file_info["file_path"],
                    file_size=file_info["file_size"]
                )
                db.add(invoice)

        db.commit()