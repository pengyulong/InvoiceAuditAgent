from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os
import uuid
import zipfile
import aiofiles
# import python_magic  # 暂时移除以避免依赖问题
from pathlib import Path

from app.core.database import get_db
from app.core.config import settings
from app.services.file_service import FileService
from app.models.audit import AuditTask

router = APIRouter()
file_service = FileService()


def _decode_zip_member_name(name: str) -> str:
    """Recover ZIP member names that were encoded with non-ASCII encodings."""
    for encoding in ("utf-8", "gbk", "cp936"):
        try:
            decoded = name.encode("cp437").decode(encoding)
            if decoded:
                return decoded
        except UnicodeError:
            continue
    return name


def _safe_zip_target(base_dir: Path, member_name: str) -> Path:
    target = base_dir / Path(member_name)
    resolved_base = base_dir.resolve()
    resolved_target = target.resolve()
    if resolved_base not in resolved_target.parents and resolved_target != resolved_base:
        raise HTTPException(status_code=400, detail="ZIP文件包含非法路径")
    return target


def _build_file_summary(files: List[dict]) -> dict:
    contracts = sum(1 for item in files if item.get("category") == "contract")
    invoices = sum(1 for item in files if item.get("category") == "invoice")
    others = len(files) - contracts - invoices
    warnings = []
    # 如果没有识别到合同但有发票，审计时协调器会自动将第一份文件视为合同
    if contracts == 0 and invoices > 0:
        contracts = 1
        invoices -= 1
        # 更新第一份原发票文件的 category
        for item in files:
            if item.get("category") == "invoice":
                item["category"] = "contract"
                break
    if contracts != 1:
        warnings.append(f"识别到{contracts}份合同，建议上传前确认ZIP中仅包含1份合同")
    if invoices < 1:
        warnings.append("未识别到发票文件")
    return {
        "contracts": contracts,
        "invoices": invoices,
        "others": others,
        "warnings": warnings,
    }


def _write_sample_pdf(path: Path, title: str, lines: List[str]):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=A4)
    _, height = A4
    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, title)
    y -= 36
    c.setFont("Helvetica", 11)
    for line in lines:
        c.drawString(72, y, line)
        y -= 20
    c.save()


