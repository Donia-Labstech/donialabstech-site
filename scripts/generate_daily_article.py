#!/usr/bin/env python3
"""
generate_daily_article.py
--------------------------
Generates one new blog article using the Claude API and inserts it at the
top of articles/articles.json, in the exact schema the website expects.

Run by: .github/workflows/daily-blog-post.yml (cron + manual trigger)

Required environment variable:
  ANTHROPIC_API_KEY   -- set as a GitHub Actions secret

Optional environment variable:
  FORCED_TOPIC        -- override the auto-picked topic (used for manual testing)
"""

import json
import os
import random
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

ARTICLES_PATH = os.path.join(os.path.dirname(__file__), "..", "articles", "articles.json")
MAX_ARTICLES_KEPT = 365  # keep the file from growing forever; drop the oldest beyond this

AUTHOR_NAME = "Daoud Touina"
AUTHOR_TITLE = "رائد أعمال | مؤسس مختبر الأفكار الذكية وقائد المشاريع"

# Rotating topic pool. Add as many as you like — the script avoids repeating
# any topic that matches a recent article title too closely.
TOPIC_POOL = [
    # ── الذكاء الاصطناعي والتكنولوجيا ──
    "كيف يغير الذكاء الاصطناعي التوظيف في المؤسسات العربية",
    "وكلاء الذكاء الاصطناعي: الجيل القادم من الأتمتة",
    "الفرق بين ChatGPT وأنظمة الذكاء الاصطناعي المتخصصة للأعمال",
    "كيف تختار نموذج الذكاء الاصطناعي المناسب لمشروعك",
    "الذكاء الاصطناعي التوليدي في خدمة المحتوى العربي",
    "مستقبل العمل عن بُعد مع أدوات الذكاء الاصطناعي",
    "أمان البيانات في عصر النماذج اللغوية الكبيرة",

    # ── ريادة الأعمال الرقمية ──
    "كيف تبني شركة رقمية ناجحة بدون مكتب فيزيائي",
    "من الفكرة إلى الإطلاق: خارطة طريق المشروع الرقمي",
    "خمسة أخطاء قاتلة يرتكبها رواد الأعمال الرقميون",
    "بناء علامة تجارية موثوقة في العالم الرقمي",
    "كيف تجد أول 10 عملاء لمشروعك الرقمي",
    "التسعير الذكي للخدمات الرقمية: استراتيجيات ونماذج",
    "العمل الحر أم الشركة: أيهما يناسبك؟",

    # ── التسويق الرقمي ──
    "التسويق بالمحتوى العربي: كيف تبني جمهوراً حقيقياً",
    "دليل عملي لبناء حضور رقمي احترافي من الصفر",
    "فيسبوك أم لينكدإن: أين يجب أن تكون في 2026؟",
    "أتمتة التسويق: أدوات تغنيك عن موظف كامل",
    "كيف تقيس فعالية حملاتك التسويقية الرقمية",
    "قصة العميل كأداة تسويقية لا تقاوَم",

    # ── التعليم والتكنولوجيا ──
    "مستقبل التكنولوجيا التعليمية في العالم العربي",
    "كيف يُحوّل الذكاء الاصطناعي الفصل الدراسي",
    "أنظمة إدارة المدارس الذكية: ما الذي يجب أن تبحث عنه",
    "الفجوة الرقمية في التعليم: المشكلة والحل",

    # ── إدارة الأعمال والإنتاجية ──
    "أتمتة الأعمال: من أين تبدأ كشركة صغيرة أو متوسطة",
    "أدوات إدارة المشاريع التي تُضاعف إنتاجية فريقك",
    "كيف تبني نظام عمل لا يعتمد على شخص واحد",
    "قياس الأداء الرقمي: المؤشرات التي تهم فعلاً",
    "إدارة العملاء عن بُعد: أفضل الممارسات والأدوات",

    # ── المجتمع وبناء الشبكات ──
    "لماذا يحتاج كل رائد أعمال إلى مجتمع احترافي",
    "كيف تبني شبكة علاقات مهنية حقيقية في العصر الرقمي",
    "قوة التعاون بين رواد الأعمال الرقميين",
    "مجتمعات تيلغرام للأعمال: كيف تستفيد منها بذكاء",

    # ── الأمن والخصوصية ──
    "الأمن السيبراني الأساسي لكل موقع ومتجر إلكتروني",
    "حماية بيانات عملائك: ما يجب على كل صاحب مشروع معرفته",
    "كيف تختار شركة استضافة آمنة وموثوقة",

    # ── تطوير المواقع والمنتجات ──
    "تجربة المستخدم: الفرق بين موقع يُقنع وموقع يُنفّر",
    "متجر إلكتروني ناجح: العوامل الخمسة الأساسية",
    "تطوير تطبيقات الويب في 2026: التقنيات الأكثر طلباً",
    "لماذا سرعة موقعك تساوي دخلك مباشرةً",

    # ── مشاريع DONIA LABS TECH ──
    "DONIA SMART SCHOOL: كيف يُحوّل إدارة المدارس رقمياً",
    "INTELLI CORE: نواة ذكاء اصطناعي للشركات العربية",
    "مستقبل أنظمة إدارة الموارد البشرية بالذكاء الاصطناعي",
    "التحول الرقمي في المؤسسات التعليمية: دليل عملي",
]

