from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

from app.core.config import settings
from app.services.ocr_service import ocr_service
from app.core.database import AsyncSessionLocal
from app.models.audit import AuditTask

router = APIRouter()


class OcrStartRequest(BaseModel):
    task_id: str
    allow_local_fallback: bool = False


@router.post("/start", summary="启动OCR识别")
async def start_ocr(request: OcrStartRequest, background_tasks: BackgroundTasks):
    """
    启动发票OCR识别任务

    - **task_id**: 上传文件时返回的任务ID
    """
    try:
        async with AsyncSessionLocal() as session:
            task = await session.get(AuditTask, request.task_id)
            if not task:
                raise HTTPException(status_code=404, detail="任务不存在")
            if task.status == "running":
                raise HTTPException(status_code=400, detail="任务正在处理中")

            task.status = "running"
            await session.commit()

            file_paths = task.result_data.get("file_paths", []) if task.result_data else []

        if not file_paths:
            # 尝试从上传目录查找文件
            task_dir = Path(settings.upload_dir) / request.task_id / "extracted"
            if task_dir.exists():
                file_paths = [
                    str(p) for p in task_dir.rglob("*")
                    if p.is_file() and p.suffix.lower() in (".pdf", ".jpg", ".jpeg", ".png")
                ]
                # 跳过系统隐藏文件
                file_paths = [
                    p for p in file_paths
                    if not any(part.startswith("__MACOSX") for part in Path(p).parts)
                    and not Path(p).name.startswith("._")
                ]

        if not file_paths:
            raise HTTPException(status_code=400, detail="未找到待识别的文件，请先上传发票文件")

        background_tasks.add_task(
            ocr_service.execute_ocr,
            request.task_id,
            file_paths,
            request.allow_local_fallback,
        )

        return {
            "task_id": request.task_id,
            "message": "OCR识别任务已启动",
            "file_count": len(file_paths),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动OCR识别失败: {str(e)}")


@router.get("/{task_id}/status", summary="获取OCR任务状态")
async def get_ocr_status(task_id: str):
    """获取OCR识别任务的实时状态"""
    try:
        status = await ocr_service.get_ocr_status(task_id)
        return {"task_id": task_id, **status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.get("/{task_id}/results", summary="获取OCR识别结果")
async def get_ocr_results(task_id: str):
    """获取OCR识别结果"""
    try:
        results = await ocr_service.get_ocr_results(task_id)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取结果失败: {str(e)}")
