"""
配置管理
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    app_name: str = "KX智能内容创作系统"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 服务配置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 千问API配置
    qwen_api_key: str = os.environ.get('QWEN_API_KEY', '')
    qwen_base_url: str = os.environ.get('QWEN_BASE_URL', '')
    qwen_model: str = os.environ.get('QWEN_MODEL', 'qwen-turbo')
    
    # 微信公众号配置
    wechat_app_id: str = os.environ.get('WECHAT_APP_ID', '')
    wechat_app_secret: str = os.environ.get('WECHAT_APP_SECRET', '')
    
    # 爬虫配置
    crawl_timeout: int = 30
    max_content_length: int = 1000000  # 1MB
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # AutoGen配置
    autogen_cache_seed: int = 42
    autogen_timeout: int = 300
    
    class Config:
        env_file = ".env"


settings = Settings()