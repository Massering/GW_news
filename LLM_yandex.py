import os
import requests

# Для YandexGPT (нужно добавить в переменные окружения)
YANDEX_API_KEY = os.getenv("YANDEX_API_KEY")  # IAM-токен или API-ключ
YANDEX_FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")  # ID каталога в Yandex Cloud


def LLM_query_yandex(full_prompt):
    """
    Функция с интерфейсом, аналогичным LLM_query для DeepSeek,
    но использующая YandexGPT API.
    """
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",  # или f"Bearer {YANDEX_API_KEY}" для IAM-токена
        "Content-Type": "application/json",
    }

    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": 2000
        },
        "messages": [
            {
                "role": "user",
                "text": full_prompt
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    try:
        return data["result"]["alternatives"][0]["message"]["text"]
    except Exception:
        print("YandexGPT error:", data)
        return None


# Альтернативная версия с поддержкой разных моделей YandexGPT
def LLM_query_yandex_advanced(full_prompt, model="yandexgpt-lite", temperature=0.7):
    """
    model: "yandexgpt-lite" (быстрая) или "yandexgpt" (более мощная)
    """
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    headers = {
        "Authorization": f"Api-Key {YANDEX_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{model}",
        "completionOptions": {
            "stream": False,
            "temperature": temperature,
            "maxTokens": 2000
        },
        "messages": [
            {
                "role": "user",
                "text": full_prompt
            }
        ]
    }

    response = requests.post(url, headers=headers, json=payload)
    data = response.json()

    try:
        return data["result"]["alternatives"][0]["message"]["text"]
    except Exception:
        print("YandexGPT error:", data)
        return None


# Пример использования
if __name__ == "__main__":
    test_prompt = "Напиши короткую новость о том, что курс доллара упал ниже 70 рублей"

    # Для YandexGPT
    result_yandex = LLM_query_yandex(test_prompt)
    print("YandexGPT ответ:", result_yandex)
