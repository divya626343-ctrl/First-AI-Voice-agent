import array, math
import backend.config as config

SAMPLE_RATE = 24000  
cache = {}

def synthesize_cached(text):
    if text not in cache:
        chunks = list(synthesize(text))
        if not chunks:
            return                      # don't cache silence
        cache[text] = chunks
    yield from cache[text]

if not config.MOCK_TTS:
    from elevenlabs.client import ElevenLabs
    client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)


def mock(text):
    """Free stand-in: a soft beep, length based on text, so you can test the UI."""
    seconds = min(0.06 * len(text), 6)
    n = int(SAMPLE_RATE * seconds)
    samples = array.array("h", (
        int(6000 * math.sin(2 * math.pi * 220 * i / SAMPLE_RATE)) for i in range(n)
    ))
    data = samples.tobytes()
    for i in range(0, len(data), 4096):
        yield data[i:i + 4096]


def synthesize(text):
    """Yields raw PCM chunks (int16, mono, 24 kHz)."""
    if config.MOCK_TTS:
        yield from mock(text)
        return

    stream = client.text_to_speech.stream(
        voice_id=config.VOICE_ID,
        model_id="eleven_flash_v2_5",       # cheaper and lower latency
        text=text,
        output_format="pcm_24000",
    )
    leftover = b""
    for chunk in stream:
        if not chunk:
            continue
        chunk = leftover + chunk
        if len(chunk) % 2:                   # keep whole 16-bit samples only
            leftover, chunk = chunk[-1:], chunk[:-1]
        else:
            leftover = b""
        yield chunk


