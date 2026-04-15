import requests
import schedule
import time
from bs4 import BeautifulSoup
from telegram import Bot
from datetime import datetime
import os
from dotenv import load_dotenv

# === LOAD ENV ===
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

SOURCES = [
    "https://example.com/ww2-article",
]

PROMPT_FILE = "prompt.txt"

# === TELEGRAM ===
bot = Bot(token=BOT_TOKEN)


# === SOURCE PARSER ===
def fetch_source_content(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        paragraphs = soup.find_all("p")
        text = "\n".join([p.get_text() for p in paragraphs])
        return text[:5000]
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""


# === LOAD PROMPT ===
def load_prompt():
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


# === LLM REQUEST ===
def generate_news(text):
    prompt_template = load_prompt()
    full_prompt = prompt_template.replace("{{content}}", text)

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        print("LLM error:", data)
        return None


# === PUBLISH ===
def publish(text):
    if not text:
        return
    bot.send_message(chat_id=CHANNEL_ID, text=text)


# === JOB ===
def job():
    print("[", datetime.now(), "] Running job...")

    all_text = ""
    for source in SOURCES:
        content = fetch_source_content(source)
        if content:
            all_text += content + "\n\n"

    if not all_text:
        print("No content fetched")
        return

    news = generate_news(all_text)
    publish(news)


# === SCHEDULER ===
def run_scheduler():
    schedule.every().day.at("10:00").do(job)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    run_scheduler()
