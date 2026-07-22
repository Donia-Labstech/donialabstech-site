#!/usr/bin/env python3
"""
generate_daily_article.py v2 — Diverse topics, premium quality
----------------------------------------------------------------
3 topic areas rotate in a planned schedule so content stays diverse
and consistent with the brand identity of DONIA LABS TECH:
  Week A: Digital Marketing & Community
  Week B: Platform Building & Technology
  Week C: Entrepreneurship & AI Business

Required env var:
  ANTHROPIC_API_KEY — set as GitHub secret

Run by: .github/workflows/generate-article.yml
"""
import json, os, re, sys, urllib.request, urllib.error
from datetime import datetime, timezone

REPO_ROOT      = os.path.join(os.path.dirname(__file__), "..")
BLOG_DIR       = os.path.join(REPO_ROOT, "blog")
SITE_URL       = "https://donialabstech.online"
AUTHOR_NAME    = "Daoud Touina"
AUTHOR_TITLE   = "رائد أعمال | مؤسس مختبر الأفكار الذكية وقائد المشاريع"
MAX_ARTICLES   = 60

# ─── 3 rotating areas, 6 topics each = 18 total, cycling weekly ───────────────
TOPIC_ROTATION = {
    # Area A — Digital Marketing & Community (days: Mon, Thu)
    "marketing": [
        "كيف تبني جمهوراً حقيقياً على منصات التواصل بدون إعلانات مدفوعة",
        "المحتوى العربي وفرص النمو العضوي في 2026",
        "قياس فعالية حملاتك الرقمية: الأرقام التي تهم فعلاً",
        "استراتيجية المجتمع: كيف تحول متابعيك إلى عملاء وفيّين",
        "أتمتة التسويق: أدوات تغنيك عن موظف كامل",
        "قصة العميل كأداة تسويقية لا تُقاوَم",
    ],
    # Area B — Platform Building & Technology (days: Tue, Fri)
    "tech": [
        "كيف تختار التقنية المناسبة لبناء منتجك الرقمي",
        "تجربة المستخدم: الفرق بين منصة تُقنع ومنصة تُنفّر",
        "الأمن السيبراني الأساسي لكل موقع ومنصة رقمية",
        "سرعة الموقع وتأثيرها المباشر على إيراداتك",
        "بناء منصة SaaS: من الفكرة إلى أول مشترك",
        "الذكاء الاصطناعي في تطوير المنتجات: كيف نستخدمه في DONIA LABS",
    ],
    # Area C — Entrepreneurship & AI Business (days: Wed, Sat)
    "entrepreneurship": [
        "كيف تبدأ مشروعاً رقمياً ناجحاً بدون مكتب أو رأس مال ضخم",
        "خمسة أخطاء تقنية يرتكبها رواد الأعمال الرقميون",
        "التسعير الذكي للخدمات الرقمية: نماذج واستراتيجيات",
        "كيف تجد أول 10 عملاء لمشروعك الرقمي",
        "وكلاء الذكاء الاصطناعي في الأعمال: ما يمكنهم فعله اليوم",
        "بناء شبكة علاقات مهنية حقيقية في العصر الرقمي",
    ],
}

AR_MONTHS = {1:"جانفي",2:"فيفري",3:"مارس",4:"أفريل",5:"ماي",6:"جوان",
             7:"جويلية",8:"أوت",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"}
AR_DAYS   = ["الإثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]

IMAGE_POOL = {
    "marketing":       "https://images.unsplash.com/photo-1552664730-d307ca884978?w=1200&q=80",
    "tech":            "https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=1200&q=80",
    "entrepreneurship":"https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=1200&q=80",
}

def ar_date(dt):
    return f"{AR_DAYS[dt.weekday()]}، {dt.day} {AR_MONTHS[dt.month]} {dt.year}"

def pick_area_and_topic(existing_titles, now):
    """Pick topic area based on weekday, then rotate through unused topics."""
    weekday = now.weekday()  # 0=Mon
    if weekday in (0, 3):   area = "marketing"
    elif weekday in (1, 4): area = "tech"
    else:                   area = "entrepreneurship"

    forced = os.environ.get("FORCED_TOPIC")
    forced_area = os.environ.get("FORCED_AREA", area)
    if forced:
        return forced_area, forced

    pool       = TOPIC_ROTATION[area]
    candidates = [t for t in pool if t not in existing_titles]
    if not candidates:
        candidates = pool  # All used — restart cycle
    import random; random.shuffle(candidates)
    return area, candidates[0]

def build_prompt(topic, area, date_str):
    area_context = {
        "marketing":       "التسويق الرقمي وبناء المجتمعات",
        "tech":            "بناء المنصات والتكنولوجيا",
        "entrepreneurship":"ريادة الأعمال الرقمية والذكاء الاصطناعي",
    }[area]

    return f"""أنت كاتب متخصص في {area_context} لمختبر DONIA LABS TECH الرقمي.
اكتب مقالاً احترافياً عملياً حول: "{topic}"
تاريخ اليوم: {date_str}

القواعد الإلزامية:
- أسلوب مباشر وعملي كأنك تتحدث لرائد أعمال يبحث عن حلول
- لا تبدأ بـ "في عصر..." أو "في عالمنا اليوم..."
- مثال عملي أو رقم أو حالة واقعية في كل قسم
- اذكر DONIA LABS TECH بشكل طبيعي مرة أو مرتين فقط
- الخاتمة: دعوة للتواصل عبر https://wa.me/213674661737

أعد الإجابة بهذا الشكل فقط (بدون أي نص إضافي):

عنوان: <عنوان جذاب ومباشر>
ملخص: <جملتان تُغريان بالقراءة>
وسوم: <3 وسوم مفصولة بفاصلة>
---
<محتوى Markdown: يبدأ بـ ## (لا #)، 4 أقسام، 600-800 كلمة>"""

def call_claude(prompt):
    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 2500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"Content-Type": "application/json",
                 "x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())["content"][0]["text"]

def parse(text, fallback_topic):
    sep = re.search(r"^---$", text, re.MULTILINE)
    if not sep:
        return {"title": fallback_topic, "excerpt": "", "tags": [], "markdown": text.strip()}
    header, body = text[:sep.start()], text[sep.end():].strip()
    tm = re.search(r"^عنوان:\s*(.+)$", header, re.M)
    em = re.search(r"^ملخص:\s*(.+)$",  header, re.M)
    km = re.search(r"^وسوم:\s*(.+)$",  header, re.M)
    return {
        "title":    tm.group(1).strip() if tm else fallback_topic,
        "excerpt":  em.group(1).strip() if em else "",
        "tags":     [t.strip() for t in km.group(1).split(",")] if km else [],
        "markdown": body,
    }

def md_to_html(md):
    h = md
    h = re.sub(r"^### (.+)$", r"<h4>\1</h4>",  h, flags=re.M)
    h = re.sub(r"^## (.+)$",  r"<h3>\1</h3>",  h, flags=re.M)
    h = re.sub(r"^# (.+)$",   r"<h2>\1</h2>",  h, flags=re.M)
    h = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", h)
    h = re.sub(r"\*(.+?)\*",     r"<em>\1</em>", h)
    h = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', h)
    h = re.sub(r"^\d+\.\s+(.+)$", r'<li data-ol="1">\1</li>', h, flags=re.M)
    h = re.sub(r"^-\s+(.+)$",     r'<li data-ol="0">\1</li>', h, flags=re.M)
    h = re.sub(r"^---$", r"<hr>", h, flags=re.M)
    lines, out, tag, para = h.split("\n"), [], None, []
    li_re = re.compile(r'^<li data-ol="(\d)">')
    def fp():
        if para:
            t = " ".join(para).strip()
            if t: out.append(f"<p>{t}</p>")
            para.clear()
    def cl():
        nonlocal tag
        if tag: out.append(f"</{tag}>"); tag = None
    for ln in lines:
        s = ln.strip()
        m = li_re.match(s)
        if m:
            fp(); want = "ol" if m.group(1)=="1" else "ul"
            if tag != want: cl(); out.append(f"<{want}>"); tag = want
            out.append(re.sub(r' data-ol="\d"', "", s))
        else:
            cl()
            if s.startswith("<h") or s.startswith("<hr"): fp(); out.append(s)
            elif s == "": fp()
            else: para.append(s)
    cl(); fp()
    return "\n".join(out)

def build_html_page(p, area, now, image):
    canonical = f"{SITE_URL}/blog/{now.strftime('%Y-%m-%d')}.html"
    esc = lambda s: str(s).replace('"','&quot;').replace('<','&lt;').replace('>','&gt;')
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p["title"], "description": p["excerpt"],
        "image": image, "datePublished": now.replace(tzinfo=timezone.utc).isoformat(),
        "author": {"@type":"Person","name":AUTHOR_NAME,"jobTitle":AUTHOR_TITLE,"url":SITE_URL},
        "publisher": {"@type":"Organization","name":"DONIA LABS TECH",
                      "logo":{"@type":"ImageObject","url":f"{SITE_URL}/images/daoud-touina.jpg"}},
        "mainEntityOfPage": {"@type":"WebPage","@id":canonical},
        "url": canonical, "keywords": ", ".join(p["tags"]), "inLanguage": "ar",
    }, ensure_ascii=False, indent=2)
    body_html = md_to_html(p["markdown"])
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{esc(p['title'])} | DONIA LABS TECH</title>
<meta name="description" content="{esc(p['excerpt'][:160])}">
<meta name="author" content="{AUTHOR_NAME}">
<meta property="og:type"        content="article">
<meta property="og:title"       content="{esc(p['title'])}">
<meta property="og:description" content="{esc(p['excerpt'][:160])}">
<meta property="og:image"       content="{image}">
<meta property="og:url"         content="{canonical}">
<meta property="og:site_name"   content="DONIA LABS TECH">
<meta name="twitter:card"       content="summary_large_image">
<meta name="twitter:title"      content="{esc(p['title'])}">
<meta name="twitter:description" content="{esc(p['excerpt'][:160])}">
<meta name="twitter:image"      content="{image}">
<link rel="canonical" href="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;800&display=swap" rel="stylesheet">
<script type="application/ld+json">
{jsonld}
</script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Tajawal',sans-serif;background:#f8fafc;color:#1e293b;line-height:1.85;direction:rtl}}
header{{background:linear-gradient(135deg,#0f172a,#1a0a3a);padding:40px 20px 30px;text-align:center}}
header a{{color:#c4b5fd;font-size:.85rem;text-decoration:none;display:inline-flex;align-items:center;gap:6px;margin-bottom:18px}}
header h1{{color:#fff;font-size:clamp(1.5rem,4vw,2.1rem);font-weight:800;line-height:1.25;margin-bottom:12px}}
.meta{{color:#94a3b8;font-size:.82rem;display:flex;flex-wrap:wrap;gap:12px;justify-content:center}}
.hero-img{{width:100%;max-height:380px;object-fit:cover;display:block}}
.container{{max-width:760px;margin:0 auto;padding:36px 20px 60px}}
h2{{font-size:1.5rem;color:#7c3aed;margin:2rem 0 .8rem;font-weight:800}}
h3{{font-size:1.2rem;color:#06b6d4;margin:1.5rem 0 .6rem;font-weight:700}}
h4{{font-size:1.05rem;color:#1e293b;margin:1.2rem 0 .5rem;font-weight:700}}
p{{margin-bottom:1rem}}
ul,ol{{padding-right:1.2rem;margin-bottom:1rem}}
li{{padding:3px 0}}
strong{{color:#0f172a}}
a{{color:#7c3aed;text-decoration:none;border-bottom:1px dashed #7c3aed}}
hr{{border:none;border-top:2px solid #e2e8f0;margin:2rem 0}}
.tags{{display:flex;flex-wrap:wrap;gap:8px;margin:2rem 0 0}}
.tag{{background:#ede9fe;color:#7c3aed;padding:4px 14px;border-radius:20px;font-size:.8rem;font-weight:700}}
footer{{text-align:center;padding:24px;font-size:.8rem;color:#64748b;border-top:1px solid #e2e8f0}}
</style>
</head>
<body>
<header>
  <a href="{SITE_URL}">← العودة إلى DONIA LABS TECH</a>
  <h1>{esc(p['title'])}</h1>
  <div class="meta">
    <span>✍ {AUTHOR_NAME}</span>
    <span>📅 {now.strftime('%Y-%m-%d')}</span>
    <span>⏱ {max(1,round(len(p['markdown'].split())//180))} دقائق</span>
  </div>
</header>
<img src="{image}" alt="{esc(p['title'])}" class="hero-img">
<div class="container">
{body_html}
<div class="tags">{''.join(f'<span class="tag">{esc(t)}</span>' for t in p["tags"])}</div>
</div>
<footer>© 2026 DONIA LABS TECH — <a href="{SITE_URL}">donialabstech.online</a></footer>
</body>
</html>"""

def main():
    now = datetime.now(timezone.utc)
    date_str = f"{AR_DAYS[now.weekday()]}، {now.day} {AR_MONTHS[now.month]} {now.year}"

    # Load existing titles for dedup check
    manifest_path = os.path.join(BLOG_DIR, "index.json")
    existing_titles = set()
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            existing_titles = {a.get("title","") for a in json.load(f).get("articles",[])}

    area, topic = pick_area_and_topic(existing_titles, now)

    # Guard against overwriting an already-published article for today when
    # the workflow is re-run manually the same day (e.g. for testing).
    fname = now.strftime("%Y-%m-%d") + ".html"
    path  = os.path.join(BLOG_DIR, fname)
    force_overwrite = os.environ.get("FORCE_OVERWRITE", "").strip().lower() == "true"
    if os.path.exists(path) and not force_overwrite:
        print(f"::warning::Article {fname} already exists — skipping to avoid overwriting "
              f"today's published article. Set force_overwrite=true to replace it intentionally.")
        gho = os.environ.get("GITHUB_OUTPUT")
        if gho:
            with open(gho, "a", encoding="utf-8") as f:
                f.write("skipped=true\n")
        return

    try:
        raw = call_claude(build_prompt(topic, area, date_str))
    except urllib.error.HTTPError as e:
        print(f"::error::Claude API {e.code}: {e.read().decode('utf-8','ignore')}", file=sys.stderr)
        sys.exit(1)

    p     = parse(raw, topic)
    image = IMAGE_POOL[area]
    html  = build_html_page(p, area, now, image)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Published: {fname} | Area: {area} | Title: {p['title']}")

    # Expose for GitHub Actions commit message
    gho = os.environ.get("GITHUB_OUTPUT")
    if gho:
        with open(gho, "a", encoding="utf-8") as f:
            f.write(f"article_title={p['title']}\n")
            f.write(f"article_area={area}\n")

if __name__ == "__main__":
    main()
