import type { StreamEvent } from "./types";

/** Convierte un fragmento NDJSON (posiblemente cortado) en eventos completos. */
export function parseNdjson(buffer: string): { events: StreamEvent[]; rest: string } {
  const lines = buffer.split("\n");
  const rest = lines.pop() ?? ""; // la última línea puede estar incompleta
  const events: StreamEvent[] = [];
  for (const line of lines) {
    if (!line.trim()) continue;
    events.push(JSON.parse(line) as StreamEvent);
  }
  return { events, rest };
}

export function formatUsd(value: number): string {
  if (value === 0) return "$0";
  return value < 0.01 ? `$${value.toFixed(6)}` : `$${value.toFixed(4)}`;
}

export type AlertTone = "ok" | "warn" | "danger";

export function budgetTone(percent: number): AlertTone {
  if (percent >= 80) return "danger";
  if (percent >= 50) return "warn";
  return "ok";
}
