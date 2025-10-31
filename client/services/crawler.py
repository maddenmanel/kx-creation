"""
Web Crawling Service
Handles HTTP requests and HTML parsing for web scraping
"""
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from loguru import logger
from urllib.parse import urljoin, urlparse

from config.config import settings


def crawl_url(
    url: str,
    extract_images: bool = True,
    extract_links: bool = True,
    timeout: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Crawl a URL and extract content
    
    Args:
        url: Target URL to crawl
        extract_images: Whether to extract image URLs
        extract_links: Whether to extract links
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with crawled data or None if failed
    """
    if timeout is None:
        timeout = settings.CRAWLER_TIMEOUT
    
    headers = {
        'User-Agent': settings.CRAWLER_USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        logger.info(f"Crawling URL: {url}")
        
        # Make HTTP request
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract title
        title = extract_title(soup)
        logger.info(f"Extracted title: {title}")
        
        # Extract main content
        content = extract_content(soup)
        logger.info(f"Extracted content: {len(content)} characters")
        
        # Extract images if requested
        images = []
        if extract_images:
            images = extract_image_urls(soup, url)
            logger.info(f"Extracted {len(images)} images")
        
        # Extract links if requested
        links = []
        if extract_links:
            links = extract_link_urls(soup, url)
            logger.info(f"Extracted {len(links)} links")
        
        # Extract metadata
        metadata = extract_metadata(soup)
        
        result = {
            "url": url,
            "title": title,
            "content": content,
            "images": images,
            "links": links,
            "metadata": metadata
        }
        
        logger.info(f"Successfully crawled: {url}")
        return result
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while crawling {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error while crawling {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error crawling {url}: {str(e)}")
        return None


def extract_title(soup: BeautifulSoup) -> str:
    """
    Extract page title
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Page title
    """
    # Try multiple strategies to find title
    
    # 1. <title> tag
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    
    # 2. og:title meta tag
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content'].strip()
    
    # 3. H1 tag
    h1 = soup.find('h1')
    if h1:
        return h1.get_text().strip()
    
    # 4. Fallback
    return "Untitled"


def extract_content(soup: BeautifulSoup) -> str:
    """
    Extract main content from page
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Main content text
    """
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
        element.decompose()
    
    # Try to find main content container
    main_content = None
    
    # Strategy 1: Look for common content containers
    for selector in ['article', 'main', '[role="main"]', '.content', '.post-content', '#content']:
        main_content = soup.select_one(selector)
        if main_content:
            break
    
    # Strategy 2: Use body if no main content found
    if not main_content:
        main_content = soup.body
    
    # Strategy 3: Fall back to entire soup
    if not main_content:
        main_content = soup
    
    # Extract text
    text = main_content.get_text(separator='\n', strip=True)
    
    # Clean up whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    content = '\n\n'.join(lines)
    
    return content


def extract_image_urls(soup: BeautifulSoup, base_url: str) -> List[str]:
    """
    Extract image URLs from page
    
    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative URLs
        
    Returns:
        List of image URLs
    """
    images = []
    
    # Find all img tags
    for img in soup.find_all('img'):
        # Try different attributes
        img_url = img.get('src') or img.get('data-src') or img.get('data-original')
        
        if img_url:
            # Resolve relative URLs
            full_url = urljoin(base_url, img_url)
            
            # Filter out common tracking/icon images
            if is_valid_image_url(full_url):
                images.append(full_url)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_images = []
    for img in images:
        if img not in seen:
            seen.add(img)
            unique_images.append(img)
    
    return unique_images


def extract_link_urls(soup: BeautifulSoup, base_url: str) -> List[str]:
    """
    Extract link URLs from page
    
    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative URLs
        
    Returns:
        List of link URLs
    """
    links = []
    base_domain = urlparse(base_url).netloc
    
    # Find all anchor tags
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        
        if href:
            # Resolve relative URLs
            full_url = urljoin(base_url, href)
            
            # Filter out internal links and anchors
            if is_valid_link_url(full_url, base_domain):
                links.append(full_url)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)
    
    return unique_links


def extract_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract page metadata
    
    Args:
        soup: BeautifulSoup object
        
    Returns:
        Dictionary of metadata
    """
    metadata = {}
    
    # Extract description
    description = soup.find('meta', attrs={'name': 'description'})
    if description and description.get('content'):
        metadata['description'] = description['content']
    
    # Extract author
    author = soup.find('meta', attrs={'name': 'author'})
    if author and author.get('content'):
        metadata['author'] = author['content']
    
    # Extract publish date
    publish_date = soup.find('meta', property='article:published_time')
    if publish_date and publish_date.get('content'):
        metadata['publish_date'] = publish_date['content']
    
    # Extract keywords
    keywords = soup.find('meta', attrs={'name': 'keywords'})
    if keywords and keywords.get('content'):
        metadata['keywords'] = keywords['content']
    
    return metadata


def is_valid_image_url(url: str) -> bool:
    """
    Check if image URL is valid and not a tracking pixel
    
    Args:
        url: Image URL to check
        
    Returns:
        True if valid, False otherwise
    """
    # Filter out common tracking/icon images
    exclude_patterns = [
        '1x1', 'pixel', 'tracker', 'beacon',
        'icon', 'favicon', 'logo',
        'blank.gif', 'transparent.png'
    ]
    
    url_lower = url.lower()
    
    for pattern in exclude_patterns:
        if pattern in url_lower:
            return False
    
    # Check file extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
    has_valid_ext = any(url_lower.endswith(ext) for ext in valid_extensions)
    
    return has_valid_ext or '?' in url  # Some images have query parameters


def is_valid_link_url(url: str, base_domain: str) -> bool:
    """
    Check if link URL is valid and external
    
    Args:
        url: Link URL to check
        base_domain: Base domain to compare against
        
    Returns:
        True if valid external link, False otherwise
    """
    try:
        parsed = urlparse(url)
        
        # Filter out anchors and javascript
        if not parsed.scheme or parsed.scheme not in ['http', 'https']:
            return False
        
        # Filter out same domain (optional - uncomment to exclude internal links)
        # if parsed.netloc == base_domain:
        #     return False
        
        return True
        
    except Exception:
        return False

