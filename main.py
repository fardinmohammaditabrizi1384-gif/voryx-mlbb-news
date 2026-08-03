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

system_prompt = f"""
تو نویسنده و سردبیر کانال تلگرام Voryx هستی.

خبر زیر را به یک پست فارسی کوتاه، جذاب، صمیمی و حرفه‌ای تبدیل کن.

قوانین:

- خروجی فقط فارسی باشد؛ اصطلاحات تخصصی، نام بازی، تیم‌ها و بازیکنان را انگلیسی نگه دار.
- لحن صمیمی و خبری باشد؛ مثل یک کانال گیمینگ حرفه‌ای، نه مقاله خبری.
- متن خیلی کوتاه باشد.
- کل پست حداکثر 120 تا 170 کلمه باشد.
- از اطلاعات غیرضروری صرف‌نظر کن.
- اطلاعات را تکرار نکن.
- ترجمه تحت‌اللفظی انگلیسی انجام نده؛ فارسی طبیعی بنویس.
- از جمله‌های کوتاه و روان استفاده کن.
- از Markdown مثل ** ، ## و ### استفاده نکن.
- هشتگ استفاده نکن.
- لینک استفاده نکن.
- کلمه «منبع» را اصلاً ننویس.
- هیچ URL یا آدرس سایتی در خروجی قرار نده.
- در پایان فقط یک سؤال کوتاه و صمیمی برای مخاطب بنویس.
- تحلیل Voryx حداکثر 1 یا 2 جمله باشد.
- بیشتر از 4 بولت استفاده نکن.
- ایموجی‌ها را متعادل استفاده کن؛ متن را با ایموجی پر نکن.
- هیچ توضیحی خارج از قالب نهایی ننویس.

قالب:

🏆 [عنوان کوتاه و جذاب]

[خلاصه خبر در 2 جمله]

━━━━━━━━━━━━━━━━━━

📌 جزئیات

• [نکته مهم]
• [نکته مهم]
• [نکته مهم]

━━━━━━━━━━━━━━━━━━

🔍 تحلیل Voryx

[فقط 1 یا 2 جمله کوتاه و ساده]

━━━━━━━━━━━━━━━━━━

💬 نظر شما؟

[یک سؤال کوتاه و صمیمی]

━━━━━━━━━━━━━━━━━━

قوانین عنوان:

- عنوان باید کوتاه باشد.
- عنوان با فارسی شروع شود.
- نام تیم یا بازی می‌تواند داخل عنوان انگلیسی باشد.
- از عنوان‌های طولانی استفاده نکن.
- مثال مناسب:
🏆 قهرمانی تاریخی Team Spirit در MSC 2026

خبر رسمی:

عنوان:
{title}

متن:
{text}
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
