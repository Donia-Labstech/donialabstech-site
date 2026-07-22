#!/usr/bin/env python3
"""
build_sitemap.py
-----------------
Generates sitemap.xml from blog/index.json + fixed site pages.
Run by the same GitHub Action (build-blog-manifest.yml).
"""
import json, os
from datetime import datetime, timezone

REPO_ROOT   = os.path.join(os.path.dirname(__file__), "..")
MANIFEST    = os.path.join(REPO_ROOT, "blog", "index.json")
SITEMAP     = os.path.join(REPO_ROOT, "sitemap.xml")
SITE_URL    = "https://donialabstech.online"

# Static pages with priority and change frequency
STATIC_PAGES = [
    ("",                     "1.0",  "weekly"),
    ("privacy-policy.html",  "0.4",  "yearly"),
    ("terms-of-service.html","0.4",  "yearly"),
]

def fmt_date(iso):
    return iso[:10]

def main():
    with open(MANIFEST, encoding="utf-8") as f:
        data = json.load(f)
    articles = data.get("articles", [])
    now      = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    urls = []

    # Static pages
    for path, priority, freq in STATIC_PAGES:
        loc = f"{SITE_URL}/{path}".rstrip("/")
        urls.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{now}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{priority}</priority>
  </url>""")

    # Blog articles
    for a in articles:
        loc     = f"{SITE_URL}/{a['url']}"
        lastmod = fmt_date(a.get("date", now))
        urls.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.75</priority>
    <news:news xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
      <news:publication>
        <news:name>DONIA LABS TECH</news:name>
        <news:language>ar</news:language>
      </news:publication>
      <news:publication_date>{lastmod}</news:publication_date>
      <news:title>{a['title'].replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')}</news:title>
    </news:news>
  </url>""")

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset
  xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
{chr(10).join(urls)}
</urlset>
"""
    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"sitemap.xml: {len(articles)} articles + {len(STATIC_PAGES)} static pages")

if __name__ == "__main__":
    main()
