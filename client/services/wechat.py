"""
微信公众号服务
"""
from typing import Optional, Dict, Any
from wechatpy import WeChatClient
from wechatpy.client.api import WeChatMedia, WeChatMaterial
from loguru import logger

from models.schemas import GeneratedArticle, WechatPublishResponse
from config.config import settings


class WechatService:
    """微信公众号服务"""
    
    def __init__(self):
        if not settings.wechat_app_id or not settings.wechat_app_secret:
            logger.warning("WeChat credentials not configured")
            self.client = None
        else:
            self.client = WeChatClient(
                app_id=settings.wechat_app_id,
                secret=settings.wechat_app_secret
            )
            self.media = WeChatMedia(self.client)
            self.material = WeChatMaterial(self.client)
    
    async def upload_thumb_media(self, image_path: str) -> Optional[str]:
        """
        上传缩略图
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            str: media_id
        """
        if not self.client:
            logger.error("WeChat client not initialized")
            return None
        
        try:
            with open(image_path, 'rb') as f:
                result = self.media.upload('thumb', f)
                return result.get('media_id')
        except Exception as e:
            logger.error(f"Failed to upload thumb media: {str(e)}")
            return None
    
    async def create_draft(
        self,
        article: GeneratedArticle,
        thumb_media_id: Optional[str] = None,
        author: Optional[str] = None,
        digest: Optional[str] = None,
        show_cover_pic: bool = True,
        need_open_comment: bool = False,
        only_fans_can_comment: bool = False
    ) -> WechatPublishResponse:
        """
        创建草稿
        
        Args:
            article: 文章内容
            thumb_media_id: 缩略图media_id
            author: 作者
            digest: 摘要
            show_cover_pic: 是否显示封面
            need_open_comment: 是否开启评论
            only_fans_can_comment: 是否仅粉丝可评论
            
        Returns:
            WechatPublishResponse: 发布结果
        """
        if not self.client:
            return WechatPublishResponse(
                success=False,
                message="WeChat client not initialized"
            )
        
        try:
            # 准备文章数据
            articles = [{
                'title': article.title,
                'content': self._format_content(article.content),
                'author': author or "KX智能创作",
                'digest': digest or article.summary,
                'show_cover_pic': 1 if show_cover_pic else 0,
                'thumb_media_id': thumb_media_id or '',
                'need_open_comment': 1 if need_open_comment else 0,
                'only_fans_can_comment': 1 if only_fans_can_comment else 0,
            }]
            
            # 创建草稿
            result = self.material.add_draft(articles)
            
            return WechatPublishResponse(
                success=True,
                message="草稿创建成功",
                media_id=result.get('media_id')
            )
            
        except Exception as e:
            logger.error(f"Failed to create draft: {str(e)}")
            return WechatPublishResponse(
                success=False,
                message=f"创建草稿失败: {str(e)}"
            )
    
    async def publish_draft(self, media_id: str) -> WechatPublishResponse:
        """
        发布草稿
        
        Args:
            media_id: 草稿的media_id
            
        Returns:
            WechatPublishResponse: 发布结果
        """
        if not self.client:
            return WechatPublishResponse(
                success=False,
                message="WeChat client not initialized"
            )
        
        try:
            # 发布草稿
            result = self.material.publish_draft(media_id)
            
            return WechatPublishResponse(
                success=True,
                message="文章发布成功",
                url=result.get('url')
            )
            
        except Exception as e:
            logger.error(f"Failed to publish draft: {str(e)}")
            return WechatPublishResponse(
                success=False,
                message=f"发布失败: {str(e)}"
            )
    
    async def publish_article(
        self,
        article: GeneratedArticle,
        thumb_media_id: Optional[str] = None,
        **kwargs
    ) -> WechatPublishResponse:
        """
        一键发布文章（创建草稿 + 发布）
        
        Args:
            article: 文章内容
            thumb_media_id: 缩略图media_id
            **kwargs: 其他参数
            
        Returns:
            WechatPublishResponse: 发布结果
        """
        # 先创建草稿
        draft_result = await self.create_draft(article, thumb_media_id, **kwargs)
        if not draft_result.success:
            return draft_result
        
        # 再发布草稿
        if draft_result.media_id:
            return await self.publish_draft(draft_result.media_id)
        else:
            return WechatPublishResponse(
                success=False,
                message="草稿创建成功但未获取到media_id"
            )
    
    def _format_content(self, content: str) -> str:
        """
        格式化文章内容为微信公众号格式
        
        Args:
            content: 原始内容
            
        Returns:
            str: 格式化后的内容
        """
        # 添加微信公众号样式
        formatted_content = f"""
<div style="font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif; line-height: 1.8; color: #333;">
{self._convert_to_html(content)}
</div>
        """.strip()
        
        return formatted_content
    
    def _convert_to_html(self, content: str) -> str:
        """
        将文本内容转换为HTML格式
        
        Args:
            content: 文本内容
            
        Returns:
            str: HTML内容
        """
        # 简单的文本到HTML转换
        lines = content.split('\n')
        html_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                html_lines.append('<br>')
            elif line.startswith('#'):
                # 标题处理
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('# ').strip()
                html_lines.append(f'<h{level} style="color: #2c3e50; margin: 20px 0 10px 0;">{title}</h{level}>')
            else:
                # 普通段落
                html_lines.append(f'<p style="margin: 10px 0; text-indent: 2em;">{line}</p>')
        
        return '\n'.join(html_lines)
