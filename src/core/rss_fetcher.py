# src/core/rss_fetcher.py - Handles fetching and parsing of RSS feeds.
import feedparser
import requests
import logging
import hashlib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from ..utils.text_cleaner import clean_html_tags, summarize_text, advanced_text_cleanup

def generate_entry_id(rss_url, entry):
    """生成更稳定的条目ID"""
    unique_id = entry.get('id') or entry.get('link')
    if not unique_id:
        title = entry.get('title', '')
        published = entry.get('published', '')
        unique_id = f"{title}_{published}"
    content = f"{rss_url}:{unique_id}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()

def fetch_webpage_content(url: str) -> str:
    """抓取网页内容并提取主要文本，增加智能去重和格式清理"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除脚本、样式和导航等无关内容
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        
        # --- 高级内容提取 ---
        # 尝试查找常见的内容容器标签
        content_selectors = [
            'article', '.post-content', '.entry-content', '.article-body', 
            '.content', 'main', '#content', '#main'
        ]
        content_area = None
        for selector in content_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                break
        
        # 如果没找到特定容器，则使用body，但会进行更严格的清理
        if not content_area:
            content_area = soup.body or soup

        # 从选定区域提取文本块
        text_blocks = [block.get_text(separator='\n', strip=True) for block in content_area.find_all(['p', 'div', 'h1', 'h2', 'h3'])]
        
        # --- 智能段落去重 ---
        unique_blocks = []
        seen_hashes = set()
        for block in text_blocks:
            # 忽略太短的文本块
            if len(block) < 20:
                continue
            
            # 创建一个简化的哈希来判断重复
            block_hash = hashlib.md5(block[:100].encode('utf-8')).hexdigest()
            if block_hash not in seen_hashes:
                unique_blocks.append(block)
                seen_hashes.add(block_hash)

        # --- 格式化和最终清理 ---
        full_text = '\n\n'.join(unique_blocks)
        
        # 使用新的高级清理函数
        cleaned_text = advanced_text_cleanup(full_text)
        
        # 稍微放宽最终长度限制，确保内容更完整
        return cleaned_text[:2000] if len(cleaned_text) > 2000 else cleaned_text
        
    except Exception as e:
        logging.error(f"抓取和处理网页内容失败: {url} - {str(e)}")
        return ""

def parse_feed(rss_url):
    """解析RSS源并返回条目列表"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(rss_url, timeout=15, headers=headers)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        if feed.bozo:
            logging.error(f"RSS解析错误: {rss_url} - {feed.bozo_exception}")
            return []
        return feed.entries
    except Exception as e:
        logging.error(f"获取RSS源失败: {rss_url} - {e}")
        return []
