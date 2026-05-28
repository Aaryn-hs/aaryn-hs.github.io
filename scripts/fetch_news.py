#!/usr/bin/env python3
"""
Daily news fetcher
Output: docs/daily-news/YYYY-MM-DD.md
"""

import os
import json
import urllib.request
import urllib.error
import ssl
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))

SOURCES = [
    {
        "name": "Zhihu Hot",
        "url": "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=10",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "parser": "zhihu"
    },
    {
        "name": "Weibo Hot",
        "url": "https://weibo.com/ajax/side/hotSearch",
        "headers": {"User-Agent": "Mozilla/5.0"},
        "parser": "weibo"
    }
]


def fetch_json(url, headers=None):
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
    if not text:
        return []
    try:
        data = json.loads(text)
        items = []
        for item in data.get("data", [])[:10]:
            target = item.get("target", {})
            title = target.get("title", "")
            hot = item.get("detail_text", "")
            if title:
                items.append("- " + title + " (" + hot + ")")
        return items
    except:
        return []


def parse_weibo(text):
    if not text:
        return []
    try:
        data = json.loads(text)
        items = []
        for item in data.get("data", {}).get("realtime", [])[:15]:
            title = item.get("word", "")
            hot = item.get("num", "")
            if title:
                items.append("- " + title + " (hot: " + str(hot) + ")")
        return items
    except:
        return []


def generate_news():
    today = datetime.now(CST).strftime("%Y-%m-%d")
    weekday_cn = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    wd = weekday_cn[datetime.now(CST).weekday()]

    lines = []
    lines.append("---")
    lines.append("layout: default")
    lines.append("title: Daily News - " + today)
    lines.append("nav_order: 1")
    lines.append("parent: Daily News")
    lines.append("---")
    lines.append("")
    lines.append("# Daily News | " + today + " " + wd)
    lines.append("")

    for source in SOURCES:
        print("  Fetching " + source["name"] + "...")
        text = fetch_json(source["url"], source["headers"])

        if source["parser"] == "zhihu":
            items = parse_zhihu(text)
        elif source["parser"] == "weibo":
            items = parse_weibo(text)
        else:
            items = []

        lines.append("## " + source["name"])
        lines.append("")
        if items:
            lines.extend(items)
        else:
            lines.append("> No data available")
        lines.append("")

    lines.append("---")
    lines.append("*Auto-generated.*")
    lines.append("")

    content = "\n".join(lines)

    news_dir = "docs/daily-news"
    os.makedirs(news_dir, exist_ok=True)
    filepath = os.path.join(news_dir, today + ".md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print("News saved: " + filepath)
    return filepath, content


if __name__ == "__main__":
    print("Fetching daily news...")
    generate_news()
