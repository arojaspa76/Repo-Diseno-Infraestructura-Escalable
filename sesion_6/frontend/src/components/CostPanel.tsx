import { formatUsd } from "../lib";
import type { DoneEvent } from "../types";

export default function CostPanel({ last, totalTokens }: { last: DoneEvent | null; totalTokens: number }) {
  return (
    <section className="card">
      <h2>Última respuesta</h2>
      {!last ? (
        <p className="muted">Envíe un mensaje para ver tokens, costo y latencia.</p>
      ) : (
        <dl>
          <dt>Tokens (entrada / salida)</dt>
          <dd>{last.usage.prompt_tokens} / {last.usage.completion_tokens}</dd>
          <dt>Costo sombra (API administrada)</dt>
          <dd>{formatUsd(last.cost.shadow_api_usd)}</dd>
          <dt>Costo infraestructura propia</dt>
          <dd>{formatUsd(last.cost.selfhosted_usd)}</dd>
          <dt>TTFT</dt>
          <dd>{last.latency.ttft_s?.toFixed(2) ?? "n/d"} s</dd>
          <dt>Latencia total</dt>
          <dd>{last.latency.total_s.toFixed(2)} s</dd>
          <dt>Velocidad de generación</dt>
          <dd>{last.latency.tokens_per_s?.toFixed(1) ?? "n/d"} tok/s</dd>
          <dt>Tokens acumulados en la sesión</dt>
          <dd>{totalTokens}</dd>
        </dl>
      )}
    </section>
  );
}