IMAGE_POOL = {
    "default": "https://images.unsplash.com/photo-1518770660439-4636190af475?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "تعليم": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "ذكاء اصطناعي": "https://images.unsplash.com/photo-1677442136019-21780ecad995?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "تسويق": "https://images.unsplash.com/photo-1552664730-d307ca884978?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "تصميم": "https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?ixlib=rb-4.0.3&auto=format&fit=crop&w=1169&q=80",
    "أمن سيبراني": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
    "أعمال": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-4.0.3&auto=format&fit=crop&w=1070&q=80",
}

AR_MONTHS = {
    1: "جانفي", 2: "فيفري", 3: "مارس", 4: "أفريل", 5: "ماي", 6: "جوان",
    7: "جويلية", 8: "أوت", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر",
}
AR_WEEKDAYS = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]


def arabic_date_str(dt):
    return f"{AR_WEEKDAYS[dt.weekday()]}، {dt.day} {AR_MONTHS[dt.month]} {dt.year}"


def slugify(text):
    text = text.strip()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^\w\u0600-\u06FF\-]", "", text)
    return text[:80] or "مقال"


def pick_topic(existing_titles):
    forced = os.environ.get("FORCED_TOPIC")
    if forced:
        return forced
    candidates = [t for t in TOPIC_POOL if t not in existing_titles]
    if not candidates:
        candidates = TOPIC_POOL
    return random.choice(candidates)


def pick_image(tags):
    for t in tags:
        for key, url in IMAGE_POOL.items():
            if key != "default" and key in t:
                return url
    return IMAGE_POOL["default"]


def call_claude(prompt):
    api_key = os.environ["ANTHROPIC_API_KEY"]
    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 2200,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["content"][0]["text"]


def build_prompt(topic, date_str):
    return f"""أنت كاتب مدونة تقنية متخصص لمختبر DONIA LABS TECH الجزائري، تكتب باسم المؤسس Daoud Touina.

اكتب مقالاً يومياً احترافياً حول الموضوع التالي: "{topic}"
تاريخ اليوم: {date_str}

أعد الإجابة بهذا الشكل الدقيق فقط (بدون أي نص إضافي قبله أو بعده):

عنوان: <عنوان جذاب ومباشر — يعكس صوت خبير ورائد أعمال، وليس أكاديمياً>
ملخص: <ملخص من سطرين، يُغري القارئ بالاستمرار>
وسوم: <3 إلى 4 وسوم مفصولة بفاصلة>
---
<محتوى المقال الكامل بصيغة Markdown. القواعد الإلزامية:
- يبدأ بـ ## (عنوان فرعي) مباشرة — لا # في البداية
- 4 إلى 5 أقسام واضحة
- بين 600 و900 كلمة
- أسلوب مباشر، عملي، ومتخصص — كأنك تتحدث لرائد أعمال
- مثال عملي أو حالة واقعية في الأقسام
- DONIA LABS TECH تُذكر بشكل طبيعي كمختبر رقمي متخصص
- لا تبدأ بـ "في عصر..." أو "في عالمنا اليوم..." — ابدأ بجملة مباشرة وجريئة
- الخاتمة: دعوة للتفاعل أو التواصل عبر https://wa.me/213674661737>
"""


