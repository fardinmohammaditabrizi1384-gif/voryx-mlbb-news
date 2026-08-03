import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from groq import Groq

NEWS_URL = "https://en.moonton.com/news/index.html"
BASE_URL = "https://en.moonton.com"
LAST_NEWS_FILE = "last_news.txt"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)




def get_latest_news():
    response = requests.get(NEWS_URL, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for link in soup.find_all("a", href=True):
        href = link["href"]

        if "/news/" in href and not href.endswith("index.html"):
            return urljoin(BASE_URL, href)

    return None


def get_news_content(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # -------------------------
    # عنوان
    # -------------------------

    title = soup.find("title")

    if title:
        title = title.get_text(" ", strip=True)
    else:
        title = "خبر MOONTON"


    # -------------------------
    # متن خبر
    # -------------------------

    text_parts = []

    for element in soup.find_all(["p", "h2", "h3"]):
        text = element.get_text(" ", strip=True)

        if text:
            text_parts.append(text)

    text = "\n\n".join(text_parts)


    # -------------------------
    # تصاویر
    # -------------------------

    images = []

    for img in soup.find_all("img"):
        src = img.get("src")

        if not src:
            continue

        image_url = urljoin(url, src)

        # حذف لوگوها و آیکون‌ها
        if any(x in image_url.lower() for x in [
            "logo",
            "flogo",
            "logob",
            "icon"
        ]):
            continue

        if image_url not in images:
            images.append(image_url)


    return {
        "title": title,
        "text": text,
        "images": images
    }


# ==================================================
# پیدا کردن آخرین خبر
# ==================================================

latest_news = get_latest_news()

if not latest_news:
    print("هیچ خبری پیدا نشد.")
    exit(1)

print("آخرین خبر:", latest_news)


# ==================================================
# بررسی خبر تکراری
# ==================================================

old_news = ""

if os.path.exists(LAST_NEWS_FILE):
    with open(LAST_NEWS_FILE, "r", encoding="utf-8") as file:
        old_news = file.read().strip()


if latest_news == old_news:
    print("خبر جدیدی وجود ندارد.")
    exit(0)


# ==================================================
# استخراج خبر
# ==================================================

news = get_news_content(latest_news)

title = news["title"]
text = news["text"]

image_url = news["images"][0] if news["images"] else None

# -------------------------
# Voryx AI News Generator
# -------------------------

system_prompt = f"""You are a professional Mobile Legends: Bang Bang (MLBB) news editor for a Persian Telegram gaming channel.

Your task is to read the raw news provided at the end of this prompt and convert it into a SHORT, SIMPLE, NATURAL, and CLEAN Persian Telegram post.

The final result must be ready to publish immediately.

IMPORTANT:
Do not translate word-for-word.
Understand the source, select the most important information, and rewrite it naturally in simple Persian.

The output must be SHORT.
Target length: approximately 80–130 Persian words.

────────────────────────

STRICT OUTPUT FORMAT

The output MUST contain exactly 4 content sections:

SECTION 1 — MAIN NEWS

Start with 🔥

Write ONE short headline only.

The headline must be maximum 10–12 words.

Do NOT write words such as:
موضوع
موضوع اصلی
Headline
خبر

Example:

🔥 Team Spirit تاریخ‌ساز شد و قهرمان MSC 2026 شد

Then:

BLANK LINE

────────────────────────

SECTION 2 — DETAILS

Start with 📌

Write 2 or 3 short sentences.

Explain only the most important facts:

* What happened?
* Who was involved?
* What was the result?

Do NOT use bullet points.

Do NOT write a section title such as:
جزئیات
جزئیات خبر
Details

Then:

BLANK LINE

────────────────────────

SECTION 3 — ANALYSIS

Start with 🔎

Write exactly 1 or 2 short sentences.

Explain why this news matters to Mobile Legends players.

Keep the analysis simple and practical.

Do NOT repeat the details.

Do NOT introduce unrelated information.

Do NOT write a section title such as:
تحلیل
Analysis

Then:

BLANK LINE

────────────────────────

SECTION 4 — CALL TO ACTION

This section MUST be completely separated from the analysis by ONE BLANK LINE.

Start with:

💬 نظر شما چیه؟

Then write ONE short question related to the news.

Then:

BLANK LINE

Then write exactly these three lines:

❤️ ری‌اکشن یادتون نره
💬 نظرتون رو کامنت کنید
📤 اگه این خبر براتون جالب بود، برای دوستاتون بفرستید

IMPORTANT:
The Call To Action is ALWAYS the final section.

Do not add anything after it.

────────────────────────

VERY IMPORTANT — DO NOT ADD SECTION LABELS

Never write these words as section headings:

موضوع
جزئیات
تحلیل
درخواست
دعوت به تعامل
نظر شما
Details
Analysis
Headline
Call to Action

The emojis themselves are the section markers.

────────────────────────

RTL / PERSIAN TEXT SAFETY

The output will be displayed in a Persian RTL Telegram environment.

Your highest priority is keeping the text visually clean and readable.

Follow these rules strictly:

1. Write the majority of the text in Persian.

2. Never start a sentence with an English word.

3. Never put an English name at the beginning of a sentence.

4. When an English name is necessary, place it AFTER Persian words.

Correct:
تیم Team Spirit قهرمان مسابقات شد.

Correct:
هیروی Gusion تغییرات مهمی دریافت کرد.

Correct:
اسکین جدید Lesley معرفی شد.

Incorrect:
Team Spirit قهرمان مسابقات شد.

Incorrect:
Gusion تغییرات مهمی دریافت کرد.

5. Keep every English name as one complete string.

6. Never split English words with Persian characters.

7. Avoid putting multiple English words next to each other whenever possible.

8. Do not use parentheses unless absolutely necessary.

9. Avoid unnecessary English text.

10. Do not use tables.

11. Do not use Markdown tables.

12. Do not use numbered lists.

13. Do not use bullet points.

14. Do not use long paragraphs.

15. Every section MUST be separated by exactly ONE empty line.

16. Keep sentences short.

17. Do not put English text at the end of a sentence immediately before punctuation if it can be avoided.

────────────────────────

ENGLISH NAMES

Keep official names in English.

Examples:

تیم Team Spirit
تیم ONIC
هیروی Gusion
هیروی Lesley
اسکین Aspirants
رویداد MSC
بازی Mobile Legends

Do not translate official Hero names, Team names, Skin names, Event names, or Tournament names.

However, always introduce them after a Persian word whenever possible.

────────────────────────

NUMBERS

Use Persian numbers whenever possible.

Examples:

۴ بر ۳
۱ میلیون دلار
۱۶ ساله

Remove unnecessary statistics.

Do not include large viewer statistics, PCV numbers, watch hours, or minor statistics unless they are essential to the main story.

────────────────────────

CONTENT RULES

Only use information contained in the source.

Never invent:

* Players
* Teams
* Results
* Dates
* Rewards
* Statistics
* Quotes
* Events
* Features

Do not turn speculation into fact.

Do not add personal opinions that are not supported by the source.

Do not repeat information.

Do not add hashtags.

Do not add a source section.

Do not add a conclusion after the Call To Action.

Do not mention that you are an AI.

Do not explain your work.

────────────────────────

FINAL OUTPUT TEMPLATE

The output MUST visually follow this exact pattern:

🔥 [SHORT HEADLINE]

📌 [SHORT DETAIL SENTENCE]
[SHORT DETAIL SENTENCE]
[SHORT DETAIL SENTENCE]

🔎 [SHORT ANALYSIS SENTENCE]
[SHORT ANALYSIS SENTENCE]

💬 نظر شما چیه؟
[ONE SHORT QUESTION]

❤️ ری‌اکشن یادتون نره
💬 نظرتون رو کامنت کنید
📤 اگه این خبر براتون جالب بود، برای دوستاتون بفرستید

Do not change this structure.

Do not merge sections.

Do not remove the blank lines.

Do not add extra sections.

RAW NEWS:
{{INPUT}}

"""


groq_response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"""
خبر رسمی MOONTON:

عنوان:
{title}

متن:
{text}
"""
        }
    ],
)

