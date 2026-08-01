import os
import requests
from bs4 import BeautifulSoup

NEWS_URL = "https://en.moonton.com/news/index.html"

response = requests.get(NEWS_URL, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# پیدا کردن لینک‌های خبر
news_links = []

for link in soup.find_all("a", href=True):
    href = link["href"]

    if "/news/" in href and href != "/news/index.html":
        if href.startswith("/"):
            href = "https://en.moonton.com" + href

        if href not in news_links:
            news_links.append(href)

print("آخرین لینک‌های پیدا شده:")

for link in news_links[:5]:
    print(link)

# ارسال نتیجه به تلگرام
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

message = "📰 تست دریافت اخبار MOONTON\n\n"

if news_links:
    message += "\n".join(news_links[:5])
else:
    message += "هیچ خبری پیدا نشد."

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    },
    timeout=30
)

print("نتیجه به تلگرام ارسال شد.")
