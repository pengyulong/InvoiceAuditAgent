import uuid as _uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


def _new_uuid():
    return str(_uuid.uuid4())


class AuditTask(Base):
    """审计任务模型"""
    __tablename__ = "audit_tasks"

    id = Column(String, primary_key=True, default=_new_uuid)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")  # pending, processing, completed, failed, paused, cancelled
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(100))
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    error_message = Column(Text)
    file_path = Column(String(500))
    config = Column(JSON)
    result_data = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))


class Contract(Base):
    """合同信息模型"""
    __tablename__ = "contracts"

    id = Column(String, primary_key=True, default=_new_uuid)
    task_id = Column(String, nullable=False)
    contract_number = Column(String(255))
    buyer_name = Column(String(255))
    seller_name = Column(String(255))
    total_amount = Column(Float)
    tax_rate = Column(Float)
    contract_date = Column(DateTime(timezone=True))
    file_path = Column(String(500))
    extracted_data = Column(JSON)
    confidence_score = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Invoice(Base):
    """发票信息模型"""
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=_new_uuid)
    task_id = Column(String, nullable=False)
    invoice_code = Column(String(255))
    invoice_number = Column(String(255))
    buyer_name = Column(String(255))
    seller_name = Column(String(255))
    total_amount = Column(Float)
    tax_amount = Column(Float)
    invoice_date = Column(DateTime(timezone=True))
    file_path = Column(String(500))
    extracted_data = Column(JSON)
    confidence_score = Column(Float)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(String)  # 重复发票的ID

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditResult(Base):
    """审计结果模型"""
    __tablename__ = "audit_results"

    id = Column(String, primary_key=True, default=_new_uuid)
    task_id = Column(String, nullable=False)
    result_type = Column(String(50), nullable=False)  # error, warning, info
    severity = Column(String(20), nullable=False)  # high, medium, low
    title = Column(String(255), nullable=False)
    description = Column(Text)
    affected_entities = Column(JSON)  # 涉及的合同/发票ID
    recommendation = Column(Text)
    auto_fixable = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AgentExecution(Base):
    """Agent执行记录模型"""
    __tablename__ = "agent_executions"

    id = Column(String, primary_key=True, default=_new_uuid)
    task_id = Column(String, nullable=False)
    agent_name = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)  # coordinator, contract_analyzer, invoice_analyzer, cross_validator
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    input_data = Column(JSON)
    output_data = Column(JSON)
    error_message = Column(Text)
    execution_time = Column(Float)  # 执行时间（秒）

    created_at = Column(DateTime(timezone=True), server_default=func.now())