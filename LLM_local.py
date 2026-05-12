import requests


def LLM_query(full_prompt):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "deepseek-r1:7b",
        "prompt": full_prompt,
        "temperature": 0.7,
        "stream": False
    })

    return response.json()["response"]
