from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import audit, upload, results
from app.services.websocket_service import websocket_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    print("🚀 智能合同发票审计系统启动中...")
    init_db()
    print("✅ 数据库初始化完成")

    yield

    # 关闭时执行
    print("👋 应用关闭中...")
    await websocket_manager.disconnect_all()

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="基于AI的智能合同发票审计系统",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 注册API路由
app.include_router(
    audit.router,
    prefix=f"{settings.API_V1_STR}/audit",
    tags=["审计管理"]
)
app.include_router(
    upload.router,
    prefix=f"{settings.API_V1_STR}/upload",
    tags=["文件上传"]
)
app.include_router(
    results.router,
    prefix=f"{settings.API_V1_STR}/results",
    tags=["结果查询"]
)

# WebSocket路由
@app.websocket("/ws/audit/{audit_id}")
async def websocket_endpoint(websocket, audit_id: str):
    """
    WebSocket连接端点，用于实时推送审计进度
    """
    await websocket_manager.connect(websocket, audit_id)
    try:
        while True:
            # 保持连接活跃
            await websocket.receive_text()
    except Exception as e:
        print(f"WebSocket连接断开: {e}")
    finally:
        websocket_manager.disconnect(audit_id)

@app.get("/")
async def root():
    """
    根路径
    """
    return {
        "message": "智能合同发票审计系统",
        "version": settings.VERSION,
        "docs": "/docs",
        "api": f"{settings.API_V1_STR}"
    }

@app.get("/health")
async def health_check():
    """
    健康检查
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": "2024-01-01T00:00:00Z"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )