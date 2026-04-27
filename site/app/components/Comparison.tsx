/**
 * What's different — vs note-takers, vs agent builders, vs doing nothing.
 * Honest, named competitors. Real differences. No marketing slop where
 * we pretend we're 5x better at everything.
 */

type Row = { label: string; instinct: string; noteTakers: string; agentBuilders: string; doingNothing: string };

const ROWS: Row[] = [
  {
    label: "Input",
    instinct: "Live meeting + screen",
    noteTakers: "Live meeting (audio)",
    agentBuilders: "Typed prompt",
    doingNothing: "Whatever you remember",
  },
  {
    label: "Output",
    instinct: "Working tool, deployed",
    noteTakers: "Notes / summary",
    agentBuilders: "App from typed brief",
    doingNothing: "A backlog ticket",
  },
  {
    label: "Latency",
    instinct: "Same meeting",
    noteTakers: "Same meeting",
    agentBuilders: "Minutes after typing",
    doingNothing: "Days, sometimes weeks",
  },
  {
    label: "Context cost",
    instinct: "Zero — they're already in the meeting",
    noteTakers: "Zero",
    agentBuilders: "You re-explain everything",
    doingNothing: "Re-explain in every standup",
  },
];

type Col = { key: keyof Omit<Row, "label">; label: string; sub?: string; accent?: boolean };

const COLS: Col[] = [
  { key: "instinct", label: "Instinctual", accent: true },
  { key: "noteTakers", label: "Note-takers", sub: "Granola, Otter, Fellow" },
  { key: "agentBuilders", label: "Agent builders", sub: "Cursor, Replit, Lovable" },
  { key: "doingNothing", label: "Doing nothing", sub: "Status quo" },
];

export function Comparison() {
  return (
    <section id="different" className="section" aria-labelledby="comparison-heading">
      <div className="container-page">
        <header style={{ maxWidth: "44ch", marginBottom: "clamp(2.5rem, 6vw, 4rem)" }}>
          <p className="eyebrow" style={{ marginBottom: 12 }}>What's different</p>
          <h2
            id="comparison-heading"
            className="headline"
            style={{ fontSize: "clamp(1.875rem, 4vw, 3rem)", margin: 0 }}
          >
            Note-takers stop at notes. Agent builders need a prompt. Instinctual does both — from the meeting.
          </h2>
        </header>

        {/* Desktop: real table. Mobile: stacked cards. */}
        <div className="comparison-wrap">
          <table className="comparison-table" aria-describedby="comparison-heading">
            <thead>
              <tr>
                <th scope="col" />
                {COLS.map((c) => (
                  <th key={c.key} scope="col" data-accent={c.accent ? "true" : undefined}>
                    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
                      <span style={{ fontWeight: 600, color: c.accent ? "var(--fg-primary)" : "var(--fg-secondary)" }}>
                        {c.label}
                      </span>
                      {c.sub && (
                        <span
                          style={{
                            fontSize: "var(--text-xs)",
                            color: "var(--fg-tertiary)",
                            fontFamily: "var(--font-mono)",
                            letterSpacing: 0,
                            textTransform: "none",
                            fontWeight: 400,
                          }}
                        >
                          {c.sub}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map((r) => (
                <tr key={r.label}>
                  <th scope="row">{r.label}</th>
                  {COLS.map((c) => (
                    <td key={c.key} data-accent={c.accent ? "true" : undefined}>
                      {r[c.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <style>{`
        .comparison-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; border-radius: var(--radius-xl); border: 1px solid var(--border-default); background: var(--bg-elevated); }
        .comparison-table { width: 100%; min-width: 720px; border-collapse: separate; border-spacing: 0; font-size: var(--text-sm); table-layout: fixed; }
        .comparison-table thead th { text-align: left; padding: 1.25rem 1.1rem 0.85rem; vertical-align: bottom; font-weight: 500; font-size: var(--text-xs); letter-spacing: 0.12em; text-transform: uppercase; color: var(--fg-tertiary); border-bottom: 1px solid var(--border-default); background: var(--bg-elevated-2); }
        .comparison-table thead th[data-accent] { background: linear-gradient(180deg, rgba(255, 99, 99, 0.08), rgba(255, 99, 99, 0.02)); border-bottom-color: rgba(255, 99, 99, 0.35); }
        .comparison-table tbody th { text-align: left; padding: 1.05rem 1.1rem; font-weight: 500; color: var(--fg-tertiary); font-size: var(--text-xs); text-transform: uppercase; letter-spacing: 0.08em; border-bottom: 1px solid var(--border-subtle); width: 22%; }
        .comparison-table tbody td { padding: 1.05rem 1.1rem; color: var(--fg-secondary); border-bottom: 1px solid var(--border-subtle); letter-spacing: -0.005em; vertical-align: top; }
        .comparison-table tbody td[data-accent] { color: var(--fg-primary); background: rgba(255, 99, 99, 0.04); font-weight: 500; }
        .comparison-table tbody tr:last-child th, .comparison-table tbody tr:last-child td { border-bottom: none; }
      `}</style>
    </section>
  );
}
