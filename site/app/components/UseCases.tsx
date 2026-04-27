/**
 * Three role-targeted cards. Each: role label, one-sentence pain,
 * one-sentence solution. The cards are not equal-weighted in copy length —
 * deliberately. Real customer pitches are uneven; pretending they're
 * symmetric reads as marketing slop.
 */

const CASES = [
  {
    role: "PMs and TPMs",
    pain: "You spend 15 hours a week in meetings that produce backlogs of follow-up work.",
    solution: "Instinctual turns that backlog into ready-to-review drafts before the meeting ends.",
  },
  {
    role: "Engineering leads",
    pain: "Your team agrees on something in standup, then spends two days re-scoping it before anyone writes code.",
    solution: "Instinctual captures the agreement as the meeting happens, in a form your engineers can act on.",
  },
  {
    role: "Founders and execs",
    pain: "You make decisions in calls that get half-remembered and three-quarters-implemented.",
    solution: "Instinctual keeps the lineage from “we said this” to “this is what got built.”",
  },
];

export function UseCases() {
  return (
    <section id="use-cases" className="section" aria-labelledby="usecases-heading">
      <div className="container-page">
        <header style={{ maxWidth: "44ch", marginBottom: "clamp(2.5rem, 6vw, 4rem)" }}>
          <p className="eyebrow" style={{ marginBottom: 12 }}>For</p>
          <h2
            id="usecases-heading"
            className="headline"
            style={{ fontSize: "clamp(1.875rem, 4vw, 3rem)", margin: 0 }}
          >
            Built for teams with AI budget but no AI integration discipline.
          </h2>
        </header>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 280px), 1fr))",
            gap: "clamp(1rem, 2.5vw, 2rem)",
          }}
        >
          {CASES.map((c) => (
            <article
              key={c.role}
              className="surface"
              style={{
                padding: "1.75rem 1.5rem 2rem",
                display: "flex",
                flexDirection: "column",
                gap: 14,
              }}
            >
              <h3
                style={{
                  fontSize: "var(--text-base)",
                  fontWeight: 500,
                  letterSpacing: "-0.012em",
                  color: "var(--fg-primary)",
                  margin: 0,
                  paddingBottom: 12,
                  borderBottom: "1px solid var(--border-subtle)",
                }}
              >
                {c.role}
              </h3>
              <p
                style={{
                  fontSize: "var(--text-sm)",
                  lineHeight: 1.6,
                  color: "var(--fg-tertiary)",
                  margin: 0,
                  letterSpacing: "-0.005em",
                }}
              >
                {c.pain}
              </p>
              <p
                style={{
                  fontSize: "var(--text-base)",
                  lineHeight: 1.55,
                  color: "var(--fg-primary)",
                  margin: 0,
                  letterSpacing: "-0.012em",
                }}
              >
                {c.solution}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
