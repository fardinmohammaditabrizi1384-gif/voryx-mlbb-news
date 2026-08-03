import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from groq import Groq


# =========================================================
# SETTINGS
# =========================================================

NEWS_URL = "https://en.moonton.com/news/index.html"
BASE_URL = "https://en.moonton.com"
LAST_NEWS_FILE = "last_news.txt"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# =========================================================
# CHECK API KEYS
# =========================================================

if not TELEGRAM_BOT_TOKEN:
    raise Exception("TELEGRAM_BOT_TOKEN پیدا نشد.")

if not TELEGRAM_CHAT_ID:
    raise Exception("TELEGRAM_CHAT_ID پیدا نشد.")

if not GROQ_API_KEY:
    raise Exception("GROQ_API_KEY پیدا نشد.")


client = Groq(api_key=GROQ_API_KEY)


# =========================================================
# GET LATEST NEWS
# =========================================================

def get_latest_news():
    response = requests.get(
        NEWS_URL,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for link in soup.find_all("a", href=True):

        href = link["href"]

        if "/news/" in href and not href.endswith("index.html"):
            return urljoin(BASE_URL, href)

    return None


# =========================================================
# GET NEWS CONTENT
# =========================================================

def get_news_content(url):

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # -------------------------
    # Title
    # -------------------------

    title_tag = soup.find("title")

    title = (
        title_tag.get_text(" ", strip=True)
        if title_tag
        else "خبر جدید Mobile Legends"
    )

    # حذف بخش اضافه عنوان سایت
    title = title.replace(
        "-Develop games and fun for players all over the world",
        ""
    ).strip()

    # -------------------------
    # Text
    # -------------------------

    text_parts = []

    for element in soup.find_all(["p", "h2", "h3"]):

        text = element.get_text(" ", strip=True)

        if not text:
            continue

        # حذف متن‌های تکراری / غیرخبری
        if text in text_parts:
            continue

        text_parts.append(text)

    text = "\n\n".join(text_parts)

    # -------------------------
    # Images
    # -------------------------

    images = []

    for img in soup.find_all("img"):

        src = img.get("src")

        if not src:
            continue

        image_url = urljoin(url, src)

        lower_url = image_url.lower()

        # حذف لوگو و آیکون
        if any(
            item in lower_url
            for item in [
                "logo",
                "flogo",
                "logob",
                "icon"
            ]
        ):
            continue

        if image_url not in images:
            images.append(image_url)

    return {
        "title": title,
        "text": text,
        "images": images
    }


# =========================================================
# GENERATE VORYX POST
# =========================================================

def generate_voryx_post(title, text):

prompt = f"""
تو فقط یک نویسنده و ویرایشگر اخبار گیمینگ فارسی برای Voryx هستی.

وظیفه تو:
خبر داده‌شده را به یک پست کوتاه و آماده انتشار در تلگرام تبدیل کن.

قوانین قطعی:

- فقط از فارسی و انگلیسی استفاده کن.
- هیچ کاراکتر چینی، ژاپنی، کره‌ای، عربیِ غیرضروری یا زبان دیگری استفاده نکن.
- اگر نام بازی، تیم، بازیکن یا تورنمنت انگلیسی است، نام اصلی آن را حفظ کن.
- متن را طبیعی و روان به فارسی بنویس.
- ترجمه تحت‌اللفظی نکن.
- لحن دوستانه، ساده و مناسب گیمرها باشد.
- کوتاه بنویس.
- اطلاعاتی که در خبر وجود ندارد اضافه نکن.
- اطلاعات را حدس نزن.
- هیچ تحلیل شخصی اضافه نکن.
- هیچ منبع یا لینکی از خبر اصلی ننویس.
- عبارت «منبع» را اصلاً ننویس.
- هیچ Markdown استفاده نکن.
- از # ، ## ، ### ، ** و * استفاده نکن.
- هیچ بخش جدیدی به ساختار اضافه نکن.
- هیچ بخشی را حذف نکن.
- بین عنوان هر بخش و متن آن یک خط خالی باشد.
- بین موارد مختلف یک خط خالی باشد.
- از ایموجی‌های کم و مرتبط استفاده کن.
- خروجی فقط شامل متن نهایی پست باشد.
- قبل یا بعد از پست هیچ توضیحی ننویس.

ساختار را دقیقاً به این شکل حفظ کن:

🎮 [نوع خبر] | [عنوان کوتاه]

[خلاصه خبر در ۱ یا ۲ جمله]


━━━━━━━━━━━━━━━━━━


📌 توضیحات

[توضیح کوتاه و روان]

• [مورد مهم اول]

• [مورد مهم دوم]

• [مورد مهم سوم]


━━━━━━━━━━━━━━━━━━


💬 نظر شما؟

[یک سؤال کوتاه و طبیعی درباره همین خبر]


━━━━━━━━━━━━━━━━━━


❤️ اگر این خبر براتون مفید بود واکنش بدید

💬 نظرتون رو کامنت کنید

🔄 خبر رو برای دوستاتون بفرستید


━━━━━━━━━━━━━━━━━━


🔗 لینک‌های Voryx

🎮 کانال جم و اخبار:
@Sinister_Mlbb

💬 گپ فعال:
@Sinister_Mlbb_Gap


خبر اصلی:

{text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.4,
        max_tokens=700
    )

    result = response.choices[0].message.content.strip()

    return result


# =========================================================
# SEND PHOTO TO TELEGRAM
# =========================================================

def send_photo(image_url):

    telegram_url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    )

    response = requests.post(
        telegram_url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": image_url
        },
        timeout=60
    )

    print("Telegram Photo:", response.json())

    response.raise_for_status()


# =========================================================
# SEND TEXT TO TELEGRAM
# =========================================================

def send_text(message):

    telegram_url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        telegram_url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        },
        timeout=60
    )

    print("Telegram Text:", response.json())

    response.raise_for_status()


# =========================================================
# MAIN
# =========================================================

print("شروع Voryx News Bot...")


# -------------------------
# Find latest news
# -------------------------

latest_news = get_latest_news()

if not latest_news:
    print("هیچ خبری پیدا نشد.")
    exit(0)

print("آخرین خبر:", latest_news)


# -------------------------
# Check duplicate
# -------------------------

old_news = ""

if os.path.exists(LAST_NEWS_FILE):

    with open(
        LAST_NEWS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        old_news = file.read().strip()


if latest_news == old_news:

    print("خبر جدیدی وجود ندارد.")
    exit(0)


# -------------------------
# Extract news
# -------------------------

news = get_news_content(latest_news)

title = news["title"]
text = news["text"]

image_url = (
    news["images"][0]
    if news["images"]
    else None
)

print("TITLE:", title)
print("IMAGE:", image_url)


# -------------------------
# Generate Voryx content
# -------------------------

print("========== VORYX AI ==========")

ai_text = generate_voryx_post(
    title,
    text
)

print(ai_text)

print("==============================")


# -------------------------
# Send to Telegram
# -------------------------

if image_url:

    send_photo(image_url)

send_text(ai_text)


# -------------------------
# Save latest news
# -------------------------

with open(
    LAST_NEWS_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write(latest_news)


print("خبر با موفقیت ارسال و ذخیره شد.")
