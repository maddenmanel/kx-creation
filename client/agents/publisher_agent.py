"""
Publisher Agent for content publishing
Handles publishing articles to various platforms (WeChat, etc.)
"""
from typing import Optional, Dict, Any
from agentscope.message import Msg
from loguru import logger
import json

from .base_agent import KXBaseAgent


class PublisherAgent(KXBaseAgent):
    """
    Publisher Agent for content publishing
    Publishes articles to WeChat Official Accounts and other platforms
    """
    
    def __init__(
        self,
        name: str = "PublisherAgent",
        **kwargs
    ):
        """Initialize Publisher Agent"""
        sys_prompt = """You are a content publishing specialist. Your role is to:

1. Prepare articles for publication on various platforms
2. Optimize content for platform-specific requirements
3. Handle metadata and formatting
4. Ensure content meets platform guidelines
5. Manage draft and final publication workflows

When publishing content, you should:
- Verify all required fields are present
- Format content appropriately for the platform
- Add necessary metadata (author, tags, etc.)
- Handle errors gracefully
- Provide clear status feedback

You support publishing to:
- WeChat Official Accounts
- Other platforms (extensible)"""
        
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            **kwargs
        )
    
    def reply(self, x: Optional[Msg] = None) -> Msg:
        """
        Process publishing request
        
        Args:
            x: Message containing publishing request with article and options
            
        Returns:
            Message with publishing result
        """
        try:
            if not self._validate_input(x):
                return self._create_message(
                    {"error": "Invalid input message"},
                    metadata={"status": "failed"}
                )
            
            request_data = x.content if isinstance(x.content, dict) else {}
            article = request_data.get("article", {})
            author = request_data.get("author", "KX Smart Creation")
            draft_only = request_data.get("draft_only", False)
            platform = request_data.get("platform", "wechat")
            
            if not article:
                logger.warning(f"{self.name}: No article provided for publishing")
                return self._create_message(
                    {"error": "No article provided"},
                    metadata={"status": "failed"}
                )
            
            logger.info(f"{self.name}: Publishing article to {platform} (draft_only={draft_only})")
            logger.info(f"{self.name}: Article title: {article.get('title', 'Untitled')}")
            
            # Validate article has required fields
            if not article.get("title") or not article.get("content"):
                logger.error(f"{self.name}: Article missing required fields (title or content)")
                return self._create_message(
                    {"error": "Article missing required fields"},
                    metadata={"status": "failed"}
                )
            
            # Publish based on platform
            if platform == "wechat":
                result = self._publish_to_wechat(article, author, draft_only)
            else:
                result = {
                    "success": False,
                    "platform": platform,
                    "message": f"Platform '{platform}' not supported yet"
                }
            
            if result.get("success"):
                logger.info(f"{self.name}: Successfully published to {platform}")
            else:
                logger.warning(f"{self.name}: Publishing failed: {result.get('message')}")
            
            return self._create_message(
                result,
                metadata={
                    "status": "success" if result.get("success") else "failed",
                    "platform": platform
                }
            )
            
        except Exception as e:
            self._log_error(e, "reply")
            return self._create_message(
                {"error": str(e)},
                metadata={"status": "failed"}
            )
    
    def _publish_to_wechat(
        self,
        article: Dict[str, Any],
        author: str,
        draft_only: bool
    ) -> Dict[str, Any]:
        """
        Publish article to WeChat Official Account
        
        Args:
            article: Article to publish
            author: Article author
            draft_only: Whether to save as draft only
            
        Returns:
            Publishing result
        """
        try:
            # Import WeChat service
            from services.wechat import publish_to_wechat
            
            # Publish article
            result = publish_to_wechat(
                title=article.get("title"),
                content=article.get("content"),
                author=author,
                draft_only=draft_only,
                digest=article.get("summary", "")[:120],  # WeChat digest limit
            )
            
            return result
            
        except ImportError:
            logger.warning(f"{self.name}: WeChat service not available")
            return {
                "success": False,
                "platform": "wechat",
                "message": "WeChat service not configured. Please check WECHAT_APP_ID and WECHAT_APP_SECRET in .env file"
            }
        except Exception as e:
            logger.error(f"{self.name}: WeChat publishing error: {str(e)}")
            return {
                "success": False,
                "platform": "wechat",
                "message": f"Publishing error: {str(e)}"
            }
    
    def publish(
        self,
        article: Dict[str, Any],
        author: str = "KX Smart Creation",
        draft_only: bool = False,
        platform: str = "wechat"
    ) -> Dict[str, Any]:
        """
        Convenience method to publish an article
        
        Args:
            article: Article to publish
            author: Article author
            draft_only: Whether to save as draft only
            platform: Publishing platform
            
        Returns:
            Publishing result as dictionary
        """
        try:
            if not article:
                logger.warning(f"{self.name}: No article provided for publishing")
                return {"error": "No article provided", "success": False}
            
            logger.info(f"{self.name}: Publishing article to {platform} (draft_only={draft_only})")
            logger.info(f"{self.name}: Article title: {article.get('title', 'Untitled')}")
            
            # Validate article has required fields
            if not article.get("title") or not article.get("content"):
                logger.error(f"{self.name}: Article missing required fields (title or content)")
                return {"error": "Article missing required fields", "success": False}
            
            # Publish based on platform
            if platform == "wechat":
                result = self._publish_to_wechat(article, author, draft_only)
            else:
                result = {
                    "success": False,
                    "platform": platform,
                    "message": f"Platform '{platform}' not supported yet"
                }
            
            if result.get("success"):
                logger.info(f"{self.name}: Successfully published to {platform}")
            else:
                logger.warning(f"{self.name}: Publishing failed: {result.get('message')}")
            
            return result
            
        except Exception as e:
            logger.error(f"{self.name}: Publishing error: {str(e)}")
            return {"error": str(e), "success": False}

