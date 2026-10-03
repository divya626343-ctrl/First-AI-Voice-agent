from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from backend.agent import VoiceAgent, ClientGone
import backend.llm as llm

app = FastAPI()


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    llm.history[:] = llm.history[:1]       

    async def emit(msg):
        try:
            if isinstance(msg, bytes):
                await ws.send_bytes(msg)
            else:
                await ws.send_json(msg)
        except Exception as e:
            raise ClientGone() from e

    agent = VoiceAgent(emit)
    try:
        while True:
            msg = await ws.receive_json()
            kind = msg.get("type")
            if kind == "start":
                agent.start()
            elif kind == "stop":
                agent.stop()
            elif kind == "playback_done":
                agent.playback_done()
    except WebSocketDisconnect:
        pass
    finally:
        agent.stop()