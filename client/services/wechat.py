"""
WeChat Official Account Service
Handles publishing articles to WeChat Official Accounts
"""
from typing import Optional, Dict, Any
from loguru import logger

from config.config import settings


def publish_to_wechat(
    title: str,
    content: str,
    author: str = "KX Smart Creation",
    draft_only: bool = False,
    digest: Optional[str] = None,
    thumb_media_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Publish article to WeChat Official Account
    
    Args:
        title: Article title
        content: Article content (HTML format supported)
        author: Article author
        draft_only: Whether to save as draft only
        digest: Article summary/digest
        thumb_media_id: Cover image media ID
        
    Returns:
        Publishing result dictionary
    """
    # Check if WeChat is configured
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        logger.warning("WeChat credentials not configured")
        return {
            "success": False,
            "platform": "wechat",
            "message": "WeChat not configured. Please set WECHAT_APP_ID and WECHAT_APP_SECRET in .env file"
        }
    
    try:
        from wechatpy import WeChatClient
        from wechatpy.client.api import WeChatMedia, WeChatMaterial
        
        logger.info(f"Publishing to WeChat: {title[:50]}... (draft_only={draft_only})")
        
        # Initialize WeChat client
        client = WeChatClient(
            appid=settings.WECHAT_APP_ID,
            secret=settings.WECHAT_APP_SECRET
        )
        
        # Prepare article data
        article_data = {
            "title": title,
            "author": author,
            "content": format_content_for_wechat(content),
            "digest": digest or title[:120],
            "show_cover_pic": 1 if thumb_media_id else 0,
        }
        
        # Add cover image if provided
        if thumb_media_id:
            article_data["thumb_media_id"] = thumb_media_id
        
        # Publish or save as draft
        if draft_only:
            # Save as draft
            result = client.material.add_news([article_data], draft=True)
            
            logger.info(f"Article saved as draft: {result}")
            
            return {
                "success": True,
                "platform": "wechat",
                "draft_id": result.get("media_id"),
                "message": "Article saved as draft successfully"
            }
        else:
            # Publish article
            result = client.material.add_news([article_data])
            
            logger.info(f"Article published: {result}")
            
            return {
                "success": True,
                "platform": "wechat",
                "article_id": result.get("media_id"),
                "message": "Article published successfully"
            }
            
    except ImportError:
        logger.error("wechatpy library not installed")
        return {
            "success": False,
            "platform": "wechat",
            "message": "wechatpy library not installed. Please install it: pip install wechatpy"
        }
    except Exception as e:
        logger.error(f"Error publishing to WeChat: {str(e)}")
        return {
            "success": False,
            "platform": "wechat",
            "message": f"Publishing error: {str(e)}"
        }


def format_content_for_wechat(content: str) -> str:
    """
    Format content for WeChat Official Account
    Converts markdown/plain text to WeChat-compatible HTML
    
    Args:
        content: Original content
        
    Returns:
        Formatted HTML content
    """
    # Basic formatting - convert line breaks to paragraphs
    paragraphs = content.split('\n\n')
    
    html_parts = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Check if it's a heading (starts with #)
        if para.startswith('# '):
            html_parts.append(f'<h1>{para[2:]}</h1>')
        elif para.startswith('## '):
            html_parts.append(f'<h2>{para[3:]}</h2>')
        elif para.startswith('### '):
            html_parts.append(f'<h3>{para[4:]}</h3>')
        else:
            # Regular paragraph
            # Convert single line breaks to <br>
            para = para.replace('\n', '<br>')
            html_parts.append(f'<p>{para}</p>')
    
    html_content = '\n'.join(html_parts)
    
    # Wrap in basic HTML structure with WeChat-friendly styling
    formatted_content = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; line-height: 1.6; color: #333;">
{html_content}
</div>
"""
    
    return formatted_content


def upload_image_to_wechat(image_path: str) -> Optional[str]:
    """
    Upload image to WeChat and get media_id
    
    Args:
        image_path: Local path to image file
        
    Returns:
        Media ID if successful, None otherwise
    """
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        logger.warning("WeChat credentials not configured")
        return None
    
    try:
        from wechatpy import WeChatClient
        
        client = WeChatClient(
            appid=settings.WECHAT_APP_ID,
            secret=settings.WECHAT_APP_SECRET
        )
        
        # Upload image
        with open(image_path, 'rb') as f:
            result = client.material.add_material('image', f)
        
        media_id = result.get('media_id')
        logger.info(f"Image uploaded to WeChat, media_id: {media_id}")
        
        return media_id
        
    except Exception as e:
        logger.error(f"Error uploading image to WeChat: {str(e)}")
        return None


def get_wechat_material_list(material_type: str = "news", offset: int = 0, count: int = 20) -> Dict[str, Any]:
    """
    Get list of materials from WeChat
    
    Args:
        material_type: Type of material (news, image, video, voice)
        offset: Offset for pagination
        count: Number of items to retrieve
        
    Returns:
        Dictionary with material list
    """
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        logger.warning("WeChat credentials not configured")
        return {"success": False, "message": "WeChat not configured"}
    
    try:
        from wechatpy import WeChatClient
        
        client = WeChatClient(
            appid=settings.WECHAT_APP_ID,
            secret=settings.WECHAT_APP_SECRET
        )
        
        result = client.material.get_materials(material_type, offset, count)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error getting WeChat materials: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

