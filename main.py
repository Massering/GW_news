import json
from telebot import TeleBot
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

import LLM_local
import LLM_online
from parser import YandexArchiveParser, YEAR_URLS

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PROMPT_FILE = "prompt.txt"

bot = TeleBot(token=BOT_TOKEN)


def load_prompt():
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def generate_news(text):
    full_prompt = load_prompt().replace("{{content}}", text)

    filename = f"promt.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_prompt)

    text = LLM_local.LLM_query(full_prompt)
    return text


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
    filename = f"Izvestia/izvestia_{target_date.strftime("%Y-%m-%d")}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    all_text = '\n\n'.join([i["text"] for i in data["pages"]])
    print(len(all_text), all_text[:200])

    news = generate_news(all_text)
    print(len(news), news[:200])

    if news:
        publish(news)


if __name__ == "__main__":
    job()
