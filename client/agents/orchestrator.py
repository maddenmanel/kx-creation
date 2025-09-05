"""
多Agent编排器
"""
import asyncio
from typing import Dict, Any, List
from loguru import logger

from .crawler_agent import CrawlerAgent
from .analyzer_agent import AnalyzerAgent
from .writer_agent import WriterAgent
from .publisher_agent import PublisherAgent
from models.schemas import AgentResponse, TaskStatus
from datetime import datetime


class AgentOrchestrator:
    """多Agent编排器，负责协调各个Agent的工作流程"""
    
    def __init__(self):
        self.crawler_agent = CrawlerAgent()
        self.analyzer_agent = AnalyzerAgent()
        self.writer_agent = WriterAgent()
        self.publisher_agent = PublisherAgent()
        
        # 任务状态存储（实际项目中应使用数据库）
        self.task_status_store: Dict[str, TaskStatus] = {}
    
    async def process_url_to_article(
        self,
        task_id: str,
        url: str,
        article_style: str = "professional",
        target_audience: str = "general",
        word_count: int = None,
        extract_images: bool = True,
        extract_links: bool = True
    ) -> Dict[str, Any]:
        """
        完整的URL到文章处理流程
        
        Args:
            task_id: 任务ID
            url: 目标URL
            article_style: 文章风格
            target_audience: 目标受众
            word_count: 字数要求
            extract_images: 是否提取图片
            extract_links: 是否提取链接
            
        Returns:
            Dict: 处理结果
        """
        # 初始化任务状态
        self._update_task_status(task_id, "processing", 0, "开始处理...")
        
        try:
            # Step 1: 爬取网页内容
            logger.info(f"[Task {task_id}] Step 1: 爬取网页内容")
            self._update_task_status(task_id, "processing", 25, "正在爬取网页...")
            
            crawl_result = await self.crawler_agent.process({
                "url": url,
                "extract_images": extract_images,
                "extract_links": extract_links
            })
            
            if not crawl_result.success:
                raise Exception(f"爬取失败: {crawl_result.message}")
            
            # Step 2: 分析内容
            logger.info(f"[Task {task_id}] Step 2: 分析内容结构")
            self._update_task_status(task_id, "processing", 50, "正在分析内容...")
            
            analyze_result = await self.analyzer_agent.process({
                "page_content": crawl_result.data["page_content"]
            })
            
            if not analyze_result.success:
                raise Exception(f"分析失败: {analyze_result.message}")
            
            # Step 3: 创作文章
            logger.info(f"[Task {task_id}] Step 3: 创作文章")
            self._update_task_status(task_id, "processing", 75, "正在创作文章...")
            
            writer_input = {
                "analysis": analyze_result.data["analysis"],
                "original_content": analyze_result.data["original_content"],
                "article_style": article_style,
                "target_audience": target_audience,
                "word_count": word_count
            }
            
            writer_result = await self.writer_agent.process(writer_input)
            
            if not writer_result.success:
                raise Exception(f"创作失败: {writer_result.message}")
            
            # 完成处理
            self._update_task_status(task_id, "completed", 100, "处理完成")
            
            result = {
                "task_id": task_id,
                "success": True,
                "message": "文章创作完成",
                "data": {
                    "crawl_result": crawl_result.data,
                    "analysis_result": analyze_result.data,
                    "article_result": writer_result.data,
                    "processing_time": {
                        "crawl": crawl_result.processing_time,
                        "analyze": analyze_result.processing_time,
                        "write": writer_result.processing_time,
                        "total": sum([
                            crawl_result.processing_time,
                            analyze_result.processing_time,
                            writer_result.processing_time
                        ])
                    }
                }
            }
            
            logger.info(f"[Task {task_id}] 处理完成")
            return result
            
        except Exception as e:
            error_msg = f"处理失败: {str(e)}"
            logger.error(f"[Task {task_id}] {error_msg}")
            self._update_task_status(task_id, "failed", 0, error_msg)
            
            return {
                "task_id": task_id,
                "success": False,
                "message": error_msg,
                "data": None
            }
    
    async def publish_to_wechat(
        self,
        task_id: str,
        article_data: Dict[str, Any],
        publish_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        发布文章到微信公众号
        
        Args:
            task_id: 任务ID
            article_data: 文章数据
            publish_params: 发布参数
            
        Returns:
            Dict: 发布结果
        """
        self._update_task_status(task_id, "processing", 0, "准备发布...")
        
        try:
            logger.info(f"[Task {task_id}] 开始发布到微信公众号")
            
            # 准备发布数据
            publish_input = {"article": article_data}
            if publish_params:
                publish_input.update(publish_params)
            
            # 执行发布
            publish_result = await self.publisher_agent.process(publish_input)
            
            if not publish_result.success:
                raise Exception(f"发布失败: {publish_result.message}")
            
            self._update_task_status(task_id, "completed", 100, "发布完成")
            
            result = {
                "task_id": task_id,
                "success": True,
                "message": "文章发布成功",
                "data": {
                    "publish_result": publish_result.data,
                    "processing_time": publish_result.processing_time
                }
            }
            
            logger.info(f"[Task {task_id}] 发布完成")
            return result
            
        except Exception as e:
            error_msg = f"发布失败: {str(e)}"
            logger.error(f"[Task {task_id}] {error_msg}")
            self._update_task_status(task_id, "failed", 0, error_msg)
            
            return {
                "task_id": task_id,
                "success": False,
                "message": error_msg,
                "data": None
            }
    
    async def process_url_to_wechat(
        self,
        task_id: str,
        url: str,
        article_params: Dict[str, Any] = None,
        publish_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        完整的URL到微信公众号发布流程
        
        Args:
            task_id: 任务ID
            url: 目标URL
            article_params: 文章创作参数
            publish_params: 发布参数
            
        Returns:
            Dict: 处理结果
        """
        try:
            # Step 1: URL到文章
            article_params = article_params or {}
            article_result = await self.process_url_to_article(
                task_id=f"{task_id}_article",
                url=url,
                **article_params
            )
            
            if not article_result["success"]:
                return article_result
            
            # Step 2: 发布到微信
            article_data = article_result["data"]["article_result"]["article"]
            publish_result = await self.publish_to_wechat(
                task_id=f"{task_id}_publish",
                article_data=article_data,
                publish_params=publish_params
            )
            
            # 合并结果
            return {
                "task_id": task_id,
                "success": publish_result["success"],
                "message": "完整流程处理完成" if publish_result["success"] else publish_result["message"],
                "data": {
                    "article_process": article_result["data"],
                    "publish_process": publish_result["data"] if publish_result["success"] else None,
                    "total_processing_time": (
                        article_result["data"]["processing_time"]["total"] +
                        (publish_result["data"]["processing_time"] if publish_result["success"] else 0)
                    )
                }
            }
            
        except Exception as e:
            error_msg = f"完整流程处理失败: {str(e)}"
            logger.error(f"[Task {task_id}] {error_msg}")
            
            return {
                "task_id": task_id,
                "success": False,
                "message": error_msg,
                "data": None
            }
    
    def get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        return self.task_status_store.get(task_id)
    
    def _update_task_status(self, task_id: str, status: str, progress: int, message: str):
        """更新任务状态"""
        current_time = datetime.now()
        
        if task_id in self.task_status_store:
            task_status = self.task_status_store[task_id]
            task_status.status = status
            task_status.progress = progress
            task_status.message = message
            task_status.updated_time = current_time
        else:
            task_status = TaskStatus(
                task_id=task_id,
                status=status,
                progress=progress,
                message=message,
                created_time=current_time,
                updated_time=current_time
            )
            
        self.task_status_store[task_id] = task_status
