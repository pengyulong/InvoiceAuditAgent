from typing import Dict, Any, List
from sqlalchemy.orm import Session
from loguru import logger

from app.services.ai_service import AIService
from app.services.websocket_service import websocket_manager
from app.models.invoice import Invoice, InvoiceItem
from app.core.database import get_db
import uuid

class InvoiceAnalyzer:
    """
    发票分析Agent - 负责分析发票文件并提取关键信息
    """

    def __init__(self):
        self.ai_service = AIService()

    async def analyze_invoices(self, invoice_files: List[str], task_id: str) -> List[Dict[str, Any]]:
        """
        分析发票文件列表
        """
        results = []
        db = next(get_db())

        try:
            # 第一轮：分析所有发票
            for i, file_path in enumerate(invoice_files):
                try:
                    logger.info(f"分析发票文件 {i+1}/{len(invoice_files)}: {file_path}")

                    # 发送进度通知
                    await websocket_manager.send_progress(task_id, {
                        "step": "分析发票",
                        "progress": 50 + (i * 20 / len(invoice_files)),
                        "message": f"正在分析发票 {i+1}/{len(invoice_files)}"
                    })

                    # 分析单个发票
                    result = await self._analyze_single_invoice(file_path, task_id, db)
                    results.append(result)

                    # 保存到数据库
                    await self._save_invoice_to_db(result, task_id, db)

                    # 发送文件处理完成通知
                    await websocket_manager.send_file_processed(task_id, {
                        "file_type": "invoice",
                        "file_path": file_path,
                        "status": "completed",
                        "extracted_data": result.get("extracted_data", {})
                    })

                except Exception as e:
                    logger.error(f"分析发票文件失败 {file_path}: {e}")
                    results.append({
                        "file_path": file_path,
                        "success": False,
                        "error": str(e),
                        "extracted_data": {}
                    })

            # 第二轮：检测重复发票
            await self._detect_duplicate_invoices(results, task_id)

        finally:
            db.close()

        return results

    async def _analyze_single_invoice(self, file_path: str, task_id: str, db: Session) -> Dict[str, Any]:
        """
        分析单个发票文件
        """
        # 使用AI分析发票图像
        analysis_result = await self.ai_service.analyze_invoice_image(file_path)

        if not analysis_result.get("success"):
            return {
                "file_path": file_path,
                "success": False,
                "error": analysis_result.get("error", "AI分析失败"),
                "extracted_data": {}
            }

        extracted_data = analysis_result.get("extracted_data", {})
        confidence_score = analysis_result.get("confidence", 0)

        # 进行发票验证
        validation_result = await self._validate_invoice(extracted_data)

        return {
            "file_path": file_path,
            "success": True,
            "extracted_data": extracted_data,
            "confidence_score": confidence_score,
            "validation_result": validation_result,
            "raw_response": analysis_result.get("raw_response", "")
        }

    async def _validate_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证发票数据的合理性
        """
        validation_errors = []
        warnings = []

        # 检查必要字段
        required_fields = ["invoice_number", "buyer_name", "seller_name", "total_amount"]
        for field in required_fields:
            if not invoice_data.get(field):
                validation_errors.append(f"缺少必要字段: {field}")

        # 检查发票号码格式
        invoice_number = invoice_data.get("invoice_number")
        if invoice_number:
            if len(str(invoice_number)) < 8:
                warnings.append("发票号码长度可能不足")

        # 检查金额合理性
        total_amount = invoice_data.get("total_amount")
        tax_amount = invoice_data.get("tax_amount")

        if total_amount is not None:
            if total_amount <= 0:
                validation_errors.append("发票总金额应大于0")
            elif total_amount > 1000000:  # 100万
                warnings.append("发票金额较大，建议复核")

        if tax_amount is not None:
            if tax_amount < 0:
                validation_errors.append("税额不能为负数")
            elif total_amount and tax_amount > total_amount:
                validation_errors.append("税额不应大于总金额")

        # 检查商品清单
        items = invoice_data.get("items", [])
        if not items:
            warnings.append("未发现商品清单信息")
        else:
            # 验证商品项目
            for i, item in enumerate(items):
                if not item.get("item_name"):
                    validation_errors.append(f"商品第{i+1}项缺少名称")

                if item.get("quantity", 0) <= 0:
                    validation_errors.append(f"商品第{i+1}项数量应大于0")

                if item.get("unit_price", 0) <= 0:
                    validation_errors.append(f"商品第{i+1}项单价应大于0")

                # 检查金额计算
                quantity = item.get("quantity", 0)
                unit_price = item.get("unit_price", 0)
                total_price = item.get("total_price", 0)
                calculated_total = quantity * unit_price

                if abs(total_price - calculated_total) > 0.01:  # 允许1分钱误差
                    validation_errors.append(f"商品第{i+1}项金额计算错误: {quantity} × {unit_price} ≠ {total_price}")

        # 计算总金额验证
        if items and total_amount is not None:
            calculated_total = sum(item.get("total_price", 0) for item in items)
            if abs(total_amount - calculated_total) > 0.01:
                validation_errors.append(f"发票总金额计算错误: 商品总额 {calculated_total} ≠ 总金额 {total_amount}")

        # 确定验证状态
        if validation_errors:
            validation_status = "error"
        elif warnings:
            validation_status = "warning"
        else:
            validation_status = "passed"

        return {
            "validation_status": validation_status,
            "validation_errors": validation_errors,
            "warnings": warnings,
            "error_count": len(validation_errors),
            "warning_count": len(warnings)
        }

    async def _detect_duplicate_invoices(self, invoice_results: List[Dict[str, Any]], task_id: str):
        """
        检测重复发票
        """
        logger.info("开始检测重复发票")

        # 提取所有成功的发票号码
        invoice_numbers = {}
        for result in invoice_results:
            if result.get("success"):
                extracted_data = result.get("extracted_data", {})
                invoice_number = extracted_data.get("invoice_number")
                file_path = result.get("file_path")

                if invoice_number:
                    if invoice_number not in invoice_numbers:
                        invoice_numbers[invoice_number] = []
                    invoice_numbers[invoice_number].append(file_path)

        # 查找重复
        duplicates = {num: files for num, files in invoice_numbers.items() if len(files) > 1}

        if duplicates:
            logger.warning(f"发现重复发票: {duplicates}")

            # 更新数据库中的重复标记
            db = next(get_db())
            try:
                for invoice_number, file_paths in duplicates.items():
                    for file_path in file_paths:
                        invoice = db.query(Invoice).filter(
                            Invoice.task_id == task_id,
                            Invoice.file_path == file_path
                        ).first()

                        if invoice:
                            invoice.is_duplicate = True
                            invoice.duplicate_group_id = invoice_number

                db.commit()

                # 发送重复发票通知
                await websocket_manager.send_message(task_id, {
                    "type": "duplicate_invoices_detected",
                    "data": {
                        "duplicates": duplicates,
                        "total_duplicates": len(duplicates)
                    }
                })

            except Exception as e:
                db.rollback()
                logger.error(f"更新重复发票标记失败: {e}")
            finally:
                db.close()

    async def _save_invoice_to_db(self, analysis_result: Dict[str, Any], task_id: str, db: Session):
        """
        将发票分析结果保存到数据库
        """
        try:
            file_path = analysis_result["file_path"]
            extracted_data = analysis_result.get("extracted_data", {})
            validation_result = analysis_result.get("validation_result", {})

            # 创建发票记录
            invoice = Invoice(
                id=str(uuid.uuid4()),
                task_id=task_id,
                invoice_code=extracted_data.get("invoice_code"),
                invoice_number=extracted_data.get("invoice_number"),
                buyer_name=extracted_data.get("buyer_name"),
                seller_name=extracted_data.get("seller_name"),
                total_amount=extracted_data.get("total_amount"),
                tax_amount=extracted_data.get("tax_amount"),
                file_path=file_path,
                file_name=file_path.split("/")[-1],
                extracted_data=extracted_data,
                confidence_score=analysis_result.get("confidence_score", 0),
                validation_status=validation_result.get("validation_status"),
                validation_errors=validation_result.get("validation_errors", [])
            )

            # 设置发票日期
            invoice_date = extracted_data.get("invoice_date")
            if invoice_date:
                from datetime import datetime
                try:
                    invoice.invoice_date = datetime.strptime(invoice_date, "%Y-%m-%d")
                except ValueError:
                    pass  # 日期格式错误时忽略

            db.add(invoice)
            db.flush()  # 获取invoice.id

            # 保存商品明细
            items = extracted_data.get("items", [])
            for item_data in items:
                item = InvoiceItem(
                    id=str(uuid.uuid4()),
                    invoice_id=invoice.id,
                    item_name=item_data.get("item_name"),
                    specification=item_data.get("specification"),
                    quantity=item_data.get("quantity"),
                    unit_price=item_data.get("unit_price"),
                    total_price=item_data.get("total_price"),
                    tax_rate=item_data.get("tax_rate")
                )
                db.add(item)

            db.commit()
            logger.info(f"发票数据已保存到数据库: {invoice.id}")

        except Exception as e:
            db.rollback()
            logger.error(f"保存发票数据失败: {e}")
            raise