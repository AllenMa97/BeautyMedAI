from pydantic_settings import BaseSettings
import os
from typing import Optional


class Settings(BaseSettings):
    # 项目基本信息
    PROJECT_NAME: str = "Lansee Backend Services"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # PostgreSQL数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://lansee_user:lansee_pass@localhost/lansee_db")
    
    # Redis配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # 算法服务配置
    ALGORITHM_SERVICE_URL: str = os.getenv("ALGORITHM_SERVICE_URL", "http://127.0.0.1:6732")
    
    # JWT配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret-key-change-in-production")
    JWT_REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY", "jwt-refresh-dev-secret-key-change-in-production")
    
    # CORS配置
    BACKEND_CORS_ORIGINS: list = ["*"]  # 在生产环境中应该限制为具体的域名
    
    # 速率限制
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # 会话超时
    SESSION_TIMEOUT_HOURS: int = 24
    
    # 对象存储配置
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # local, s3, oss
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    STORAGE_BUCKET_NAME: str = os.getenv("STORAGE_BUCKET_NAME", "lansee-chatbot")
    
    # RAG配置
    RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
    RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
    RAG_SEARCH_STRATEGY: str = os.getenv("RAG_SEARCH_STRATEGY", "hybrid")  # semantic, keyword, hybrid
    
    # GPU配置
    ENABLE_GPU_MANAGEMENT: bool = os.getenv("ENABLE_GPU_MANAGEMENT", "false").lower() == "true"
    MAX_CONCURRENT_GPU_TASKS: int = int(os.getenv("MAX_CONCURRENT_GPU_TASKS", "4"))
    
    # 系统资源限制
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "50"))  # MB
    MAX_SESSION_MESSAGES: int = int(os.getenv("MAX_SESSION_MESSAGES", "1000"))
    
    class Config:
        env_file = ".env"


settings = Settings()