def parse_response(text, fallback_topic):
    header_match = re.search(r"^---$", text, re.MULTILINE)
    if not header_match:
        # Could not find the separator — treat whole thing as body, use fallback topic as title
        return {
            "title": fallback_topic,
            "excerpt": "",
            "tags": [],
            "markdown": text.strip(),
        }

    header = text[: header_match.start()]
    body = text[header_match.end():].strip()

    title_m = re.search(r"^عنوان:\s*(.+)$", header, re.MULTILINE)
    excerpt_m = re.search(r"^ملخص:\s*(.+)$", header, re.MULTILINE)
    tags_m = re.search(r"^وسوم:\s*(.+)$", header, re.MULTILINE)

    title = title_m.group(1).strip() if title_m else fallback_topic
    excerpt = excerpt_m.group(1).strip() if excerpt_m else ""
    tags = [t.strip() for t in tags_m.group(1).split(",")] if tags_m else []

    return {"title": title, "excerpt": excerpt, "tags": tags, "markdown": body}


def markdown_to_html(md):
    html = md
    html = re.sub(r"^### (.+)$", r"<h4>\1</h4>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)
    html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', html)
    html = re.sub(r"^\d+\.\s+(.+)$", r'<li data-ol="1">\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r"^-\s+(.+)$", r'<li data-ol="0">\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r"^---$", r"<hr>", html, flags=re.MULTILINE)

    # Wrap consecutive <li> lines in <ol>/<ul> (matching their original marker type),
    # and remaining paragraphs in <p>
    lines = html.split("\n")
    out, list_tag, para = [], None, []
    li_re = re.compile(r'^<li data-ol="(\d)">')

    def flush_para():
        if para:
            text = " ".join(para).strip()
            if text:
                out.append(f"<p>{text}</p>")
            para.clear()

    def close_list():
        nonlocal list_tag
        if list_tag:
            out.append(f"</{list_tag}>")
            list_tag = None

    for line in lines:
        stripped = line.strip()
        li_match = li_re.match(stripped)
        if li_match:
            flush_para()
            wanted_tag = "ol" if li_match.group(1) == "1" else "ul"
            if list_tag != wanted_tag:
                close_list()
                out.append(f"<{wanted_tag}>")
                list_tag = wanted_tag
            out.append(re.sub(r' data-ol="\d"', "", stripped))
        else:
            close_list()
            if stripped.startswith("<h") or stripped.startswith("<hr"):
                flush_para()
                out.append(stripped)
            elif stripped == "":
                flush_para()
            else:
                para.append(stripped)
    close_list()
    flush_para()

    return "\n".join(out)


def estimate_read_time(markdown_text):
    words = len(re.findall(r"\S+", markdown_text))
    minutes = max(1, round(words / 180))
    return f"{minutes} دقائق قراءة" if minutes != 1 else "دقيقة قراءة واحدة"


def main():
    with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_titles = {a.get("title", "") for a in data.get("articles", [])}
    topic = pick_topic(existing_titles)
    now = datetime.now(timezone.utc)
    date_str = arabic_date_str(now)

    prompt = build_prompt(topic, date_str)

    try:
        raw = call_claude(prompt)
    except urllib.error.HTTPError as e:
        print(f"::error::Claude API HTTP error: {e.code} {e.read().decode('utf-8', 'ignore')}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"::error::Claude API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    parsed = parse_response(raw, topic)
    html = markdown_to_html(parsed["markdown"])

    article = {
        "id": str(int(now.timestamp() * 1000)),
        "slug": slugify(parsed["title"]),
        "title": parsed["title"],
        "excerpt": parsed["excerpt"],
        "image": pick_image(parsed["tags"]),
        "author": AUTHOR_NAME,
        "authorTitle": AUTHOR_TITLE,
        "date": now.isoformat(),
        "dateStr": date_str,
        "readTime": estimate_read_time(parsed["markdown"]),
        "views": 0,
        "tags": parsed["tags"],
        "aiGenerated": True,
        "html": html,
        "markdown": parsed["markdown"],
    }

    data.setdefault("articles", []).insert(0, article)
    data["articles"] = data["articles"][:MAX_ARTICLES_KEPT]
    data["lastUpdated"] = now.isoformat()

    with open(ARTICLES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Published article: {article['title']} ({article['id']})")
    # Expose the title to the workflow step for the commit message
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"article_title={article['title']}\n")


if __name__ == "__main__":
    main()
