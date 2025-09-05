"""
KX智能内容创作系统 - FastAPI主应用
"""
import uuid
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from loguru import logger

from config.config import settings
from models.schemas import (
    CrawlRequest, ArticleRequest, WechatPublishRequest,
    TaskStatus, AgentResponse
)
from agents.orchestrator import AgentOrchestrator


# 全局编排器实例
orchestrator = AgentOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 KX智能内容创作系统启动")
    yield
    logger.info("📴 KX智能内容创作系统关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于AutoGen的智能内容创作系统，支持网页爬取、内容分析、文章创作和微信公众号发布",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API请求模型
class UrlToArticleRequest(BaseModel):
    """URL到文章请求模型"""
    url: HttpUrl
    article_style: str = "professional"
    target_audience: str = "general"
    word_count: Optional[int] = None
    extract_images: bool = True
    extract_links: bool = True


class UrlToWechatRequest(BaseModel):
    """URL到微信发布请求模型"""
    url: HttpUrl
    article_style: str = "professional"
    target_audience: str = "general"
    word_count: Optional[int] = None
    extract_images: bool = True
    extract_links: bool = True
    # 微信发布参数
    thumb_media_id: Optional[str] = None
    author: Optional[str] = None
    digest: Optional[str] = None
    show_cover_pic: bool = True
    need_open_comment: bool = False
    only_fans_can_comment: bool = False
    draft_only: bool = False


class TaskResponse(BaseModel):
    """任务响应模型"""
    task_id: str
    message: str
    status_url: str


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用{settings.app_name}",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": settings.app_version}


@app.post("/api/crawl", response_model=Dict[str, Any])
async def crawl_page(request: CrawlRequest):
    """
    爬取单个网页
    """
    try:
        result = await orchestrator.crawler_agent.process({
            "url": str(request.url),
            "extract_images": request.extract_images,
            "extract_links": request.extract_links
        })
        
        if result.success:
            return {"success": True, "data": result.data, "message": result.message}
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except Exception as e:
        logger.error(f"爬取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")


@app.post("/api/analyze", response_model=Dict[str, Any])
async def analyze_content(page_content: Dict[str, Any]):
    """
    分析页面内容
    """
    try:
        result = await orchestrator.analyzer_agent.process({
            "page_content": page_content
        })
        
        if result.success:
            return {"success": True, "data": result.data, "message": result.message}
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except Exception as e:
        logger.error(f"分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/api/write", response_model=Dict[str, Any])
async def write_article(
    analysis: Dict[str, Any],
    original_content: Dict[str, Any],
    article_style: str = "professional",
    target_audience: str = "general",
    word_count: Optional[int] = None
):
    """
    创作文章
    """
    try:
        result = await orchestrator.writer_agent.process({
            "analysis": analysis,
            "original_content": original_content,
            "article_style": article_style,
            "target_audience": target_audience,
            "word_count": word_count
        })
        
        if result.success:
            return {"success": True, "data": result.data, "message": result.message}
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except Exception as e:
        logger.error(f"创作失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创作失败: {str(e)}")


@app.post("/api/publish", response_model=Dict[str, Any])
async def publish_to_wechat(request: WechatPublishRequest):
    """
    发布到微信公众号
    """
    try:
        result = await orchestrator.publisher_agent.process({
            "article": request.article.dict(),
            "thumb_media_id": request.thumb_media_id,
            "author": request.author,
            "digest": request.digest,
            "show_cover_pic": request.show_cover_pic,
            "need_open_comment": request.need_open_comment,
            "only_fans_can_comment": request.only_fans_can_comment
        })
        
        if result.success:
            return {"success": True, "data": result.data, "message": result.message}
        else:
            raise HTTPException(status_code=400, detail=result.message)
            
    except Exception as e:
        logger.error(f"发布失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")


@app.post("/api/url-to-article", response_model=TaskResponse)
async def url_to_article(request: UrlToArticleRequest, background_tasks: BackgroundTasks):
    """
    URL到文章的完整流程（异步）
    """
    task_id = str(uuid.uuid4())
    
    # 添加后台任务
    background_tasks.add_task(
        run_url_to_article_task,
        task_id,
        str(request.url),
        {
            "article_style": request.article_style,
            "target_audience": request.target_audience,
            "word_count": request.word_count,
            "extract_images": request.extract_images,
            "extract_links": request.extract_links
        }
    )
    
    return TaskResponse(
        task_id=task_id,
        message="任务已提交，正在处理中...",
        status_url=f"/api/task/{task_id}/status"
    )


@app.post("/api/url-to-wechat", response_model=TaskResponse)
async def url_to_wechat(request: UrlToWechatRequest, background_tasks: BackgroundTasks):
    """
    URL到微信公众号发布的完整流程（异步）
    """
    task_id = str(uuid.uuid4())
    
    # 准备参数
    article_params = {
        "article_style": request.article_style,
        "target_audience": request.target_audience,
        "word_count": request.word_count,
        "extract_images": request.extract_images,
        "extract_links": request.extract_links
    }
    
    publish_params = {
        "thumb_media_id": request.thumb_media_id,
        "author": request.author,
        "digest": request.digest,
        "show_cover_pic": request.show_cover_pic,
        "need_open_comment": request.need_open_comment,
        "only_fans_can_comment": request.only_fans_can_comment,
        "draft_only": request.draft_only
    }
    
    # 添加后台任务
    background_tasks.add_task(
        run_url_to_wechat_task,
        task_id,
        str(request.url),
        article_params,
        publish_params
    )
    
    return TaskResponse(
        task_id=task_id,
        message="任务已提交，正在处理中...",
        status_url=f"/api/task/{task_id}/status"
    )


@app.get("/api/task/{task_id}/status")
async def get_task_status(task_id: str):
    """
    获取任务状态
    """
    task_status = orchestrator.get_task_status(task_id)
    
    if not task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task_status.dict()


@app.get("/api/task/{task_id}/result")
async def get_task_result(task_id: str):
    """
    获取任务结果
    """
    task_status = orchestrator.get_task_status(task_id)
    
    if not task_status:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task_status.status == "completed":
        return {
            "success": True,
            "data": task_status.result,
            "message": "任务完成"
        }
    elif task_status.status == "failed":
        return {
            "success": False,
            "message": task_status.message,
            "data": None
        }
    else:
        return {
            "success": False,
            "message": "任务尚未完成",
            "status": task_status.status,
            "progress": task_status.progress
        }


# 后台任务函数
async def run_url_to_article_task(task_id: str, url: str, params: Dict[str, Any]):
    """运行URL到文章的后台任务"""
    try:
        result = await orchestrator.process_url_to_article(task_id, url, **params)
        
        # 更新任务结果
        task_status = orchestrator.get_task_status(task_id)
        if task_status:
            task_status.result = result
            
    except Exception as e:
        logger.error(f"后台任务失败 [{task_id}]: {str(e)}")


async def run_url_to_wechat_task(
    task_id: str,
    url: str,
    article_params: Dict[str, Any],
    publish_params: Dict[str, Any]
):
    """运行URL到微信发布的后台任务"""
    try:
        result = await orchestrator.process_url_to_wechat(
            task_id, url, article_params, publish_params
        )
        
        # 更新任务结果
        task_status = orchestrator.get_task_status(task_id)
        if task_status:
            task_status.result = result
            
    except Exception as e:
        logger.error(f"后台任务失败 [{task_id}]: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
