from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AuditConfig(BaseModel):
    """审计配置"""
    enable_duplicate_detection: bool = Field(default=True, description="启用重复检测")
    enable_amount_validation: bool = Field(default=True, description="启用金额验证")
    enable_content_matching: bool = Field(default=True, description="启用内容匹配")
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="置信度阈值")
    max_processing_time: int = Field(default=300, ge=60, le=1800, description="最大处理时间（秒）")

    model_config = {
        "json_schema_extra": {
            "example": {
                "enable_duplicate_detection": True,
                "enable_amount_validation": True,
                "enable_content_matching": True,
                "confidence_threshold": 0.8,
                "max_processing_time": 300
            }
        }
    }


class AuditRequest(BaseModel):
    """审计请求"""
    task_id: str = Field(..., description="任务ID")
    audit_config: AuditConfig = Field(..., description="审计配置")


class AgentStatus(BaseModel):
    """Agent状态"""
    name: str = Field(..., description="Agent名称")
    status: str = Field(..., description="状态：idle, running, completed, error")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="进度百分比")
    message: Optional[str] = Field(None, description="状态消息")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class AuditStatusResponse(BaseModel):
    """审计状态响应"""
    audit_id: str = Field(..., description="审计ID")
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: int = Field(..., description="进度百分比")
    current_step: str = Field(..., description="当前步骤")
    agent_status: Dict[str, AgentStatus] = Field(default_factory=dict, description="Agent状态")
    estimated_time_remaining: Optional[int] = Field(None, description="预计剩余时间（秒）")
    error_message: Optional[str] = Field(None, description="错误信息")
    total_files: int = Field(default=0, description="总文件数")
    processed_files: int = Field(default=0, description="已处理文件数")
    processing_time: float = Field(default=0, description="处理耗时（秒）")
    confidence_score: float = Field(default=0, description="总体置信度")


class AuditResponse(BaseModel):
    """审计响应"""
    audit_id: str = Field(..., description="审计ID")
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="状态")
    message: str = Field(..., description="消息")


class FileInfo(BaseModel):
    """文件信息"""
    id: str = Field(..., description="文件ID")
    name: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
    type: str = Field(..., description="文件类型")
    category: str = Field(..., description="文件分类")
    path: str = Field(..., description="文件路径")
    created_at: datetime = Field(..., description="创建时间")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")


class ContractInfo(BaseModel):
    """合同信息"""
    contract_number: str = Field(..., description="合同编号")
    buyer_name: str = Field(..., description="买方名称")
    seller_name: str = Field(..., description="卖方名称")
    total_amount: float = Field(..., description="合同总金额")
    tax_rate: float = Field(..., description="税率")
    contract_date: Optional[datetime] = Field(None, description="合同日期")
    items: list = Field(default_factory=list, description="商品清单")
    confidence_score: float = Field(..., description="置信度")


class InvoiceInfo(BaseModel):
    """发票信息"""
    invoice_number: str = Field(..., description="发票号码")
    invoice_code: Optional[str] = Field(None, description="发票代码")
    buyer_name: str = Field(..., description="买方名称")
    seller_name: str = Field(..., description="卖方名称")
    total_amount: float = Field(..., description="发票总金额")
    tax_amount: float = Field(..., description="税额")
    invoice_date: Optional[datetime] = Field(None, description="发票日期")
    status: str = Field(..., description="发票状态")
    confidence_score: float = Field(..., description="置信度")
    is_duplicate: bool = Field(default=False, description="是否重复")
    duplicate_of: Optional[str] = Field(None, description="重复的发票ID")


class IssueInfo(BaseModel):
    """问题信息"""
    id: str = Field(..., description="问题ID")
    type: str = Field(..., description="问题类型")
    severity: str = Field(..., description="严重程度")
    title: str = Field(..., description="问题标题")
    description: str = Field(..., description="问题描述")
    recommendation: str = Field(..., description="建议")
    affected_entities: list = Field(default_factory=list, description="影响的实体")
    auto_fixable: bool = Field(default=False, description="是否可自动修复")


class ComparisonResult(BaseModel):
    """对比结果"""
    product_name: str = Field(..., description="商品名称")
    contract_quantity: float = Field(..., description="合同数量")
    invoice_quantity: float = Field(..., description="发票数量")
    difference: float = Field(..., description="差异数量")
    status: str = Field(..., description="匹配状态")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")


class AuditSummary(BaseModel):
    """审计摘要"""
    audit_id: str = Field(..., description="审计ID")
    status: str = Field(..., description="审计状态")
    contract_amount: float = Field(..., description="合同金额")
    invoice_total: float = Field(..., description="发票总金额")
    coverage: float = Field(..., description="覆盖率")
    issue_count: int = Field(..., description="问题数量")
    processing_time: float = Field(..., description="处理时间（秒）")
    confidence_score: float = Field(..., description="总体置信度")
    conclusion: str = Field(..., description="审计结论")


class AuditResults(BaseModel):
    """完整审计结果"""
    audit_id: str = Field(..., description="审计ID")
    task_id: str = Field(..., description="任务ID")
    summary: AuditSummary = Field(..., description="审计摘要")
    contract_info: Optional[ContractInfo] = Field(None, description="合同信息")
    invoices: list[InvoiceInfo] = Field(default_factory=list, description="发票列表")
    issues: list[IssueInfo] = Field(default_factory=list, description="问题列表")
    comparisons: list[ComparisonResult] = Field(default_factory=list, description="对比结果")
    agent_executions: list = Field(default_factory=list, description="Agent执行记录")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class AuditHistoryItem(BaseModel):
    """审计历史项"""
    task_id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    status: str = Field(..., description="状态")
    progress: int = Field(..., description="进度")
    total_files: int = Field(..., description="总文件数")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    processing_time: Optional[float] = Field(None, description="处理时间")


class AuditStatistics(BaseModel):
    """审计统计"""
    total_audits: int = Field(..., description="总审计次数")
    completed_audits: int = Field(..., description="已完成审计次数")
    failed_audits: int = Field(..., description="失败审计次数")
    success_rate: float = Field(..., description="成功率")
    average_processing_time: float = Field(..., description="平均处理时间")
    total_amount_processed: float = Field(..., description="处理的总金额")
    total_issues_found: int = Field(..., description="发现的总问题数")
    contracts_processed: int = Field(..., description="处理的合同数")
    invoices_processed: int = Field(..., description="处理的发票数")
