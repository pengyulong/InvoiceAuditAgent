"""
审计服务 - 处理审计任务的核心业务逻辑
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.audit import AuditTask, AuditStatus, SeverityLevel
from app.models.contract import Contract
from app.models.invoice import Invoice
from app.agents.coordinator import CoordinatorAgent


class AuditService:
    """审计服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.coordinator = CoordinatorAgent()

    async def create_audit_task(self, task_name: str, file_count: int) -> AuditTask:
        """创建新的审计任务"""
        task = AuditTask(
            task_name=task_name,
            status=AuditStatus.PENDING,
            total_files=file_count,
            processed_files=0,
            current_step="任务创建",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)

        return task

    async def start_audit(self, task_id: str, websocket_manager=None) -> bool:
        """开始审计流程"""
        task = self.db.query(AuditTask).filter(AuditTask.id == task_id).first()
        if not task:
            return False

        try:
            # 更新任务状态
            task.status = AuditStatus.PROCESSING
            task.current_step = "开始审计流程"
            task.updated_at = datetime.utcnow()
            self.db.commit()

            # 启动协调器Agent
            await self.coordinator.run_audit(task_id, self.db, websocket_manager)

            return True
        except Exception as e:
            # 更新任务状态为失败
            task.status = AuditStatus.FAILED
            task.current_step = f"审计失败: {str(e)}"
            task.updated_at = datetime.utcnow()
            self.db.commit()
            return False

    async def get_task_status(self, task_id: str) -> Optional[AuditTask]:
        """获取任务状态"""
        return self.db.query(AuditTask).filter(AuditTask.id == task_id).first()

    async def update_task_progress(
        self,
        task_id: str,
        progress: int,
        current_step: str,
        processed_files: Optional[int] = None
    ) -> bool:
        """更新任务进度"""
        task = self.db.query(AuditTask).filter(AuditTask.id == task_id).first()
        if not task:
            return False

        task.progress_percentage = progress
        task.current_step = current_step
        task.updated_at = datetime.utcnow()

        if processed_files is not None:
            task.processed_files = processed_files

        self.db.commit()
        return True

    async def complete_task(
        self,
        task_id: str,
        status: AuditStatus,
        summary: Optional[Dict[str, Any]] = None
    ) -> bool:
        """完成任务"""
        task = self.db.query(AuditTask).filter(AuditTask.id == task_id).first()
        if not task:
            return False

        task.status = status
        task.progress_percentage = 100
        task.current_step = "审计完成"
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()

        if summary:
            task.summary = summary

        self.db.commit()
        return True

    async def get_all_tasks(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[AuditStatus] = None
    ) -> List[AuditTask]:
        """获取所有审计任务"""
        query = self.db.query(AuditTask)

        if status:
            query = query.filter(AuditTask.status == status)

        return query.order_by(AuditTask.created_at.desc()).offset(skip).limit(limit).all()

    async def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        total_tasks = self.db.query(AuditTask).count()
        completed_tasks = self.db.query(AuditTask).filter(
            AuditTask.status == AuditStatus.COMPLETED
        ).count()
        failed_tasks = self.db.query(AuditTask).filter(
            AuditTask.status == AuditStatus.FAILED
        ).count()
        processing_tasks = self.db.query(AuditTask).filter(
            AuditTask.status == AuditStatus.PROCESSING
        ).count()

        # 获取关联的合同和发票数量
        total_contracts = self.db.query(Contract).count()
        total_invoices = self.db.query(Invoice).count()

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "processing_tasks": processing_tasks,
            "total_contracts": total_contracts,
            "total_invoices": total_invoices,
            "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }

    async def delete_task(self, task_id: str) -> bool:
        """删除审计任务"""
        task = self.db.query(AuditTask).filter(AuditTask.id == task_id).first()
        if not task:
            return False

        # 删除关联的合同和发票
        self.db.query(Contract).filter(Contract.audit_task_id == task_id).delete()
        self.db.query(Invoice).filter(Invoice.audit_task_id == task_id).delete()

        # 删除任务
        self.db.delete(task)
        self.db.commit()

        return True