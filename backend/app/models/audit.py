from sqlalchemy import Column, String, Integer, Text, DateTime, Enum, Float, ForeignKey
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel

class AuditStatus(enum.Enum):
    """审计状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ResultType(enum.Enum):
    """结果类型枚举"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class SeverityLevel(enum.Enum):
    """严重程度枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AuditTask(BaseModel):
    """
    审计任务模型
    """
    __tablename__ = "audit_tasks"

    task_name = Column(String(255), nullable=False)
    status = Column(Enum(AuditStatus), default=AuditStatus.PENDING, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    current_step = Column(String(100), nullable=True)
    progress_percentage = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)

    # 关联关系
    contracts = relationship("Contract", back_populates="task", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="task", cascade="all, delete-orphan")
    results = relationship("AuditResult", back_populates="task", cascade="all, delete-orphan")

class AuditResult(BaseModel):
    """
    审计结果模型
    """
    __tablename__ = "audit_results"

    task_id = Column(String, ForeignKey("audit_tasks.id"), nullable=False, index=True)
    result_type = Column(Enum(ResultType), nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    affected_entities = Column(Text, nullable=True)  # JSON string
    recommendation = Column(Text, nullable=True)

    # 关联关系
    task = relationship("AuditTask", back_populates="results")