#!/usr/bin/env python3
"""
build_rss_feed.py — builds feed.xml from blog/index.json
Improvements: no <category> tags, richer description with excerpt,
clean professional output for Facebook/Zapier sharing.
"""
import json, os
from datetime import datetime, timezone
from xml.sax.saxutils import escape

REPO_ROOT  = os.path.join(os.path.dirname(__file__), "..")
MANIFEST   = os.path.join(REPO_ROOT, "blog", "index.json")
FEED_PATH  = os.path.join(REPO_ROOT, "feed.xml")

SITE_URL   = "https://donialabstech.online"
SITE_TITLE = "DONIA LABS TECH — مدونة مختبر الأفكار الذكية"
SITE_DESC  = "أحدث مقالات التكنولوجيا، الذكاء الاصطناعي، وريادة الأعمال الرقمية من مختبر DONIA LABS TECH"
AUTHOR     = "Daoud Touina"

def rss_date(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

def main():
    with open(MANIFEST, encoding="utf-8") as f:
        data = json.load(f)

    articles = data.get("articles", [])
    now_rfc  = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

    items = []
    for a in articles[:20]:
        url      = f"{SITE_URL}/{a['url']}"
        title    = escape(a.get("title", ""))
        excerpt  = escape(a.get("excerpt", a.get("title", "")))
        # Rich description: emoji header + title + excerpt + link — no tags
        desc = escape(
            f"📝 {a.get('title','')}\n\n"
            f"{a.get('excerpt','')}\n\n"
            f"🔗 {url}"
        )
        pub_date = rss_date(a["date"]) if a.get("date") else now_rfc
        image    = a.get("image", "")
        enclosure = (
            f'    <enclosure url="{escape(image)}" type="image/jpeg" length="0"/>\n'
            if image else ""
        )
        # No <category> tags — keeps Facebook posts clean
        items.append(f"""  <item>
    <title>{title}</title>
    <link>{escape(url)}</link>
    <guid isPermaLink="true">{escape(url)}</guid>
    <description>{desc}</description>
    <author>noreply@donialabstech.online ({AUTHOR})</author>
    <pubDate>{pub_date}</pubDate>
{enclosure}  </item>""")

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{escape(SITE_TITLE)}</title>
  <link>{SITE_URL}</link>
  <description>{escape(SITE_DESC)}</description>
  <language>ar</language>
  <lastBuildDate>{now_rfc}</lastBuildDate>
  <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
  <image>
    <url>{SITE_URL}/images/daoud-touina.jpg</url>
    <title>{escape(SITE_TITLE)}</title>
    <link>{SITE_URL}</link>
  </image>
{chr(10).join(items)}
</channel>
</rss>
"""
    with open(FEED_PATH, "w", encoding="utf-8") as f:
        f.write(feed)
    print(f"feed.xml built: {len(articles[:20])} items (no category tags)")

if __name__ == "__main__":
    main()
