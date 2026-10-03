from openai import OpenAI
import backend.config as config

client = OpenAI(api_key = config.GROQ_API_KEY, base_url= config.LLM_BASE_URL)
history = [{"role": "system", "content": config.SYSTEM_PROMPT}]
MAX_TURNS = 10

def add_bot_message(text: str):
    history.append({"role": "assistant", "content": text})

def reply(user_text: str)->str:
    history.append({"role":"user", "content": user_text})
    resp = client.chat.completions.create(model=config.LLM_MODEL, messages=history)
    text = resp.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": text})

    if len(history) > 1 + MAX_TURNS * 2:
        del history[1:3]
    return text

