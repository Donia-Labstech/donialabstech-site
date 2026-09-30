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
  DEEPSEEK_API_KEY — set as GitHub secret

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
        "كيف تستثمر المحتوى المرئي لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر الفيديوهات القصيرة لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر التصميم البصري للمنشورات لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر الرسائل الإخبارية (Newsletter) لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر التعليقات والتفاعل لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر المسابقات الرقمية لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر الشراكات مع المؤثرين المحليين لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر البث المباشر لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر الاستطلاعات التفاعلية لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر المحتوى التعليمي المجاني لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر قصص العملاء (Case Studies) لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر الرسائل الصوتية لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر مجموعات فيسبوك النشطة لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر قنوات تيليغرام لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر حسابات إنستغرام التجارية لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر تحسين محركات البحث المحلي لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر الكلمات المفتاحية العربية لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر تحليل المنافسين لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر جدولة المحتوى الأسبوعي لزيادة مبيعاتك دون ميزانية كبيرة",
        "كيف تستثمر إعادة توظيف المحتوى القديم لزيادة مبيعاتك دون ميزانية كبيرة",
        "دليلك العملي لبناء استراتيجية المحتوى المرئي من الصفر",
        "دليلك العملي لبناء استراتيجية الفيديوهات القصيرة من الصفر",
        "دليلك العملي لبناء استراتيجية التصميم البصري للمنشورات من الصفر",
        "دليلك العملي لبناء استراتيجية الرسائل الإخبارية (Newsletter) من الصفر",
        "دليلك العملي لبناء استراتيجية التعليقات والتفاعل من الصفر",
        "دليلك العملي لبناء استراتيجية المسابقات الرقمية من الصفر",
        "دليلك العملي لبناء استراتيجية الشراكات مع المؤثرين المحليين من الصفر",
        "دليلك العملي لبناء استراتيجية البث المباشر من الصفر",
        "دليلك العملي لبناء استراتيجية الاستطلاعات التفاعلية من الصفر",
        "دليلك العملي لبناء استراتيجية المحتوى التعليمي المجاني من الصفر",
        "دليلك العملي لبناء استراتيجية قصص العملاء (Case Studies) من الصفر",
        "دليلك العملي لبناء استراتيجية الرسائل الصوتية من الصفر",
        "دليلك العملي لبناء استراتيجية مجموعات فيسبوك النشطة من الصفر",
        "دليلك العملي لبناء استراتيجية قنوات تيليغرام من الصفر",
        "دليلك العملي لبناء استراتيجية حسابات إنستغرام التجارية من الصفر",
        "دليلك العملي لبناء استراتيجية تحسين محركات البحث المحلي من الصفر",
        "دليلك العملي لبناء استراتيجية الكلمات المفتاحية العربية من الصفر",
        "دليلك العملي لبناء استراتيجية تحليل المنافسين من الصفر",
        "دليلك العملي لبناء استراتيجية جدولة المحتوى الأسبوعي من الصفر",
        "دليلك العملي لبناء استراتيجية إعادة توظيف المحتوى القديم من الصفر",
        "خمس خطوات لتحويل المحتوى المرئي إلى مصدر عملاء دائم",
        "خمس خطوات لتحويل الفيديوهات القصيرة إلى مصدر عملاء دائم",
        "خمس خطوات لتحويل التصميم البصري للمنشورات إلى مصدر عملاء دائم",
        "خمس خطوات لتحويل الرسائل الإخبارية (Newsletter) إلى مصدر عملاء دائم",
        "خمس خطوات لتحويل التعليقات والتفاعل إلى مصدر عملاء دائم",
        "خمس خطوات لتحويل المسابقات الرقمية إلى مصدر عملاء دائم",
        "خمس خطوات لتحويل الشراكات مع المؤثرين المحليين إلى مصدر عملاء دائم",
        "خمس خطوات لتحويل البث المباشر إلى مصدر عملاء دائم",
        "خمس خطوات لتحويل الاستطلاعات التفاعلية إلى مصدر عملاء دائم",
        "خمس خطوات لتحويل المحتوى التعليمي المجاني إلى مصدر عملاء دائم",
    ],
    # Area B — Platform Building & Technology (days: Tue, Fri)
    "tech": [
        "لماذا تحتاج منصتك إلى قواعد البيانات السحابية قبل التوسع",
        "لماذا تحتاج منصتك إلى واجهات برمجة التطبيقات (API) قبل التوسع",
        "لماذا تحتاج منصتك إلى التصميم المتجاوب قبل التوسع",
        "لماذا تحتاج منصتك إلى تحسين سرعة التحميل قبل التوسع",
        "لماذا تحتاج منصتك إلى الاستضافة السحابية قبل التوسع",
        "لماذا تحتاج منصتك إلى النسخ الاحتياطي التلقائي قبل التوسع",
        "لماذا تحتاج منصتك إلى المصادقة الثنائية قبل التوسع",
        "لماذا تحتاج منصتك إلى أنظمة إدارة المحتوى قبل التوسع",
        "لماذا تحتاج منصتك إلى تطبيقات الويب التقدمية (PWA) قبل التوسع",
        "لماذا تحتاج منصتك إلى أتمتة العمليات الداخلية قبل التوسع",
        "لماذا تحتاج منصتك إلى لوحات التحكم الذكية قبل التوسع",
        "لماذا تحتاج منصتك إلى تكامل أنظمة الدفع الإلكتروني قبل التوسع",
        "لماذا تحتاج منصتك إلى بنية المنصات متعددة اللغات قبل التوسع",
        "لماذا تحتاج منصتك إلى اختبار الأداء قبل الإطلاق قبل التوسع",
        "لماذا تحتاج منصتك إلى الترحيل الآمن بين الخوادم قبل التوسع",
        "لماذا تحتاج منصتك إلى بروتوكولات التشفير قبل التوسع",
        "لماذا تحتاج منصتك إلى أنظمة التنبيهات الذكية قبل التوسع",
        "لماذا تحتاج منصتك إلى توثيق الكود للفرق التقنية قبل التوسع",
        "لماذا تحتاج منصتك إلى التكامل مع أدوات الذكاء الاصطناعي قبل التوسع",
        "لماذا تحتاج منصتك إلى بنية الميكروسيرفيس المبسطة قبل التوسع",
        "دليل مبسط لفهم قواعد البيانات السحابية حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم واجهات برمجة التطبيقات (API) حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم التصميم المتجاوب حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم تحسين سرعة التحميل حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم الاستضافة السحابية حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم النسخ الاحتياطي التلقائي حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم المصادقة الثنائية حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم أنظمة إدارة المحتوى حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم تطبيقات الويب التقدمية (PWA) حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم أتمتة العمليات الداخلية حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم لوحات التحكم الذكية حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم تكامل أنظمة الدفع الإلكتروني حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم بنية المنصات متعددة اللغات حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم اختبار الأداء قبل الإطلاق حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم الترحيل الآمن بين الخوادم حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم بروتوكولات التشفير حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم أنظمة التنبيهات الذكية حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم توثيق الكود للفرق التقنية حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم التكامل مع أدوات الذكاء الاصطناعي حتى لو لم تكن مبرمجاً",
        "دليل مبسط لفهم بنية الميكروسيرفيس المبسطة حتى لو لم تكن مبرمجاً",
        "كيف يؤثر قواعد البيانات السحابية على تجربة عملائك مباشرة",
        "كيف يؤثر واجهات برمجة التطبيقات (API) على تجربة عملائك مباشرة",
        "كيف يؤثر التصميم المتجاوب على تجربة عملائك مباشرة",
        "كيف يؤثر تحسين سرعة التحميل على تجربة عملائك مباشرة",
        "كيف يؤثر الاستضافة السحابية على تجربة عملائك مباشرة",
        "كيف يؤثر النسخ الاحتياطي التلقائي على تجربة عملائك مباشرة",
        "كيف يؤثر المصادقة الثنائية على تجربة عملائك مباشرة",
        "كيف يؤثر أنظمة إدارة المحتوى على تجربة عملائك مباشرة",
        "كيف يؤثر تطبيقات الويب التقدمية (PWA) على تجربة عملائك مباشرة",
        "كيف يؤثر أتمتة العمليات الداخلية على تجربة عملائك مباشرة",
    ],
    # Area C — Entrepreneurship & AI Business (days: Wed, Sat)
    "entrepreneurship": [
        "كيف تبني دراسة جدوى مصغرة تناسب واقع السوق الجزائري",
        "كيف تبني نموذج العمل التجاري (Business Model) تناسب واقع السوق الجزائري",
        "كيف تبني التمويل الذاتي تناسب واقع السوق الجزائري",
        "كيف تبني الشراكات الاستراتيجية تناسب واقع السوق الجزائري",
        "كيف تبني إدارة التدفق النقدي تناسب واقع السوق الجزائري",
        "كيف تبني توسيع فريق العمل عن بعد تناسب واقع السوق الجزائري",
        "كيف تبني بناء علامة تجارية موثوقة تناسب واقع السوق الجزائري",
        "كيف تبني التفاوض مع الموردين تناسب واقع السوق الجزائري",
        "كيف تبني تقييم فرص السوق الجزائري تناسب واقع السوق الجزائري",
        "كيف تبني إدارة الوقت كمؤسس منفرد تناسب واقع السوق الجزائري",
        "كيف تبني قرارات التسعير الصعبة تناسب واقع السوق الجزائري",
        "كيف تبني التعامل مع أول فشل مشروع تناسب واقع السوق الجزائري",
        "كيف تبني بناء عرض قيمة واضح تناسب واقع السوق الجزائري",
        "كيف تبني استراتيجية الخروج (Exit Strategy) تناسب واقع السوق الجزائري",
        "كيف تبني التحول من فريلانسر إلى شركة تناسب واقع السوق الجزائري",
        "كيف تبني إدارة العملاء الصعبين باحترافية تناسب واقع السوق الجزائري",
        "كيف تبني بناء فريق مبيعات صغير وفعّال تناسب واقع السوق الجزائري",
        "كيف تبني استخدام الذكاء الاصطناعي في اتخاذ القرار تناسب واقع السوق الجزائري",
        "كيف تبني أتمتة خدمة العملاء بالذكاء الاصطناعي تناسب واقع السوق الجزائري",
        "كيف تبني قياس العائد على الاستثمار في المشاريع الرقمية تناسب واقع السوق الجزائري",
        "أهم الدروس المستفادة حول دراسة جدوى مصغرة من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول نموذج العمل التجاري (Business Model) من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول التمويل الذاتي من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول الشراكات الاستراتيجية من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول إدارة التدفق النقدي من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول توسيع فريق العمل عن بعد من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول بناء علامة تجارية موثوقة من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول التفاوض مع الموردين من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول تقييم فرص السوق الجزائري من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول إدارة الوقت كمؤسس منفرد من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول قرارات التسعير الصعبة من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول التعامل مع أول فشل مشروع من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول بناء عرض قيمة واضح من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول استراتيجية الخروج (Exit Strategy) من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول التحول من فريلانسر إلى شركة من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول إدارة العملاء الصعبين باحترافية من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول بناء فريق مبيعات صغير وفعّال من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول استخدام الذكاء الاصطناعي في اتخاذ القرار من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول أتمتة خدمة العملاء بالذكاء الاصطناعي من تجارب رواد أعمال حقيقيين",
        "أهم الدروس المستفادة حول قياس العائد على الاستثمار في المشاريع الرقمية من تجارب رواد أعمال حقيقيين",
        "متى يجب أن تفكر جدياً في دراسة جدوى مصغرة",
        "متى يجب أن تفكر جدياً في نموذج العمل التجاري (Business Model)",
        "متى يجب أن تفكر جدياً في التمويل الذاتي",
        "متى يجب أن تفكر جدياً في الشراكات الاستراتيجية",
        "متى يجب أن تفكر جدياً في إدارة التدفق النقدي",
        "متى يجب أن تفكر جدياً في توسيع فريق العمل عن بعد",
        "متى يجب أن تفكر جدياً في بناء علامة تجارية موثوقة",
        "متى يجب أن تفكر جدياً في التفاوض مع الموردين",
        "متى يجب أن تفكر جدياً في تقييم فرص السوق الجزائري",
        "متى يجب أن تفكر جدياً في إدارة الوقت كمؤسس منفرد",
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

    forced_area  = os.environ.get("FORCED_AREA") or area
    forced_topic = os.environ.get("FORCED_TOPIC")
    if forced_topic:
        return forced_area, forced_topic

    pool       = TOPIC_ROTATION[forced_area]
    candidates = [t for t in pool if t not in existing_titles]
    if not candidates:
        candidates = pool  # All used — restart cycle
    import random; random.shuffle(candidates)
    return forced_area, candidates[0]

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

def call_deepseek(prompt):
    body = json.dumps({
        "model": "deepseek-chat",
        "max_tokens": 2500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"].strip()},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

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
        "tags":     [t.strip() for t in re.split(r"[,،]", km.group(1)) if t.strip()] if km else [],
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
        raw = call_deepseek(build_prompt(topic, area, date_str))
    except urllib.error.HTTPError as e:
        print(f"::error::DeepSeek API {e.code}: {e.read().decode('utf-8','ignore')}", file=sys.stderr)
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
