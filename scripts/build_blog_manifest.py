#!/usr/bin/env python3
"""
build_blog_manifest.py
-----------------------
Scans blog/*.html (the real daily pages already being published by the
existing automation) and builds blog/index.json — a lightweight manifest
the homepage reads to build the article cards (title, excerpt, tags, date,
and a link to the real page). It does NOT duplicate the full article text;
"read more" on the homepage fetches the real page content on demand.

Run by: .github/workflows/build-blog-manifest.yml
(triggered automatically whenever something is pushed into blog/, plus a
daily safety-net schedule and a manual button)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
BLOG_DIR = os.path.join(REPO_ROOT, "blog")
MANIFEST_PATH = os.path.join(BLOG_DIR, "index.json")

AUTHOR_NAME = "Daoud Touina"
AUTHOR_TITLE = "رائد أعمال | مؤسس مختبر الأفكار الذكية وقائد المشاريع"

DATE_FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.html$")

AR_MONTHS = {
    1: "جانفي", 2: "فيفري", 3: "مارس", 4: "أفريل", 5: "ماي", 6: "جوان",
    7: "جويلية", 8: "أوت", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر",
}
AR_WEEKDAYS = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]

IMAGE_POOL = {
    "default": "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "تعليم": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "ذكاء اصطناعي": "https://images.unsplash.com/photo-1677442136019-21780ecad995?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "تسويق": "https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "تصميم": "https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1169&q=80",
    "أمن سيبراني": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "أعمال": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
}


def arabic_date_str(dt):
    return f"{AR_WEEKDAYS[dt.weekday()]}، {dt.day} {AR_MONTHS[dt.month]} {dt.year}"


def pick_image(tags):
    for t in tags:
        for key, url in IMAGE_POOL.items():
            if key != "default" and key in t:
                return url
    return IMAGE_POOL["default"]


def strip_html_tags(text):
    return re.sub(r"<[^>]+>", " ", text)


def extract(html, fname, file_date):
    title_m = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    title = title_m.group(1).strip() if title_m else fname
    title = re.sub(r"\s*\|\s*DONIA LABS TECH\s*$", "", title).strip()

    desc_m = re.search(r'<meta\s+name="description"\s+content="(.*?)"', html, re.DOTALL)
    excerpt = desc_m.group(1).strip() if desc_m else ""
    excerpt = re.sub(r"\s*-\s*مقال من مدونة DONIA LABS TECH\s*$", "", excerpt).strip()

    tags_m = re.search(r"الوسوم:\s*</strong>\s*([^<]+)", html)
    if not tags_m:
        tags_m = re.search(r"الوسوم:\s*([^<\n]+)", html)
    tags = [t.strip() for t in tags_m.group(1).split(",")] if tags_m else []

    body_m = re.search(r"<body>(.*?)</body>", html, re.DOTALL)
    body_text = strip_html_tags(body_m.group(1)) if body_m else strip_html_tags(html)
    word_count = len(re.findall(r"\S+", body_text))
    minutes = max(1, round(word_count / 180))
    read_time = f"{minutes} دقائق قراءة" if minutes != 1 else "دقيقة قراءة واحدة"

    return {
        "id": file_date.strftime("%Y-%m-%d"),
        "slug": file_date.strftime("%Y-%m-%d"),
        "title": title,
        "excerpt": excerpt,
        "image": pick_image(tags),
        "author": AUTHOR_NAME,
        "authorTitle": AUTHOR_TITLE,
        "date": file_date.replace(tzinfo=timezone.utc).isoformat(),
        "dateStr": arabic_date_str(file_date),
        "readTime": read_time,
        "views": 0,
        "tags": tags,
        "aiGenerated": True,
        "url": f"blog/{fname}",
    }


def main():
    if not os.path.isdir(BLOG_DIR):
        print(f"::error::Blog directory not found at {BLOG_DIR}", file=sys.stderr)
        sys.exit(1)

    entries = []
    for fname in sorted(os.listdir(BLOG_DIR)):
        m = DATE_FILENAME_RE.match(fname)
        if not m:
            continue  # skip privacy.html, index.json, anything not a dated post
        file_date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        path = os.path.join(BLOG_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        entries.append(extract(html, fname, file_date))

    entries.sort(key=lambda a: a["date"], reverse=True)

    manifest = {
        "_readme": "هذا الملف يُبنى تلقائياً بواسطة scripts/build_blog_manifest.py — لا تعدّله يدوياً.",
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "articles": entries,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Built manifest with {len(entries)} article(s) at {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
