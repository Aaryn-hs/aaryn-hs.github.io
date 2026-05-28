#!/usr/bin/env python3
"""
Daily news fetcher - Chinese RSS sources
Output: docs/daily-news/YYYY-MM-DD.md
"""

import os
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import json
import ssl
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser

CST = timezone(timedelta(hours=8))


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return "".join(self.text)


def strip_html(html):
    s = MLStripper()
    s.feed(html or "")
    return s.get_data()


def fetch(url, headers_extra=None):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    }
    if headers_extra:
        headers.update(headers_extra)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            return resp.read()
    except Exception as e:
        print("  Error: " + str(e))
        return None


def parse_rss(data, limit=10):
    if not data:
        return []
    try:
        root = ET.fromstring(data)
        items = []
        for item in root.iter("item"):
            title = item.findtext("title", "")
            if title:
                items.append("- " + title.strip())
            if len(items) >= limit:
                break
        if not items:
            for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
                title = entry.findtext("{http://www.w3.org/2005/Atom}title", "")
                if title:
                    items.append("- " + title.strip())
                if len(items) >= limit:
                    break
        return items
    except Exception as e:
        print("  Parse error: " + str(e))
        return []


SOURCES = [
    # Use RSS Bridge as relay for Chinese sources
    {
        "name": "36氪",
        "url": "https://feedx.net/rss/36kr.xml",
        "type": "rss"
    },
    {
        "name": "知乎每日精选",
        "url": "https://feedx.net/rss/zhihu_daily.xml",
        "type": "rss"
    },
    {
        "name": "华尔街见闻",
        "url": "https://feedx.net/rss/wallstreetcn.xml",
        "type": "rss"
    },
]


def generate_news():
    today = datetime.now(CST).strftime("%Y-%m-%d")
    weekday_cn = ["一", "二", "三", "四", "五", "六", "日"]
    wd = weekday_cn[datetime.now(CST).weekday()]
    cn_date = "%s年%s月%s日" % (today.split("-")[0], today.split("-")[1], today.split("-")[2])

    lines = []
    lines.append("---")
    lines.append("layout: default")
    lines.append("title: 每日新闻 - " + today)
    lines.append("nav_order: 0")
    lines.append("parent: Daily News")
    lines.append("---")
    lines.append("")
    lines.append("# 📰 每日新闻 | " + cn_date + " 周" + wd)
    lines.append("")

    for source in SOURCES:
        print("Fetching " + source["name"] + "...")
        data = fetch(source["url"])
        items = parse_rss(data)

        lines.append("## " + source["name"])
        lines.append("")
        if items:
            lines.extend(items)
        else:
            lines.append("> 暂无数据")
        lines.append("")

    lines.append("---")
    lines.append("*本内容由自动化脚本生成，仅供参考*")
    lines.append("")

    content = "\n".join(lines)

    news_dir = "docs/daily-news"
    os.makedirs(news_dir, exist_ok=True)
    filepath = os.path.join(news_dir, today + ".md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print("新闻已保存: " + filepath)


if __name__ == "__main__":
    print("开始抓取每日新闻...")
    generate_news()
