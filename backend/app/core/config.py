from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    # 应用基础配置
    PROJECT_NAME: str = "智能合同发票审计系统"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    DEBUG: bool = True

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./audit.db"

    # Redis配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS配置
    ALLOWED_HOSTS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]

    # AI模型API配置
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_API_KEY: Optional[str] = None
    QWEN_MODEL: str = "qwen3-vl-plus"

    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # 文件上传配置
    MAX_FILE_SIZE: int = 52428800  # 50MB
    UPLOAD_DIR: str = "./uploads"
    ALLOWED_EXTENSIONS: List[str] = [".zip", ".pdf", ".jpg", ".jpeg", ".png"]

    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "../logs/backend.log"

    # WebSocket配置
    WS_HEARTBEAT_INTERVAL: int = 30

    # 审计配置
    MAX_CONCURRENT_AUDITS: int = 5
    AUDIT_TIMEOUT: int = 300  # 5分钟

    model_config = SettingsConfigDict(
        env_file="../.env",  # 从backend目录查找项目根目录的.env
        case_sensitive=True,
        extra="allow"
    )

# 创建全局设置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)