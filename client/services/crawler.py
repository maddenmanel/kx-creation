"""
网页爬取服务
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

from models.schemas import PageContent
from config.config import settings


class WebCrawler:
    """网页爬取器"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=settings.crawl_timeout)
        self.headers = {
            'User-Agent': settings.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def crawl_page(self, url: str, extract_images: bool = True, extract_links: bool = True) -> PageContent:
        """
        爬取单个页面
        
        Args:
            url: 目标URL
            extract_images: 是否提取图片
            extract_links: 是否提取链接
            
        Returns:
            PageContent: 页面内容对象
        """
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=self.headers) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
                    
                    content = await response.text()
                    
                    # 检查内容长度
                    if len(content) > settings.max_content_length:
                        logger.warning(f"Content too long for {url}, truncating...")
                        content = content[:settings.max_content_length]
                    
                    # 解析HTML
                    soup = BeautifulSoup(content, 'lxml')
                    
                    # 提取标题
                    title = self._extract_title(soup)
                    
                    # 提取正文内容
                    main_content = self._extract_main_content(soup)
                    
                    # 提取图片
                    images = []
                    if extract_images:
                        images = self._extract_images(soup, url)
                    
                    # 提取链接
                    links = []
                    if extract_links:
                        links = self._extract_links(soup, url)
                    
                    # 提取元数据
                    metadata = self._extract_metadata(soup)
                    
                    return PageContent(
                        url=url,
                        title=title,
                        content=main_content,
                        images=images,
                        links=links,
                        metadata=metadata,
                        crawl_time=datetime.now()
                    )
                    
        except Exception as e:
            logger.error(f"Failed to crawl {url}: {str(e)}")
            raise
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取页面标题"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # 尝试从h1标签提取
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "无标题"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """提取主要内容"""
        # 移除脚本和样式标签
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # 尝试找到主要内容区域
        main_selectors = [
            'article', 'main', '.content', '.post-content', '.entry-content',
            '.article-content', '#content', '.main-content'
        ]
        
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                return main_content.get_text(strip=True, separator='\n')
        
        # 如果没找到主要内容区域，提取body内容
        body = soup.find('body')
        if body:
            return body.get_text(strip=True, separator='\n')
        
        return soup.get_text(strip=True, separator='\n')
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """提取图片URL"""
        images = []
        img_tags = soup.find_all('img', src=True)
        
        for img in img_tags:
            src = img.get('src')
            if src:
                # 转换为绝对URL
                absolute_url = urljoin(base_url, src)
                images.append(absolute_url)
        
        return list(set(images))  # 去重
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """提取链接URL"""
        links = []
        link_tags = soup.find_all('a', href=True)
        
        for link in link_tags:
            href = link.get('href')
            if href and not href.startswith('#'):
                # 转换为绝对URL
                absolute_url = urljoin(base_url, href)
                # 只保留同域名或外部HTTP链接
                if self._is_valid_link(absolute_url):
                    links.append(absolute_url)
        
        return list(set(links))  # 去重
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取元数据"""
        metadata = {}
        
        # 提取meta标签
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        # 提取描述
        description = soup.find('meta', attrs={'name': 'description'})
        if description:
            metadata['description'] = description.get('content')
        
        # 提取关键词
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        if keywords:
            metadata['keywords'] = keywords.get('content')
        
        return metadata
    
    def _is_valid_link(self, url: str) -> bool:
        """检查链接是否有效"""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ['http', 'https'] and bool(parsed.netloc)
        except:
            return False
