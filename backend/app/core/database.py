from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
import asyncio

from app.core.config import settings


# SQLAlchemy Base类
class Base(DeclarativeBase):
    pass


# 异步数据库引擎
async_engine = create_async_engine(
    settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///"),
    echo=settings.debug,
    future=True
)

# 同步数据库引擎（用于Alembic迁移）
sync_engine = create_engine(
    settings.database_url,
    echo=settings.debug
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# 依赖注入：获取数据库会话
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# 初始化数据库
async def init_db():
    async with async_engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)


# 创建所有表（同步版本，用于Alembic）
def create_all_tables():
    Base.metadata.create_all(bind=sync_engine)


# 删除所有表（仅用于开发环境）
def drop_all_tables():
    Base.metadata.drop_all(bind=sync_engine)