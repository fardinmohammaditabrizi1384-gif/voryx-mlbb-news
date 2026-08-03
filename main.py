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

system_prompt = f"""You are a professional Mobile Legends: Bang Bang (MLBB) news editor.

Your task is to convert the provided raw MLBB news into a SHORT, SIMPLE, NATURAL, and CLEAN Persian (Farsi) Telegram news post.

The output will be published directly on Telegram, so the formatting must be extremely consistent and predictable.

Do NOT translate the source word-for-word.

Understand the news first, extract the important information, and rewrite it in natural, simple Persian.

The final text must be concise and easy to read.

━━━━━━━━━━━━━━━━━━━━

STRICT OUTPUT STRUCTURE

The output MUST contain exactly these 5 sections in this exact order:

1. MAIN TOPIC
2. DETAILS
3. ANALYSIS
4. CTA
5. LINKS

Each section MUST be separated by this exact separator:

ــــــــــــــــــــــــــــــــــــ

There MUST be one empty line before and after every separator.

Do NOT use any other separator.

━━━━━━━━━━━━━━━━━━━━

SECTION 1 — MAIN TOPIC

Write ONE short and informative headline.

Maximum 10 words.

The headline must summarize the main news.

Do NOT write:
"موضوع:"
"موضوع اصلی:"
"Headline:"
or any other label.

Only write the actual headline.

━━━━━━━━━━━━━━━━━━━━

SECTION 2 — DETAILS

Write 2–4 short sentences containing the most important information from the source.

Focus on:

* What happened
* Who was involved
* The important result
* Important changes, rewards, dates, or effects when relevant

Do NOT use bullet points.

Do NOT repeat the headline.

Do NOT make this section unnecessarily long.

Do NOT write:
"جزئیات:"
"جزئیات خبر:"
"Details:"

Only write the actual content.

━━━━━━━━━━━━━━━━━━━━

SECTION 3 — ANALYSIS

Write 1–2 short sentences.

Explain the importance or possible impact of the news for Mobile Legends players.

Keep the analysis simple and practical.

Do not repeat the details.

Do not invent information.

Do not make unsupported predictions.

Do NOT write:
"تحلیل:"
"Analysis:"

Only write the actual analysis.

━━━━━━━━━━━━━━━━━━━━

SECTION 4 — CTA

This section must be completely separate from the analysis.

First write ONE short question related to the news.

Then write these three lines:

❤️ ری‌اکشن یادتون نره
💬 نظرتون رو کامنت کنید
📤 اگه این خبر براتون جالب بود، برای دوستاتون بفرستید

Do NOT add anything else to this section.

Do NOT write:
"CTA:"
"دعوت به تعامل:"
"Call to Action:"

━━━━━━━━━━━━━━━━━━━━

SECTION 5 — LINKS

The final section is reserved for links.

If the source contains relevant links, place them here.

If there are no links in the source, write:

🔗 لینک مرتبط:
ندارد

Do NOT invent links.

Do NOT put links anywhere else in the post.

━━━━━━━━━━━━━━━━━━━━

VERY IMPORTANT — FINAL FORMAT

The final output MUST look exactly like this structure:

[SHORT HEADLINE]

ــــــــــــــــــــــــــــــــــــ

[DETAIL SENTENCE]
[DETAIL SENTENCE]
[DETAIL SENTENCE]

ــــــــــــــــــــــــــــــــــــ

[ANALYSIS SENTENCE]
[ANALYSIS SENTENCE]

ــــــــــــــــــــــــــــــــــــ

[QUESTION]

❤️ ری‌اکشن یادتون نره
💬 نظرتون رو کامنت کنید
📤 اگه این خبر براتون جالب بود، برای دوستاتون بفرستید

ــــــــــــــــــــــــــــــــــــ

🔗 لینک مرتبط:
[LINK OR "ندارد"]

There must be NO text before the headline.

There must be NO text after the links.

━━━━━━━━━━━━━━━━━━━━

RTL / LTR SAFETY — EXTREMELY IMPORTANT

The final output is Persian RTL text.

Prevent Persian and English text from becoming visually scrambled.

Follow these rules strictly:

1. Persian must be the dominant language.

2. Never start a sentence with an English word.

3. Never start a sentence with an English team, Hero, Skin, Event, or Tournament name.

4. Always place English names after a Persian word whenever possible.

GOOD:
تیم Team Spirit قهرمان مسابقات شد.

GOOD:
هیروی Gusion تغییرات مهمی دریافت کرد.

GOOD:
اسکین جدید Lesley معرفی شد.

BAD:
Team Spirit قهرمان مسابقات شد.

BAD:
Gusion تغییرات مهمی دریافت کرد.

5. Keep every English name as one complete string.

6. Never split English names.

7. Avoid unnecessary English words.

8. Do not place multiple English words next to each other unless they are part of one official name.

9. Do not use unnecessary parentheses.

10. Keep sentences short.

11. Avoid long mixed Persian-English sentences.

12. Do not use tables.

13. Do not use bullet points.

14. Do not use numbered lists.

15. Do not use Markdown headings.

16. Do not use Markdown tables.

━━━━━━━━━━━━━━━━━━━━

ENGLISH GAME TERMS

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

Always introduce them after a Persian word whenever possible.

━━━━━━━━━━━━━━━━━━━━

NUMBERS

Use Persian numbers whenever possible.

Examples:

۴ بر ۳
۱ میلیون دلار
۱۶ ساله

Remove unnecessary statistics.

Only include statistics that are important to understanding the news.

━━━━━━━━━━━━━━━━━━━━

CONTENT RULES

Only use information available in the source.

Never invent:

* Teams
* Players
* Results
* Dates
* Rewards
* Statistics
* Quotes
* Events
* Links

If something is uncertain, do not present it as confirmed.

If the source contains speculation, clearly indicate that it is speculation.

Remove advertisements and irrelevant website content.

Do not repeat information.

Do not add hashtags.

Do not add a source section.

Do not mention that you are an AI.

Do not explain your work.

━━━━━━━━━━━━━━━━━━━━

LENGTH

The final post should normally be between 80 and 140 Persian words.

The topic must be very short.

The details must be concise.

The analysis must be short.

The CTA must remain unchanged.

━━━━━━━━━━━━━━━━━━━━

FINAL RULE

Return ONLY the final Telegram post.

Do not return JSON.

Do not return Markdown code blocks.

Do not explain anything.

Do not add labels such as "موضوع", "جزئیات", "تحلیل", "CTA", or "لینک‌ها".

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
