"""审计服务 - 使用Agent工作流执行审计任务"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

from app.agents.coordinator import CoordinatorAgent
from app.agents.base import AgentError
from app.core.database import AsyncSessionLocal
from app.models.audit import AuditTask
from app.services.websocket_service import websocket_manager

logger = logging.getLogger(__name__)


class AuditService:
    """审计服务，管理审计任务的生命周期"""

    def __init__(self):
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.coordinator = CoordinatorAgent()

    async def execute_audit(self, task_id: str, config: Optional[Dict[str, Any]] = None):
        """执行审计任务"""
        config = config or {}
        start_time = time.time()

        try:
            logger.info(f"开始审计任务: {task_id}")
            task_total_files = await self._get_task_total_files(task_id)
            self.active_tasks[task_id] = {
                "status": "running",
                "progress": 0,
                "current_step": "初始化",
                "start_time": start_time,
                "total_files": task_total_files,
                "processed_files": 0,
            }

            await websocket_manager.send_step_change(task_id, {
                "previous_step_id": None,
                "next_step_id": "file_parsing",
                "step_name": "文件解析",
                "message": "正在初始化审计流程..."
            })

            await websocket_manager.send_progress(task_id, {
                "progress": 0,
                "current_step": "启动审计",
                "step_id": "file_parsing",
                "message": "正在初始化审计流程...",
            })

            # 设置协调器的进度回调，通过WebSocket推送给前端
            async def progress_callback(agent_name: str, progress: float, message: str):
                current_step = self._step_name(progress)
                step_id = self._progress_to_step_id(progress)
                self.active_tasks[task_id].update({
                    "progress": int(progress),
                    "current_step": current_step,
                    "processed_files": int(task_total_files * min(progress, 99) / 100) if task_total_files else 0,
                })

                # 发送 Agent 状态
                await websocket_manager.send_agent_status(task_id, agent_name, "running", {
                    "progress": int(progress),
                    "message": message,
                    "step_id": step_id
                })

                # 发送日志
                await websocket_manager.send_log(task_id, message, "info", agent_name)

                # 发送进度
                await websocket_manager.send_progress(task_id, {
                    "step_id": step_id,
                    "step_name": current_step,
                    "progress": int(progress),
                    "message": message,
                    "agent_name": agent_name
                })

            self.coordinator.set_progress_callback(progress_callback)

            # 执行审计工作流
            result = await self.coordinator.run(
                task_id=task_id,
                upload_dir="uploads",
                config=config,
            )

            # 计算处理时间
            elapsed = time.time() - start_time
            summary = result.get("summary", {})
            summary["processing_time"] = round(elapsed, 1)

            # 任务完成
            self.active_tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "current_step": "完成",
                "result": result,
                "elapsed": elapsed,
                "processed_files": task_total_files,
            })
            await self._persist_task_state(
                task_id,
                status="completed",
                progress=100,
                current_step="完成",
                processed_files=task_total_files,
                result_data=result,
                completed_at=datetime.utcnow(),
            )

            await websocket_manager.send_step_change(task_id, {
                "previous_step_id": "report_generation",
                "next_step_id": "completed",
                "step_name": "审计完成",
                "message": f"审计任务完成，耗时 {elapsed:.1f} 秒"
            })

            await websocket_manager.send_progress(task_id, {
                "progress": 100,
                "step_id": "completed",
                "current_step": "审计完成",
                "message": f"审计任务完成，耗时 {elapsed:.1f} 秒",
            })
            await websocket_manager.send_completed(task_id, {
                "task_id": task_id,
                "status": "completed",
                "summary": summary,
                "elapsed": elapsed,
            })

            logger.info(f"审计任务完成: {task_id}, 耗时 {elapsed:.1f}s")

        except AgentError as e:
            await self._handle_failure(task_id, str(e), start_time)
        except Exception as e:
            logger.error(f"审计任务异常: {task_id}, {e}", exc_info=True)
            await self._handle_failure(task_id, str(e), start_time)

    async def _handle_failure(self, task_id: str, error: str, start_time: float):
        elapsed = time.time() - start_time
        self.active_tasks[task_id] = {
            "status": "failed",
            "progress": 0,
            "error": error,
            "elapsed": elapsed,
        }
        await self._persist_task_state(
            task_id,
            status="failed",
            progress=0,
            current_step="执行失败",
            error_message=error,
            completed_at=datetime.utcnow(),
        )
        await websocket_manager.send_error(task_id, {
            "error": error,
            "message": "审计任务执行失败",
            "elapsed": elapsed,
        })
        logger.error(f"审计任务失败: {task_id}, 错误: {error}")

    async def _persist_task_state(
        self,
        task_id: str,
        *,
        status: str,
        progress: int,
        current_step: str,
        result_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None,
        processed_files: Optional[int] = None,
    ):
        async with AsyncSessionLocal() as session:
            task = await session.get(AuditTask, task_id)
            if not task:
                logger.warning(f"审计任务不存在，无法更新状态: {task_id}")
                return

            task.status = status
            task.progress = progress
            task.current_step = current_step
            task.error_message = error_message
            if processed_files is not None:
                task.processed_files = processed_files
            if result_data is not None:
                task.result_data = result_data
            if completed_at is not None:
                task.completed_at = completed_at
            await session.commit()

    async def _get_task_total_files(self, task_id: str) -> int:
        async with AsyncSessionLocal() as session:
            task = await session.get(AuditTask, task_id)
            return task.total_files if task else 0

    async def get_audit_status(self, task_id: str) -> Dict[str, Any]:
        """获取审计状态"""
        if task_id not in self.active_tasks:
            return {"current_step": "未知", "agent_status": {}, "estimated_time_remaining": None}

        state = self.active_tasks[task_id]
        return {
            "current_step": state.get("current_step", "未知"),
            "agent_status": state.get("agent_status", {}),
            "estimated_time_remaining": self._estimate_remaining(task_id),
        }

    async def get_audit_results(self, task_id: str) -> Dict[str, Any]:
        """获取审计结果"""
        state = self.active_tasks.get(task_id, {})
        result = state.get("result", {})
        if not result:
            async with AsyncSessionLocal() as session:
                task = await session.get(AuditTask, task_id)
                if task and task.result_data:
                    result = task.result_data

        if not result:
            return {
                "audit_id": task_id,
                "summary": {"status": "unknown", "contract_amount": 0, "invoice_total": 0,
                             "coverage": 0, "issue_count": 0, "processing_time": 0, "confidence_score": 0},
                "contract_info": None,
                "invoices": [],
                "issues": [],
                "comparisons": [],
            }

        return {
            "audit_id": task_id,
            "task_id": task_id,
            "status": "completed",
            "summary": result.get("summary", {}),
            "contract_info": result.get("contract_info"),
            "invoices": result.get("invoice_list", []),
            "issues": result.get("issues", []),
            "comparisons": result.get("comparisons", []),
        }

    async def pause_audit(self, task_id: str):
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "paused"
            await websocket_manager.send_log(task_id, "审计任务已暂停", "warning")

    async def resume_audit(self, task_id: str):
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "running"
            await websocket_manager.send_log(task_id, "审计任务已恢复", "info")

    async def cancel_audit(self, task_id: str):
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "cancelled"
            await websocket_manager.send_log(task_id, "审计任务已取消", "warning")

    async def get_audit_history(self, limit: int = 20, offset: int = 0,
                                 status: Optional[str] = None) -> Dict[str, Any]:
        items = []
        for tid, state in list(self.active_tasks.items())[offset:offset + limit]:
            if status and state.get("status") != status:
                continue
            items.append({
                "task_id": tid,
                "status": state.get("status"),
                "progress": state.get("progress", 0),
                "created_at": None,
            })
        return {"items": items, "total": len(self.active_tasks), "limit": limit, "offset": offset}

    async def get_audit_statistics(self) -> Dict[str, Any]:
        tasks = self.active_tasks
        completed = sum(1 for t in tasks.values() if t.get("status") == "completed")
        failed = sum(1 for t in tasks.values() if t.get("status") == "failed")
        total = len(tasks)
        return {
            "total_audits": total,
            "completed_audits": completed,
            "failed_audits": failed,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "average_processing_time": 0,
            "total_amount_processed": 0,
            "total_issues_found": 0,
            "contracts_processed": total,
            "invoices_processed": 0,
        }

    def _estimate_remaining(self, task_id: str) -> Optional[int]:
        state = self.active_tasks.get(task_id, {})
        progress = state.get("progress", 0)
        if progress >= 100:
            return 0
        return max(int((100 - progress) * 2), 5)

    @staticmethod
    def _step_name(progress: float) -> str:
        if progress < 10:
            return "文件解析"
        if progress < 35:
            return "合同分析"
        if progress < 60:
            return "发票分析"
        if progress < 85:
            return "交叉验证"
        return "报告生成"

    @staticmethod
    def _progress_to_step_id(progress: float) -> str:
        if progress < 10:
            return "file_parsing"
        if progress < 35:
            return "contract_analysis"
        if progress < 60:
            return "invoice_analysis"
        if progress < 85:
            return "cross_validation"
        return "report_generation"


audit_service = AuditService()
