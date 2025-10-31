"""
Crawler Agent for web scraping
Handles URL crawling and content extraction
"""
from typing import Optional, Dict, Any
from agentscope.message import Msg
from loguru import logger
import json

from .base_agent import KXBaseAgent


class CrawlerAgent(KXBaseAgent):
    """
    Crawler Agent for intelligent web scraping
    Extracts content, images, links and metadata from web pages
    """
    
    def __init__(
        self,
        name: str = "CrawlerAgent",
        **kwargs
    ):
        """Initialize Crawler Agent"""
        sys_prompt = """You are an intelligent web crawling agent. Your responsibilities:
1. Analyze and extract main content from web pages
2. Identify and extract relevant images
3. Extract important links and references
4. Identify page structure and metadata
5. Filter out noise and irrelevant content
6. Provide clean, structured output

Always extract:
- Page title
- Main content body
- Images with their URLs
- Important links
- Metadata (author, date, etc.)

Output should be in JSON format."""
        
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            **kwargs
        )
    
    def reply(self, x: Optional[Msg] = None) -> Msg:
        """
        Process crawling request
        
        Args:
            x: Message containing crawl request with URL and options
            
        Returns:
            Message with crawl results
        """
        try:
            if not self._validate_input(x):
                return self._create_message(
                    {"error": "Invalid input message"},
                    metadata={"status": "failed"}
                )
            
            # Extract request parameters
            request_data = x.content if isinstance(x.content, dict) else {"url": str(x.content)}
            url = request_data.get("url")
            extract_images = request_data.get("extract_images", True)
            extract_links = request_data.get("extract_links", True)
            
            logger.info(f"{self.name}: Starting to crawl URL: {url}")
            
            # Import crawler service
            from services.crawler import crawl_url
            
            # Perform crawling
            result = crawl_url(
                url=url,
                extract_images=extract_images,
                extract_links=extract_links
            )
            
            if result is None:
                logger.error(f"{self.name}: Failed to crawl URL: {url}")
                return self._create_message(
                    {"error": f"Failed to crawl URL: {url}"},
                    metadata={"status": "failed"}
                )
            
            logger.info(f"{self.name}: Successfully crawled URL: {url}")
            logger.info(f"{self.name}: Extracted {len(result.get('content', ''))} characters of content")
            
            return self._create_message(
                result,
                metadata={
                    "status": "success",
                    "url": url,
                    "content_length": len(result.get('content', ''))
                }
            )
            
        except Exception as e:
            self._log_error(e, "reply")
            return self._create_message(
                {"error": str(e)},
                metadata={"status": "failed"}
            )
    
    def crawl(self, url: str, extract_images: bool = True, extract_links: bool = True) -> Dict[str, Any]:
        """
        Convenience method to crawl a URL
        
        Args:
            url: Target URL to crawl
            extract_images: Whether to extract images
            extract_links: Whether to extract links
            
        Returns:
            Crawl results as dictionary
        """
        try:
            logger.info(f"{self.name}: Starting to crawl URL: {url}")
            
            # Import crawler service
            from services.crawler import crawl_url
            
            # Perform crawling
            result = crawl_url(
                url=url,
                extract_images=extract_images,
                extract_links=extract_links
            )
            
            if result is None:
                logger.error(f"{self.name}: Failed to crawl URL: {url}")
                return {"error": f"Failed to crawl URL: {url}"}
            
            logger.info(f"{self.name}: Successfully crawled URL: {url}")
            return result
            
        except Exception as e:
            logger.error(f"{self.name}: Error crawling: {str(e)}")
            return {"error": str(e)}

