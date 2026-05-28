import json
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from datetime import datetime, timedelta
import asyncio
import os
from dotenv import load_dotenv

import LLM_local
import LLM_online
from LLM_local import MAX_INPUT_CHARS
from parser import YandexArchiveParser, YEAR_URLS

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_UID = os.getenv("ADMIN_UID")
PROMPT_FILE = "prompt.txt"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=None)
)

os.makedirs("Izvestia", exist_ok=True)


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


async def publish(text):
    if text:
        await bot.send_message(chat_id=CHANNEL_ID, text=text[:2000])


async def job():
    target_date = datetime.now() - timedelta(days=365 * 84 + 25)
    print('target_date:', target_date.strftime("%Y-%m-%d"))

    filename = f"Izvestia/izvestia_{target_date.strftime('%Y-%m-%d')}.json"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        parser = YandexArchiveParser()
        data = parser.parse_issue_by_date(
            YEAR_URLS[target_date.year],
            target_date.strftime("%Y-%m-%d")
        )
        del parser

        if not data:
            return

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    all_text = '\n\n'.join([i["text"] for i in data["pages"]])
    all_text = 'ИЗВЕСТИЯ'.join(all_text.split('ИЗВЕСТИЯ')[1:])
    full_prompt = load_prompt().replace("{{content}}", all_text)

    print(len(full_prompt), full_prompt)

    await bot.send_message(
        chat_id=ADMIN_UID,
        text=full_prompt[:2000]
    )

    news = generate_news(all_text)

    print(len(news), news)

    if news:
        await publish(news)


async def main():
    print(datetime.now(), '- Started')
    await job()
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
