import os

import requests

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def LLM_query(full_prompt):
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
