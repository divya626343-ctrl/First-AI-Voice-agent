# Voice Agent

A local demo of a hands-free voice assistant. You speak, it listens, thinks, and answers out loud, while a chat panel shows the conversation and an audio-reactive orb shows what the agent is doing.

The pipeline is built by hand, with no orchestration framework:

```
Mic -> VAD -> STT -> LLM -> TTS -> Speaker
```

## Project structure

```
voice-agent/
├── requirements.txt       # backend Python dependencies
├── README.md
├── backend/
│   ├── main.py            # FastAPI app and /ws endpoint
│   ├── agent.py           # listen -> stt -> llm -> tts loop
│   ├── stt.py             # mic capture, VAD, Google STT
│   ├── llm.py             # LLM call and conversation history
│   ├── tts.py             # ElevenLabs streaming, mock mode
│   ├── config.py          # settings
│   └── .env               # API keys (you create this)
└── frontend/
    ├── package.json
    └── src/               # React app: chat panel, orb, WebSocket hook
```

## Setup

### 1. Prerequisites

- Python 3.10+ and Node.js 18+
- A working microphone, and headphones (prevents the agent hearing itself)
- A free [Groq](https://console.groq.com) API key (or any OpenAI-compatible provider)
- An [ElevenLabs](https://elevenlabs.io) API key (the free tier is enough for a demo)

### 2. Python dependencies

`requirements.txt` sits in the project root, outside `backend/` and `frontend/`:

```
SpeechRecognition
pyaudio
openai
elevenlabs
python-dotenv
sounddevice
fastapi
uvicorn[standard]
websockets
```

If `pyaudio` fails to install, use a prebuilt wheel for your Python version (common on Windows).

### 3. API keys

Create `backend/.env`:

```
GROQ_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
LLM_MODEL=openai/gpt-oss-120b
MOCK_TTS=true
```

- Keep `MOCK_TTS=true` while developing (a beep instead of a voice, no credits used). Set it to `false` to hear the real voice.
- If the model name is rejected, check Groq's current model list.

## Run the project

From the project root:

```bash
# 1. install backend dependencies (once)
pip install -r requirements.txt

# 2. start the backend (terminal 1
uvicorn backend.main:app --port 8000

# 3. start the frontend (terminal 2)
cd frontend
npm install        # first time only
npm run dev
```

Open the URL Vite prints, click **Start conversation**, and speak. Click **Stop** to end it.

### Test each stage on its own

Run these from `backend/`:

```bash
python stt.py    # speak, see the transcript
python llm.py    # type, get a reply
python tts.py    # hear a beep (mock) or the real voice
```

## How it works

```
                 Python backend (runs locally)                       Browser (React)
 ┌──────────────────────────────────────────────────────┐        ┌───────────────────────┐
 │  mic ─► stt.py ─► llm.py ─► tts.py                    │        │  ChatPanel (bubbles)  │
 │          └──────────┴─────────┴──► agent.py (loop)    │        │  Orb (state + volume) │
 │                                      │ emit()         │        │  Web Audio playback   │
 │                                  main.py (FastAPI) ───┼── WebSocket ──► JSON + PCM audio  │
 └──────────────────────────────────────────────────────┘        └───────────────────────┘
```

- **`agent.py` is a conductor.** It only knows the order of the pipeline and reports progress through an `emit` callback, so it has no dependency on WebSockets.
- **One module per stage** (`stt`, `llm`, `tts`), so providers can be swapped without touching the loop.
- **Blocking calls run in threads** (`asyncio.to_thread`) so the server never freezes.
- **Playback handshake:** the browser sends `playback_done` only when audio has really finished, so the agent does not listen to its own voice.
- **The browser only plays audio.** The Python process captures the microphone, which is why this version runs locally

## Tuning

| Setting                       | Where         | Effect                                                                               |
| ----------------------------- | ------------- | ------------------------------------------------------------------------------------ |
| `pause_threshold`           | `stt.py`    | Silence that ends your turn. Raise it if you get cut off, lower it if it feels slow. |
| `timeout`, `phrase_limit` | `stt.py`    | Max wait for speech, and max utterance length.                                       |
| `SYSTEM_PROMPT`             | `config.py` | Persona and answer style.                                                            |
| `MAX_TURNS`                 | `llm.py`    | How much history is kept.                                                            |

## Troubleshooting

| Problem                   | Likely cause                                                         |
| ------------------------- | -------------------------------------------------------------------- |
| Only a beep, no voice     | `MOCK_TTS=true`. Set it to `false` and restart the backend.      |
| "Can't reach the backend" | The backend is not running on port 8000.                             |
| No sound in the browser   | Click Start first, since browsers block audio before a user gesture. |
| Agent hears itself        | Use headphones.                                                      |
| Stop takes a few seconds  | The mic thread finishes its current listen (up to 8 s).              |

## Known limitations

- Local only: the Python process captures the mic.
- No barge-in: you cannot interrupt the agent while it speaks.
- The agent waits for the full LLM reply before speaking.
- One conversation per backend process.
- Free tiers (Google speech, ElevenLabs credits) are limited and change often.

## Scope and experimentation

1. **Stream the LLM and speak sentence by sentence.** Start TTS on the first complete sentence instead of the whole reply. This is the biggest latency win, and worth measuring with per-turn timing logs.
2. **Barge-in.** Keep listening while the agent speaks, cancel TTS and clear the browser's audio queue when the user interrupts, and tag audio with a turn ID so stale chunks never play.
3. **RAG for a brand or business.** Ingest company documents, retrieve per question, and answer in a fixed brand persona, with one collection per brand and a "don't know, hand off to a human" fallback.
4. **3D avatar.** Replace the orb with a Three.js avatar driven by the same `state` and volume inputs, starting with amplitude-based mouth movement before trying viseme lip-sync.

| Meaning                                             |
| --------------------------------------------------- |
| begin or end the loop                               |
| the reply finished playing                          |
| `listening`, `thinking`, `speaking`, `idle` |
| chat bubbles                                        |
| PCM chunks follow                                   |
| raw int16 mono PCM                                  |
| end of this reply's audio                           |
| a turn failed, the loop continues                   |
