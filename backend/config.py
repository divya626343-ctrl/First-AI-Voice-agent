import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_BASE_URL = "https://api.groq.com/openai/v1"
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
MOCK_TTS = os.getenv("MOCK_TTS", "true").lower() == "true"

SYSTEM_PROMPT = (
    "You are a friendly voice assistant. Reply in 1-3 short sentences. "
    "No markdown, lists, URLs or emojis."
)

GREETING = "Hello, how can I help you today?"
