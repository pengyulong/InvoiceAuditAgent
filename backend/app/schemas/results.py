"""
结果相关的Pydantic模型
"""

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class TaskSummary(BaseModel):
    """任务摘要"""
    id: str
    task_name: str
    status: str
    progress_percentage: int
    total_files: int
    processed_files: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应"""
    data: List[TaskSummary]
    total: int
    page: int
    size: int
    pages: int


class TaskStatisticsResponse(BaseModel):
    """任务统计响应"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    processing_tasks: int
    total_contracts: int
    total_invoices: int
    success_rate: float


class ValidationResult(BaseModel):
    """验证结果"""
    type: str
    severity: str
    description: str
    details: Optional[str] = None
    contract_id: Optional[str] = None
    invoice_id: Optional[str] = None


class ValidationSummary(BaseModel):
    """验证摘要"""
    total_validations: int
    passed_validations: int
    failed_validations: int
    success_rate: float
    total_issues: int
    severity_distribution: dict
    validation_status: str


class AuditReportResponse(BaseModel):
    """审计报告响应"""
    task_id: str
    task_name: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    summary: ValidationSummary
    issues: List[ValidationResult]
    contracts: List[dict]
    invoices: List[dict]