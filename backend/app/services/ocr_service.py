"""OCR识别服务 - 批量发票OCR识别"""
import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from app.core.database import AsyncSessionLocal
from app.models.audit import AuditTask
from app.services.websocket_service import websocket_manager
from app.services.ai_service import OCRConfigError

logger = logging.getLogger(__name__)


class OcrService:
    """OCR识别服务，管理发票识别任务的生命周期"""

    def __init__(self):
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

    async def execute_ocr(self, task_id: str, file_paths: List[str], allow_local_fallback: bool = False):
        """执行批量OCR识别"""
        start_time = time.time()

        try:
            logger.info(f"开始OCR识别任务: {task_id}, 文件数: {len(file_paths)}")
            self.active_tasks[task_id] = {
                "status": "running",
                "progress": 0,
                "current_step": "初始化",
                "start_time": start_time,
                "total_files": len(file_paths),
                "processed_files": 0,
                "allow_local_fallback": allow_local_fallback,
            }

            await websocket_manager.send_progress(task_id, {
                "progress": 0,
                "current_step": "启动识别",
                "step_id": "init",
                "message": f"正在初始化OCR识别，共 {len(file_paths)} 个文件",
            })
            await websocket_manager.send_log(task_id,
                f"开始OCR识别 - 共 {len(file_paths)} 个发票文件", "info")

            from app.services.ai_service import ai_service

            results = []
            total = len(file_paths)

            for i, file_path in enumerate(file_paths):
                file_name = Path(file_path).name
                progress_pct = int((i / total) * 100) if total > 0 else 0
                step_name = f"识别发票 ({i + 1}/{total})"

                self.active_tasks[task_id].update({
                    "progress": progress_pct,
                    "current_step": step_name,
                    "processed_files": i,
                })

                await websocket_manager.send_progress(task_id, {
                    "progress": progress_pct,
                    "current_step": step_name,
                    "step_id": "ocr_processing",
                    "message": f"正在识别: {file_name} ({i + 1}/{total})",
                })
                await websocket_manager.send_log(task_id,
                    f"[{i + 1}/{total}] 开始识别: {file_name}", "info")

                try:
                    async def ocr_progress(agent_name, pct, msg):
                        overall_progress = min(
                            99,
                            int((i / total) * 100 + (pct / 100) * (100 / total))
                        ) if total > 0 else pct
                        self.active_tasks[task_id].update({
                            "progress": overall_progress,
                            "current_step": msg,
                        })
                        await websocket_manager.send_progress(task_id, {
                            "progress": overall_progress,
                            "current_step": step_name,
                            "step_id": "ocr_processing",
                            "message": msg,
                        })
                        await websocket_manager.send_log(task_id, msg, "info")

                    extracted = await ai_service.extract_invoice_info(
                        file_path,
                        ocr_progress,
                        allow_local_fallback=allow_local_fallback,
                    )
                    extracted_results = extracted if isinstance(extracted, list) else [extracted]
                    for result in extracted_results:
                        result["source_file"] = file_path
                        page_number = result.get("page_number")
                        if page_number:
                            result["file_name"] = f"{file_name} 第{page_number}页"
                        else:
                            result["file_name"] = file_name
                        results.append(result)

                    success_pages = sum(1 for r in extracted_results if "error" not in r)
                    await websocket_manager.send_log(task_id,
                        f"[{i + 1}/{total}] 识别完成: {file_name} "
                        f"(成功 {success_pages}/{len(extracted_results)})", "success")

                except OCRConfigError as e:
                    logger.error(f"OCR配置不可用: {file_path}, {e}")
                    await self._handle_failure(
                        task_id,
                        str(e),
                        start_time,
                        error_code=e.error_code,
                        can_fallback=True,
                    )
                    return
                except Exception as e:
                    logger.error(f"识别发票失败: {file_path}, {e}")
                    results.append({
                        "source_file": file_path,
                        "file_name": file_name,
                        "error": str(e),
                        "invoice_number": "识别失败",
                    })
                    await websocket_manager.send_log(task_id,
                        f"[{i + 1}/{total}] 识别失败: {file_name} - {e}", "error")

            elapsed = time.time() - start_time
            success_count = sum(1 for r in results if "error" not in r)

            recognized_total = len(results)
            result_data = {
                "invoices": results,
                "total_count": recognized_total,
                "success_count": success_count,
                "fail_count": recognized_total - success_count,
                "processing_time": round(elapsed, 1),
            }

            self.active_tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "current_step": "完成",
                "result": result_data,
                "elapsed": elapsed,
                "processed_files": total,
            })

            await self._persist_result(task_id, result_data, elapsed)

            await websocket_manager.send_progress(task_id, {
                "progress": 100,
                "step_id": "completed",
                "current_step": "识别完成",
                "message": f"OCR识别完成 - 成功 {success_count}/{recognized_total}，耗时 {elapsed:.1f} 秒",
            })
            await websocket_manager.send_completed(task_id, {
                "task_id": task_id,
                "status": "completed",
                "summary": {
                    "total": recognized_total,
                    "success": success_count,
                    "fail": recognized_total - success_count,
                    "elapsed": elapsed,
                },
            })

            logger.info(f"OCR识别完成: {task_id}, 耗时 {elapsed:.1f}s")

        except Exception as e:
            await self._handle_failure(task_id, str(e), start_time)

    async def _handle_failure(
        self,
        task_id: str,
        error: str,
        start_time: float,
        error_code: str = "OCR_FAILED",
        can_fallback: bool = False,
    ):
        elapsed = time.time() - start_time
        self.active_tasks[task_id] = {
            "status": "failed",
            "progress": 0,
            "error": error,
            "error_code": error_code,
            "can_fallback": can_fallback,
            "elapsed": elapsed,
        }
        await self._persist_result(
            task_id,
            {"error": error, "error_code": error_code, "can_fallback": can_fallback},
            elapsed,
            status="failed",
            error_message=error,
        )
        await websocket_manager.send_error(task_id, {
            "error": error,
            "error_code": error_code,
            "can_fallback": can_fallback,
            "message": "OCR识别任务执行失败",
            "elapsed": elapsed,
        })
        logger.error(f"OCR识别失败: {task_id}, 错误: {error}")

    async def _persist_result(
        self,
        task_id: str,
        result_data: Dict[str, Any],
        elapsed: float,
        status: str = "completed",
        error_message: Optional[str] = None,
    ):
        try:
            async with AsyncSessionLocal() as session:
                task = await session.get(AuditTask, task_id)
                if task:
                    task.status = status
                    task.progress = 100 if status == "completed" else 0
                    task.error_message = None if status == "completed" else error_message
                    task.result_data = result_data
                    task.completed_at = datetime.utcnow()
                    await session.commit()
        except Exception as e:
            logger.error(f"保存OCR结果失败: {task_id}, {e}")

    async def get_ocr_status(self, task_id: str) -> Dict[str, Any]:
        """获取OCR任务状态"""
        state = self.active_tasks.get(task_id)
        if not state:
            return {"status": "unknown", "progress": 0, "current_step": "未知"}
        return {
            "status": state.get("status"),
            "progress": state.get("progress", 0),
            "current_step": state.get("current_step", "未知"),
            "total_files": state.get("total_files", 0),
            "processed_files": state.get("processed_files", 0),
            "error": state.get("error"),
            "error_code": state.get("error_code"),
            "can_fallback": state.get("can_fallback", False),
        }

    async def get_ocr_results(self, task_id: str) -> Dict[str, Any]:
        """获取OCR识别结果"""
        state = self.active_tasks.get(task_id, {})
        result = state.get("result")
        if result:
            return {"task_id": task_id, "status": state.get("status", "completed"), **result}

        async with AsyncSessionLocal() as session:
            task = await session.get(AuditTask, task_id)
            if task and task.result_data:
                return {"task_id": task_id, "status": task.status, **task.result_data}

        return {"task_id": task_id, "status": "unknown", "invoices": []}


ocr_service = OcrService()
