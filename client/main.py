"""
KX Intelligent Content Creation System
FastAPI application with AgentScope multi-agent architecture
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config.config import settings
from models.schemas import (
    CrawlRequest, AnalyzeRequest, WriteRequest, PublishRequest,
    UrlToArticleRequest, UrlToWeChatRequest,
    TaskResponse, TaskStatusResponse, TaskResultResponse,
    HealthResponse, ErrorResponse,
    TaskStatus
)
from agents.orchestrator import init_orchestrator, get_orchestrator


# Task storage (in production, use Redis or a database)
tasks: Dict[str, Dict[str, Any]] = {}


def create_qwen_model_config() -> Dict[str, Any]:
    """Create Qwen model configuration for AgentScope"""
    return {
        "config_name": "qwen_config",
        "model_type": "openai_chat",  # AgentScope uses OpenAI-compatible API
        "model_name": settings.QWEN_MODEL,
        "api_key": settings.QWEN_API_KEY,
        "base_url": settings.QWEN_BASE_URL,
        "temperature": 0.7,
        "max_tokens": 4000,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting KX Intelligent Content Creation System...")
    logger.info(f"Version: {settings.APP_VERSION}")
    
    # Initialize AgentScope with Qwen configuration
    try:
        model_config = create_qwen_model_config()
        init_orchestrator(model_config)
        logger.info("AgentScope orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {str(e)}")
        raise
    
    logger.info("System ready!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down KX Intelligent Content Creation System...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent content creation system with multi-agent architecture using AgentScope and Qwen",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper functions
def create_task(task_type: str) -> str:
    """Create a new task and return task ID"""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "task_id": task_id,
        "type": task_type,
        "status": TaskStatus.PENDING,
        "message": "Task created and queued",
        "progress": None,
        "data": None,
        "error": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "completed_at": None
    }
    return task_id


def update_task(task_id: str, **kwargs):
    """Update task information"""
    if task_id in tasks:
        tasks[task_id].update(kwargs)
        tasks[task_id]["updated_at"] = datetime.now()


async def process_url_to_article_task(task_id: str, request: UrlToArticleRequest):
    """Background task processor for URL to Article workflow"""
    try:
        update_task(
            task_id,
            status=TaskStatus.PROCESSING,
            message="Processing URL to article workflow",
            progress="Step 1/3: Crawling URL"
        )
        
        orchestrator = get_orchestrator()
        
        # Run workflow
        result = orchestrator.url_to_article(
            url=str(request.url),
            article_style=request.article_style,
            target_audience=request.target_audience,
            word_count=request.word_count,
            extract_images=request.extract_images,
            extract_links=request.extract_links
        )
        
        if result.get("success"):
            update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                message="Article created successfully",
                data=result,
                completed_at=datetime.now()
            )
        else:
            update_task(
                task_id,
                status=TaskStatus.FAILED,
                message="Failed to create article",
                error=result.get("error", "Unknown error"),
                completed_at=datetime.now()
            )
            
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {str(e)}")
        update_task(
            task_id,
            status=TaskStatus.FAILED,
            message="Task processing error",
            error=str(e),
            completed_at=datetime.now()
        )


async def process_url_to_wechat_task(task_id: str, request: UrlToWeChatRequest):
    """Background task processor for URL to WeChat workflow"""
    try:
        update_task(
            task_id,
            status=TaskStatus.PROCESSING,
            message="Processing URL to WeChat workflow",
            progress="Step 1/4: Crawling URL"
        )
        
        orchestrator = get_orchestrator()
        
        # Run workflow
        result = orchestrator.url_to_wechat(
            url=str(request.url),
            article_style=request.article_style,
            target_audience=request.target_audience,
            author=request.author,
            draft_only=request.draft_only
        )
        
        if result.get("success"):
            update_task(
                task_id,
                status=TaskStatus.COMPLETED,
                message="Article created and published successfully" if result.get("publish_success") else "Article created, but publishing failed",
                data=result,
                completed_at=datetime.now()
            )
        else:
            update_task(
                task_id,
                status=TaskStatus.FAILED,
                message="Failed to process workflow",
                error=result.get("error", "Unknown error"),
                completed_at=datetime.now()
            )
            
    except Exception as e:
        logger.error(f"Error processing task {task_id}: {str(e)}")
        update_task(
            task_id,
            status=TaskStatus.FAILED,
            message="Task processing error",
            error=str(e),
            completed_at=datetime.now()
        )


# API Endpoints

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        timestamp=datetime.now()
    )


@app.post("/api/url-to-article", response_model=TaskResponse, tags=["Core Workflows"])
async def url_to_article(request: UrlToArticleRequest, background_tasks: BackgroundTasks):
    """
    Convert URL to article (Recommended workflow)
    
    This endpoint crawls a URL, analyzes the content, and creates a new article.
    Returns a task ID for tracking progress.
    """
    try:
        task_id = create_task("url_to_article")
        background_tasks.add_task(process_url_to_article_task, task_id, request)
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Task created and processing",
            created_at=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error creating url_to_article task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/url-to-wechat", response_model=TaskResponse, tags=["Core Workflows"])
async def url_to_wechat(request: UrlToWeChatRequest, background_tasks: BackgroundTasks):
    """
    Convert URL to WeChat article (One-click publishing)
    
    This endpoint crawls a URL, analyzes the content, creates a new article,
    and publishes it to WeChat Official Account.
    Returns a task ID for tracking progress.
    """
    try:
        task_id = create_task("url_to_wechat")
        background_tasks.add_task(process_url_to_wechat_task, task_id, request)
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Task created and processing",
            created_at=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error creating url_to_wechat task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/task/{task_id}/status", response_model=TaskStatusResponse, tags=["Task Management"])
async def get_task_status(task_id: str):
    """
    Get task status
    
    Returns the current status of a task.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        message=task["message"],
        progress=task.get("progress"),
        created_at=task["created_at"],
        updated_at=task["updated_at"]
    )


