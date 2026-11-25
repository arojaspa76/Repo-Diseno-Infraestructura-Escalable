// Cliente mínimo del backend. Importante (seguridad): el texto del modelo se muestra SIEMPRE
// como texto plano en React (nunca con dangerouslySetInnerHTML) para evitar XSS por salidas del LLM.

export interface Metrics {
  model: string;
  ttft_ms: number | null;
  tpot_ms: number | null;
  total_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  decode_tokens_per_s: number | null;
  prompt_eval_ms: number | null;
  load_ms: number | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface StreamHandlers {
  onToken: (text: string) => void;
  onMetrics: (m: Metrics) => void;
  onError: (message: string) => void;
}

function headers(apiKey: string): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (apiKey) h["X-API-Key"] = apiKey;
  return h;
}

async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json();
    const d = body.detail;
    if (typeof d === "string") return d;
    if (d?.reasons) return `Bloqueado por guardrail: ${d.reasons.join("; ")}`;
    return JSON.stringify(d ?? body);
  } catch {
    return `HTTP ${res.status}`;
  }
}

/** Consume SSE sobre POST (EventSource solo soporta GET, por eso se usa fetch + ReadableStream). */
export async function streamChat(
  messages: ChatMessage[],
  opts: { apiKey: string; model?: string; maxTokens: number; signal?: AbortSignal },
  h: StreamHandlers,
): Promise<void> {
  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers: headers(opts.apiKey),
    body: JSON.stringify({ messages, model: opts.model || undefined, max_tokens: opts.maxTokens }),
    signal: opts.signal,
  });
  if (!res.ok || !res.body) {
    h.onError(await errorMessage(res));
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      let event = "message";
      let data = "";
      for (const line of raw.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7);
        else if (line.startsWith("data: ")) data += line.slice(6);
      }
      if (!data) continue;
      const parsed = JSON.parse(data);
      if (event === "token") h.onToken(parsed.text);
      else if (event === "metrics") h.onMetrics(parsed as Metrics);
      else if (event === "error") h.onError(parsed.message);
    }
  }
}

export async function getJson<T>(path: string, apiKey: string): Promise<T> {
  const res = await fetch(path, { headers: headers(apiKey) });
  if (!res.ok) throw new Error(await errorMessage(res));
  return (await res.json()) as T;
}

export async function postJson<T>(path: string, body: unknown, apiKey: string): Promise<T> {
  const res = await fetch(path, { method: "POST", headers: headers(apiKey), body: JSON.stringify(body) });
  if (!res.ok) throw new Error(await errorMessage(res));
  return (await res.json()) as T;
}
