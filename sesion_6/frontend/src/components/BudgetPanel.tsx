import { budgetTone, formatUsd } from "../lib";
import type { Budget } from "../types";

export default function BudgetPanel({ budget }: { budget: Budget | null }) {
  if (!budget) return <section className="card"><h2>Presupuesto diario</h2><p className="muted">Sin datos aún.</p></section>;
  const pct = Math.min(budget.percent_used, 100);
  return (
    <section className="card">
      <h2>Presupuesto diario (costo sombra)</h2>
      <div className="bar" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className={`bar-fill ${budgetTone(budget.percent_used)}`} style={{ width: `${pct}%` }} />
      </div>
      <p>
        <strong>{formatUsd(budget.spent_usd)}</strong> de {formatUsd(budget.limit_usd)} ({budget.percent_used.toFixed(1)} %)
      </p>
      {budget.alert_level && <p className="alert">Alerta alcanzada: {budget.alert_level} %</p>}
      {budget.blocked && <p className="alert danger">Presupuesto agotado: el gateway rechaza nuevas solicitudes.</p>}
    </section>
  );
}