@app.get("/api/task/{task_id}/result", response_model=TaskResultResponse, tags=["Task Management"])
async def get_task_result(task_id: str):
    """
    Get task result
    
    Returns the result of a completed task.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    return TaskResultResponse(
        task_id=task_id,
        status=task["status"],
        data=task.get("data"),
        error=task.get("error"),
        created_at=task["created_at"],
        completed_at=task.get("completed_at")
    )


# Step-by-step endpoints for more granular control

@app.post("/api/crawl", tags=["Step-by-step Operations"])
async def crawl(request: CrawlRequest):
    """
    Step 1: Crawl a URL
    
    Crawls a URL and extracts content, images, and links.
    """
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.crawl_url(
            url=str(request.url),
            extract_images=request.extract_images,
            extract_links=request.extract_links
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        logger.error(f"Error in crawl endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze", tags=["Step-by-step Operations"])
async def analyze(request: AnalyzeRequest):
    """
    Step 2: Analyze content
    
    Analyzes content and extracts key information, themes, and recommendations.
    """
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.analyze_content(
            title=request.title,
            content=request.content,
            images=request.images,
            links=request.links
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/write", tags=["Step-by-step Operations"])
async def write(request: WriteRequest):
    """
    Step 3: Write article
    
    Creates an article based on analysis results.
    """
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.write_article(
            analysis_result=request.analysis_result,
            article_style=request.article_style,
            target_audience=request.target_audience,
            word_count=request.word_count
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except Exception as e:
        logger.error(f"Error in write endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/publish", tags=["Step-by-step Operations"])
async def publish(request: PublishRequest):
    """
    Step 4: Publish article
    
    Publishes an article to WeChat Official Account or other platforms.
    """
    try:
        orchestrator = get_orchestrator()
        result = orchestrator.publish_article(
            article=request.article,
            author=request.author,
            draft_only=request.draft_only
        )
        
        if not result.get("success"):
            logger.warning(f"Publishing failed: {result.get('message')}")
        
        return result
    except Exception as e:
        logger.error(f"Error in publish endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            timestamp=datetime.now()
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message="Internal server error",
            details={"detail": str(exc)},
            timestamp=datetime.now()
        ).model_dump()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

