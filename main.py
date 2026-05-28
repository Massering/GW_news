import json
import asyncio
import os
import time
import schedule
from datetime import datetime, timedelta
from dotenv import load_dotenv

import telebot
from telebot.types import Message

import LLM_local
import LLM_online
from LLM_local import MAX_INPUT_CHARS
from parser import YandexArchiveParser, YEAR_URLS

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_UID = int(os.getenv("ADMIN_UID"))
PROMPT_FILE = "prompt.txt"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

os.makedirs("Izvestia", exist_ok=True)


def load_prompt():
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return f.read()


def generate_news(text):
    full_prompt = load_prompt().replace("{{content}}", text)

    with open("prompt_generated.txt", "w", encoding="utf-8") as f:
        f.write(full_prompt)

    result = LLM_local.LLM_query(full_prompt)
    return result


def publish(text):
    if text:
        bot.send_message(CHANNEL_ID, text[:4000])


def job():
    try:
        target_date = datetime.now() - timedelta(days=365 * 84 + 25)

        print("target_date:", target_date.strftime("%Y-%m-%d"))

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
                print("Нет данных")
                return

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        all_text = '\n\n'.join([i["text"] for i in data["pages"]])

        if "ИЗВЕСТИЯ" in all_text:
            all_text = 'ИЗВЕСТИЯ'.join(all_text.split('ИЗВЕСТИЯ')[1:])

        full_prompt = load_prompt().replace("{{content}}", all_text)

        print("Prompt length:", len(full_prompt))

        # Отправка админу
        bot.send_message(
            ADMIN_UID,
            full_prompt[:4000]
        )

        news = generate_news(all_text)

        print("News length:", len(news))
        print(news)

        if news:
            publish(news)

    except Exception as e:
        print("ERROR:", e)

        try:
            bot.send_message(
                ADMIN_UID,
                f"Ошибка:\n{e}"
            )
        except:
            pass


# Обработчик сообщений
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_UID)
def admin_messages(message: Message):
    """
    Если пишет админ — публикуем сообщение в канал.
    """

    try:
        if message.text:
            bot.send_message(CHANNEL_ID, message.text)

        elif message.caption:
            # Фото/документы с подписью
            if message.photo:
                bot.send_photo(
                    CHANNEL_ID,
                    message.photo[-1].file_id,
                    caption=message.caption
                )

            elif message.document:
                bot.send_document(
                    CHANNEL_ID,
                    message.document.file_id,
                    caption=message.caption
                )

        elif message.photo:
            bot.send_photo(
                CHANNEL_ID,
                message.photo[-1].file_id
            )

        elif message.document:
            bot.send_document(
                CHANNEL_ID,
                message.document.file_id
            )

        bot.reply_to(message, "Опубликовано.")

    except Exception as e:
        bot.reply_to(message, f"Ошибка:\n{e}")


# Планировщик
def scheduler_loop():
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    print(datetime.now(), "- Started")

    # Каждый день в 09:00
    schedule.every().day.at("09:00").do(job)

    # Можно запустить сразу при старте:
    job()

    # Поток планировщика
    import threading

    scheduler_thread = threading.Thread(target=scheduler_loop)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    # Telegram polling
    bot.infinity_polling()


if __name__ == "__main__":
    main()
