"""
Data models and schemas for API requests and responses
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from datetime import datetime


# Enums
class ArticleStyle(str, Enum):
    """Article writing styles"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    NEWS = "news"


class TargetAudience(str, Enum):
    """Target audience types"""
    GENERAL = "general"
    TECHNICAL = "technical"
    BUSINESS = "business"


class TaskStatus(str, Enum):
    """Task status types"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Request Models
class CrawlRequest(BaseModel):
    """Web crawling request"""
    url: HttpUrl = Field(..., description="Target URL to crawl")
    extract_images: bool = Field(True, description="Whether to extract images")
    extract_links: bool = Field(True, description="Whether to extract links")


class AnalyzeRequest(BaseModel):
    """Content analysis request"""
    title: str = Field(..., description="Content title")
    content: str = Field(..., description="Content body text")
    images: Optional[List[str]] = Field(None, description="Image URLs")
    links: Optional[List[str]] = Field(None, description="Link URLs")


class WriteRequest(BaseModel):
    """Article writing request"""
    analysis_result: Dict[str, Any] = Field(..., description="Analysis result from analyzer")
    article_style: ArticleStyle = Field(ArticleStyle.PROFESSIONAL, description="Writing style")
    target_audience: TargetAudience = Field(TargetAudience.GENERAL, description="Target audience")
    word_count: int = Field(1000, ge=300, le=5000, description="Target word count")


class PublishRequest(BaseModel):
    """Publishing request"""
    article: Dict[str, Any] = Field(..., description="Article to publish")
    author: str = Field("KX Smart Creation", description="Article author")
    draft_only: bool = Field(False, description="Save as draft only")


class UrlToArticleRequest(BaseModel):
    """URL to article conversion request (recommended)"""
    url: HttpUrl = Field(..., description="Target URL")
    article_style: ArticleStyle = Field(ArticleStyle.PROFESSIONAL, description="Writing style")
    target_audience: TargetAudience = Field(TargetAudience.GENERAL, description="Target audience")
    word_count: int = Field(1000, ge=300, le=5000, description="Target word count")
    extract_images: bool = Field(True, description="Extract images")
    extract_links: bool = Field(True, description="Extract links")


class UrlToWeChatRequest(BaseModel):
    """URL to WeChat publishing request (one-click)"""
    url: HttpUrl = Field(..., description="Target URL")
    article_style: ArticleStyle = Field(ArticleStyle.PROFESSIONAL, description="Writing style")
    target_audience: TargetAudience = Field(TargetAudience.GENERAL, description="Target audience")
    author: str = Field("KX Smart Creation", description="Article author")
    draft_only: bool = Field(False, description="Save as draft only")


# Response Models
class CrawlResult(BaseModel):
    """Crawling result"""
    url: str = Field(..., description="Crawled URL")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Main content")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    links: List[str] = Field(default_factory=list, description="Link URLs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AnalysisResult(BaseModel):
    """Analysis result"""
    summary: str = Field(..., description="Content summary")
    key_points: List[str] = Field(..., description="Key points")
    themes: List[str] = Field(..., description="Main themes")
    sentiment: str = Field(..., description="Overall sentiment")
    structure: Dict[str, Any] = Field(..., description="Content structure analysis")
    recommendations: List[str] = Field(..., description="Writing recommendations")


class ArticleResult(BaseModel):
    """Article creation result"""
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article content")
    summary: str = Field(..., description="Article summary")
    tags: List[str] = Field(default_factory=list, description="Article tags")
    word_count: int = Field(..., description="Actual word count")
    style: ArticleStyle = Field(..., description="Article style used")


class PublishResult(BaseModel):
    """Publishing result"""
    success: bool = Field(..., description="Whether publish succeeded")
    platform: str = Field(..., description="Publishing platform")
    article_id: Optional[str] = Field(None, description="Published article ID")
    article_url: Optional[str] = Field(None, description="Published article URL")
    draft_id: Optional[str] = Field(None, description="Draft ID if draft_only")
    message: str = Field(..., description="Result message")


class TaskResponse(BaseModel):
    """Task creation response"""
    task_id: str = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="Task status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")


class TaskStatusResponse(BaseModel):
    """Task status response"""
    task_id: str = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="Current status")
    message: str = Field(..., description="Status message")
    progress: Optional[str] = Field(None, description="Progress description")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")


class TaskResultResponse(BaseModel):
    """Task result response"""
    task_id: str = Field(..., description="Task ID")
    status: TaskStatus = Field(..., description="Task status")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="System status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")


class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

