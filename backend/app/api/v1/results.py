from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import os

from app.core.database import get_db
from app.services.result_service import ResultService
from app.core.config import settings

router = APIRouter()
result_service = ResultService()


@router.get("/{audit_id}", summary="获取审计结果详情")
async def get_result_details(
    audit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定审计任务的详细结果

    - **audit_id**: 审计ID
    """
    try:
        result = await result_service.get_result_details(audit_id)
        if not result:
            raise HTTPException(status_code=404, detail="审计结果不存在")
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取审计结果失败: {str(e)}")


@router.get("/{audit_id}/summary", summary="获取审计结果摘要")
async def get_result_summary(
    audit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取审计结果的摘要信息

    - **audit_id**: 审计ID
    """
    try:
        summary = await result_service.get_result_summary(audit_id)
        if not summary:
            raise HTTPException(status_code=404, detail="审计结果不存在")
        return summary

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取结果摘要失败: {str(e)}")


@router.get("/{audit_id}/issues", summary="获取发现的问题")
async def get_audit_issues(
    audit_id: str,
    severity: Optional[str] = None,
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取审计中发现的问题列表

    - **audit_id**: 审计ID
    - **severity**: 问题严重程度筛选
    - **type**: 问题类型筛选
    """
    try:
        issues = await result_service.get_audit_issues(audit_id, severity, type)
        return {
            "audit_id": audit_id,
            "issues": issues,
            "total_count": len(issues)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取问题列表失败: {str(e)}")


@router.get("/{audit_id}/comparisons", summary="获取合同-发票对比结果")
async def get_comparisons(
    audit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取合同与发票的详细对比结果

    - **audit_id**: 审计ID
    """
    try:
        comparisons = await result_service.get_comparisons(audit_id)
        return {
            "audit_id": audit_id,
            "comparisons": comparisons
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取对比结果失败: {str(e)}")


@router.get("/{audit_id}/contract-info", summary="获取合同信息")
async def get_contract_info(
    audit_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取提取的合同信息

    - **audit_id**: 审计ID
    """
    try:
        contract_info = await result_service.get_contract_info(audit_id)
        if not contract_info:
            raise HTTPException(status_code=404, detail="合同信息不存在")
        return contract_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取合同信息失败: {str(e)}")


@router.get("/{audit_id}/invoices", summary="获取发票信息")
async def get_invoice_info(
    audit_id: str,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取提取的发票信息

    - **audit_id**: 审计ID
    - **status**: 发票状态筛选
    """
    try:
        invoices = await result_service.get_invoice_info(audit_id, status)
        return {
            "audit_id": audit_id,
            "invoices": invoices,
            "total_count": len(invoices)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取发票信息失败: {str(e)}")


@router.get("/{audit_id}/export/pdf", summary="导出PDF报告")
@router.post("/{audit_id}/export/pdf", summary="导出PDF报告")
async def export_pdf_report(
    audit_id: str,
    include_details: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    导出PDF格式的审计报告

    - **audit_id**: 审计ID
    - **include_details**: 是否包含详细信息
    """
    try:
        pdf_path = await result_service.generate_pdf_report(audit_id, include_details)

        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF报告生成失败")

        return FileResponse(
            path=pdf_path,
            filename=f"audit_report_{audit_id}.pdf",
            media_type="application/pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出PDF报告失败: {str(e)}")


@router.get("/{audit_id}/export/excel", summary="导出Excel报告")
@router.post("/{audit_id}/export/excel", summary="导出Excel报告")
async def export_excel_report(
    audit_id: str,
    include_raw_data: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    导出Excel格式的审计报告

    - **audit_id**: 审计ID
    - **include_raw_data**: 是否包含原始数据
    """
    try:
        excel_path = await result_service.generate_excel_report(audit_id, include_raw_data)

        if not os.path.exists(excel_path):
            raise HTTPException(status_code=500, detail="Excel报告生成失败")

        return FileResponse(
            path=excel_path,
            filename=f"audit_report_{audit_id}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出Excel报告失败: {str(e)}")


@router.get("/{audit_id}/export/json", summary="导出JSON数据")
@router.post("/{audit_id}/export/json", summary="导出JSON数据")
async def export_json_data(
    audit_id: str,
    include_images: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    导出JSON格式的原始数据

    - **audit_id**: 审计ID
    - **include_images**: 是否包含图像数据
    """
    try:
        json_data = await result_service.export_json_data(audit_id, include_images)
        return {
            "audit_id": audit_id,
            "export_time": json_data.get("export_time"),
            "data": json_data.get("data"),
            "metadata": json_data.get("metadata")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出JSON数据失败: {str(e)}")


@router.get("/{audit_id}/images/{image_type}/{image_id}", summary="获取图像文件")
async def get_image_file(
    audit_id: str,
    image_type: str,  # contract, invoice, etc.
    image_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取审计过程中的图像文件

    - **audit_id**: 审计ID
    - **image_type**: 图像类型
    - **image_id**: 图像ID
    """
    try:
        image_path = await result_service.get_image_file(audit_id, image_type, image_id)

        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="图像文件不存在")

        return FileResponse(
            path=image_path,
            filename=os.path.basename(image_path)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取图像文件失败: {str(e)}")


@router.post("/{audit_id}/share", summary="生成分享链接")
async def generate_share_link(
    audit_id: str,
    expire_hours: int = 24,
    password: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    生成审计结果的分享链接

    - **audit_id**: 审计ID
    - **expire_hours**: 链接有效期（小时）
    - **password**: 访问密码（可选）
    """
    try:
        share_info = await result_service.generate_share_link(audit_id, expire_hours, password)
        return share_info

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成分享链接失败: {str(e)}")


@router.get("/shared/{share_id}", summary="访问分享的审计结果")
async def get_shared_result(
    share_id: str,
    password: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    通过分享链接访问审计结果

    - **share_id**: 分享ID
    - **password**: 访问密码（如果设置了密码）
    """
    try:
        result = await result_service.get_shared_result(share_id, password)
        if not result:
            raise HTTPException(status_code=404, detail="分享链接不存在或已过期")
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"访问分享结果失败: {str(e)}")
