#!/usr/bin/env python3
"""
Daily news fetcher - International RSS sources
Works reliably from GitHub Actions runners.
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
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print("  Error: " + str(e))
        return None


def parse_rss_text(text, limit=10):
    if not text:
        return []
    try:
        root = ET.fromstring(text)
        items = []
        for item in root.iter("item"):
            title = item.findtext("title", "")
            desc = item.findtext("description", "")
            if title:
                clean = strip_html(title).strip()
                if clean:
                    items.append("- " + clean)
            if len(items) >= limit:
                break
        if not items:
            for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
                title = entry.findtext("{http://www.w3.org/2005/Atom}title", "")
                if title:
                    clean = strip_html(title).strip()
                    if clean:
                        items.append("- " + clean)
                if len(items) >= limit:
                    break
        return items
    except Exception as e:
        print("  Parse error: " + str(e))
        return []


def fetch_hackernews():
    """Hacker News API - very reliable"""
    text = fetch("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not text:
        return []
    try:
        ids = json.loads(text)[:15]
        items = []
        for sid in ids:
            item = fetch("https://hacker-news.firebaseio.com/v0/item/" + str(sid) + ".json")
            if item:
                data = json.loads(item)
                title = data.get("title", "")
                if title:
                    items.append("- " + title)
        return items
    except:
        return []


def fetch_github_trending():
    """GitHub trending repos via API"""
    text = fetch("https://api.github.com/search/repositories?q=created:>2026-05-26+stars:>100&sort=stars&order=desc&per_page=10",
                 headers_extra={"Accept": "application/vnd.github.v3+json"})
    if not text:
        return []
    try:
        data = json.loads(text)
        items = []
        for repo in data.get("items", [])[:10]:
            name = repo.get("full_name", "")
            desc = repo.get("description", "") or ""
            stars = repo.get("stargazers_count", 0)
            lang = repo.get("language") or ""
            desc_short = strip_html(desc)[:60] if desc else ""
            parts = ["- " + name]
            if desc_short:
                parts.append(": " + desc_short)
            if lang:
                parts.append(" [" + lang + "]" if not desc_short else " (" + lang + ")")
            items.append("".join(parts))
        return items
    except:
        return []


def generate_news():
    today = datetime.now(CST).strftime("%Y-%m-%d")
    weekday_cn = ["一", "二", "三", "四", "五", "六", "日"]
    wd = weekday_cn[datetime.now(CST).weekday()]
    cn_date = today[0:4] + "年" + today[5:7] + "月" + today[8:10] + "日"

    lines = []
    lines.append("---")
    lines.append("layout: default")
    lines.append("title: Daily News - " + today)
    lines.append("nav_order: 0")
    lines.append("parent: Daily News")
    lines.append("---")
    lines.append("")
    lines.append("# 📰 Daily News | " + cn_date + " 周" + wd)
    lines.append("")

    # Hacker News
    print("Fetching Hacker News...")
    hn_items = fetch_hackernews()
    lines.append("## Hacker News (科技)")
    lines.append("")
    if hn_items:
        lines.extend(hn_items)
    else:
        lines.append("> No data")
    lines.append("")

    # GitHub Trending
    print("Fetching GitHub Trending...")
    gh_items = fetch_github_trending()
    lines.append("## GitHub Trending (热门项目)")
    lines.append("")
    if gh_items:
        lines.extend(gh_items)
    else:
        lines.append("> No data")
    lines.append("")

    # BBC News - XML RSS
    print("Fetching BBC News...")
    bbc = fetch("https://feeds.bbci.co.uk/news/rss.xml")
    bbc_items = parse_rss_text(bbc)
    lines.append("## BBC (国际)")
    lines.append("")
    if bbc_items:
        lines.extend(bbc_items)
    else:
        lines.append("> No data")
    lines.append("")

    lines.append("---")
    lines.append("*Auto-generated*")
    lines.append("")

    content = "\n".join(lines)

    news_dir = "docs/daily-news"
    os.makedirs(news_dir, exist_ok=True)
    filepath = os.path.join(news_dir, today + ".md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print("Saved: " + filepath)


if __name__ == "__main__":
    print("Fetching daily news...")
    generate_news()
