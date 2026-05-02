from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.services.audit_service import audit_service
from app.services.ai_service import ai_service
from app.models.audit import AuditTask
from app.schemas.audit import AuditRequest, AuditResponse, AuditStatusResponse

router = APIRouter()


@router.post("/start", response_model=AuditResponse, summary="开始审计任务")
async def start_audit(
    audit_request: AuditRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    开始执行审计任务

    - **task_id**: 任务ID
    - **audit_config**: 审计配置
    """
    try:
        # 验证任务是否存在
        task = await db.get(AuditTask, audit_request.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task.status not in ["pending", "failed", "completed", "cancelled"]:
            raise HTTPException(status_code=400, detail="任务状态不允许重新开始")

        # 更新任务状态
        task.status = "processing"
        task.progress = 0
        task.current_step = "初始化"
        task.error_message = None
        task.result_data = None
        task.completed_at = None
        task.config = audit_request.audit_config.model_dump()
        await db.commit()

        # 在后台任务中执行审计
        background_tasks.add_task(
            audit_service.execute_audit,
            audit_request.task_id,
            audit_request.audit_config.model_dump()
        )

        return AuditResponse(
            audit_id=str(uuid.uuid4()),
            task_id=audit_request.task_id,
            status="started",
            message="审计任务已开始"
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"启动审计任务失败: {str(e)}")


@router.get("/{audit_id}/status", response_model=AuditStatusResponse, summary="查询审计状态")
async def get_audit_status(
    audit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    查询审计任务的当前状态和进度

    - **audit_id**: 审计ID
    """
    try:
        # 优先检查内存中的任务状态
        in_memory = audit_service.active_tasks.get(audit_id, {})
        mem_status = in_memory.get("status", "pending")

        # 获取DB任务状态
        task = await db.get(AuditTask, audit_id)
        if not task and not in_memory:
            raise HTTPException(status_code=404, detail="审计任务不存在")

        # 获取详细状态
        status_info = await audit_service.get_audit_status(audit_id)

        db_status = task.status if task else None
        if mem_status in ["completed", "failed", "paused", "cancelled"]:
            status = mem_status
        elif db_status:
            status = db_status
        else:
            status = "processing" if mem_status == "running" else mem_status

        current_step = status_info.get("current_step", "")
        if (not current_step or current_step == "未知") and task and task.current_step:
            current_step = task.current_step

        progress = in_memory.get("progress", task.progress if task else 0) or 0
        total_files = task.total_files if task else in_memory.get("total_files", 0)
        if status == "completed":
            processed_files = total_files
        else:
            processed_files = in_memory.get(
                "processed_files",
                int(total_files * min(progress, 99) / 100) if total_files else 0,
            )
        if in_memory.get("result"):
            summary = in_memory["result"].get("summary", {})
        elif task and task.result_data:
            summary = (task.result_data or {}).get("summary", {})
        else:
            summary = {}

        return AuditStatusResponse(
            audit_id=audit_id,
            task_id=audit_id,
            status=status,
            progress=progress,
            current_step=current_step,
            agent_status=status_info.get("agent_status", {}),
            estimated_time_remaining=status_info.get("estimated_time_remaining"),
            error_message=task.error_message if task else None,
            total_files=total_files or 0,
            processed_files=processed_files or 0,
            processing_time=in_memory.get("elapsed", summary.get("processing_time", 0)) if in_memory else 0,
            confidence_score=summary.get("confidence_score", 0) if summary else 0,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询审计状态失败: {str(e)}")


@router.get("/{audit_id}/results", summary="获取审计结果")
async def get_audit_results(
    audit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取审计任务的完整结果

    - **audit_id**: 审计ID
    """
    try:
        # 检查内存中的审计状态（优先）
        in_memory = audit_service.active_tasks.get(audit_id, {})
        mem_status = in_memory.get("status", "")

        # 验证任务是否存在（DB或内存）
        task = await db.get(AuditTask, audit_id)
        if not task and not in_memory:
            raise HTTPException(status_code=404, detail="审计任务不存在")

        if mem_status not in ["completed", ""] and task and task.status != "completed":
            raise HTTPException(status_code=400, detail="审计任务尚未完成")

        if mem_status == "failed":
            raise HTTPException(status_code=400, detail=f"审计任务执行失败: {in_memory.get('error', '未知错误')}")

        # 获取审计结果
        results = await audit_service.get_audit_results(audit_id)

        db_status = task.status if task else None
        status = "completed" if mem_status == "completed" else (db_status or mem_status or "completed")
        return {
            "audit_id": audit_id,
            "task_id": audit_id,
            "status": status,
            "completed_at": task.completed_at if task else None,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取审计结果失败: {str(e)}")


@router.post("/{audit_id}/pause", summary="暂停审计任务")
async def pause_audit(
    audit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    暂停正在执行的审计任务

    - **audit_id**: 审计ID
    """
    try:
        task = await db.get(AuditTask, audit_id)
        if not task:
            raise HTTPException(status_code=404, detail="审计任务不存在")

        if task.status != "processing":
            raise HTTPException(status_code=400, detail="只能暂停正在处理的任务")

        # 暂停任务
        await audit_service.pause_audit(audit_id)

        task.status = "paused"
        await db.commit()

        return {
            "audit_id": audit_id,
            "status": "paused",
            "message": "审计任务已暂停"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"暂停审计任务失败: {str(e)}")


@router.post("/{audit_id}/resume", summary="恢复审计任务")
async def resume_audit(
    audit_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    恢复暂停的审计任务

    - **audit_id**: 审计ID
    """
    try:
        task = await db.get(AuditTask, audit_id)
        if not task:
            raise HTTPException(status_code=404, detail="审计任务不存在")

        if task.status != "paused":
            raise HTTPException(status_code=400, detail="只能恢复暂停的任务")

        # 恢复任务
        task.status = "processing"
        await db.commit()

        # 在后台任务中恢复审计
        background_tasks.add_task(audit_service.resume_audit, audit_id)

        return {
            "audit_id": audit_id,
            "status": "resumed",
            "message": "审计任务已恢复"
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"恢复审计任务失败: {str(e)}")


@router.delete("/{audit_id}", summary="取消审计任务")
async def cancel_audit(
    audit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    取消审计任务

    - **audit_id**: 审计ID
    """
    try:
        task = await db.get(AuditTask, audit_id)
        if not task:
            raise HTTPException(status_code=404, detail="审计任务不存在")

        if task.status in ["completed", "cancelled"]:
            raise HTTPException(status_code=400, detail="任务已结束，无法取消")

        # 取消任务
        await audit_service.cancel_audit(audit_id)

        task.status = "cancelled"
        await db.commit()

        return {
            "audit_id": audit_id,
            "status": "cancelled",
            "message": "审计任务已取消"
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"取消审计任务失败: {str(e)}")


@router.get("/history", summary="获取审计历史")
async def get_audit_history(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取审计任务历史列表

    - **limit**: 返回数量限制
    - **offset**: 偏移量
    - **status**: 状态筛选
    """
    try:
        history = await audit_service.get_audit_history(limit, offset, status)
        return history

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取审计历史失败: {str(e)}")


@router.get("/statistics", summary="获取审计统计")
async def get_audit_statistics(db: AsyncSession = Depends(get_db)):
    """
    获取系统审计统计数据
    """
    try:
        statistics = await audit_service.get_audit_statistics()
        return statistics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.get("/ai-health", summary="AI服务健康检查")
async def get_ai_service_health():
    """
    检查AI服务（千问、DeepSeek）的连接状态和可用性
    """
    try:
        health_status = await ai_service.health_check()
        return {
            "status": "success",
            "message": "AI服务健康检查完成",
            "data": health_status,
            "timestamp": uuid.uuid4().hex[:16]  # 简单的时间戳标识
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI服务健康检查失败: {str(e)}")
