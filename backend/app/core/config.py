from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # 基础配置
    app_name: str = "智能合同发票审计系统"
    environment: str = "development"
    debug: bool = True

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8000

    # 数据库配置
    database_url: str = "sqlite:///./audit.db"

    # Redis配置
    redis_url: str = "redis://localhost:6379/0"

    # JWT配置
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 24 * 60
    auth_username: str = "admin"
    auth_password: str = "your-password-here"

    # 文件上传配置
    upload_dir: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: List[str] = [
        "application/pdf",
        "application/zip",
        "image/jpeg",
        "image/png"
    ]
    allowed_extensions: List[str] = [".zip", ".pdf", ".jpg", ".jpeg", ".png"]

    # AI模型配置 - 百度云OCR (传统AK/SK)
    baidu_ocr_api_key: Optional[str] = None
    baidu_ocr_secret_key: Optional[str] = None
    baidu_ocr_api_base: str = "https://aip.baidubce.com/rest/2.0/ocr/v1"

    # AI模型配置 - DeepSeek
    deepseek_api_key: Optional[str] = None
    deepseek_api_base: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # CORS配置
    allowed_hosts: List[str] = ["*"]

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # Celery配置
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # WebSocket配置
    ws_heartbeat_interval: int = 30

    # 审计配置
    max_concurrent_audits: int = 5
    audit_timeout: int = 300
    max_contract_ocr_pages: int = 20
    max_invoice_ocr_pages: int = 5

    class Config:
        env_file = "../.env"  # 从项目根目录加载.env文件
        case_sensitive = False


# 创建全局设置实例
settings = Settings()

# 确保必要的目录存在
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
