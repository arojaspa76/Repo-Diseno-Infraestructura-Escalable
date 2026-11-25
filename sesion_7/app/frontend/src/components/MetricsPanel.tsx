import { useEffect, useState } from "react";
import { getJson } from "../api";

interface Stat { p50: number | null; p95: number | null; p99: number | null; mean: number | null }
interface Summary {
  window_size: number;
  requests_total: number;
  errors_total: number;
  guard_blocked_total: number;
  ttft_ms: Stat;
  tpot_ms: Stat;
  total_ms: Stat;
  decode_tokens_per_s: Stat;
  embedding_cache: { entries: number; hits: number; misses: number; hit_rate: number };
}

const f = (v: number | null) => (v == null ? "—" : v.toFixed(1));

function Bar({ label, stat, unit }: { label: string; stat: Stat; unit: string }) {
  const max = Math.max(stat.p99 ?? 0, stat.p95 ?? 0, stat.p50 ?? 0, 1);
  const row = (name: string, v: number | null) => (
    <div className="barrow">
      <span className="barname">{name}</span>
      <div className="bartrack"><div className="barfill" style={{ width: `${((v ?? 0) / max) * 100}%` }} /></div>
      <span className="barval">{f(v)} {unit}</span>
    </div>
  );
  return (
    <div className="panel">
      <h3>{label}</h3>
      {row("p50", stat.p50)}
      {row("p95", stat.p95)}
      {row("p99", stat.p99)}
    </div>
  );
}

export default function MetricsPanel({ apiKey }: { apiKey: string }) {
  const [data, setData] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () =>
      getJson<Summary>("/api/metrics/summary", apiKey)
        .then((d) => alive && (setData(d), setError(null)))
        .catch((e: Error) => alive && setError(e.message));
    load();
    const id = setInterval(load, 3000);
    return () => { alive = false; clearInterval(id); };
  }, [apiKey]);

  return (
    <section>
      <p className="explain">
        En producción no se mira “el promedio”: se miran <b>percentiles</b>. El p95 indica que el 95 % de las peticiones
        fue más rápido que ese valor; el p99 revela la “cola” de latencias que sufren los usuarios más desafortunados.
        Esta vista se actualiza cada 3 s.
      </p>
      {error && <div className="error">{error}</div>}
      {data && (
        <>
          <div className="cards">
            <div className="card"><div className="card-title">Peticiones</div><div className="card-value">{data.requests_total}</div></div>
            <div className="card"><div className="card-title">Errores</div><div className="card-value">{data.errors_total}</div></div>
            <div className="card"><div className="card-title">Bloqueos guardrail</div><div className="card-value">{data.guard_blocked_total}</div></div>
            <div className="card"><div className="card-title">Cache embeddings</div><div className="card-value">{(data.embedding_cache.hit_rate * 100).toFixed(0)} %</div><div className="card-help">{data.embedding_cache.hits} aciertos / {data.embedding_cache.misses} fallos</div></div>
          </div>
          <div className="grid2">
            <Bar label="TTFT (ms)" stat={data.ttft_ms} unit="ms" />
            <Bar label="TPOT (ms/token)" stat={data.tpot_ms} unit="ms" />
            <Bar label="Latencia total (ms)" stat={data.total_ms} unit="ms" />
            <Bar label="Decode (tokens/s)" stat={data.decode_tokens_per_s} unit="tok/s" />
          </div>
        </>
      )}
    </section>
  );
}
