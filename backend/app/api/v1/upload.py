from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import zipfile
import tempfile
from pathlib import Path

from app.core.database import get_db
from app.core.config import settings
from app.services.file_service import FileService
from app.models.audit import AuditTask, AuditStatus

router = APIRouter()

@router.post("/zip")
async def upload_zip_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传ZIP文件（包含合同和发票）
    """
    # 验证文件类型
    if not file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=400,
            detail="只支持ZIP格式文件"
        )

    # 验证文件大小
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制({settings.MAX_FILE_SIZE} bytes)"
        )

    try:
        # 创建审计任务
        task_id = str(uuid.uuid4())
        audit_task = AuditTask(
            id=task_id,
            task_name=file.filename,
            status=AuditStatus.PENDING,
            total_files=0
        )
        db.add(audit_task)
        db.commit()

        # 保存ZIP文件
        file_service = FileService()
        zip_path = await file_service.save_uploaded_file(file, task_id)

        # 解压并分析文件
        extracted_files = await file_service.extract_zip_file(zip_path, task_id)

        # 统计文件数量
        audit_task.total_files = len(extracted_files)
        db.commit()

        return {
            "code": 200,
            "message": "文件上传成功",
            "data": {
                "task_id": task_id,
                "file_name": file.filename,
                "file_size": file.size,
                "extracted_files": extracted_files,
                "total_files": len(extracted_files)
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"文件处理失败: {str(e)}"
        )

@router.post("/contract")
async def upload_contract_file(
    task_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传单个合同文件
    """
    # 验证任务是否存在
    task = db.query(AuditTask).filter(AuditTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail="审计任务不存在"
        )

    # 验证文件类型
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型，支持的格式: {', '.join(allowed_extensions)}"
        )

    try:
        file_service = FileService()
        file_path = await file_service.save_uploaded_file(file, task_id, "contracts")

        return {
            "code": 200,
            "message": "合同文件上传成功",
            "data": {
                "file_id": str(uuid.uuid4()),
                "file_name": file.filename,
                "file_path": file_path,
                "file_size": file.size
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )

@router.post("/invoices")
async def upload_invoice_files(
    task_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    批量上传发票文件
    """
    # 验证任务是否存在
    task = db.query(AuditTask).filter(AuditTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail="审计任务不存在"
        )

    # 验证文件数量
    if len(files) > 50:  # 限制最多50个文件
        raise HTTPException(
            status_code=400,
            detail="文件数量超过限制，最多支持50个文件"
        )

    try:
        file_service = FileService()
        uploaded_files = []

        for file in files:
            # 验证文件类型
            allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext not in allowed_extensions:
                continue  # 跳过不支持的文件

            file_path = await file_service.save_uploaded_file(file, task_id, "invoices")
            uploaded_files.append({
                "file_id": str(uuid.uuid4()),
                "file_name": file.filename,
                "file_path": file_path,
                "file_size": file.size
            })

        return {
            "code": 200,
            "message": f"成功上传{len(uploaded_files)}个发票文件",
            "data": {
                "task_id": task_id,
                "uploaded_files": uploaded_files,
                "total_count": len(uploaded_files)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件上传失败: {str(e)}"
        )

@router.get("/files/{task_id}")
async def get_task_files(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取任务下的所有文件列表
    """
    # 验证任务是否存在
    task = db.query(AuditTask).filter(AuditTask.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=404,
            detail="审计任务不存在"
        )

    file_service = FileService()
    files = file_service.get_task_files(task_id)

    return {
        "code": 200,
        "message": "获取文件列表成功",
        "data": {
            "task_id": task_id,
            "files": files,
            "total_count": len(files)
        }
    }