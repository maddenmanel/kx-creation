"""
发布Agent
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from models.schemas import AgentResponse, GeneratedArticle, WechatPublishRequest
from services.wechat import WechatService


class PublisherAgent(BaseAgent):
    """内容发布Agent"""
    
    def __init__(self):
        super().__init__(
            name="PublisherAgent",
            description="负责将文章发布到微信公众号"
        )
        self.wechat_service = WechatService()
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        处理文章发布请求
        
        Args:
            input_data: 包含article和发布参数的字典
            
        Returns:
            AgentResponse: 发布结果
        """
        self._start_timer()
        
        try:
            # 解析文章数据
            article_data = input_data.get("article", {})
            article = GeneratedArticle(**article_data)
            
            # 解析发布参数
            publish_params = {
                "thumb_media_id": input_data.get("thumb_media_id"),
                "author": input_data.get("author"),
                "digest": input_data.get("digest"),
                "show_cover_pic": input_data.get("show_cover_pic", True),
                "need_open_comment": input_data.get("need_open_comment", False),
                "only_fans_can_comment": input_data.get("only_fans_can_comment", False)
            }
            
            self.log_info(f"开始发布文章: {article.title}")
            
            # 检查是否只创建草稿
            draft_only = input_data.get("draft_only", False)
            
            if draft_only:
                # 只创建草稿
                result = await self.wechat_service.create_draft(
                    article=article,
                    **publish_params
                )
                
                if result.success:
                    self.log_info("草稿创建成功")
                    return self.create_response(
                        success=True,
                        message="草稿创建成功",
                        data={
                            "publish_result": result.dict(),
                            "article_info": {
                                "title": article.title,
                                "word_count": article.word_count
                            }
                        }
                    )
                else:
                    raise Exception(result.message)
                    
            else:
                # 直接发布
                result = await self.wechat_service.publish_article(
                    article=article,
                    **publish_params
                )
                
                if result.success:
                    self.log_info("文章发布成功")
                    return self.create_response(
                        success=True,
                        message="文章发布成功",
                        data={
                            "publish_result": result.dict(),
                            "article_info": {
                                "title": article.title,
                                "word_count": article.word_count
                            }
                        }
                    )
                else:
                    raise Exception(result.message)
                    
        except Exception as e:
            error_msg = f"文章发布失败: {str(e)}"
            self.log_error(error_msg)
            return self.create_response(
                success=False,
                message=error_msg
            )
    
    async def upload_thumb_media(self, image_path: str) -> AgentResponse:
        """
        上传缩略图
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            AgentResponse: 上传结果
        """
        self._start_timer()
        
        try:
            self.log_info(f"开始上传缩略图: {image_path}")
            
            media_id = await self.wechat_service.upload_thumb_media(image_path)
            
            if media_id:
                self.log_info("缩略图上传成功")
                return self.create_response(
                    success=True,
                    message="缩略图上传成功",
                    data={"media_id": media_id}
                )
            else:
                raise Exception("上传失败，未获取到media_id")
                
        except Exception as e:
            error_msg = f"缩略图上传失败: {str(e)}"
            self.log_error(error_msg)
            return self.create_response(
                success=False,
                message=error_msg
            )
