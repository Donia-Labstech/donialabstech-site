#!/usr/bin/env python3
"""
build_blog_manifest.py (SEO-enhanced version)
----------------------------------------------
Scans blog/*.html, deduplicates by title, and builds blog/index.json.
Each article in the manifest includes a full SEO block for Open Graph,
Twitter Card, JSON-LD, and canonical URL — injected into the HTML page
via enhance_article_seo().
"""
import json, os, re, sys, shutil
from datetime import datetime, timezone

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
BLOG_DIR  = os.path.join(REPO_ROOT, "blog")
MANIFEST  = os.path.join(BLOG_DIR, "index.json")
SITE_URL  = "https://donialabstech.online"

AUTHOR_NAME  = "Daoud Touina"
AUTHOR_TITLE = "رائد أعمال | مؤسس مختبر الأفكار الذكية وقائد المشاريع"
SITE_NAME    = "DONIA LABS TECH — مختبر الأفكار الذكية"

DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})\.html$")
AR_MONTHS = {1:"جانفي",2:"فيفري",3:"مارس",4:"أفريل",5:"ماي",6:"جوان",
             7:"جويلية",8:"أوت",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"}
AR_DAYS   = ["الإثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]

IMAGE_POOL = {
    "default":      "https://images.unsplash.com/photo-1518770660439-4636190af475?w=1200&q=80",
    "تعليم":        "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=1200&q=80",
    "ذكاء اصطناعي": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1200&q=80",
    "تسويق":        "https://images.unsplash.com/photo-1552664730-d307ca884978?w=1200&q=80",
    "ريادة":        "https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=1200&q=80",
    "منصة":         "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=1200&q=80",
    "أمن":          "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=1200&q=80",
    "أعمال":        "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=1200&q=80",
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
    title_m   = re.search(r"<title>(.*?)</title>", html)
    title     = re.sub(r"\s*\|?\s*DONIA LABS TECH\s*$", "", title_m.group(1)).strip() if title_m else fname

    desc_m    = re.search(r'<meta\s+name="description"\s+content="(.*?)"', html)
    raw_desc  = desc_m.group(1).strip() if desc_m else title
    excerpt   = re.sub(r"\s*-\s*مقال من مدونة DONIA LABS TECH\s*$", "", raw_desc).strip()

    # Better excerpt from body if meta desc is generic
    if excerpt == title or len(excerpt) < 30:
        body_m = re.search(r"<body>(.*?)</body>", html, re.DOTALL)
        if body_m:
            clean   = re.sub(r"<[^>]+>", " ", body_m.group(1))
            clean   = re.sub(r"\s+", " ", clean).strip()
            excerpt = clean[150:380].strip() or title

    tags_m = re.search(r"الوسوم[:：]\s*</?\w*>?\s*([^\n<]+)", html)
    tags   = [t.strip() for t in tags_m.group(1).split(",")] if tags_m else []

    body_text = re.sub(r"<[^>]+>", " ", html)
    words     = len(re.findall(r"\S+", body_text))
    minutes   = max(1, round(words / 180))
    read_time = f"{minutes} دقائق قراءة"

    image = pick_image(tags)
    url   = f"blog/{fname}"

    return {
        "id":          file_date.strftime("%Y-%m-%d"),
        "slug":        file_date.strftime("%Y-%m-%d"),
        "title":       title,
        "excerpt":     excerpt[:240],
        "image":       image,
        "author":      AUTHOR_NAME,
        "authorTitle": AUTHOR_TITLE,
        "date":        file_date.replace(tzinfo=timezone.utc).isoformat(),
        "dateStr":     ar_date(file_date),
        "readTime":    read_time,
        "views":       0,
        "tags":        tags,
        "aiGenerated": True,
        "url":         url,
    }

def seo_head_block(a):
    """Returns the <head> SEO block to inject into the blog HTML page."""
    canonical = f"{SITE_URL}/{a['url']}"
    esc = lambda s: s.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline":       a["title"],
        "description":    a["excerpt"],
        "image":          a["image"],
        "datePublished":  a["date"],
        "dateModified":   a["date"],
        "author": {
            "@type": "Person",
            "name":  AUTHOR_NAME,
            "jobTitle": AUTHOR_TITLE,
            "url":   SITE_URL,
        },
        "publisher": {
            "@type": "Organization",
            "name":  "DONIA LABS TECH",
            "logo":  {"@type": "ImageObject", "url": f"{SITE_URL}/images/daoud-touina.jpg"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        "url":       canonical,
        "keywords":  ", ".join(a["tags"]),
        "inLanguage": "ar",
    }
    return f"""  <!-- SEO: Open Graph & Twitter Card -->
  <meta property="og:type"        content="article">
  <meta property="og:title"       content="{esc(a['title'])}">
  <meta property="og:description" content="{esc(a['excerpt'][:160])}">
  <meta property="og:image"       content="{a['image']}">
  <meta property="og:url"         content="{canonical}">
  <meta property="og:site_name"   content="{SITE_NAME}">
  <meta property="article:author" content="{AUTHOR_NAME}">
  <meta property="article:published_time" content="{a['date']}">
  <meta name="twitter:card"        content="summary_large_image">
  <meta name="twitter:title"       content="{esc(a['title'])}">
  <meta name="twitter:description" content="{esc(a['excerpt'][:160])}">
  <meta name="twitter:image"       content="{a['image']}">
  <link rel="canonical" href="{canonical}">
  <!-- SEO: JSON-LD Structured Data -->
  <script type="application/ld+json">
  {json.dumps(jsonld, ensure_ascii=False, indent=2)}
  </script>"""

def enhance_article_seo(filepath, a):
    """Injects SEO block into a blog HTML file if not already present."""
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        html = f.read()
    if 'og:type' in html:
        return  # Already enhanced
    block = seo_head_block(a)
    html = html.replace("</head>", block + "\n</head>", 1)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    if not os.path.isdir(BLOG_DIR):
        print(f"::error::Blog dir not found: {BLOG_DIR}", file=sys.stderr)
        sys.exit(1)

    raw = []
    for fname in sorted(os.listdir(BLOG_DIR), reverse=True):
        m = DATE_RE.match(fname)
        if not m: continue
        file_date = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        path = os.path.join(BLOG_DIR, fname)
        with open(path, encoding="utf-8", errors="ignore") as f:
            html = f.read()
        raw.append((fname, file_date, html, path))

    # Deduplication — keep newest per unique title
    seen, entries = set(), []
    for fname, file_date, html, path in raw:
        a = extract(html, fname, file_date)
        if a["title"] not in seen:
            seen.add(a["title"])
            entries.append(a)
            enhance_article_seo(path, a)   # inject SEO into the HTML file
        else:
            print(f"[dedup] skipped: {fname} — {a['title'][:50]}")

    manifest = {
        "_readme":     "Auto-built by scripts/build_blog_manifest.py",
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "articles":    entries,
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"✅ Manifest: {len(entries)} unique articles (from {len(raw)} files)")

if __name__ == "__main__":
    main()
