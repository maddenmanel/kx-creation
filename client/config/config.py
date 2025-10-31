"""
Configuration module for KX Intelligent Content Creation System
Handles environment variables and application settings
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application Settings"""
    
    # Application Configuration
    APP_NAME: str = "KX Intelligent Content Creation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Qwen API Configuration (Required)
    QWEN_API_KEY: str
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    QWEN_MODEL: str = "qwen-turbo"
    
    # AgentScope Configuration
    AGENTSCOPE_TIMEOUT: int = 300
    AGENTSCOPE_MAX_RETRIES: int = 3
    
    # WeChat Official Account Configuration (Optional)
    WECHAT_APP_ID: Optional[str] = None
    WECHAT_APP_SECRET: Optional[str] = None
    
    # Task Management
    TASK_TIMEOUT: int = 600  # 10 minutes
    TASK_CLEANUP_INTERVAL: int = 3600  # 1 hour
    
    # Crawler Configuration
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_MAX_RETRIES: int = 3
    CRAWLER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Content Configuration
    DEFAULT_WORD_COUNT: int = 1000
    MIN_WORD_COUNT: int = 300
    MAX_WORD_COUNT: int = 5000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()

