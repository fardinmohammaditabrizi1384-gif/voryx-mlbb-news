import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

NEWS_URL = "https://en.moonton.com/news/index.html"
BASE_URL = "https://en.moonton.com"
LAST_NEWS_FILE = "last_news.txt"


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

    title = soup.find("h1")

    # متن اصلی خبر
    text_parts = []

    for element in soup.find_all(["p", "h2", "h3"]):
        text = element.get_text(" ", strip=True)

        if text:
            text_parts.append(text)

    # تصاویر
    images = []

    for img in soup.find_all("img"):
        src = img.get("src")

        if src:
            image_url = urljoin(url, src)

            if image_url not in images:
                images.append(image_url)

    return {
        "title": title.get_text(" ", strip=True) if title else "بدون عنوان",
        "text": "\n\n".join(text_parts),
        "images": images
    }


# -------------------------
# پیدا کردن خبر جدید
# -------------------------

latest_news = get_latest_news()

if not latest_news:
    print("هیچ خبری پیدا نشد.")
    exit()

print("آخرین خبر:", latest_news)


# -------------------------
# بررسی تکراری بودن
# -------------------------

old_news = ""

if os.path.exists(LAST_NEWS_FILE):
    with open(LAST_NEWS_FILE, "r") as file:
        old_news = file.read().strip()

if latest_news == old_news:
    print("خبر جدیدی وجود ندارد.")
    exit()


# -------------------------
# استخراج خبر
# -------------------------

news = get_news_content(latest_news)

print("\n========== NEWS ==========\n")
print("TITLE:")
print(news["title"])

print("\nTEXT:")
print(news["text"])

print("\nIMAGES:")

for image in news["images"]:
    print(image)


# -------------------------
# ذخیره خبر
# -------------------------

with open(LAST_NEWS_FILE, "w") as file:
    file.write(latest_news)

print("\nخبر با موفقیت استخراج شد.")
