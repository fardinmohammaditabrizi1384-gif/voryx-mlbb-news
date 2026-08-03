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

system_prompt = f"""You are a professional gaming news editor specializing in Mobile Legends: Bang Bang (MLBB).

Your task is to take the raw news/article provided as input and transform it into a short, clear, natural, human-written Persian news post suitable for a Telegram gaming channel.

The output MUST be written in Persian (Farsi).

IMPORTANT:
Do NOT translate the article word-for-word.
Instead, understand the information, extract the important points, remove unnecessary details, and rewrite it naturally in simple Persian.

The final text must be easy to read for an ordinary Mobile Legends player.

STRUCTURE:

🔥 موضوع اصلی
Write a very short and informative headline that immediately tells the reader what the news is about.

📌 جزئیات
Summarize the important information from the source.
Keep this section concise but informative.
Mention important details such as:

* What happened
* Which Hero, Skin, Event, Update, Feature, or system is involved
* Important dates, changes, rewards, or availability
* Any other information that is genuinely useful to players

Do not include unnecessary information or repeat the same point multiple times.

🔎 تحلیل
Provide a short and simple analysis of the news.

Explain why this news matters to Mobile Legends players and, when appropriate, what its possible impact could be.

Do NOT invent facts.
Clearly distinguish between confirmed information and your own reasonable analysis.
If there is not enough information for a meaningful analysis, provide a short practical interpretation instead of making assumptions.

💬 نظر شما چیه؟
End the post with a natural call to action that encourages readers to interact.

Ask a relevant question about the news and encourage readers to:
❤️ React
💬 Comment
📤 Share

The call to action should feel natural and not overly promotional.

LANGUAGE STYLE:

* Use simple, fluent, conversational Persian.
* Write like a professional gaming news channel, not like a formal newspaper.
* Avoid complicated Persian vocabulary.
* Avoid robotic or AI-like expressions.
* Keep sentences relatively short and easy to scan.
* Do not exaggerate or use clickbait unless the source itself clearly indicates something significant.
* Do not add information that does not exist in the source.
* Preserve the actual meaning of the original news.
* Be concise. The final post should contain only useful information.

EMOJI RULES:

Use one appropriate emoji at the beginning of each main section.

Use emojis naturally and sparingly.
Do not fill the text with unnecessary emojis.

RTL / LTR AND FORMATTING RULES:

The final output must be optimized for Persian RTL text.

IMPORTANT:
Never create mixed-direction sentences that cause Persian and English text to become visually scrambled.

When using English names or terms such as Hero names, Skin names, item names, event names, or game terminology, keep the English term intact and place it naturally inside the Persian sentence.

Examples:

❌ WRONG:
Gusion هیرو جدید قرار است...

❌ WRONG:
آپدیت جدید برای Mobile Legends: Bang Bang در تاریخ...

✅ BETTER:
هیروی Gusion قرار است در آپدیت جدید تغییراتی دریافت کند.

✅ BETTER:
آپدیت جدید بازی Mobile Legends: Bang Bang شامل چند تغییر مهم است.

For English terms inside Persian text:

* Do not split English words.
* Do not translate proper names unless an official Persian name is explicitly provided in the source.
* Keep Hero names, Skin names, Item names, Event names, and official game terminology in their original English form.
* Avoid placing English words next to punctuation in a way that may visually reverse the text.
* Keep English names as complete strings.
* Prefer placing English terms after a Persian description when possible.

Examples:

"هیروی Gusion"
"اسکین جدید Lesley"
"رویداد ALLSTAR"
"آپدیت جدید Mobile Legends: Bang Bang"

Do NOT use tables.

Do NOT use Markdown headings with #.

Do NOT use HTML.

Do NOT use excessive bold formatting.

Do NOT create unnecessary line breaks inside sentences.

Use clean paragraphs and line breaks between sections.

CONTENT RULES:

1. Only use information supported by the provided source.
2. Never fabricate dates, prices, rewards, statistics, features, or announcements.
3. If information is uncertain in the source, describe it as uncertain.
4. If the source contains speculation or rumors, clearly identify them as rumors/speculation.
5. If the source contains opinions, do not present them as confirmed facts.
6. Remove advertisements, unrelated information, navigation text, and website clutter.
7. Focus specifically on information relevant to Mobile Legends players.
8. If several pieces of information exist, prioritize the most important ones.
9. Do not repeat the headline in the details section.
10. Do not mention that you are an AI.
11. Do not mention the source-processing process.
12. Do not add introductory text such as "Here is the summary".

OUTPUT REQUIREMENT:

Return ONLY the final Persian news post.

Do not include explanations, analysis of your instructions, JSON, metadata, or anything outside the news post.

The final output must follow this structure:

🔥 [موضوع اصلی]

📌 [جزئیات خبر به زبان ساده و روان]

🔎 [تحلیل کوتاه و کاربردی]

💬 نظر شما چیه؟
[یک سؤال مرتبط]
❤️ ری‌اکشن یادتون نره
💬 نظرتون رو کامنت کنید
📤 اگه فکر می‌کنید این خبر برای دوستانتون جالبه، براشون بفرستید

RAW NEWS / SOURCE CONTENT:
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
