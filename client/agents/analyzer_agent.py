"""
分析Agent
"""
import json
from typing import Dict, Any
import autogen
from .base_agent import BaseAgent
from models.schemas import AgentResponse, PageContent
from config.config import settings


class AnalyzerAgent(BaseAgent):
    """内容分析Agent"""
    
    def __init__(self):
        super().__init__(
            name="AnalyzerAgent", 
            description="负责分析网页内容结构，提取关键信息和主题"
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
        
        # 创建分析助手
        self.assistant = autogen.AssistantAgent(
            name="ContentAnalyzer",
            system_message="""你是一个专业的内容分析师。你的任务是：
1. 分析网页内容的主题和核心观点
2. 识别关键信息和重要段落
3. 提取文章的结构层次
4. 分析目标受众和写作风格
5. 总结内容要点

请以JSON格式返回分析结果，包含以下字段：
- main_topic: 主要主题
- key_points: 关键要点列表
- structure: 内容结构分析
- target_audience: 目标受众
- writing_style: 写作风格
- summary: 内容摘要
- keywords: 关键词列表""",
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
        处理内容分析请求
        
        Args:
            input_data: 包含page_content的字典
            
        Returns:
            AgentResponse: 分析结果
        """
        self._start_timer()
        
        try:
            # 解析页面内容
            page_content = PageContent(**input_data.get("page_content", {}))
            
            self.log_info(f"开始分析内容: {page_content.title}")
            
            # 准备分析提示
            analysis_prompt = f"""
请分析以下网页内容：

标题：{page_content.title}
URL：{page_content.url}

内容：
{page_content.content[:3000]}  # 限制内容长度避免token超限

元数据：
{json.dumps(page_content.metadata, ensure_ascii=False, indent=2)}

请提供详细的内容分析。
"""
            
            # 执行分析
            self.user_proxy.initiate_chat(
                self.assistant,
                message=analysis_prompt
            )
            
            # 获取分析结果
            chat_history = self.user_proxy.chat_messages[self.assistant]
            if chat_history:
                analysis_result = chat_history[-1]['content']
                
                # 尝试解析JSON结果
                try:
                    analysis_data = json.loads(analysis_result)
                except json.JSONDecodeError:
                    # 如果不是JSON格式，包装为字符串
                    analysis_data = {"analysis": analysis_result}
                
                self.log_info("内容分析完成")
                
                return self.create_response(
                    success=True,
                    message="内容分析完成",
                    data={
                        "analysis": analysis_data,
                        "original_content": {
                            "title": page_content.title,
                            "url": page_content.url,
                            "content_length": len(page_content.content)
                        }
                    }
                )
            else:
                raise Exception("未获取到分析结果")
                
        except Exception as e:
            error_msg = f"内容分析失败: {str(e)}"
            self.log_error(error_msg)
            return self.create_response(
                success=False,
                message=error_msg
            )
