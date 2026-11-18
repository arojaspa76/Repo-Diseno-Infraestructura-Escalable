import type { DoneEvent } from "../types";

export default function SecurityPanel({ last }: { last: DoneEvent | null }) {
  const flags = last?.security.flags ?? [];
  return (
    <section className="card">
      <h2>Controles de seguridad</h2>
      {!last ? (
        <p className="muted">Aquí verá qué hizo el gateway con su solicitud.</p>
      ) : (
        <>
          <p>Datos personales redactados: <strong>{last.security.pii_redactions}</strong></p>
          {flags.length === 0 ? (
            <p className="muted">Sin banderas de seguridad.</p>
          ) : (
            <ul>{flags.map((f) => <li key={f}><code>{f}</code></li>)}</ul>
          )}
        </>
      )}
    </section>
  );
}