ai_text = groq_response.choices[0].message.content

print("========== VORYX AI ==========")
print(ai_text)
print("==============================")

ai_text = groq_response.choices[0].message.content

print("========== GROQ AI ==========")
print(ai_text)
print("==============================")


print("TITLE:", title)
print("IMAGE:", image_url)


# ==================================================
# Telegram
# ==================================================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


if not TOKEN or not CHAT_ID:
    print("Telegram credentials پیدا نشد.")
    exit(1)


# ==================================================
# ارسال عکس + کپشن
# ==================================================

if image_url:

    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

    caption = f"""📰 {title[:500]}

🔗 منبع:
{latest_news}
"""

    response = requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "photo": image_url,
            "caption": caption
        },
        timeout=60
    )


# ==================================================
# اگر عکس وجود نداشت → ارسال متن
# ==================================================

else:

    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    message = f"""📰 {title}

{text[:3500]}

🔗 منبع:
{latest_news}
"""

    response = requests.post(
        telegram_url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=60
    )


# -------------------------
# Telegram
# -------------------------

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ارسال عکس اصلی خبر
if image_url:

    telegram_photo_url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

    photo_response = requests.post(
        telegram_photo_url,
        data={
            "chat_id": CHAT_ID,
            "photo": image_url
        },
        timeout=60
    )

    print("Telegram Photo:", photo_response.json())

    if not photo_response.ok:
        print("ارسال عکس ناموفق بود.")
        exit(1)


# ارسال متن کامل Voryx
telegram_text_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

message = ai_text



text_response = requests.post(
    telegram_text_url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    },
    timeout=60
)

print("Telegram Text:", text_response.json())

if not text_response.ok:
    print("ارسال متن ناموفق بود.")
    exit(1)

print("خبر با موفقیت به Telegram ارسال شد.")

# ==================================================
# ذخیره خبر پردازش‌شده
# ==================================================

with open(LAST_NEWS_FILE, "w", encoding="utf-8") as file:
    file.write(latest_news)

print("خبر پردازش و ذخیره شد.")
