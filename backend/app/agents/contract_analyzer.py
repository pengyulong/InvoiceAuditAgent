from typing import Dict, Any, List
from sqlalchemy.orm import Session
from loguru import logger

from app.services.ai_service import AIService
from app.services.websocket_service import websocket_manager
from app.models.contract import Contract, ContractItem
from app.models.audit import AuditStatus
from app.core.database import get_db
import uuid

class ContractAnalyzer:
    """
    合同分析Agent - 负责分析合同文件并提取关键信息
    """

    def __init__(self):
        self.ai_service = AIService()

    async def analyze_contracts(self, contract_files: List[str], task_id: str) -> List[Dict[str, Any]]:
        """
        分析合同文件列表
        """
        results = []
        db = next(get_db())

        try:
            for i, file_path in enumerate(contract_files):
                try:
                    logger.info(f"分析合同文件 {i+1}/{len(contract_files)}: {file_path}")

                    # 发送进度通知
                    await websocket_manager.send_progress(task_id, {
                        "step": "分析合同",
                        "progress": 20 + (i * 20 / len(contract_files)),
                        "message": f"正在分析合同 {i+1}/{len(contract_files)}"
                    })

                    # 分析单个合同
                    result = await self._analyze_single_contract(file_path, task_id, db)
                    results.append(result)

                    # 保存到数据库
                    await self._save_contract_to_db(result, task_id, db)

                    # 发送文件处理完成通知
                    await websocket_manager.send_file_processed(task_id, {
                        "file_type": "contract",
                        "file_path": file_path,
                        "status": "completed",
                        "extracted_data": result.get("extracted_data", {})
                    })

                except Exception as e:
                    logger.error(f"分析合同文件失败 {file_path}: {e}")
                    results.append({
                        "file_path": file_path,
                        "success": False,
                        "error": str(e),
                        "extracted_data": {}
                    })

        finally:
            db.close()

        return results

    async def _analyze_single_contract(self, file_path: str, task_id: str, db: Session) -> Dict[str, Any]:
        """
        分析单个合同文件
        """
        # 使用AI分析合同图像
        analysis_result = await self.ai_service.analyze_contract_image(file_path)

        if not analysis_result.get("success"):
            return {
                "file_path": file_path,
                "success": False,
                "error": analysis_result.get("error", "AI分析失败"),
                "extracted_data": {}
            }

        extracted_data = analysis_result.get("extracted_data", {})
        confidence_score = analysis_result.get("confidence", 0)

        # 进行合同合理性验证
        validation_result = await self._validate_contract(extracted_data)

        return {
            "file_path": file_path,
            "success": True,
            "extracted_data": extracted_data,
            "confidence_score": confidence_score,
            "validation_result": validation_result,
            "raw_response": analysis_result.get("raw_response", "")
        }

    async def _validate_contract(self, contract_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证合同数据的合理性
        """
        validation_errors = []
        warnings = []

        # 检查必要字段
        required_fields = ["contract_number", "buyer_name", "seller_name", "total_amount"]
        for field in required_fields:
            if not contract_data.get(field):
                validation_errors.append(f"缺少必要字段: {field}")

        # 检查金额合理性
        total_amount = contract_data.get("total_amount")
        if total_amount is not None:
            if total_amount <= 0:
                validation_errors.append("合同总金额应大于0")
            elif total_amount > 100000000:  # 1亿
                warnings.append("合同金额较大，建议复核")

        # 检查税率合理性
        tax_rate = contract_data.get("tax_rate")
        if tax_rate is not None:
            if tax_rate < 0 or tax_rate > 1:
                validation_errors.append("税率应在0-1之间")
            elif tax_rate not in [0, 0.06, 0.09, 0.13]:  # 常见税率
                warnings.append("税率非常规，请确认")

        # 检查商品清单
        items = contract_data.get("items", [])
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
                validation_errors.append(f"合同总金额计算错误: 商品总额 {calculated_total} ≠ 总金额 {total_amount}")

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

    async def _save_contract_to_db(self, analysis_result: Dict[str, Any], task_id: str, db: Session):
        """
        将合同分析结果保存到数据库
        """
        try:
            file_path = analysis_result["file_path"]
            extracted_data = analysis_result.get("extracted_data", {})
            validation_result = analysis_result.get("validation_result", {})

            # 创建合同记录
            contract = Contract(
                id=str(uuid.uuid4()),
                task_id=task_id,
                contract_number=extracted_data.get("contract_number"),
                buyer_name=extracted_data.get("buyer_name"),
                seller_name=extracted_data.get("seller_name"),
                total_amount=extracted_data.get("total_amount"),
                tax_rate=extracted_data.get("tax_rate"),
                file_path=file_path,
                file_name=file_path.split("/")[-1],
                extracted_data=extracted_data,
                confidence_score=analysis_result.get("confidence_score", 0),
                validation_status=validation_result.get("validation_status"),
                validation_errors=validation_result.get("validation_errors", [])
            )

            # 设置合同日期
            contract_date = extracted_data.get("contract_date")
            if contract_date:
                from datetime import datetime
                try:
                    contract.contract_date = datetime.strptime(contract_date, "%Y-%m-%d")
                except ValueError:
                    pass  # 日期格式错误时忽略

            db.add(contract)
            db.flush()  # 获取contract.id

            # 保存商品明细
            items = extracted_data.get("items", [])
            for item_data in items:
                item = ContractItem(
                    id=str(uuid.uuid4()),
                    contract_id=contract.id,
                    item_name=item_data.get("item_name"),
                    specification=item_data.get("specification"),
                    quantity=item_data.get("quantity"),
                    unit_price=item_data.get("unit_price"),
                    total_price=item_data.get("total_price"),
                    tax_rate=item_data.get("tax_rate")
                )
                db.add(item)

            db.commit()
            logger.info(f"合同数据已保存到数据库: {contract.id}")

        except Exception as e:
            db.rollback()
            logger.error(f"保存合同数据失败: {e}")
            raise