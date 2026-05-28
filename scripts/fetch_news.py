#!/usr/bin/env python3
"""
Daily news fetcher - RSS based
Output: docs/daily-news/YYYY-MM-DD.md
"""

import os
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
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


def fetch(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36"
    })
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
        # Handle RSS and Atom
        items = []
        for item in root.iter("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            desc = item.findtext("description", "")
            desc = strip_html(desc)[:100] if desc else ""
            if title:
                items.append("- " + title)
            if len(items) >= limit:
                break
        if not items:
            for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
                title = entry.findtext("{http://www.w3.org/2005/Atom}title", "")
                link_el = entry.find("{http://www.w3.org/2005/Atom}link")
                link = link_el.attrib.get("href", "") if link_el is not None else ""
                if title:
                    items.append("- " + title)
                if len(items) >= limit:
                    break
        return items
    except Exception as e:
        print("  Parse error: " + str(e))
        return []


SOURCES = [
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage?count=10",
        "type": "rss"
    },
    {
        "name": "BBC News",
        "url": "https://feeds.bbci.co.uk/news/rss.xml",
        "type": "rss"
    },
    {
        "name": "Reuters",
        "url": "https://www.rss-bridge.org/bridge01/?action=display&bridge=FilterBridge&url=https%3A%2F%2Fwww.reuters.com&content_filter=&content_filter_type=text&title_filter=&title_filter_type=text&inverse=on&case_insensitive=on&fix_encoding=on&format=Atom",
        "type": "rss"
    }
]


def generate_news():
    today = datetime.now(CST).strftime("%Y-%m-%d")
    weekday_cn = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    wd = weekday_cn[datetime.now(CST).weekday()]

    lines = []
    lines.append("---")
    lines.append("layout: default")
    lines.append("title: Daily News - " + today)
    lines.append("nav_order: 0")
    lines.append("parent: Daily News")
    lines.append("---")
    lines.append("")
    lines.append("# Daily News | " + today + " " + wd)
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


if __name__ == "__main__":
    print("Fetching daily news...")
    generate_news()
