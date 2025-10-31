"""
Agent Orchestrator for multi-agent workflow coordination
Manages the complete workflow from URL to published article
"""
from typing import Optional, Dict, Any
from loguru import logger
import agentscope
from agentscope.model import OpenAIChatModel

from .crawler_agent import CrawlerAgent
from .analyzer_agent import AnalyzerAgent
from .writer_agent import WriterAgent
from .publisher_agent import PublisherAgent


class AgentOrchestrator:
    """
    Orchestrates multi-agent workflow using AgentScope
    Manages the complete content creation pipeline
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize orchestrator with model configuration
        
        Args:
            model_config: Model configuration for Qwen
        """
        # Initialize AgentScope
        agentscope.init(
            project="kx-creation",
            name="content-creation-workflow",
            logging_path="./logs",
            logging_level="INFO"
        )
        
        logger.info("AgentScope initialized successfully")
        
        # Initialize Qwen model using OpenAI-compatible API
        self.model = OpenAIChatModel(
            model_name=model_config["model_name"],
            api_key=model_config["api_key"],
            client_args={"base_url": model_config["base_url"]},
            generate_kwargs={
                "temperature": model_config.get("temperature", 0.7),
                "max_tokens": model_config.get("max_tokens", 4000)
            }
        )
        
        logger.info(f"Qwen model initialized: {model_config['model_name']}")
        
        # Initialize agents (crawler and publisher don't need the model directly)
        self.crawler = CrawlerAgent(name="CrawlerAgent")
        
        self.analyzer = AnalyzerAgent(
            name="AnalyzerAgent",
            model=self.model
        )
        
        self.writer = WriterAgent(
            name="WriterAgent",
            model=self.model
        )
        
        self.publisher = PublisherAgent(name="PublisherAgent")
        
        logger.info("All agents initialized successfully")
    
    def url_to_article(
        self,
        url: str,
        article_style: str = "professional",
        target_audience: str = "general",
        word_count: int = 1000,
        extract_images: bool = True,
        extract_links: bool = True
    ) -> Dict[str, Any]:
        """
        Complete workflow: URL -> Crawl -> Analyze -> Write Article
        
        Args:
            url: Target URL to process
            article_style: Writing style
            target_audience: Target audience
            word_count: Target word count
            extract_images: Whether to extract images
            extract_links: Whether to extract links
            
        Returns:
            Complete workflow results
        """
        logger.info(f"Starting URL to Article workflow for: {url}")
        
        try:
            # Step 1: Crawl
            logger.info("Step 1/3: Crawling URL...")
            # Use crawler's direct method instead of Msg
            crawl_result_dict = self.crawler.crawl(url, extract_images, extract_links)
            
            if not crawl_result_dict or "error" in crawl_result_dict:
                error_msg = crawl_result_dict.get("error", "Failed to crawl URL") if crawl_result_dict else "Failed to crawl URL"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "crawl_result": crawl_result_dict
                }
            
            crawl_result = crawl_result_dict  # Now it's a dict directly
            
            logger.info(f"Crawling completed: {crawl_result.get('title', 'Untitled')}")
            
            # Step 2: Analyze
            logger.info("Step 2/3: Analyzing content...")
            # Use analyzer's direct method
            analysis_result_dict = self.analyzer.analyze(
                title=crawl_result.get("title", ""),
                content=crawl_result.get("content", ""),
                images=crawl_result.get("images", []),
                links=crawl_result.get("links", [])
            )
            
            if not analysis_result_dict or "error" in analysis_result_dict:
                error_msg = analysis_result_dict.get("error", "Failed to analyze content") if analysis_result_dict else "Failed to analyze content"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "crawl_result": crawl_result,
                    "analysis_result": analysis_result_dict
                }
            
            analysis_result = analysis_result_dict
            logger.info("Analysis completed successfully")
            
            # Step 3: Write Article
            logger.info("Step 3/3: Writing article...")
            # Use writer's direct method
            article_result_dict = self.writer.write(
                analysis_result=analysis_result,
                article_style=article_style,
                target_audience=target_audience,
                word_count=word_count
            )
            
            if not article_result_dict or "error" in article_result_dict:
                error_msg = article_result_dict.get("error", "Failed to write article") if article_result_dict else "Failed to write article"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "crawl_result": crawl_result,
                    "analysis_result": analysis_result,
                    "article_result": article_result_dict
                }
            
            article_result = article_result_dict
            logger.info(f"Article created successfully: {article_result.get('title', 'Untitled')}")
            
            # Return complete results
            return {
                "success": True,
                "crawl_result": crawl_result,
                "analysis_result": analysis_result,
                "article_result": article_result
            }
            
        except Exception as e:
            logger.error(f"Error in URL to Article workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def url_to_wechat(
        self,
        url: str,
        article_style: str = "professional",
        target_audience: str = "general",
        author: str = "KX Smart Creation",
        draft_only: bool = False
    ) -> Dict[str, Any]:
        """
        Complete workflow: URL -> Crawl -> Analyze -> Write -> Publish to WeChat
        
        Args:
            url: Target URL to process
            article_style: Writing style
            target_audience: Target audience
            author: Article author
            draft_only: Whether to save as draft only
            
        Returns:
            Complete workflow results including publishing
        """
        logger.info(f"Starting URL to WeChat workflow for: {url}")
        
        try:
            # First, create the article
            article_workflow = self.url_to_article(
                url=url,
                article_style=article_style,
                target_audience=target_audience,
                word_count=1000,  # Default for WeChat
                extract_images=True,
                extract_links=False  # Usually don't need links for WeChat
            )
            
            if not article_workflow.get("success"):
                return article_workflow
            
            # Step 4: Publish to WeChat
            logger.info("Step 4/4: Publishing to WeChat...")
            # Use publisher's direct method
            publish_result_dict = self.publisher.publish(
                article=article_workflow["article_result"],
                author=author,
                draft_only=draft_only,
                platform="wechat"
            )
            
            if not publish_result_dict or not publish_result_dict.get("success"):
                error_msg = publish_result_dict.get("message", "Failed to publish to WeChat") if publish_result_dict else "Failed to publish to WeChat"
                logger.warning(error_msg)
                # Still return article results even if publishing fails
                return {
                    "success": True,
                    "publish_success": False,
                    "crawl_result": article_workflow["crawl_result"],
                    "analysis_result": article_workflow["analysis_result"],
                    "article_result": article_workflow["article_result"],
                    "publish_result": publish_result_dict
                }
            
            logger.info("Publishing completed successfully")
            
            # Return complete results
            return {
                "success": True,
                "publish_success": True,
                "crawl_result": article_workflow["crawl_result"],
                "analysis_result": article_workflow["analysis_result"],
                "article_result": article_workflow["article_result"],
                "publish_result": publish_result_dict
            }
            
        except Exception as e:
            logger.error(f"Error in URL to WeChat workflow: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def crawl_url(self, url: str, extract_images: bool = True, extract_links: bool = True) -> Dict[str, Any]:
        """Single step: Crawl URL"""
        return self.crawler.crawl(url, extract_images, extract_links)
    
    def analyze_content(self, title: str, content: str, images: list = None, links: list = None) -> Dict[str, Any]:
        """Single step: Analyze content"""
        return self.analyzer.analyze(title, content, images, links)
    
    def write_article(
        self,
        analysis_result: Dict[str, Any],
        article_style: str = "professional",
        target_audience: str = "general",
        word_count: int = 1000
    ) -> Dict[str, Any]:
        """Single step: Write article"""
        return self.writer.write(analysis_result, article_style, target_audience, word_count)
    
    def publish_article(
        self,
        article: Dict[str, Any],
        author: str = "KX Smart Creation",
        draft_only: bool = False,
        platform: str = "wechat"
    ) -> Dict[str, Any]:
        """Single step: Publish article"""
        return self.publisher.publish(article, author, draft_only, platform)


# Global orchestrator instance (will be initialized in main.py)
orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """Get the global orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        raise RuntimeError("Orchestrator not initialized. Call init_orchestrator() first.")
    return orchestrator


def init_orchestrator(model_config: Dict[str, Any]) -> AgentOrchestrator:
    """Initialize the global orchestrator"""
    global orchestrator
    orchestrator = AgentOrchestrator(model_config)
    return orchestrator

