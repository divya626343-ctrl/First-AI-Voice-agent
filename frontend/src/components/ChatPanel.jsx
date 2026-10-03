import { useEffect, useRef } from "react";

export default function ChatPanel({ messages }) {
  const endRef = useRef(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <section className="chat">
      <header className="chat-header">Conversation</header>
      <div className="chat-list">
        {messages.length === 0 && (
          <p className="empty">Press Start and say something.</p>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`bubble ${m.role}`}>{m.text}</div>
        ))}
        <div ref={endRef} />
      </div>
    </section>
  );
}
