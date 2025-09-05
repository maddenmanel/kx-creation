"""
API数据模型定义
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl
from datetime import datetime


class CrawlRequest(BaseModel):
    """爬取请求模型"""
    url: HttpUrl
    extract_images: bool = True
    extract_links: bool = True


class PageContent(BaseModel):
    """页面内容模型"""
    url: str
    title: str
    content: str
    images: List[str] = []
    links: List[str] = []
    metadata: Dict[str, Any] = {}
    crawl_time: datetime


class ArticleRequest(BaseModel):
    """文章生成请求模型"""
    page_content: PageContent
    article_style: str = "professional"  # professional, casual, news
    target_audience: str = "general"
    word_count: Optional[int] = None


class GeneratedArticle(BaseModel):
    """生成的文章模型"""
    title: str
    content: str
    summary: str
    tags: List[str] = []
    word_count: int
    generated_time: datetime


class WechatPublishRequest(BaseModel):
    """微信公众号发布请求模型"""
    article: GeneratedArticle
    thumb_media_id: Optional[str] = None  # 封面图片media_id
    author: Optional[str] = None
    digest: Optional[str] = None
    show_cover_pic: bool = True
    need_open_comment: bool = False
    only_fans_can_comment: bool = False


class WechatPublishResponse(BaseModel):
    """微信公众号发布响应模型"""
    success: bool
    message: str
    media_id: Optional[str] = None
    url: Optional[str] = None


class TaskStatus(BaseModel):
    """任务状态模型"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int = 0
    message: str = ""
    result: Optional[Dict[str, Any]] = None
    created_time: datetime
    updated_time: datetime


class AgentResponse(BaseModel):
    """Agent响应模型"""
    agent_name: str
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    processing_time: float
