from typing import List, Literal, Optional, Dict, Any
from config import Config
import requests
import json
import os
from bs4 import BeautifulSoup as bs
from datetime import datetime
from urllib.parse import urlparse, urljoin
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from .ocr import extract_text_from_image, extract_text_from_image_by_llm




def baidu_search(
    query: str,
    top_k: int = 20,
    search_recency_filter: Optional[Literal['week', 'month']] = 'week',
    sites: Optional[List[str]] = None,
    timeout: tuple = (5, 30),
) -> Dict[str, Any]:
    """
    使用百度搜索，获取相关信息
    
    Args:
        query: 搜索关键词
    """
    api_key = Config().get_tool_api_key("baidu")
    if not api_key:
        raise RuntimeError("缺少 Baidu 工具 api_key，请在 config.toml 的 [tools.baidu] 配置 api_key")

    url = 'https://qianfan.baidubce.com/v2/ai_search/chat/completions'
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
            "messages": [
                {
                    "content": query,
                    "role": "user"
                }
            ],
            "search_source": "baidu_search_v2",
            # 默认返回20条网页结果
            "resource_type_filter":[{"type": "web", "top_k": top_k}],
            #  "search_filter": {"match": {"site": ['www.cls.cn']}}s
        }
    
    if search_recency_filter:
        payload['search_recency_filter'] = search_recency_filter
        
    if sites:
        payload['search_filter'] = {"match": {"site": sites}}
        
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}

def parse_url_filename(url: str) -> str:
    from urllib.parse import urlparse
    import os
    
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)

def url_got_extracted(url: str, folder: str = 'temp') -> bool:
    file_name = parse_url_filename(url)
    return os.path.exists(os.path.join(folder, file_name))

@retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(
            (Exception, ValueError)
        ),  # Don't retry TokenLimitExceeded
    )
def download_image(url: str, folder: str = 'temp', timeout: tuple = (5, 30)) -> str:
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, parse_url_filename(url))
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        with open(path, 'wb') as f:
            f.write(resp.content)
        return path
    except Exception as e:
        print(e)
        raise 

