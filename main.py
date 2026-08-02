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
