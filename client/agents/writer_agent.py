"""
写作Agent
"""
import json
from typing import Dict, Any
from datetime import datetime
import autogen
from .base_agent import BaseAgent
from models.schemas import AgentResponse, GeneratedArticle
from config.config import settings


class WriterAgent(BaseAgent):
    """内容写作Agent"""
    
    def __init__(self):
        super().__init__(
            name="WriterAgent",
            description="负责根据分析结果创作高质量文章"
        )
        
        # 配置AutoGen
        self.llm_config = {
            "config_list": [{
                "model": settings.qwen_model,
                "api_key": settings.qwen_api_key,
                "base_url": settings.qwen_base_url,
                "api_type": "openai"
            }],
            "cache_seed": settings.autogen_cache_seed,
            "timeout": settings.autogen_timeout
        }
        
        # 创建写作助手
        self.assistant = autogen.AssistantAgent(
            name="ContentWriter",
            system_message="""你是一个专业的内容创作者和编辑。你的任务是根据内容分析结果创作高质量的文章。

创作要求：
1. 保持原文的核心观点和重要信息
2. 改写和优化语言表达，使其更加流畅
3. 调整文章结构，使其更加清晰易读
4. 添加适当的过渡句和连接词
5. 确保文章符合目标受众的阅读习惯

请以JSON格式返回创作结果，包含以下字段：
- title: 优化后的标题
- content: 完整的文章内容（使用Markdown格式）
- summary: 文章摘要（100-200字）
- tags: 相关标签列表
- word_count: 字数统计""",
            llm_config=self.llm_config
        )
        
        self.user_proxy = autogen.UserProxyAgent(
            name="UserProxy",
            human_input_mode="NEVER",
            code_execution_config=False,
            max_consecutive_auto_reply=1
        )
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        处理文章创作请求
        
        Args:
            input_data: 包含analysis和page_content的字典
            
        Returns:
            AgentResponse: 创作结果
        """
        self._start_timer()
        
        try:
            # 获取分析结果和原始内容
            analysis_data = input_data.get("analysis", {})
            original_content = input_data.get("original_content", {})
            article_style = input_data.get("article_style", "professional")
            target_audience = input_data.get("target_audience", "general")
            word_count = input_data.get("word_count")
            
            self.log_info(f"开始创作文章，风格: {article_style}")
            
            # 准备创作提示
            writing_prompt = f"""
基于以下内容分析结果，请创作一篇高质量的文章：

原文标题：{original_content.get('title', '')}
原文URL：{original_content.get('url', '')}

内容分析：
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}

创作要求：
- 文章风格：{article_style}
- 目标受众：{target_audience}
- 字数要求：{word_count if word_count else '不限制'}

请确保文章内容准确、生动、有价值，适合在微信公众号发布。
"""
            
            # 执行创作
            self.user_proxy.initiate_chat(
                self.assistant,
                message=writing_prompt
            )
            
            # 获取创作结果
            chat_history = self.user_proxy.chat_messages[self.assistant]
            if chat_history:
                writing_result = chat_history[-1]['content']
                
                # 尝试解析JSON结果
                try:
                    article_data = json.loads(writing_result)
                    
                    # 创建GeneratedArticle对象
                    generated_article = GeneratedArticle(
                        title=article_data.get('title', original_content.get('title', '无标题')),
                        content=article_data.get('content', ''),
                        summary=article_data.get('summary', ''),
                        tags=article_data.get('tags', []),
                        word_count=article_data.get('word_count', len(article_data.get('content', ''))),
                        generated_time=datetime.now()
                    )
                    
                except json.JSONDecodeError:
                    # 如果不是JSON格式，直接作为内容
                    generated_article = GeneratedArticle(
                        title=original_content.get('title', '无标题'),
                        content=writing_result,
                        summary=writing_result[:200] + "..." if len(writing_result) > 200 else writing_result,
                        tags=[],
                        word_count=len(writing_result),
                        generated_time=datetime.now()
                    )
                
                self.log_info(f"文章创作完成，字数: {generated_article.word_count}")
                
                return self.create_response(
                    success=True,
                    message=f"文章创作完成，共{generated_article.word_count}字",
                    data={
                        "article": generated_article.dict(),
                        "creation_info": {
                            "style": article_style,
                            "target_audience": target_audience,
                            "word_count": generated_article.word_count
                        }
                    }
                )
            else:
                raise Exception("未获取到创作结果")
                
        except Exception as e:
            error_msg = f"文章创作失败: {str(e)}"
            self.log_error(error_msg)
            return self.create_response(
                success=False,
                message=error_msg
            )
