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

system_prompt = f""You are a professional Mobile Legends: Bang Bang news editor.

Your job is to convert the provided raw article into a SHORT, CLEAN, STRUCTURED, and EASY-TO-READ Persian (Farsi) Telegram news post.

The final output must look like a polished human-written gaming news post.

IMPORTANT:
Do NOT translate the article literally.
Understand it first, then summarize only the most important information.

The output MUST be SHORT.
Remove unnecessary statistics, repeated information, minor details, long explanations, and irrelevant context.

TARGET LENGTH:
Approximately 100–160 Persian words.
Never make the post unnecessarily long.

────────────────────

FIXED OUTPUT STRUCTURE

The output MUST contain exactly these 4 sections and nothing else:

🔥 موضوع

Write ONE short headline.
Maximum 12 words.

The headline must immediately explain the main news.

Then leave one empty line.

📌 جزئیات

Write 2–4 short Persian sentences explaining the most important facts.

Answer only:
What happened?
Who was involved?
What was the important result?

Do not use bullet points.

Then leave one empty line.

🔎 تحلیل

Write ONLY 2 short sentences.

Explain why this news matters to MLBB players.

Do not speculate.
Do not introduce unrelated information.
Do not give analysis if the source does not provide enough information.

Then leave one empty line.

💬 نظر شما چیه؟

Write ONE short question related to the news.

Then write exactly:

❤️ ری‌اکشن یادتون نره
💬 نظرتون رو کامنت کنید
📤 اگه این خبر براتون جالب بود، برای دوستاتون بفرستید

────────────────────

PERSIAN WRITING STYLE

Write natural, simple, modern Persian.

The reader should understand every sentence immediately.

Use short sentences.

Avoid:

* Formal newspaper language
* Complicated Persian words
* Long sentences
* Repetition
* Marketing language
* Clickbait
* Robotic expressions
* Unnecessary explanations

Write like a professional Persian gaming Telegram channel.

────────────────────

CRITICAL RTL / LTR RULES

The output will be displayed in a Persian RTL environment.

Prevent Persian and English text from becoming visually mixed or scrambled.

RULES:

1. Keep English names completely intact.

2. Never write a sentence that starts with an English word.

3. Prefer putting English names AFTER a Persian description.

GOOD:
هیروی Gusion در این مسابقات عملکرد خوبی داشت.

GOOD:
تیم Team Spirit قهرمان مسابقات شد.

GOOD:
اسکین جدید Lesley معرفی شد.

BAD:
Gusion هیرو در این مسابقات...

BAD:
Team Spirit تیمی بود که...

4. Do NOT use English words unnecessarily.

5. Do NOT write English names in ALL CAPS unless they are official names.

6. Do NOT put multiple English terms next to each other.

7. Do NOT use tables.

8. Do NOT use Markdown headings.

9. Do NOT use numbered lists.

10. Do NOT use bullet points.

11. Do NOT use long paragraphs.

12. Put every section on separate lines.

13. Keep each paragraph visually simple.

────────────────────

NUMBERS AND DATES

Use Persian numerals whenever possible.

Examples:

۴ بر ۳
۱ میلیون دلار
۱۶ ساله

Do NOT use unnecessary decimal statistics.

If a statistic is not essential to understanding the news, remove it.

────────────────────

ENGLISH GAME TERMS

Keep official Mobile Legends names in English.

Examples:

هیروی Gusion
هیروی Lesley
تیم Team Spirit
مسابقات MSC
بازی Mobile Legends

Do NOT translate official Hero, Team, Skin, Event, or Tournament names into Persian unless an official Persian translation is explicitly provided.

────────────────────

FACT-CHECKING RULE

Use ONLY information contained in the provided source.

Never invent:

* Results
* Dates
* Players
* Teams
* Statistics
* Rewards
* Quotes
* Events
* Explanations

If something is uncertain, do not present it as confirmed.

────────────────────

IMPORTANT

The final output must contain ONLY the finished Persian Telegram post.

Do NOT explain your work.
Do NOT mention these instructions.
Do NOT include the original article.
Do NOT include JSON.
Do NOT add extra sections.
Do NOT add a source section.
Do NOT add hashtags.

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
