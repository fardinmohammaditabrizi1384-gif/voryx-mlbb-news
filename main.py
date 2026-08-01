import os
import requests
from bs4 import BeautifulSoup

NEWS_URL = "https://en.moonton.com/news/index.html"
BASE_URL = "https://en.moonton.com"
LAST_NEWS_FILE = "last_news.txt"

# -----------------------------
# دریافت صفحه اخبار
# -----------------------------

response = requests.get(NEWS_URL, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

news_links = []

for link in soup.find_all("a", href=True):
    href = link["href"]

    if "/news/" not in href:
        continue

    if href.endswith("index.html"):
        continue

    if href.startswith("/"):
        href = BASE_URL + href

    if href not in news_links:
        news_links.append(href)


# -----------------------------
# آخرین خبر
# -----------------------------

if not news_links:
    print("هیچ خبری پیدا نشد.")
    exit()

latest_news = news_links[0]

print("آخرین خبر:")
print(latest_news)


# -----------------------------
# بررسی خبر قبلی
# -----------------------------

old_news = ""

if os.path.exists(LAST_NEWS_FILE):
    with open(LAST_NEWS_FILE, "r") as file:
        old_news = file.read().strip()


if latest_news == old_news:
    print("خبر جدیدی وجود ندارد.")
    exit()


# -----------------------------
# ذخیره خبر جدید
# -----------------------------

with open(LAST_NEWS_FILE, "w") as file:
    file.write(latest_news)


# -----------------------------
# ارسال به تلگرام
# -----------------------------

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

message = f"""🆕 خبر جدید MOONTON

{latest_news}
"""

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    },
    timeout=30
)

print("خبر جدید به تلگرام ارسال شد.")
