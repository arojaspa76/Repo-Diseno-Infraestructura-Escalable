import { useRef, useState } from "react";
import { streamChat, type ChatMessage, type Metrics } from "../api";

function fmt(v: number | null | undefined, unit = "ms"): string {
  return v == null ? "—" : `${v.toFixed(1)} ${unit}`;
}

export default function ChatPanel({ apiKey }: { apiKey: string }) {
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [lastMetrics, setLastMetrics] = useState<Metrics | null>(null);
  const [input, setInput] = useState("Explica con una analogía qué es el KV cache en un LLM.");
  const [model, setModel] = useState("");
  const [maxTokens, setMaxTokens] = useState(200);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  async function send() {
    if (!input.trim() || busy) return;
    const next: ChatMessage[] = [...history, { role: "user", content: input }, { role: "assistant", content: "" }];
    setHistory(next);
    setInput("");
    setBusy(true);
    setError(null);
    setLastMetrics(null);
    abortRef.current = new AbortController();
    try {
      await streamChat(
        next.slice(0, -1),
        { apiKey, model, maxTokens, signal: abortRef.current.signal },
        {
          onToken: (t) =>
            setHistory((h) => {
              const copy = [...h];
              const last = copy[copy.length - 1];
              copy[copy.length - 1] = { ...last, content: last.content + t };
              return copy;
            }),
          onMetrics: setLastMetrics,
          onError: setError,
        },
      );
    } catch (e) {
      if ((e as Error).name !== "AbortError") setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <p className="explain">
        Cada respuesta llega <b>token a token</b> (streaming). Observe que el primer texto aparece mucho antes de que
        termine la respuesta: eso es la latencia <i>percibida</i>. Abajo se muestran las métricas reales medidas por el
        servidor.
      </p>
      <div className="row">
        <label>
          Modelo (vacío = por defecto)
          <input value={model} onChange={(e) => setModel(e.target.value)} placeholder="llama3.2:1b" />
        </label>
        <label>
          Máx. tokens de salida
          <input type="number" min={1} max={512} value={maxTokens} onChange={(e) => setMaxTokens(Number(e.target.value))} />
        </label>
      </div>
      <div className="chat">
        {history.length === 0 && <em>Escriba una pregunta para comenzar.</em>}
        {history.map((m, i) => (
          // Texto plano: React escapa el contenido; nunca se inyecta HTML del modelo.
          <div key={i} className={`bubble ${m.role}`}>
            <strong>{m.role === "user" ? "Usted" : "Modelo"}</strong>
            <div style={{ whiteSpace: "pre-wrap" }}>{m.content || (busy ? "…" : "")}</div>
          </div>
        ))}
      </div>
      {error && <div className="error">{error}</div>}
      <div className="row">
        <textarea rows={2} value={input} onChange={(e) => setInput(e.target.value)} />
        <button onClick={send} disabled={busy}>
          {busy ? "Generando…" : "Enviar"}
        </button>
        {busy && <button className="secondary" onClick={() => abortRef.current?.abort()}>Cancelar</button>}
      </div>
      {lastMetrics && (
        <div className="cards">
          <Card title="TTFT" value={fmt(lastMetrics.ttft_ms)} help="Tiempo hasta el primer token (cola + carga + prefill)" />
          <Card title="TPOT" value={fmt(lastMetrics.tpot_ms)} help="Tiempo medio por token en la fase decode" />
          <Card title="Decode" value={fmt(lastMetrics.decode_tokens_per_s, "tok/s")} help="Velocidad de generación" />
          <Card title="Total" value={fmt(lastMetrics.total_ms)} help="Latencia extremo a extremo" />
          <Card title="Prefill" value={fmt(lastMetrics.prompt_eval_ms)} help={`${lastMetrics.prompt_tokens} tokens de prompt`} />
          <Card title="Carga del modelo" value={fmt(lastMetrics.load_ms)} help="Solo > 0 en un arranque en frío" />
        </div>
      )}
    </section>
  );
}

function Card({ title, value, help }: { title: string; value: string; help: string }) {
  return (
    <div className="card" title={help}>
      <div className="card-title">{title}</div>
      <div className="card-value">{value}</div>
      <div className="card-help">{help}</div>
    </div>
  );
}
