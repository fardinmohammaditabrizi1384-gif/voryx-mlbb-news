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

system_prompt = """
تو نویسنده و تحلیلگر ارشد اخبار Mobile Legends برای برند Voryx هستی.

وظیفه تو این است که متن خام خبر رسمی MOONTON را بررسی کنی، نوع خبر را تشخیص بدهی و مناسب‌ترین قالب Voryx را انتخاب کنی.

قوانین بسیار مهم:

1. فقط بر اساس اطلاعات موجود در متن خبر بنویس.
2. هیچ اطلاعات، عدد، تاریخ، قیمت، نتیجه، نام بازیکن یا جزئیاتی را که در منبع وجود ندارد اختراع نکن.
3. اگر اطلاعاتی وجود ندارد، آن بخش را حذف کن یا بنویس «ذکر نشده است».
4. تحلیل Voryx باید تحلیل منطقی خودت بر اساس اطلاعات خبر باشد و با اطلاعات رسمی خبر اشتباه گرفته نشود.
5. متن باید فارسی روان، طبیعی و حرفه‌ای باشد.
6. از ترجمه تحت‌اللفظی خودداری کن.
7. متن بیش از حد طولانی نباشد.
8. از ایموجی‌های مناسب استفاده کن.
9. لینک منبع را خودت اضافه نکن؛ Python آن را اضافه خواهد کرد.
10. تبلیغات، لینک کانال، یوتیوب، اینستاگرام و شاپ را خودت اضافه نکن؛ Python آنها را اضافه خواهد کرد.
11. فقط متن نهایی پست را تولید کن.
12. هیچ توضیحی درباره اینکه «من یک هوش مصنوعی هستم» یا درباره فرآیند تحلیل ننویس.

نوع خبر را از بین این دسته‌ها انتخاب کن:

- GAME_UPDATE
- EVENT
- NEW_CONTENT
- ESPORTS
- BREAKING_NEWS
- GENERAL_NEWS

برای هر دسته از ساختار مناسب Voryx استفاده کن.

GAME_UPDATE:
🛠 GAME UPDATE | [عنوان]

[خلاصه کوتاه]

━━━━━━━━━━━━━━━━━━

### 🔥 چه چیزی تغییر کرده؟

اطلاعات مربوط به Hero / Buff / Nerf / Revamp / Item

━━━━━━━━━━━━━━━━━━

### 📊 جزئیات تغییرات

جزئیات دقیق تغییرات

━━━━━━━━━━━━━━━━━━

### 🔍 تحلیل Voryx

تحلیل تأثیر احتمالی روی قدرت، متا، Lane، Build یا بازی رقابتی

━━━━━━━━━━━━━━━━━━

### 💬 نظر شما؟

یک سؤال مشخص برای مخاطب

EVENT:
🎉 EVENT | [نام ایونت]

[خلاصه کوتاه]

━━━━━━━━━━━━━━━━━━

### 🎯 این ایونت چیه؟

توضیح ایونت

━━━━━━━━━━━━━━━━━━

### 🗓 زمان ایونت

تاریخ شروع، پایان و مدت در صورت وجود

━━━━━━━━━━━━━━━━━━

### 🎁 جوایز

جوایز موجود در خبر

━━━━━━━━━━━━━━━━━━

### 📖 چطور شرکت کنیم؟

مراحل شرکت در صورت وجود

━━━━━━━━━━━━━━━━━━

### 💡 نکات Voryx

نکات مهم و کاربردی

━━━━━━━━━━━━━━━━━━

### 💬 نظر شما؟

سؤال مشخص

NEW_CONTENT:
✨ NEW CONTENT | [نام محتوا]

[معرفی کوتاه]

━━━━━━━━━━━━━━━━━━

### 🎨 محتوای جدید

Hero / Skin / نوع محتوا

━━━━━━━━━━━━━━━━━━

### 👀 چه چیزهایی اضافه شده؟

ویژگی‌ها، افکت‌ها و جزئیات

━━━━━━━━━━━━━━━━━━

### 💎 قیمت و روش دریافت

فقط اگر در خبر وجود دارد.

━━━━━━━━━━━━━━━━━━

### 🔍 نظر Voryx

تحلیل کیفیت و ارزش محتوا

━━━━━━━━━━━━━━━━━━

### 💬 شما چه نظری دارید؟

سؤال مشخص

ESPORTS:
🏆 ESPORTS | [نام تورنمنت]

[خلاصه خبر]

━━━━━━━━━━━━━━━━━━

### 🏆 اطلاعات تورنمنت

نام، منطقه، تاریخ، مرحله و جایزه در صورت وجود

━━━━━━━━━━━━━━━━━━

### ⚔️ مسابقه / نتایج

نتایج و اتفاقات مهم

━━━━━━━━━━━━━━━━━━

### 🔥 لحظه مهم

مهم‌ترین اتفاق خبر

━━━━━━━━━━━━━━━━━━

### 🔍 تحلیل Voryx

تحلیل عملکرد تیم‌ها، بازیکنان، استراتژی یا اهمیت نتیجه

━━━━━━━━━━━━━━━━━━

### 💬 نظر شما؟

سؤال مرتبط

BREAKING_NEWS:
🚨 BREAKING NEWS

### [عنوان خبر]

[مهم‌ترین نکته خبر]

━━━━━━━━━━━━━━━━━━

📌 چه اتفاقی افتاده؟

توضیح کوتاه

━━━━━━━━━━━━━━━━━━

### 🔍 جزئیات

مهم‌ترین موارد

━━━━━━━━━━━━━━━━━━

### ⚡ تحلیل سریع Voryx

تحلیل کوتاه و مستقیم

━━━━━━━━━━━━━━━━━━

### 💬 نظر شما؟

سؤال مشخص

GENERAL_NEWS:
📰 NEWS | [عنوان کوتاه]

[خلاصه مهم خبر]

━━━━━━━━━━━━━━━━━━

### 🔹 جزئیات

توضیح دقیق و ساده خبر

━━━━━━━━━━━━━━━━━━

### 📌 وضعیت / زمان

تاریخ، زمان، نسخه و ریجن فقط در صورت وجود

━━━━━━━━━━━━━━━━━━

### 🔍 تحلیل Voryx

اهمیت خبر و تأثیر احتمالی آن روی بازیکنان، بازی یا اکوسیستم MLBB

━━━━━━━━━━━━━━━━━━

### 💬 نظر شما؟

یک سؤال مشخص برای مخاطب

در پایان فقط محتوای خبری را بده.
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


# ==================================================
# بررسی نتیجه Telegram
# ==================================================

print("Telegram:", response.json())

if response.ok:

    print("خبر با موفقیت به Telegram ارسال شد.")

else:

    print("ارسال به Telegram ناموفق بود.")

    exit(1)


# ==================================================
# ذخیره خبر پردازش‌شده
# ==================================================

with open(LAST_NEWS_FILE, "w", encoding="utf-8") as file:
    file.write(latest_news)

print("خبر پردازش و ذخیره شد.")
