from sqlalchemy import Column, String, Integer, Text, DateTime, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Invoice(BaseModel):
    """
    发票模型
    """
    __tablename__ = "invoices"

    task_id = Column(String, ForeignKey("audit_tasks.id"), nullable=False, index=True)
    invoice_code = Column(String(255), nullable=True, index=True)
    invoice_number = Column(String(255), nullable=True, index=True)
    buyer_name = Column(String(255), nullable=True)
    seller_name = Column(String(255), nullable=True)
    total_amount = Column(Float, nullable=True)
    tax_amount = Column(Float, nullable=True)
    invoice_date = Column(DateTime(timezone=True), nullable=True)
    file_path = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)

    # AI分析结果
    extracted_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    validation_status = Column(String(50), nullable=True)
    validation_errors = Column(JSON, nullable=True)

    # 重复检测
    is_duplicate = Column(Boolean, default=False)
    duplicate_group_id = Column(String(255), nullable=True)

    # 关联关系
    task = relationship("AuditTask", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceItem(BaseModel):
    """
    发票商品明细模型
    """
    __tablename__ = "invoice_items"

    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False, index=True)
    item_name = Column(String(255), nullable=True)
    specification = Column(String(500), nullable=True)
    quantity = Column(Float, nullable=True)
    unit_price = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)
    tax_rate = Column(Float, nullable=True)

    # 关联关系
    invoice = relationship("Invoice", back_populates="items")