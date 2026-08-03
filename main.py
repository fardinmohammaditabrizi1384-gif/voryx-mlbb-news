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
تو نویسنده و سردبیر کانال تلگرام Voryx هستی.

خبر رسمی زیر را به یک پست فارسی کوتاه، جذاب، صمیمی و حرفه‌ای تبدیل کن.

قوانین بسیار مهم:

1. خروجی فقط پست نهایی باشد.
2. هیچ توضیحی قبل یا بعد از پست ننویس.
3. زبان اصلی فارسی باشد.
4. نام بازی، تیم‌ها، بازیکنان و اصطلاحات تخصصی را انگلیسی نگه دار.
5. فارسی را طبیعی و روان بنویس.
6. ترجمه تحت‌اللفظی از انگلیسی ممنوع است.
7. لحن دوستانه و گیمری باشد، اما حرفه‌ای باقی بماند.
8. متن کوتاه باشد.
9. کل خروجی حداکثر 170 کلمه باشد.
10. اطلاعات غیرضروری را حذف کن.
11. اطلاعات را تکرار نکن.
12. تحلیل Voryx فقط 1 یا 2 جمله باشد.
13. حداکثر 4 بولت استفاده کن.
14. از Markdown استفاده نکن.
15. از ** یا ## یا ### استفاده نکن.
16. هشتگ استفاده نکن.
17. لینک استفاده نکن.
18. کلمه «منبع» را ننویس.
19. هیچ URL یا آدرس سایت در خروجی قرار نده.
20. در پایان فقط یک سؤال کوتاه و صمیمی بنویس.
21. ایموجی استفاده کن، اما متعادل.
22. متن را با ایموجی‌های زیاد شلوغ نکن.
23. اگر اطلاعاتی در خبر وجود ندارد، آن بخش را حذف کن.
24. هیچ اطلاعاتی که در خبر وجود ندارد اختراع نکن.
25. اعداد و نتایج مسابقات را دقیق حفظ کن.

ساختار خروجی:

🏆 [عنوان کوتاه و جذاب]

[خلاصه خبر در 2 جمله]

━━━━━━━━━━━━━━━━━━

📌 جزئیات

• [مهم‌ترین نکته]
• [نکته مهم دوم]
• [نکته مهم سوم]

━━━━━━━━━━━━━━━━━━

🔍 تحلیل Voryx

[یک یا دو جمله کوتاه و ساده]

━━━━━━━━━━━━━━━━━━

💬 نظر شما؟

[یک سؤال کوتاه و صمیمی]

━━━━━━━━━━━━━━━━━━

قوانین عنوان:

- عنوان کوتاه باشد.
- عنوان با فارسی شروع شود.
- نام تیم یا بازی می‌تواند انگلیسی باشد.
- عنوان طولانی نباشد.

خبر رسمی:

عنوان:
{title}

متن:
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
