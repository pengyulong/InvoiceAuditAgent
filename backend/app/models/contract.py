from sqlalchemy import Column, String, Integer, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from decimal import Decimal
from app.models.base import BaseModel

class Contract(BaseModel):
    """
    合同模型
    """
    __tablename__ = "contracts"

    task_id = Column(String, ForeignKey("audit_tasks.id"), nullable=False, index=True)
    contract_number = Column(String(255), nullable=True, index=True)
    buyer_name = Column(String(255), nullable=True)
    seller_name = Column(String(255), nullable=True)
    total_amount = Column(Float, nullable=True)
    tax_rate = Column(Float, nullable=True)
    contract_date = Column(DateTime(timezone=True), nullable=True)
    file_path = Column(Text, nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)

    # AI分析结果
    extracted_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    validation_status = Column(String(50), nullable=True)
    validation_errors = Column(JSON, nullable=True)

    # 关联关系
    task = relationship("AuditTask", back_populates="contracts")

class ContractItem(BaseModel):
    """
    合同商品明细模型
    """
    __tablename__ = "contract_items"

    contract_id = Column(String, ForeignKey("contracts.id"), nullable=False, index=True)
    item_name = Column(String(255), nullable=True)
    specification = Column(String(500), nullable=True)
    quantity = Column(Float, nullable=True)
    unit_price = Column(Float, nullable=True)
    total_price = Column(Float, nullable=True)
    tax_rate = Column(Float, nullable=True)

    # 关联关系
    contract = relationship("Contract", backref="items")