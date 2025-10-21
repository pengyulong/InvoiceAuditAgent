from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.core.database import get_db
from app.models.audit import AuditTask, AuditStatus
from app.services.audit_service import AuditService
from app.services.celery_app import celery_app
from pydantic import BaseModel

router = APIRouter()

class AuditStartRequest(BaseModel):
    task_id: str
    audit_config: Optional[dict] = None

class AuditResponse(BaseModel):
    audit_id: str
    status: str
    message: str

@router.post("/start", response_model=AuditResponse)
async def start_audit(
    request: AuditStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    开始审计任务
    """
    # 验证任务是否存在
    task = db.query(AuditTask).filter(AuditTask.id == request.task_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail="审计任务不存在"
        )

    # 检查任务状态
    if task.status != AuditStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"任务状态不正确，当前状态: {task.status.value}"
        )

    try:
        # 创建审计ID
        audit_id = str(uuid.uuid4())

        # 更新任务状态
        task.status = AuditStatus.PROCESSING
        task.current_step = "准备开始审计"
        task.progress_percentage = 0.0
        db.commit()

        # 启动后台审计任务
        background_tasks.add_task(
            run_audit_task,
            audit_id=audit_id,
            task_id=request.task_id,
            audit_config=request.audit_config or {}
        )

        return AuditResponse(
            audit_id=audit_id,
            status=AuditStatus.PROCESSING.value,
            message="审计任务已开始"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"启动审计任务失败: {str(e)}"
        )

@router.get("/{audit_id}/status")
async def get_audit_status(
    audit_id: str,
    db: Session = Depends(get_db)
):
    """
    查询审计状态
    """
    # 这里简化处理，实际应该有audit表来跟踪审计状态
    # 暂时通过task_id来查询
    task = db.query(AuditTask).filter(AuditTask.id == audit_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail="审计任务不存在"
        )

    return {
        "code": 200,
        "message": "获取审计状态成功",
        "data": {
            "audit_id": audit_id,
            "status": task.status.value,
            "progress": task.progress_percentage,
            "current_step": task.current_step or "准备中",
            "processed_files": task.processed_files,
            "total_files": task.total_files,
            "error_message": task.error_message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
    }

@router.get("/{audit_id}/results")
async def get_audit_results(
    audit_id: str,
    db: Session = Depends(get_db)
):
    """
    获取审计结果
    """
    task = db.query(AuditTask).filter(AuditTask.id == audit_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail="审计任务不存在"
        )

    if task.status != AuditStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="审计任务尚未完成"
        )

    audit_service = AuditService()
    results = await audit_service.get_audit_results(audit_id)

    return {
        "code": 200,
        "message": "获取审计结果成功",
        "data": results
    }

@router.post("/{audit_id}/stop")
async def stop_audit(
    audit_id: str,
    db: Session = Depends(get_db)
):
    """
    停止审计任务
    """
    task = db.query(AuditTask).filter(AuditTask.id == audit_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail="审计任务不存在"
        )

    if task.status != AuditStatus.PROCESSING:
        raise HTTPException(
            status_code=400,
            detail="只能停止正在处理的任务"
        )

    try:
        # 更新任务状态
        task.status = AuditStatus.FAILED
        task.error_message = "用户手动停止"
        db.commit()

        # 这里可以添加停止Celery任务的逻辑
        # celery_app.control.revoke(audit_id, terminate=True)

        return {
            "code": 200,
            "message": "审计任务已停止",
            "data": {
                "audit_id": audit_id,
                "status": task.status.value
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"停止审计任务失败: {str(e)}"
        )

@router.get("/tasks")
async def get_audit_tasks(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    获取审计任务列表
    """
    query = db.query(AuditTask)

    if status:
        try:
            status_enum = AuditStatus(status)
            query = query.filter(AuditTask.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的状态值: {status}"
            )

    total = query.count()
    tasks = query.order_by(AuditTask.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "code": 200,
        "message": "获取审计任务列表成功",
        "data": {
            "tasks": [
                {
                    "id": task.id,
                    "task_name": task.task_name,
                    "status": task.status.value,
                    "progress_percentage": task.progress_percentage,
                    "current_step": task.current_step,
                    "total_files": task.total_files,
                    "processed_files": task.processed_files,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "error_message": task.error_message
                }
                for task in tasks
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    }

async def run_audit_task(audit_id: str, task_id: str, audit_config: dict):
    """
    运行审计任务（后台任务）
    """
    from app.services.websocket_service import websocket_manager
    from app.agents.coordinator import CoordinatorAgent

    try:
        # 发送开始通知
        await websocket_manager.send_progress(task_id, {
            "step": "开始审计",
            "progress": 0,
            "message": "正在初始化审计流程..."
        })

        # 创建协调器Agent并执行审计
        coordinator = CoordinatorAgent()
        result = await coordinator.coordinate_audit(task_id, audit_config)

        # 发送完成通知
        await websocket_manager.send_progress(task_id, {
            "step": "审计完成",
            "progress": 100,
            "message": "审计流程已完成"
        })

    except Exception as e:
        # 发送错误通知
        await websocket_manager.send_progress(task_id, {
            "step": "审计失败",
            "progress": 0,
            "message": f"审计过程中发生错误: {str(e)}"
        })
        raise