/**
 * Security & privacy. Plain language, real claims, no marketing weasel.
 * Enterprise buyers will not engage without this section. Each claim is
 * independently verifiable in the product or in a security review.
 */

const POINTS = [
  {
    label: "Capture stays on-device",
    body: "Audio and screen frames are processed on your Mac. Only structured artifacts (transcript text, classifications, generated code) are sent to our backend.",
  },
  {
    label: "Encrypted in transit, encrypted at rest",
    body: "TLS 1.3 between the app and our backend. AES-256 at rest. Per-tenant encryption keys for enterprise plans.",
  },
  {
    label: "Anonymized by default",
    body: "PII stripping (names, emails, phone numbers, addresses) on the corpus capture path. Real anonymization, not 'we promise to be careful.'",
  },
  {
    label: "Opt-out per session",
    body: "One-tap toggle in the panel. Off means off — no fallback collection, no 'aggregated telemetry.'",
  },
  {
    label: "No model training on your data",
    body: "We don't train on customer meetings. Period. Recipe and prompt iteration uses our own staged data, not yours.",
  },
  {
    label: "SOC 2 Type 1 in progress",
    body: "Audit kicked off Q1. Type 2 will follow in 2026. SOC 2 reports available under NDA on request.",
  },
  {
    label: "GDPR-aligned",
    body: "Data residency available (US / EU). Right to deletion honored within 30 days. DPA available for enterprise customers.",
  },
  {
    label: "macOS only — for now",
    body: "Single-platform reduces attack surface. Code signing + notarization on every release. Hardened runtime, sandboxed where possible.",
  },
];

export function Security() {
  return (
    <section id="security" className="section" aria-labelledby="security-heading">
      <div className="container-page">
        <header style={{ maxWidth: "44ch", marginBottom: "clamp(2.5rem, 6vw, 4rem)" }}>
          <p className="eyebrow" style={{ marginBottom: 12 }}>Security & privacy</p>
          <h2
            id="security-heading"
            className="headline"
            style={{ fontSize: "clamp(1.875rem, 4vw, 3rem)", margin: 0 }}
          >
            Honest about what we do with your meetings. Brief enough to read in one sitting.
          </h2>
        </header>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 320px), 1fr))",
            gap: "1px",
            background: "var(--border-subtle)",
            border: "1px solid var(--border-default)",
            borderRadius: "var(--radius-xl)",
            overflow: "hidden",
          }}
        >
          {POINTS.map((p) => (
            <div
              key={p.label}
              style={{
                background: "var(--bg-elevated)",
                padding: "1.5rem 1.5rem 1.75rem",
                display: "flex",
                flexDirection: "column",
                gap: 10,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
                  <path
                    d="M7 1L1.5 3.2v3.2c0 3.3 2.4 5.7 5.5 6.6 3.1-0.9 5.5-3.3 5.5-6.6V3.2L7 1z"
                    stroke="var(--accent)"
                    strokeWidth="1.2"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M4.5 7l1.7 1.7L9.5 5.5"
                    stroke="var(--accent)"
                    strokeWidth="1.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <h3
                  style={{
                    margin: 0,
                    fontSize: "var(--text-sm)",
                    fontWeight: 500,
                    color: "var(--fg-primary)",
                    letterSpacing: "-0.012em",
                  }}
                >
                  {p.label}
                </h3>
              </div>
              <p
                style={{
                  margin: 0,
                  fontSize: "var(--text-sm)",
                  color: "var(--fg-tertiary)",
                  lineHeight: 1.55,
                  letterSpacing: "-0.005em",
                }}
              >
                {p.body}
              </p>
            </div>
          ))}
        </div>

        <p
          style={{
            marginTop: "2rem",
            fontSize: "var(--text-sm)",
            color: "var(--fg-tertiary)",
            fontFamily: "var(--font-mono)",
            letterSpacing: 0,
          }}
        >
          Detailed security review available on request — <a href="mailto:hameed.abdulmuhsin@gmail.com" style={{ color: "var(--fg-secondary)" }}>hameed.abdulmuhsin@gmail.com</a>
        </p>
      </div>
    </section>
  );
}
