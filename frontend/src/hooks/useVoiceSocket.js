import { useRef, useState, useCallback, useEffect } from "react";

const WS_URL = "ws://localhost:8000/ws";

export function useVoiceSocket() {
  const [status, setStatus] = useState("disconnected"); // disconnected | connecting | connected
  const [agentState, setAgentState] = useState("idle"); // idle | listening | thinking | speaking
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const ctxRef = useRef(null);
  const analyserRef = useRef(null);
  const dataRef = useRef(null);
  const sourcesRef = useRef([]);
  const nextTimeRef = useRef(0);
  const rateRef = useRef(24000);

  const send = (obj) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
  };

  // Schedule each PCM chunk right after the previous one, so playback is seamless
  const playChunk = (buffer) => {
    const ctx = ctxRef.current;
    if (!ctx) return;
    const int16 = new Int16Array(buffer);
    const buf = ctx.createBuffer(1, int16.length, rateRef.current);
    const ch = buf.getChannelData(0);
    for (let i = 0; i < int16.length; i++) ch[i] = int16[i] / 32768;

    const src = ctx.createBufferSource();
    src.buffer = buf;
    src.connect(analyserRef.current); // analyser -> speakers
    src.onended = () => {
      sourcesRef.current = sourcesRef.current.filter((s) => s !== src);
    };
    nextTimeRef.current = Math.max(nextTimeRef.current, ctx.currentTime);
    src.start(nextTimeRef.current);
    nextTimeRef.current += buf.duration;
    sourcesRef.current.push(src);
  };

  // Tell the server only when audio has actually finished playing
  const finishPlayback = () => {
    const last = sourcesRef.current[sourcesRef.current.length - 1];
    if (!last) return send({ type: "playback_done" });
    last.onended = () => {
      sourcesRef.current = [];
      send({ type: "playback_done" });
    };
  };

  const stop = useCallback(() => {
    send({ type: "stop" });
    const ws = wsRef.current;
    wsRef.current = null;
    ws?.close();
    sourcesRef.current.forEach((s) => { try { s.stop(); } catch {} });
    sourcesRef.current = [];
    ctxRef.current?.close();
    ctxRef.current = null;
    analyserRef.current = null;
    setStatus("disconnected");
    setAgentState("idle");
  }, []);

  const start = useCallback(async () => {
    if (wsRef.current) return;
    setStatus("connecting");
    setError(null);
    setMessages([]);

    // Must happen inside the click handler, or the browser blocks audio
    const ctx = new AudioContext();
    await ctx.resume();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 512;
    analyser.connect(ctx.destination);
    ctxRef.current = ctx;
    analyserRef.current = analyser;
    dataRef.current = new Uint8Array(analyser.fftSize);
    nextTimeRef.current = 0;

    const ws = new WebSocket(WS_URL);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus("connected");
      send({ type: "start" });
    };
    ws.onmessage = (e) => {
      if (typeof e.data !== "string") return playChunk(e.data); // binary = audio
      const msg = JSON.parse(e.data);
      switch (msg.type) {
        case "state":
          setAgentState(msg.state);
          break;
        case "transcript":
          setMessages((m) => [...m, { id: crypto.randomUUID(), role: msg.role, text: msg.text }]);
          break;
        case "audio_start":
          rateRef.current = msg.sample_rate;
          break;
        case "audio_end":
          finishPlayback();
          break;
        case "error":
          setError(msg.message);
          break;
      }
    };
    ws.onerror = () => setError("Can't reach the backend on port 8000");
    ws.onclose = () => { if (wsRef.current === ws) stop(); };
  }, [stop]);

  // Current loudness of whatever is playing, 0..~0.5
  const getLevel = useCallback(() => {
    const a = analyserRef.current;
    const d = dataRef.current;
    if (!a || !d) return 0;
    a.getByteTimeDomainData(d);
    let sum = 0;
    for (const v of d) { const x = (v - 128) / 128; sum += x * x; }
    return Math.sqrt(sum / d.length);
  }, []);

  useEffect(() => stop, [stop]); // clean up on unmount

  return { status, agentState, messages, error, start, stop, getLevel };
}
