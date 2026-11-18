import { FormEvent, useRef, useState } from "react";
import type { ChatTurn } from "../types";

interface Props {
  turns: ChatTurn[];
  busy: boolean;
  error: string | null;
  onSend: (text: string) => void;
}

export default function ChatPanel({ turns, busy, error, onSend }: Props) {
  const [text, setText] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  function submit(e: FormEvent) {
    e.preventDefault();
    const t = text.trim();
    if (!t || busy) return;
    onSend(t);
    setText("");
    setTimeout(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), 0);
  }

  return (
    <section className="card chat">
      <h2>Conversación</h2>
      <div className="messages" aria-live="polite">
        {turns.length === 0 && <p className="muted">Pregunte algo sobre FinOps. Pruebe también un intento de inyección de prompt.</p>}
        {turns.map((t, i) => (
          // El contenido se renderiza como TEXTO (React lo escapa): nunca como HTML.
          <div key={i} className={`msg ${t.role}`}>
            <span className="who">{t.role === "user" ? "Usted" : "Asistente"}</span>
            <p>{t.content}</p>
          </div>
        ))}
        <div ref={endRef} />
      </div>
      {error && <p className="alert danger" role="alert">{error}</p>}
      <form onSubmit={submit}>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Escriba su pregunta…" disabled={busy} aria-label="Mensaje" />
        <button type="submit" disabled={busy || !text.trim()}>{busy ? "Generando…" : "Enviar"}</button>
      </form>
    </section>
  );
}
