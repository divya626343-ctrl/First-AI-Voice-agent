import { useVoiceSocket } from "./hooks/useVoiceSocket";
import ChatPanel from "./components/ChatPanel";
import Orb from "./components/Orb";

const LABELS = {
  idle: "Ready",
  listening: "Listening...",
  thinking: "Thinking...",
  speaking: "Speaking...",
};

export default function App() {
  const { status, agentState, messages, error, start, stop, getLevel } = useVoiceSocket();
  const connected = status === "connected";
  const state = connected ? agentState : "idle";

  return (
    <div className="app">
      <ChatPanel messages={messages} />
      <section className="stage">
        <Orb state={state} getLevel={getLevel} />
        <p className="status">{status === "connecting" ? "Connecting..." : LABELS[state]}</p>
        {error && <p className="error">{error}</p>}
        {connected ? (
          <button className="btn stop" onClick={stop}>Stop</button>
        ) : (
          <button className="btn start" onClick={start} disabled={status === "connecting"}>
            Start conversation
          </button>
        )}
      </section>
    </div>
  );
}
