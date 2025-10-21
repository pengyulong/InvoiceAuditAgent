from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func
from app.core.database import Base

class BaseModel(Base):
    """
    基础模型类
    """
    __abstract__ = True

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())