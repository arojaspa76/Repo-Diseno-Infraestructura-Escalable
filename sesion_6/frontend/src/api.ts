import { parseNdjson } from "./lib";
import type { Budget, ChatTurn, StreamEvent } from "./types";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

function headers(apiKey: string): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (apiKey) h["X-API-Key"] = apiKey;
  return h;
}

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

async function toApiError(res: Response): Promise<ApiError> {
  try {
    const body = await res.json();
    const e = body.error ?? {};
    return new ApiError(res.status, e.code ?? "error", e.message ?? res.statusText);
  } catch {
    return new ApiError(res.status, "error", res.statusText);
  }
}

export async function getBudget(apiKey: string): Promise<Budget> {
  const res = await fetch(`${BASE}/v1/budget`, { headers: headers(apiKey) });
  if (!res.ok) throw await toApiError(res);
  return res.json();
}

/** Envía la conversación y emite eventos NDJSON a medida que llegan. */
export async function streamChat(
  apiKey: string,
  messages: ChatTurn[],
  onEvent: (ev: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${BASE}/v1/chat/stream`, {
    method: "POST",
    headers: headers(apiKey),
    body: JSON.stringify({ messages }),
    signal,
  });
  if (!res.ok || !res.body) throw await toApiError(res);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const { events, rest } = parseNdjson(buffer);
    buffer = rest;
    events.forEach(onEvent);
  }
}
