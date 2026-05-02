from fastapi import Depends, FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1 import audit as audit_api, auth, upload, results
from app.core.auth import get_current_user, verify_access_token
from app.core.database import init_db
from app.services.websocket_service import websocket_manager
from app.services.audit_service import audit_service
# 确保导入所有模型以便创建数据库表
from app.models import audit as audit_model
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("正在启动智能合同发票审计系统...")
    # 初始化数据库表
    await init_db()
    logger.info("系统启动完成")
    yield
    # 关闭时执行
    logger.info("正在关闭系统...")


# 创建FastAPI应用实例
app = FastAPI(
    title="智能合同发票审计系统",
    description="基于AI的智能合同发票审计系统API",
    version="1.0.0",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan
)

# 配置CORS
allowed_origins = list(settings.allowed_hosts)
if settings.environment == "development":
    allowed_origins = sorted(set(allowed_origins) | {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    })

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["登录认证"])
app.include_router(audit_api.router, prefix="/api/v1/audit", tags=["审计"], dependencies=[Depends(get_current_user)])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["文件上传"], dependencies=[Depends(get_current_user)])
app.include_router(results.router, prefix="/api/v1/results", tags=["结果查询"], dependencies=[Depends(get_current_user)])

# WebSocket路由
@app.websocket("/ws/audit/{audit_id}")
async def websocket_endpoint(websocket: WebSocket, audit_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    try:
        verify_access_token(token)
    except Exception:
        await websocket.close(code=1008)
        return

    connection_id = await websocket_manager.connect(websocket, audit_id)

    # 连接后立即发送当前审计状态（解决前端连接延迟导致错过初始消息的问题）
    try:
        state = audit_service.active_tasks.get(audit_id, {})
        if state and state.get("status") == "running":
            status_info = await audit_service.get_audit_status(audit_id)
            cur_step = state.get("current_step", "未知")
            cur_progress = state.get("progress", 0)
            await websocket_manager.send_progress(audit_id, {
                "progress": cur_progress,
                "current_step": cur_step,
                "step_id": "reconnect",
                "step_name": cur_step,
                "message": f"已恢复连接，当前进度: {cur_progress}%"
            })
            await websocket_manager.send_log(audit_id,
                f"审计已在进行中 - 当前步骤: {cur_step}, 进度: {cur_progress}%", "info")
    except Exception as e:
        logger.warning(f"发送初始状态失败: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息（如心跳响应等）
            logger.debug(f"WebSocket收到消息: audit_id={audit_id}, data={data[:100]}")
    except Exception:
        pass
    finally:
        websocket_manager.disconnect(audit_id, connection_id)


@app.get("/")
async def root():
    return {
        "message": "智能合同发票审计系统API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.environment == "development" else False,
        log_level="info"
    )
