import { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import MetricsPanel from "./components/MetricsPanel";
import CapacityPanel from "./components/CapacityPanel";
import SecurityPanel from "./components/SecurityPanel";

type Tab = "chat" | "metrics" | "capacity" | "security";

const TABS: { id: Tab; label: string; hint: string }[] = [
  { id: "chat", label: "1 · Chat con streaming", hint: "Mide TTFT y TPOT de cada respuesta" },
  { id: "metrics", label: "2 · Métricas del servidor", hint: "Percentiles p50/p95/p99 y cache" },
  { id: "capacity", label: "3 · Calculadora de memoria", hint: "Pesos + KV cache por GPU" },
  { id: "security", label: "4 · Guardrails", hint: "Prompt injection y PII" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("chat");
  const [apiKey, setApiKey] = useState("");

  return (
    <div className="app">
      <header>
        <div>
          <h1>Sesión 7 · Laboratorio de latencia y throughput</h1>
          <p className="sub">Diseño de Infraestructura Escalable para LLMs — Capítulo 4</p>
        </div>
        <label className="apikey">
          API key (opcional)
          <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="solo si el backend la exige" />
        </label>
      </header>
      <nav>
        {TABS.map((t) => (
          <button key={t.id} className={t.id === tab ? "active" : ""} onClick={() => setTab(t.id)} title={t.hint}>
            {t.label}
          </button>
        ))}
      </nav>
      <main>
        {tab === "chat" && <ChatPanel apiKey={apiKey} />}
        {tab === "metrics" && <MetricsPanel apiKey={apiKey} />}
        {tab === "capacity" && <CapacityPanel apiKey={apiKey} />}
        {tab === "security" && <SecurityPanel apiKey={apiKey} />}
      </main>
    </div>
  );
}
