export interface Usage { prompt_tokens: number; completion_tokens: number; total_tokens: number }
export interface Cost { shadow_api_usd: number; selfhosted_usd: number }
export interface Latency { total_s: number; ttft_s: number | null; tokens_per_s: number | null }
export interface Budget {
  spent_usd: number; limit_usd: number; percent_used: number;
  alert_level: number | null; blocked: boolean;
}
export interface Security { pii_redactions: number; flags: string[] }

export interface DoneEvent {
  type: "done"; request_id: string; content: string;
  usage: Usage; cost: Cost; latency: Latency; budget: Budget; security: Security;
}
export type StreamEvent =
  | { type: "token"; text: string }
  | DoneEvent
  | { type: "error"; code: string; request_id?: string };

export interface ChatTurn { role: "user" | "assistant"; content: string }
