#!/usr/bin/env python3
"""
姣忔棩鏂伴椈鎶撳彇鑴氭湰
杩愯鏂瑰紡锛歱ython3 fetch_news.py
杈撳嚭锛氱敓鎴?docs/姣忔棩鏂伴椈/YYYY-MM-DD.md 鏂囦欢
"""

import os
import json
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))

# 鏂伴椈婧?SOURCES = [
    {
        "name": "鐭ヤ箮鐑",
        "url": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "parser": "zhihu"
    },
    {
        "name": "寰崥鐑悳",
        "url": "https://weibo.com/ajax/side/hotSearch",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "parser": "weibo"
    },
    {
        "name": "36姘揩璁?,
        "url": "https://36kr.com/newsflashes",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "parser": "36kr"
    }
]

def fetch_json(url, headers=None):
    """鑾峰彇 JSON 鏁版嵁"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None

def parse_zhihu(text):
    """瑙ｆ瀽鐭ヤ箮鐑"""
    if not text:
        return []
    try:
        data = json.loads(text)
        items = []
        for item in data.get("data", [])[:10]:
            target = item.get("target", {})
            title = target.get("title", "")
            url = target.get("url", "")
           鐑害 = item.get("detail_text", "")
            if title:
                items.append(f"- [{title}](https://www.zhihu.com/question/{target.get('id', '')}) ({鐑害})")
        return items
    except:
        return []

def parse_weibo(text):
    """瑙ｆ瀽寰崥鐑悳"""
    if not text:
        return []
    try:
        data = json.loads(text)
        items = []
        for item in data.get("data", {}).get("realtime", [])[:15]:
            title = item.get("word", "")
            鐑害 = item.get("num", "")
            if title:
                items.append(f"- {title} (鐑害: {鐑害})")
        return items
    except:
        return []

def parse_36kr(text):
    """瑙ｆ瀽 36姘?""
    # 36姘渶瑕佹覆鏌擄紝璺宠繃 HTML 瑙ｆ瀽
    return []

def generate_news():
    """鐢熸垚褰撴棩鏂伴椈"""
    today = datetime.now(CST).strftime("%Y-%m-%d")
    weekday_cn = ["涓€", "浜?, "涓?, "鍥?, "浜?, "鍏?, "鏃?]
    wd = weekday_cn[datetime.now(CST).weekday()]

    content = f"""---
layout: default
title: 姣忔棩鏂伴椈 - {today}
nav_order: 1
parent: 姣忔棩鏂伴椈
---

# 馃摪 姣忔棩鏂伴椈 | {today} 鍛▄wd}

"""

    for source in SOURCES:
        print(f"  Fetching {source['name']}...")
        text = fetch_json(source["url"], source["headers"])

        if source["parser"] == "zhihu":
            items = parse_zhihu(text)
        elif source["parser"] == "weibo":
            items = parse_weibo(text)
        else:
            items = []

        content += f"## {source['name']}\n\n"
        if items:
            content += "\n".join(items) + "\n\n"
        else:
            content += "> 鑾峰彇澶辫触鎴栨殏鏃犳暟鎹甛n\n"

    content += """\n---
*鏈唴瀹圭敱鑷姩鍖栬剼鏈敓鎴愶紝浠呬緵鍙傝€冦€?
"""

    # 鍐欏叆鏂囦欢
    news_dir = "docs/姣忔棩鏂伴椈"
    os.makedirs(news_dir, exist_ok=True)
    filepath = os.path.join(news_dir, f"{today}.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"鉁?鏂伴椈宸茬敓鎴? {filepath}")
    return filepath, content

if __name__ == "__main__":
    print("馃摪 寮€濮嬫姄鍙栨瘡鏃ユ柊闂?..")
    generate_news()