def _ensure_sample_zip() -> Path:
    sample_dir = Path(settings.upload_dir) / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample_zip = sample_dir / "sample_contract_invoice_audit.zip"
    if sample_zip.exists():
        return sample_zip

    work_dir = sample_dir / "sample_source"
    work_dir.mkdir(parents=True, exist_ok=True)
    contract_pdf = work_dir / "contract_sample.pdf"
    invoice_pdf = work_dir / "invoice_sample.pdf"

    _write_sample_pdf(contract_pdf, "Sample Service Contract", [
        "Contract No: SAMPLE-2026-001",
        "Buyer: Demo Buyer Co., Ltd.",
        "Seller: Demo Seller Co., Ltd.",
        "Contract Date: 2026-05-01",
        "Service Item: Promotion Service",
        "Total Amount Including Tax: 50000.00 CNY",
        "Tax Rate: 6%",
        "Payment Terms: Pay within 30 days after invoice received.",
    ])
    _write_sample_pdf(invoice_pdf, "Sample VAT Invoice", [
        "Invoice No: SAMPLE-INVOICE-001",
        "Invoice Date: 2026-05-01",
        "Buyer: Demo Buyer Co., Ltd.",
        "Seller: Demo Seller Co., Ltd.",
        "Item: Promotion Service",
        "Amount Without Tax: 47169.81 CNY",
        "Tax Rate: 6%",
        "Tax Amount: 2830.19 CNY",
        "Total Amount Including Tax: 50000.00 CNY",
    ])

    with zipfile.ZipFile(sample_zip, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        zip_ref.write(contract_pdf, contract_pdf.name)
        zip_ref.write(invoice_pdf, invoice_pdf.name)
    return sample_zip


@router.get("/sample", summary="下载示例ZIP文件")
async def download_sample_zip():
    try:
        sample_zip = _ensure_sample_zip()
        return FileResponse(
            path=sample_zip,
            filename=sample_zip.name,
            media_type="application/zip",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成示例文件失败: {str(e)}")


@router.post("/zip", summary="上传ZIP文件")
async def upload_zip(
    file: UploadFile = File(...),
    task_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    上传包含合同和发票的ZIP文件

    - **file**: ZIP文件，包含1份合同和多份发票
    - **task_name**: 可选的任务名称
    """
    # 验证文件类型
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="只支持ZIP文件格式")

    # 验证文件大小
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制({settings.max_file_size / 1024 / 1024:.1f}MB)"
        )

    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 创建任务目录
        task_dir = Path(settings.upload_dir) / task_id
        task_dir.mkdir(exist_ok=True)

        # 保存ZIP文件
        zip_path = task_dir / file.filename
        async with aiofiles.open(zip_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # 解压ZIP文件
        extracted_files = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            extracted_dir = task_dir / "extracted"
            extracted_dir.mkdir(parents=True, exist_ok=True)

            for member in zip_ref.infolist():
                decoded_name = _decode_zip_member_name(member.filename)
                target_path = _safe_zip_target(extracted_dir, decoded_name)

                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue

                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zip_ref.open(member, "r") as source, open(target_path, "wb") as target:
                    target.write(source.read())

            # 分析解压的文件（跳过macOS隐藏文件和目录）
            for file_path in sorted(extracted_dir.rglob("*")):
                if file_path.is_file():
                    # 跳过macOS资源分支文件和系统隐藏文件
                    parts = file_path.parts
                    if any(p.startswith("__MACOSX") for p in parts):
                        continue
                    if file_path.name.startswith("._"):
                        continue
                    file_info = await file_service.analyze_file(file_path)
                    extracted_files.append(file_info)

        file_summary = _build_file_summary(extracted_files)

        # 创建审计任务
        task = AuditTask(
            id=task_id,
            name=task_name or f"审计任务-{task_id[:8]}",
            status="pending",
            total_files=len(extracted_files),
            file_path=str(zip_path)
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        return {
            "task_id": task_id,
            "message": "文件上传成功",
            "files": extracted_files,
            "summary": file_summary,
            "task": {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "total_files": task.total_files,
                "summary": file_summary
            }
        }

    except Exception as e:
        await db.rollback()
        import traceback
        error_detail = f"文件处理失败: {str(e)}\n堆栈信息:\n{traceback.format_exc()}"
        print(f"上传文件错误: {error_detail}")  # 临时添加调试信息
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/contract", summary="上传单个合同文件")
async def upload_contract(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    上传单个合同文件

    - **file**: 合同文件（PDF、JPG、PNG）
    """
    # 验证文件类型
    if not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="合同文件只支持PDF、JPG、PNG格式")

    try:
        # 生成文件ID
        file_id = str(uuid.uuid4())

        # 保存文件
        file_path = Path(settings.upload_dir) / "contracts" / f"{file_id}_{file.filename}"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # 分析文件
        file_info = await file_service.analyze_file(file_path)

        return {
            "file_id": file_id,
            "message": "合同文件上传成功",
            "file_info": file_info
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/invoice-batch", summary="批量上传发票文件（发票识别模式）")
async def upload_invoice_batch(
    files: List[UploadFile] = File(...),
    task_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    批量上传发票文件用于独立发票识别（不需要合同）

    - **files**: 发票文件列表（PDF、JPG、PNG）
    - **task_name**: 可选的任务名称
    """
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="请至少上传一个文件")
    if len(files) > 50:
        raise HTTPException(status_code=400, detail="单次最多上传50个文件")

    try:
        task_id = str(uuid.uuid4())
        task_dir = Path(settings.upload_dir) / task_id
        extracted_dir = task_dir / "extracted"
        extracted_dir.mkdir(parents=True, exist_ok=True)

        uploaded_files = []
        file_paths = []

        for file in files:
            if not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                continue

            safe_name = f"{str(uuid.uuid4())[:8]}_{file.filename}"
            file_path = extracted_dir / safe_name

            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)

            file_info = await file_service.analyze_file(file_path)
            uploaded_files.append(file_info)
            file_paths.append(str(file_path))

        task = AuditTask(
            id=task_id,
            name=task_name or f"发票识别-{task_id[:8]}",
            status="pending",
            total_files=len(uploaded_files),
            file_path=str(extracted_dir),
            result_data={"file_paths": file_paths},
        )

        db.add(task)
        await db.commit()
        await db.refresh(task)

        return {
            "task_id": task_id,
            "message": f"成功上传{len(uploaded_files)}个发票文件",
            "files": uploaded_files,
            "file_count": len(uploaded_files),
            "task": {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "total_files": task.total_files,
            },
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/invoices", summary="批量上传发票文件")
async def upload_invoices(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    批量上传发票文件

    - **files**: 发票文件列表（PDF、JPG、PNG）
    """
    if len(files) == 0:
        raise HTTPException(status_code=400, detail="请至少上传一个文件")

    if len(files) > 50:  # 限制单次上传数量
        raise HTTPException(status_code=400, detail="单次最多上传50个文件")

    try:
        uploaded_files = []

        for file in files:
            # 验证文件类型
            if not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
                continue  # 跳过不支持的文件类型

            # 生成文件ID
            file_id = str(uuid.uuid4())

            # 保存文件
            file_path = Path(settings.upload_dir) / "invoices" / f"{file_id}_{file.filename}"
            file_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)

            # 分析文件
            file_info = await file_service.analyze_file(file_path)
            uploaded_files.append({
                "file_id": file_id,
                "file_info": file_info
            })

        return {
            "message": f"成功上传{len(uploaded_files)}个发票文件",
            "files": uploaded_files
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/preview", summary="预览文件")
async def preview_file(path: str):
    """
    预览上传的文件（PDF/图片），返回文件内容供浏览器直接渲染

    - **path**: 文件的绝对路径（由上传接口返回的 path 字段）
    """
    try:
        file_path = Path(path).resolve()
        upload_dir = Path(settings.upload_dir).resolve()

        # 安全检查：确保文件在允许的目录内（防路径穿越）
        if upload_dir not in file_path.parents and file_path != upload_dir:
            raise HTTPException(status_code=403, detail="禁止访问该路径")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        ext = file_path.suffix.lower()
        media_types = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }
        media_type = media_types.get(ext, "application/octet-stream")

        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            headers={"Content-Disposition": "inline"},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览文件失败: {str(e)}")


@router.get("/file/{file_id}/info", summary="获取文件信息")
async def get_file_info(file_id: str):
    """
    获取已上传文件的信息

    - **file_id**: 文件ID
    """
    try:
        # 查找文件
        for root_dir in [settings.upload_dir, "uploads"]:
            for file_path in Path(root_dir).rglob(f"*{file_id}*"):
                if file_path.is_file():
                    file_info = await file_service.analyze_file(file_path)
                    return {
                        "file_id": file_id,
                        "file_info": file_info,
                        "file_path": str(file_path)
                    }

        raise HTTPException(status_code=404, detail="文件未找到")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")


@router.delete("/file/{file_id}", summary="删除文件")
async def delete_file(file_id: str):
    """
    删除已上传的文件

    - **file_id**: 文件ID
    """
    try:
        # 查找并删除文件
        deleted_files = []
        for root_dir in [settings.upload_dir, "uploads"]:
            for file_path in Path(root_dir).rglob(f"*{file_id}*"):
                if file_path.is_file():
                    file_path.unlink()
                    deleted_files.append(str(file_path))

        if not deleted_files:
            raise HTTPException(status_code=404, detail="文件未找到")

        return {
            "message": "文件删除成功",
            "deleted_files": deleted_files
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")
