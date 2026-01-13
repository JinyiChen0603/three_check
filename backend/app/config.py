"""
应用配置文件
使用 pydantic-settings 管理环境变量
"""

from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基本信息
    APP_NAME: str = "数学题目三重质检工具"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    INSTANCE_NAME: str = "development"
    
    # 安全配置
    SECRET_KEY: str = "dev-secret-change-me-in-production"
    
    # 数据库配置
    DATABASE_URL: Optional[str] = None
    MONGODB_URL: Optional[str] = None
    
    # Redis 配置（用于进度追踪）
    REDIS_URL: Optional[str] = None
    
    # CORS 配置
    CORS_ORIGINS: str = "*"
    
    # AI API Keys
    OPENROUTER_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    CANOPY_WAVE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ZHIPU_API_KEY: Optional[str] = None
    DOUBAO_API_KEY: Optional[str] = None
    
    # 业务配置
    PROBLEM_REWARD: float = 50.0
    REVIEW_REWARD: float = 10.0
    MAX_TASKS_PER_CLAIM: int = 50
    TASK_TIMEOUT_HOURS: int = 12
    VALIDATION_ATTEMPTS: int = 8
    VALIDATION_MAX_CORRECT: int = 4
    VALIDATION_CONCURRENT_PROBLEMS: int = 1
    ADMIN_APPROVAL_ENABLED: bool = False
    
    # JWT 配置
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    
    @property
    def cors_origins_list(self) -> List[str]:
        """将 CORS_ORIGINS 字符串转换为列表"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # 允许额外的环境变量


# 创建全局配置实例
settings = Settings()
