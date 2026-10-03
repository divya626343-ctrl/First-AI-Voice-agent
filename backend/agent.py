import asyncio
import backend.config as config
import backend.stt as stt
import backend.llm as llm
import backend.tts as tts


class ClientGone(Exception):
    """Raised by emit() when the browser has disconnected."""


class VoiceAgent:
    """Runs listen -> stt -> llm -> tts. Knows nothing about WebSockets:
    it only calls emit(dict) for events and emit(bytes) for audio."""

    def __init__(self, emit):
        self.emit = emit
        self._running = False
        self._task = None
        self._greeted = False
        self._playback_done = asyncio.Event()

    
    def start(self):
        self._running = True
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    def stop(self):
        self._running = False
        self._playback_done.set()      

    def playback_done(self):
        self._playback_done.set()

    # --- main loop ---
    async def _loop(self):
        try:
            if not self._greeted:
                self._greeted = True
                await self._greet()
            while self._running:
                try:
                    await self._turn()
                except ClientGone:
                    break
                except Exception as e:    
                    print("Turn error:", e)
                    await self.emit({"type": "error", "message": str(e)})
        except ClientGone:
            pass
        finally:
            try:
                await self.emit({"type": "state", "state": "idle"})
            except ClientGone:
                pass

    async def _turn(self):
        await self.emit({"type": "state", "state": "listening"})
        text = await asyncio.to_thread(stt.listen_and_transcribe)   
        if not self._running or not text:
            return                                                  

        await self.emit({"type": "transcript", "role": "user", "text": text})
        await self.emit({"type": "state", "state": "thinking"})
        reply = await asyncio.to_thread(llm.reply, text)            
        await self.emit({"type": "transcript", "role": "bot", "text": reply})

        await self._speak(reply)

    async def _greet(self):
        text = config.GREETING
        llm.add_bot_message(text)
        await self.emit({"type": "transcript", "role": "bot", "text": text})
        await self._speak(text, cached=True)

    async def _speak(self, text, cached=False):
        self._playback_done.clear()
        await self.emit({"type": "state", "state": "speaking"})
        await self.emit({"type": "audio_start", "sample_rate": tts.SAMPLE_RATE})

        gen = (tts.synthesize_cached if cached else tts.synthesize)(text)
        total = 0
        while self._running:
            chunk = await asyncio.to_thread(next, gen, None)
            if chunk is None:
                break
            total += len(chunk)
            await self.emit(chunk)
        await self.emit({"type": "audio_end"})
        print(f"Sent {total} bytes of audio")

        try:
            await asyncio.wait_for(self._playback_done.wait(), timeout=30)
        except asyncio.TimeoutError:
            pass