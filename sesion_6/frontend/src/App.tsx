import { useCallback, useEffect, useState } from "react";
import { ApiError, getBudget, streamChat } from "./api";
import BudgetPanel from "./components/BudgetPanel";
import ChatPanel from "./components/ChatPanel";
import CostPanel from "./components/CostPanel";
import SecurityPanel from "./components/SecurityPanel";
import type { Budget, ChatTurn, DoneEvent } from "./types";

export default function App() {
  // La API key vive solo en memoria (no en localStorage) para no persistir secretos.
  const [apiKey, setApiKey] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [last, setLast] = useState<DoneEvent | null>(null);
  const [budget, setBudget] = useState<Budget | null>(null);
  const [totalTokens, setTotalTokens] = useState(0);

  const refreshBudget = useCallback(async () => {
    try {
      setBudget(await getBudget(apiKey));
    } catch {
      setBudget(null);
    }
  }, [apiKey]);

  useEffect(() => {
    void refreshBudget();
  }, [refreshBudget]);

  async function send(text: string) {
    setError(null);
    setBusy(true);
    const history: ChatTurn[] = [...turns, { role: "user", content: text }];
    setTurns([...history, { role: "assistant", content: "" }]);
    try {
      await streamChat(apiKey, history, (ev) => {
        if (ev.type === "token") {
          setTurns((cur) => {
            const copy = [...cur];
            const lastTurn = copy[copy.length - 1];
            copy[copy.length - 1] = { ...lastTurn, content: lastTurn.content + ev.text };
            return copy;
          });
        } else if (ev.type === "done") {
          // Se reemplaza por el texto final ya sanitizado por el servidor.
          setTurns((cur) => {
            const copy = [...cur];
            copy[copy.length - 1] = { role: "assistant", content: ev.content };
            return copy;
          });
          setLast(ev);
          setBudget(ev.budget);
          setTotalTokens((t) => t + ev.usage.total_tokens);
        } else if (ev.type === "error") {
          setError(`Error del servicio (${ev.code}).`);
        }
      });
    } catch (e) {
      setTurns(history); // quita el mensaje vacío del asistente
      setError(e instanceof ApiError ? `${e.code}: ${e.message}` : "No se pudo contactar el gateway.");
      void refreshBudget();
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <header>
        <h1>LLM Gateway · FinOps y Seguridad</h1>
        <label className="key">
          API key (opcional en dev)
          <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} autoComplete="off" />
        </label>
      </header>
      <div className="grid">
        <ChatPanel turns={turns} busy={busy} error={error} onSend={send} />
        <aside>
          <BudgetPanel budget={budget} />
          <CostPanel last={last} totalTokens={totalTokens} />
          <SecurityPanel last={last} />
        </aside>
      </div>
    </main>
  );
}
