import { useEffect, useState } from "react";
import { getJson, postJson } from "../api";

interface Presets { models: Record<string, unknown>; quantizations: Record<string, number> }
interface Result {
  weights_gb: number; kv_cache_gb: number; kv_cache_per_sequence_gb: number; overhead_gb: number;
  total_gb: number; fits_in_gpu: boolean | null; max_sequences_that_fit: number | null; notes: string[];
}

export default function CapacityPanel({ apiKey }: { apiKey: string }) {
  const [presets, setPresets] = useState<Presets | null>(null);
  const [preset, setPreset] = useState("llama-3.1-8b");
  const [quant, setQuant] = useState("fp16");
  const [context, setContext] = useState(8192);
  const [seqs, setSeqs] = useState(8);
  const [gpu, setGpu] = useState(24);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { getJson<Presets>("/api/capacity/presets", apiKey).then(setPresets).catch((e: Error) => setError(e.message)); }, [apiKey]);

  useEffect(() => {
    postJson<Result>("/api/capacity/estimate", {
      preset, quant, context_tokens: context, concurrent_sequences: seqs, gpu_memory_gb: gpu,
    }, apiKey).then((r) => { setResult(r); setError(null); }).catch((e: Error) => setError(e.message));
  }, [preset, quant, context, seqs, gpu, apiKey]);

  const parts = result ? [
    { name: "Pesos del modelo", v: result.weights_gb, cls: "w" },
    { name: "KV cache", v: result.kv_cache_gb, cls: "kv" },
    { name: "Overhead", v: result.overhead_gb, cls: "oh" },
  ] : [];
  const scale = Math.max(gpu, result?.total_gb ?? 0, 1);

  return (
    <section>
      <p className="explain">
        La memoria de la GPU se reparte entre los <b>pesos</b> (fijos), el <b>KV cache</b> (crece con el contexto y con el número de
        conversaciones simultáneas) y un <b>overhead</b>. Cuando no cabe todo, se reduce el batch, se cuantiza o se agrega hardware.
      </p>
      <div className="row wrap">
        <label>Modelo
          <select value={preset} onChange={(e) => setPreset(e.target.value)}>
            {presets && Object.keys(presets.models).map((k) => <option key={k}>{k}</option>)}
          </select>
        </label>
        <label>Cuantización
          <select value={quant} onChange={(e) => setQuant(e.target.value)}>
            {presets && Object.keys(presets.quantizations).map((k) => <option key={k}>{k}</option>)}
          </select>
        </label>
        <label>Contexto (tokens)<input type="number" min={256} step={256} value={context} onChange={(e) => setContext(Number(e.target.value))} /></label>
        <label>Conversaciones simultáneas<input type="number" min={1} value={seqs} onChange={(e) => setSeqs(Number(e.target.value))} /></label>
        <label>GPU (GB)<input type="number" min={1} value={gpu} onChange={(e) => setGpu(Number(e.target.value))} /></label>
      </div>
      {error && <div className="error">{error}</div>}
      {result && (
        <>
          <div className="stack" title="Uso de memoria frente a la capacidad de la GPU">
            {parts.map((p) => <div key={p.name} className={`seg ${p.cls}`} style={{ width: `${(p.v / scale) * 100}%` }} title={`${p.name}: ${p.v} GB`} />)}
            <div className="gpumark" style={{ left: `${(gpu / scale) * 100}%` }} title={`Capacidad GPU: ${gpu} GB`} />
          </div>
          <ul className="legend">
            {parts.map((p) => <li key={p.name}><span className={`dot ${p.cls}`} /> {p.name}: <b>{p.v.toFixed(2)} GB</b></li>)}
          </ul>
          <div className={`verdict ${result.fits_in_gpu ? "ok" : "bad"}`}>
            Total {result.total_gb.toFixed(2)} GB {result.fits_in_gpu ? "≤" : ">"} {gpu} GB → {result.fits_in_gpu ? "CABE" : "NO CABE"}.
            {" "}KV cache por conversación: {result.kv_cache_per_sequence_gb.toFixed(2)} GB. Máx. conversaciones que caben: <b>{result.max_sequences_that_fit}</b>.
          </div>
          <ul className="notes">{result.notes.map((n) => <li key={n}>{n}</li>)}</ul>
        </>
      )}
    </section>
  );
}
