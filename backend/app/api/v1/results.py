"""
结果API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.audit import AuditTask, AuditStatus
from app.schemas.results import (
    TaskStatisticsResponse,
    TaskListResponse,
    TaskSummary
)

router = APIRouter()


@router.get("/statistics", response_model=TaskStatisticsResponse)
async def get_task_statistics(db: Session = Depends(get_db)):
    """获取任务统计信息"""
    try:
        # 统计任务数量
        total_tasks = db.query(AuditTask).count()
        completed_tasks = db.query(AuditTask).filter(
            AuditTask.status == AuditStatus.COMPLETED
        ).count()
        failed_tasks = db.query(AuditTask).filter(
            AuditTask.status == AuditStatus.FAILED
        ).count()
        processing_tasks = db.query(AuditTask).filter(
            AuditTask.status == AuditStatus.PROCESSING
        ).count()

        # 统计合同和发票数量
        from app.models.contract import Contract
        from app.models.invoice import Invoice

        total_contracts = db.query(Contract).count()
        total_invoices = db.query(Invoice).count()

        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return TaskStatisticsResponse(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            processing_tasks=processing_tasks,
            total_contracts=total_contracts,
            total_invoices=total_invoices,
            success_rate=round(success_rate, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=TaskListResponse)
async def get_tasks(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """获取任务列表"""
    try:
        query = db.query(AuditTask)

        # 状态筛选
        if status:
            try:
                status_enum = AuditStatus(status)
                query = query.filter(AuditTask.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的状态参数")

        # 分页
        total = query.count()
        tasks = query.order_by(AuditTask.created_at.desc()).offset(
            (page - 1) * size
        ).limit(size).all()

        # 转换为响应模型
        task_summaries = []
        for task in tasks:
            task_summaries.append(TaskSummary(
                id=task.id,
                task_name=task.task_name,
                status=task.status.value,
                progress_percentage=task.progress_percentage or 0,
                total_files=task.total_files,
                processed_files=task.processed_files,
                created_at=task.created_at,
                completed_at=task.completed_at
            ))

        return TaskListResponse(
            data=task_summaries,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str, db: Session = Depends(get_db)):
    """获取任务详情"""
    try:
        task = db.query(AuditTask).filter(AuditTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        return {
            "id": task.id,
            "task_name": task.task_name,
            "status": task.status.value,
            "progress_percentage": task.progress_percentage or 0,
            "current_step": task.current_step,
            "total_files": task.total_files,
            "processed_files": task.processed_files,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "completed_at": task.completed_at,
            "summary": task.summary
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """删除任务"""
    try:
        task = db.query(AuditTask).filter(AuditTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 删除关联的合同和发票
        from app.models.contract import Contract
        from app.models.invoice import Invoice

        db.query(Contract).filter(Contract.audit_task_id == task_id).delete()
        db.query(Invoice).filter(Invoice.audit_task_id == task_id).delete()

        # 删除任务
        db.delete(task)
        db.commit()

        return {"message": "任务删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))