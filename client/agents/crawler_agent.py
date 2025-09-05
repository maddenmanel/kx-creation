"""
爬取Agent
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from models.schemas import AgentResponse, CrawlRequest, PageContent
from services.crawler import WebCrawler


class CrawlerAgent(BaseAgent):
    """网页爬取Agent"""
    
    def __init__(self):
        super().__init__(
            name="CrawlerAgent",
            description="负责网页内容爬取和基础信息提取"
        )
        self.crawler = WebCrawler()
    
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        处理爬取请求
        
        Args:
            input_data: 包含url等爬取参数的字典
            
        Returns:
            AgentResponse: 爬取结果
        """
        self._start_timer()
        
        try:
            # 解析输入数据
            crawl_request = CrawlRequest(**input_data)
            
            self.log_info(f"开始爬取: {crawl_request.url}")
            
            # 执行爬取
            page_content = await self.crawler.crawl_page(
                url=str(crawl_request.url),
                extract_images=crawl_request.extract_images,
                extract_links=crawl_request.extract_links
            )
            
            self.log_info(f"爬取完成，内容长度: {len(page_content.content)}")
            
            return self.create_response(
                success=True,
                message=f"成功爬取页面: {page_content.title}",
                data={
                    "page_content": page_content.dict(),
                    "stats": {
                        "content_length": len(page_content.content),
                        "images_count": len(page_content.images),
                        "links_count": len(page_content.links)
                    }
                }
            )
            
        except Exception as e:
            error_msg = f"爬取失败: {str(e)}"
            self.log_error(error_msg)
            return self.create_response(
                success=False,
                message=error_msg
            )