def get_cls_topics(subject_id: int):
    headers = {"Content-Type": "application/json",
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
    response = requests.get(f'https://www.cls.cn/subject/{subject_id}', headers=headers)
    page = bs(response.text, 'lxml')
    
    topics = []
    for p in page.find_all('div', class_='clearfix b-c-e6e7ea subject-interest-list'):
        pub_time = p.find('div', class_='clearfix subject-interest-small-title').text[:16]
        title = p.find('a', class_='f-w-b c-222').text
        url = p.find('a', class_='f-w-b c-222').get('href')
        content = p.find('div', class_='f-s-14 c-666 line2 subject-interest-brief').text
        
        topics.append({'pub_time': pub_time, 'title': title, 'url': url, 'content': content})
        
    return topics

def get_cls_market_summaries():
    return get_cls_topics(1135)

def get_cls_morning_news_brief():
    return get_cls_topics(1151)

def get_local_path(url: str) -> str:
    """
    根据URL生成缓存文件路径
    
    Args:
        url: 要缓存的URL
        
    Returns:
        缓存文件的完整路径
    """
    cache_dir = 'data'
    
    # 解析URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    # 处理路径部分，去除开头斜杠，并替换斜杠为下划线
    filename = parsed_url.path.lstrip('/').replace('/', '_')
    
    # 确保缓存目录存在
    local_path = os.path.join(cache_dir, domain, f"{filename}.md")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    return local_path

def is_saved(url: str) -> bool:
    """
    检查URL是否已经缓存且未过期
    
    Args:
        url: 要检查的URL
        
    Returns:
        如果缓存存在且未过期返回True，否则返回False
    """
    cache_path = get_local_path(url)
    
    return os.path.exists(cache_path)

def load_from_local(url: str) -> str:
    """
    从缓存中加载内容
    
    Args:
        url: 要加载的URL
        
    Returns:
        缓存的内容
    """
    local_path = get_local_path(url)
    

    try:
        with open(local_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取缓存文件失败: {e}")
        return ''

def save_to_local(url: str, content: str) -> bool:
    """
    将内容保存到缓存
    
    Args:
        url: 要缓存的URL
        content: 要缓存的内容
        
    Returns:
        保存成功返回True，失败返回False
    """
    local_path = get_local_path(url)
    try:
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except IOError as e:
        print(f"保存缓存文件失败: {e}")
        return False

def get_cls_topic_detail(url, img_rec: bool = False):
    """
    获取市场总结，支持本地缓存功能
    
    Args:
        url: 要获取的市场总结URL
        
    Returns:
        市场总结内容
    """
    # 构建完整的URL
    full_url = urljoin('https://www.cls.cn/', url)
    
    # 第一步：检查本地缓存
    if is_saved(full_url):
        print(f"从缓存加载内容: {url}")
        content = load_from_local(full_url)
        if content:
            return content
    
    # 第二步：从网络获取内容
    print(f"从网络获取内容: {url}")
    try:
        headers = {
            "Content-Type": "application/json",
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }
        
        # 获取页面内容
        response = requests.get(full_url, headers=headers)
        response.raise_for_status()  # 检查HTTP错误
        
        page = bs(response.text, 'lxml')
        msg = ''
        first_img_skipped = False
        
        # 查找内容区域
        content_div = page.find('div', class_='m-b-40 detail-content')
        if not content_div:
            raise ValueError("未找到内容区域")
        
        # 解析内容
        for p in content_div.find_all('p'):
            img_tag = p.find('img')
            if img_tag and img_rec:
                img_url = urljoin('https://www.cls.cn/', img_tag.get('src'))
                try:
                    if first_img_skipped:
                        local_path = download_image(img_url)
                        first_img_skipped = True
                    msg += extract_text_from_image(local_path)
                except Exception as e:
                    msg += f"[图片文字提取失败: {e}]\n"
            else:
                msg += p.get_text()
            msg += '\n'
        
        # 第三步：保存到缓存
        if msg.strip():  # 确保内容不为空
            if save_to_local(full_url, msg):
                print(f"内容已保存到缓存: {get_local_path(full_url)}")
            else:
                print(f"保存缓存失败")
        
        return msg
        
    except Exception as e:
        print(f"获取内容失败: {e}")
        return f"获取内容失败: {str(e)}"

def get_cls_market_summary_by_date(date: str):
    """
    根据日期获取大盘总结
    
    Args:
        date: 日期，格式为YYYY-MM-DD
    """
    if date > datetime.now().strftime('%Y-%m-%d'):
        return f"日期{date}大于当前日期{datetime.now().strftime('%Y-%m-%d')}, 请输入正确的日期"
    
    if date == datetime.now().strftime('%Y-%m-%d'):
        if datetime.now().hour < 16:
            return f"当前时间{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}小于16点，无法获取今日的大盘总结"

    summaries = get_cls_market_summaries()
    for s in summaries:
        if s['pub_time'][:10] == date:
            return get_cls_topic_detail(s['url'], img_rec=True)
    return f"没有找到{date}的大盘总结, 可能由于日期不是开盘时间"

def get_cls_morning_brief_by_date(date: str):
    """
    根据日期获取晨报
    
    Args:
        date: 日期，格式为YYYY-MM-DD
    """
    if date > datetime.now().strftime('%Y-%m-%d'):
        return f"日期{date}大于当前日期{datetime.now().strftime('%Y-%m-%d')}, 请输入正确的日期"
    
    if date == datetime.now().strftime('%Y-%m-%d'):
        if datetime.now().hour < 16:
            return f"当前时间{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}小于16点，无法获取今日的晨报"

    summaries = get_cls_morning_news_brief()
    for s in summaries:
        if s['pub_time'][:10] == date:
            return get_cls_topic_detail(s['url'], img_rec=True)
    return f"没有找到{date}的晨报, 可能由于日期不是开盘时间"


def get_news_from_eastmoney(query: str):
    """
    获取东方财富网的新闻
    
    Args:
        query: 搜索关键词
        
    Returns:
        新闻列表
    """
    import akshare as ak
    df = ak.stock_news_em(symbol = query)
    df = df[['新闻标题','新闻内容', '发布时间', '文章来源', '新闻链接']]
    
    return df.to_dict(orient='records')
    
    
def get_news_content_from_eastmoney(urls: List[str]):
    """
    获取东方财富网的新闻内容
    
    Args:
        urls: 新闻URL列表
        
    Returns:
        新闻内容列表
    """
    headers = {
            "Content-Type": "application/json",
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }
    
    contents = []
    for i, url in enumerate(urls):
        msg = f'{i+1}. **{url}**' + '\n'
        
        msg += 'content:\n'
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        page = bs(response.text, 'lxml')
        try:
            for txt in page.find_all(class_ = 'txtinfos'):
                for p in txt.find_all('p'):
                    msg += p.get_text()
                    msg += '\n'
        except Exception as e:
            msg += f'获取内容失败: {str(e)}'
        
        contents.append(msg)
    return contents