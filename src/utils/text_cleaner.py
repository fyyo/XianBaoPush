# src/utils/text_cleaner.py - 高级线报内容清理和优化工具
import re
import html
import hashlib
from typing import List, Set, Tuple
from urllib.parse import urlparse

def clean_html_tags(text: str) -> str:
    """
    1. 完整的HTML标签清理（改进版 - 先提取链接再清理）
    - 先提取并保护所有链接
    - 完全移除所有HTML标签，保留纯文本内容
    - 将换行标签转换为实际换行符
    - 处理HTML实体编码
    - 恢复提取的链接
    """
    if not text:
        return ""
    
    # 第1步：提取并保护商品链接（过滤掉图片和其他无关链接）
    url_pattern = r'https?://[^\s<>"\'\(\)，。；！？]+[^\s<>"\'\(\)，。；！？\.]'
    
    # 从HTML属性中提取链接
    attr_links = re.findall(r'(?:href|src)=["\']?(https?://[^"\'>\s]+)', text, re.IGNORECASE)
    
    # 从普通文本中提取链接
    text_links = re.findall(url_pattern, text)
    
    # 合并所有链接并去重
    all_links = list(dict.fromkeys(attr_links + text_links))
    
    # 定义商品链接域名模式（只保护这些商品链接）
    shopping_domains = [
        # 淘宝系
        's.click.taobao.com',
        'uland.taobao.com',
        'detail.tmall.com',
        'detail.taobao.com',
        
        # 京东系
        'u.jd.com',
        'item.jd.com',
        'pro.jd.com',
        'coupon.m.jd.com',
        
        # 拼多多系
        'p.pinduoduo.com',
        'mobile.yangkeduo.com',
        
        # 其他购物平台短链
        'dwz.cn',
        'dpurl.cn',
        't.cn',
        'tb.cn',
        
        # 线报和优惠网站
        'm.zzzdm.com',
        'ym.030217.xyz'
    ]
    
    # 过滤并清理商品链接
    cleaned_links = []
    for link in all_links:
        # 移除链接末尾的HTML标记如 " 、 </a> 等
        link = re.sub(r'["\']?</?\w+>?$', '', link)
        link = re.sub(r'["\']$', '', link)
        
        if link and link not in cleaned_links:
            # 检查是否是商品链接
            is_shopping_link = False
            for domain in shopping_domains:
                if domain in link:
                    is_shopping_link = True
                    break
            
            # 只保护商品链接，过滤掉图片链接和其他无关链接
            if is_shopping_link:
                cleaned_links.append(link)
    
    # 第2步：处理HTML实体编码
    text = html.unescape(text)
    
    # 第3步：将换行相关标签转换为换行符
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?p[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</?div[^>]*>', '\n', text, flags=re.IGNORECASE)
    
    # 第4步：完全移除所有其他HTML标签
    text = re.sub(r'<[^<>]+?>', '', text)
    
    # 第5步：清理特殊HTML实体编码
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&apos;', "'", text)
    
    # 第6步：基础空白字符处理
    text = re.sub(r'[ \t]+', ' ', text)  # 多个空格合并为单个
    text = re.sub(r'\r\n', '\n', text)   # 统一换行符
    text = re.sub(r'\r', '\n', text)     # 统一换行符
    
    # 第7步：只添加文本中缺失的链接（避免重复）
    if cleaned_links:
        text = text.strip()
        missing_links = []
        
        for link in cleaned_links:
            # 检查链接是否已经在文本中存在
            if link not in text:
                missing_links.append(link)
        
        # 只添加缺失的链接
        if missing_links:
            text += '\n' + '\n'.join(missing_links)
    
    return text.strip()

def remove_images_and_media(text: str) -> str:
    """
    2. 图片和媒体处理
    - 完全删除所有图片标签
    - 移除包含图片的div容器
    - 清理图片相关的描述文字
    - 保持文本内容的完整性
    """
    if not text:
        return ""
    
    # 移除图片标签和相关内容
    text = re.sub(r'<img[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<picture[^>]*>.*?</picture>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<video[^>]*>.*?</video>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<audio[^>]*>.*?</audio>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # 移除包含图片的div容器
    text = re.sub(r'<div[^>]*class[^>]*image[^>]*>.*?</div>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<div[^>]*class[^>]*photo[^>]*>.*?</div>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<div[^>]*class[^>]*pic[^>]*>.*?</div>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # 清理图片相关的描述文字
    image_desc_patterns = [
        r'图片[:：]\s*[^\n]*',
        r'图[:：]\s*[^\n]*',
        r'截图[:：]\s*[^\n]*',
        r'配图[:：]\s*[^\n]*',
        r'如图[:：]\s*[^\n]*',
        r'见图[:：]\s*[^\n]*',
    ]
    
    for pattern in image_desc_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text

def remove_duplicate_content(text: str, title: str = "") -> str:
    """
    3. 重复内容处理
    - 识别并删除完全相同的文本行
    - 去除重复的分隔线
    - 清理重复的空行和空白字符
    - 处理标题重复
    """
    if not text:
        return ""
    
    lines = text.split('\n')
    unique_lines = []
    seen_lines: Set[str] = set()
    
    # 预处理标题，用于重复检测
    title_normalized = ""
    if title:
        title_normalized = re.sub(r'[^\w\s]', '', title.lower()).strip()
    
    for line in lines:
        line_stripped = line.strip()
        
        # 跳过空行（稍后统一处理）
        if not line_stripped:
            unique_lines.append("")
            continue
            
        # 去除重复的分隔线
        if re.match(r'^[-=—_\*\#]{3,}$', line_stripped):
            continue
            
        # 检测与标题重复的内容
        if title_normalized:
            line_normalized = re.sub(r'[^\w\s]', '', line_stripped.lower()).strip()
            if line_normalized and title_normalized in line_normalized:
                # 如果行内容包含标题且相似度很高，跳过
                similarity = len(set(title_normalized.split()) & set(line_normalized.split()))
                if similarity >= len(title_normalized.split()) * 0.7:
                    continue
        
        # 生成行的哈希值用于去重
        line_hash = hashlib.md5(line_stripped.encode('utf-8')).hexdigest()
        
        if line_hash not in seen_lines:
            seen_lines.add(line_hash)
            unique_lines.append(line_stripped)
    
    # 清理连续的空行
    cleaned_lines = []
    prev_empty = False
    
    for line in unique_lines:
        is_empty = not line.strip()
        
        if is_empty:
            if not prev_empty:  # 只保留一个空行
                cleaned_lines.append("")
            prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False
    
    # 移除开头和结尾的空行
    while cleaned_lines and not cleaned_lines[0].strip():
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()
    
    return '\n'.join(cleaned_lines)

def normalize_formatting(text: str) -> str:
    """
    4. 格式规范化
    - 空白字符处理
    - 换行符优化
    - 控制连续空行数量
    - 清理行首行尾空白字符
    """
    if not text:
        return ""
    
    # 规范化制表符和特殊空白字符
    text = re.sub(r'\t', ' ', text)  # 制表符转空格
    text = re.sub(r'[\u00A0\u2000-\u200B\u2028\u2029]', ' ', text)  # 特殊空白字符
    text = re.sub(r'[ ]{2,}', ' ', text)  # 多个空格合并为单个
    
    # 统一换行符格式
    text = re.sub(r'\r\n|\r', '\n', text)
    
    lines = text.split('\n')
    normalized_lines = []
    
    for line in lines:
        # 清理行首行尾的空白字符
        cleaned_line = line.strip()
        normalized_lines.append(cleaned_line)
    
    # 控制连续空行的数量（最多保留一个空行）
    final_lines = []
    prev_empty = False
    
    for line in normalized_lines:
        is_empty = not line
        
        if is_empty:
            if not prev_empty:
                final_lines.append("")
            prev_empty = True
        else:
            final_lines.append(line)
            prev_empty = False
    
    # 确保文本开头和结尾没有空行
    while final_lines and not final_lines[0]:
        final_lines.pop(0)
    while final_lines and not final_lines[-1]:
        final_lines.pop()
    
    return '\n'.join(final_lines)

def intelligent_content_compression(text: str, max_length: int = 1500) -> Tuple[str, bool]:
    """
    5. 智能内容压缩和长度控制
    - 设置最大长度限制
    - 智能截断策略
    - 识别并删除无意义的短行
    - 保留关键商品信息和价格
    """
    if not text:
        return "", False
    
    truncated = False
    
    # 如果文本长度在限制内，直接返回
    if len(text) <= max_length:
        return text, False
    
    lines = text.split('\n')
    compressed_lines = []
    current_length = 0
    
    # 识别重要信息的关键词
    important_keywords = [
        '价格', '元', '折', '优惠', '券', '送', '免费', '包邮', '限时',
        '抢购', '秒杀', '特价', '活动', '满减', '叠加', '返现', '红包',
        '¥', '$', '￥', '促销', '打折', '减价', '特卖'
    ]
    
    # 第一轮：保留重要信息行
    important_lines = []
    other_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # 识别包含重要关键词的行
        is_important = any(keyword in line_stripped for keyword in important_keywords)
        
        # 识别包含价格信息的行
        has_price = re.search(r'[¥￥$]\d+|(\d+\.?\d*)元|\d+折', line_stripped)
        
        # 过滤无意义的短行（少于3个字符且不包含重要信息）
        is_meaningless_short = len(line_stripped) < 3 and not is_important and not has_price
        
        if is_meaningless_short:
            continue
            
        if is_important or has_price:
            important_lines.append(line_stripped)
        else:
            other_lines.append(line_stripped)
    
    # 第二轮：按优先级添加内容
    # 先添加重要信息
    for line in important_lines:
        if current_length + len(line) + 1 <= max_length:
            compressed_lines.append(line)
            current_length += len(line) + 1
        else:
            truncated = True
            break
    
    # 再添加其他信息
    for line in other_lines:
        if current_length + len(line) + 1 <= max_length:
            compressed_lines.append(line)
            current_length += len(line) + 1
        else:
            truncated = True
            break
    
    # 合并相关的短句（如果空间允许）
    final_lines = []
    temp_sentence = ""
    
    for line in compressed_lines:
        if len(temp_sentence) + len(line) + 1 < 100:  # 合并短句
            if temp_sentence:
                temp_sentence += " " + line
            else:
                temp_sentence = line
        else:
            if temp_sentence:
                final_lines.append(temp_sentence)
            temp_sentence = line
    
    if temp_sentence:
        final_lines.append(temp_sentence)
    
    result = '\n'.join(final_lines)
    
    # 如果仍然超长，进行最后的截断
    if len(result) > max_length:
        result = result[:max_length-3] + "..."
        truncated = True
    
    return result, truncated
def extract_and_categorize_links(text: str) -> Tuple[List[str], List[str]]:
    """
    6. 链接处理 - 识别和分类链接
    - 识别文本中的所有链接
    - 区分商品链接和其他链接
    - 保持链接的完整性
    """
    if not text:
        return [], []
    
    # 正则表达式匹配各种链接格式
    url_pattern = r'https?://[^\s<>"\'\(\)，。；！？]+[^\s<>"\'\(\)，。；！？\.]'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        return [], []
    
    # 去重保持顺序
    unique_urls = list(dict.fromkeys(urls))
    
    # 分类链接
    shopping_links = []
    other_links = []
    
    # 商品链接的域名模式
    shopping_domains = [
        'taobao.com', 'tmall.com', 's.click.taobao.com',
        'jd.com', 'item.jd.com', 'u.jd.com',
        'pinduoduo.com', 'yangkeduo.com', 'p.pinduoduo.com',
        'vip.com', 'suning.com', 'gome.com.cn',
        'amazon.cn', 'kaola.com', 'dangdang.com'
    ]
    
    for url in unique_urls:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # 检查是否为商品链接
            is_shopping = any(shop_domain in domain for shop_domain in shopping_domains)
            
            if is_shopping:
                shopping_links.append(url)
            else:
                other_links.append(url)
                
        except Exception:
            # 解析失败的链接归为其他类型
            other_links.append(url)
    
    return shopping_links, other_links

def advanced_text_cleanup(text: str, title: str = "", max_length: int = 1500) -> str:
    """
    高级文本清理 - 整合所有清理步骤
    这是主要的清理函数，按顺序执行所有清理步骤
    """
    if not text:
        return ""
    
    # 步骤1: HTML标签清理
    text = clean_html_tags(text)
    
    # 步骤2: 图片和媒体处理
    text = remove_images_and_media(text)
    
    # 步骤3: 重复内容处理
    text = remove_duplicate_content(text, title)
    
    # 步骤4: 格式规范化
    text = normalize_formatting(text)
    
    # 步骤5: 智能内容压缩
    text, was_truncated = intelligent_content_compression(text, max_length)
    
    return text

def summarize_text(text: str, max_lines: int = 10, max_chars: int = 1500, title: str = "") -> str:
    """
    优化的文本摘要函数
    结合所有高级清理功能，生成高质量的线报摘要
    """
    if not text:
        return ""
    
    # 使用高级清理功能
    cleaned_text = advanced_text_cleanup(text, title, max_chars)
    
    if not cleaned_text:
        return ""
    
    lines = cleaned_text.split('\n')
    
    # 过滤噪音前缀行
    noisy_prefixes = (
        "分组", "时间", "关键词", "链接", "来源", "分类", "作者",
        "标签", "发布", "更新", "阅读", "点击", "浏览"
    )
    
    filtered_lines = []
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
            
        # 跳过噪音行
        is_noisy = any(
            line_stripped.startswith(p + "：") or
            line_stripped.startswith(p + ":") or
            line_stripped.startswith(p + " ")
            for p in noisy_prefixes
        )
        
        if not is_noisy:
            filtered_lines.append(line_stripped)
        
        # 控制行数
        if len(filtered_lines) >= max_lines:
            break
    
    result = '\n'.join(filtered_lines)
    
    # 最终长度检查
    if len(result) > max_chars:
        result = result[:max_chars-3] + "..."
    
    return result

# 为了向后兼容，保留旧函数名
def extract_and_format_links(text: str) -> str:
    """
    提取并格式化链接（向后兼容函数）
    """
    shopping_links, other_links = extract_and_categorize_links(text)
    all_links = shopping_links + other_links
    return '\n'.join(all_links) if all_links else ""
    