#!/usr/bin/env python3
"""
build_blog_manifest.py
-----------------------
Scans blog/*.html and builds blog/index.json.
Key improvement: deduplicates by title (keeps only the LATEST file for each title).

Run by: .github/workflows/build-blog-manifest.yml
"""

import json, os, re, sys
from datetime import datetime, timezone

REPO_ROOT   = os.path.join(os.path.dirname(__file__), "..")
BLOG_DIR    = os.path.join(REPO_ROOT, "blog")
MANIFEST    = os.path.join(BLOG_DIR, "index.json")

AUTHOR_NAME  = "Daoud Touina"
AUTHOR_TITLE = "رائد أعمال | مؤسس مختبر الأفكار الذكية وقائد المشاريع"

DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.html$")

AR_MONTHS = {
    1:"جانفي",2:"فيفري",3:"مارس",4:"أفريل",5:"ماي",6:"جوان",
    7:"جويلية",8:"أوت",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر",
}
AR_DAYS = ["الإثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]

IMAGE_POOL = {
    "default":     "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "تعليم":       "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "ذكاء اصطناعي":"https://images.unsplash.com/photo-1677442136019-21780ecad995?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "تسويق":       "https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "تصميم":       "https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1169&q=80",
    "أمن":         "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "أعمال":       "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "مجتمع":       "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "ريادة":       "https://images.unsplash.com/photo-1559136555-9303baea8ebd?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "تقنية":       "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
}

def ar_date(dt):
    return f"{AR_DAYS[dt.weekday()]}، {dt.day} {AR_MONTHS[dt.month]} {dt.year}"

def pick_image(tags):
    for t in tags:
        for k, url in IMAGE_POOL.items():
            if k != "default" and k in t:
                return url
    return IMAGE_POOL["default"]

def extract(html, fname, file_date):
    title_m = re.search(r"<title>(.*?)</title>", html)
    title = re.sub(r"\s*\|?\s*DONIA LABS TECH\s*$", "", title_m.group(1)).strip() if title_m else fname

    desc_m = re.search(r'<meta\s+name="description"\s+content="(.*?)"', html)
    excerpt = re.sub(r"\s*-\s*مقال من مدونة DONIA LABS TECH\s*$", "",
                     desc_m.group(1)).strip() if desc_m else title

    # Extract clean body text for a better excerpt if meta desc is generic
    if excerpt == title:
        body_m = re.search(r"<body>(.*?)</body>", html, re.DOTALL)
        if body_m:
            clean = re.sub(r"<[^>]+>", " ", body_m.group(1))
            clean = re.sub(r"\s+", " ", clean).strip()
            # Skip first 200 chars (likely nav/meta) and take 200 chars of content
            excerpt = clean[200:400].strip() or title

    tags_m = re.search(r"الوسوم[:：]\s*</?\w*>?\s*([^\n<]+)", html)
    tags = [t.strip() for t in tags_m.group(1).split(",")] if tags_m else []

    body_text = re.sub(r"<[^>]+>", " ", html)
    words = len(re.findall(r"\S+", body_text))
    minutes = max(1, round(words / 180))
    read_time = f"{minutes} دقائق قراءة" if minutes != 1 else "دقيقة قراءة"

    return {
        "id":        file_date.strftime("%Y-%m-%d"),
        "slug":      file_date.strftime("%Y-%m-%d"),
        "title":     title,
        "excerpt":   excerpt[:220],
        "image":     pick_image(tags),
        "author":    AUTHOR_NAME,
        "authorTitle": AUTHOR_TITLE,
        "date":      file_date.replace(tzinfo=timezone.utc).isoformat(),
        "dateStr":   ar_date(file_date),
        "readTime":  read_time,
        "views":     0,
        "tags":      tags,
        "aiGenerated": True,
        "url":       f"blog/{fname}",
    }

def main():
    if not os.path.isdir(BLOG_DIR):
        print(f"::error::Blog dir not found: {BLOG_DIR}", file=sys.stderr)
        sys.exit(1)

    # Parse all dated files — newest first
    raw = []
    for fname in sorted(os.listdir(BLOG_DIR), reverse=True):
        m = DATE_RE.match(fname)
        if not m:
            continue
        file_date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        path = os.path.join(BLOG_DIR, fname)
        with open(path, encoding="utf-8", errors="ignore") as f:
            html = f.read()
        raw.append(extract(html, fname, file_date))

    # ── DEDUPLICATION: keep only the LATEST file for each unique title ──
    seen_titles = set()
    entries = []
    for a in raw:                   # already sorted newest→oldest
        if a["title"] not in seen_titles:
            seen_titles.add(a["title"])
            entries.append(a)
        else:
            print(f"[dedup] skipped older duplicate: {a['url']} — '{a['title'][:50]}'")

    manifest = {
        "_readme": "Auto-built by scripts/build_blog_manifest.py — do not edit manually.",
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "articles": entries,
    }

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Manifest built: {len(entries)} unique articles (deduplicated from {len(raw)} files)")

if __name__ == "__main__":
    main()
