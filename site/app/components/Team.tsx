/**
 * Team. Single founder, pre-seed, no advisors yet. Honest bio — does not
 * claim funding, advisors, or specific credentials beyond what's verifiable.
 * The bio paragraph is intentionally light on resume-isms; expand only with
 * facts the founder can defend in a call.
 *
 * TODO when you're ready: replace the initials tile with a real photo via
 * <Image src="/team/abdul-hameed.jpg" ... /> in /public/team/.
 */

export function Team() {
  return (
    <section id="team" className="section" aria-labelledby="team-heading">
      <div className="container-narrow">
        <header style={{ marginBottom: "clamp(2rem, 5vw, 3rem)" }}>
          <p className="eyebrow" style={{ marginBottom: 12 }}>Team</p>
          <h2
            id="team-heading"
            className="headline"
            style={{ fontSize: "clamp(1.875rem, 4vw, 2.75rem)", margin: 0 }}
          >
            Built by one founder. Pre-seed. Hiring two.
          </h2>
        </header>

        <article
          className="surface"
          style={{
            padding: "1.75rem",
            display: "grid",
            gridTemplateColumns: "auto 1fr",
            gap: "1.5rem",
            alignItems: "start",
          }}
        >
          {/* Avatar — initials tile until a real photo is added to /public/team/ */}
          <div
            aria-hidden
            style={{
              width: 84,
              height: 84,
              borderRadius: "var(--radius-lg)",
              background: "linear-gradient(135deg, var(--bg-elevated-2), var(--bg-elevated-3))",
              border: "1px solid var(--border-default)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: "var(--font-display)",
              fontSize: "1.75rem",
              fontWeight: 500,
              letterSpacing: "-0.02em",
              color: "var(--fg-secondary)",
            }}
          >
            AH
          </div>

          <div>
            <h3
              style={{
                margin: 0,
                fontSize: "var(--text-xl)",
                fontWeight: 500,
                letterSpacing: "-0.018em",
                color: "var(--fg-primary)",
              }}
            >
              Abdul Hameed
            </h3>
            <p
              style={{
                margin: "4px 0 0",
                fontSize: "var(--text-sm)",
                color: "var(--fg-tertiary)",
                fontFamily: "var(--font-mono)",
                letterSpacing: 0,
              }}
            >
              Founder
            </p>
            <p
              style={{
                marginTop: 14,
                marginBottom: 0,
                fontSize: "var(--text-base)",
                color: "var(--fg-secondary)",
                lineHeight: 1.6,
                letterSpacing: "-0.005em",
              }}
            >
              Building Instinctual because the same meeting kept happening —
              somebody describing a tool they needed, and nobody having time to
              build it. The tool should build itself. Pre-seed and shipping
              from a kitchen table; happy to talk to investors, customers, and
              prospective founding engineers.
            </p>
            <div
              style={{
                marginTop: 18,
                display: "flex",
                gap: 14,
                fontSize: "var(--text-sm)",
                flexWrap: "wrap",
              }}
            >
              <a
                href="mailto:hameed.abdulmuhsin@gmail.com"
                style={{ color: "var(--fg-secondary)" }}
              >
                hameed.abdulmuhsin@gmail.com
              </a>
            </div>
          </div>
        </article>

        <p
          style={{
            marginTop: "2rem",
            fontSize: "var(--text-sm)",
            color: "var(--fg-tertiary)",
            fontFamily: "var(--font-mono)",
            letterSpacing: 0,
          }}
        >
          Hiring · founding engineers (macOS, Python/agents, full-stack) — <a
            href="mailto:hameed.abdulmuhsin@gmail.com?subject=Founding%20engineer"
            style={{ color: "var(--fg-secondary)" }}
          >
            email Abdul
          </a>
        </p>
      </div>
    </section>
  );
}
