from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import sys
import os
import time
from datetime import datetime

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import audit, upload, results
from app.services.websocket_service import websocket_manager

# 配置全局日志
import logging
from logging.handlers import RotatingFileHandler

def setup_global_logger():
    """设置全局日志系统"""
    # 创建日志目录
    log_dir = os.path.dirname(settings.LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)

    # 调试环境变量加载
    logger_temp = logging.getLogger("temp_debug")
    logger_temp.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger_temp.addHandler(handler)

    logger_temp.info(f"🔍 当前工作目录: {os.getcwd()}")
    logger_temp.info(f"🔍 .env文件路径: {os.path.abspath('.env')}")
    logger_temp.info(f"🔍 .env文件存在: {os.path.exists('.env')}")

    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
            has_qwen = 'QWEN_API_KEY=' in env_content
            has_deepseek = 'DEEPSEEK_API_KEY=' in env_content
            logger_temp.info(f"🔍 .env文件包含QWEN_API_KEY: {has_qwen}")
            logger_temp.info(f"🔍 .env文件包含DEEPSEEK_API_KEY: {has_deepseek}")

    logger_temp.handlers.clear()

    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件处理器
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger

# 初始化全局日志
logger = setup_global_logger()

# 请求日志中间件
async def log_requests(request: Request, call_next):
    """记录所有HTTP请求"""
    start_time = time.time()

    # 记录请求开始
    logger.info(f"🚀 请求开始: {request.method} {request.url}")
    logger.info(f"📋 请求头: {dict(request.headers)}")

    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            logger.info(f"📦 请求体大小: {len(body)} bytes")
            # 只记录前500字符的请求体用于调试
            if body:
                body_preview = body[:500].decode('utf-8', errors='ignore')
                logger.info(f"📝 请求体预览: {body_preview}")
        except Exception as e:
            logger.error(f"❌ 读取请求体失败: {e}")

    try:
        # 执行请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录响应
        logger.info(f"✅ 请求完成: {request.method} {request.url} | 状态码: {response.status_code} | 耗时: {process_time:.3f}s")

        return response

    except Exception as e:
        # 记录错误
        process_time = time.time() - start_time
        logger.error(f"❌ 请求失败: {request.method} {request.url} | 错误: {str(e)} | 耗时: {process_time:.3f}s")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时执行
    logger.info("🚀 智能合同发票审计系统启动中...")
    logger.info(f"📋 配置信息: HOST={settings.HOST}, PORT={settings.PORT}, DEBUG={settings.DEBUG}")
    logger.info(f"🔑 API配置: QWEN_API_KEY={'已配置' if settings.QWEN_API_KEY else '未配置'}, DEEPSEEK_API_KEY={'已配置' if settings.DEEPSEEK_API_KEY else '未配置'}")

    # 初始化数据库
    try:
        init_db()
        logger.info("✅ 数据库初始化完成")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise

    logger.info("🎉 应用启动完成，开始接收请求...")
    yield

    # 关闭时执行
    logger.info("👋 应用关闭中...")
    try:
        await websocket_manager.disconnect_all()
        logger.info("✅ WebSocket连接已断开")
    except Exception as e:
        logger.error(f"❌ WebSocket断开失败: {e}")

    logger.info("🛑 应用已完全关闭")

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="基于AI的智能合同发票审计系统",
    lifespan=lifespan
)

# 添加请求日志中间件
app.middleware("http")(log_requests)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("🔧 中间件配置完成")

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
@app.websocket("/ws/audit/{task_id}")
async def websocket_endpoint(websocket, task_id: str):
    """
    WebSocket连接端点，用于实时推送审计进度
    """
    logger.info(f"🔌 WebSocket连接请求: task_id={task_id}")
    try:
        await websocket_manager.connect(websocket, task_id)
        logger.info(f"✅ WebSocket连接成功: task_id={task_id}")

        while True:
            try:
                # 保持连接活跃
                message = await websocket.receive_text()
                logger.info(f"📨 收到WebSocket消息: task_id={task_id}, message={message}")
            except Exception as e:
                logger.warning(f"⚠️ WebSocket消息接收异常: task_id={task_id}, error={e}")
                break

    except Exception as e:
        logger.error(f"❌ WebSocket连接异常: task_id={task_id}, error={e}")
    finally:
        try:
            websocket_manager.disconnect(task_id)
            logger.info(f"🔌 WebSocket连接已断开: task_id={task_id}")
        except Exception as e:
            logger.error(f"❌ WebSocket断开失败: task_id={task_id}, error={e}")

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