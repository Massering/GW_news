import json
import requests
import time
from bs4 import BeautifulSoup
from telegram import Bot
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from parser import YandexArchiveParser, YEAR_URLS

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PROMPT_FILE = "prompt.txt"

bot = Bot(token=BOT_TOKEN)


def load_prompt():
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def generate_news(text):
    full_prompt = load_prompt().replace("{{content}}", text)

    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "deepseek-r1:7b",
        "prompt": full_prompt,
        "temperature": 0.7,
        "stream": False
    })

    return response.json()["response"]


def publish(text):
    if text:
        bot.send_message(chat_id=CHANNEL_ID, text=text)


def job():
    target_date = datetime.now() - timedelta(days=365 * 84 + 23)

    parser = YandexArchiveParser()
    data = parser.parse_issue_by_date(
        YEAR_URLS[target_date.year],
        target_date.strftime("%Y-%m-%d")
    )

    os.makedirs("Izvestia", exist_ok=True)
    with open(f"Izvestia/izvestia_{target_date.strftime('%Y-%m-%d')}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    all_text = '\n\n'.join([i["text"] for i in data["pages"]])
    news = generate_news(all_text)
    publish(news)


if __name__ == "__main__":
    job()
