/**
 * Three tiers. Specific numbers force commercial honesty even if they
 * change later. Free trial / Team / Enterprise.
 */

type Tier = {
  name: string;
  price: string;
  cadence?: string;
  pitch: string;
  features: string[];
  cta: { label: string; href: string };
  highlight?: boolean;
};

const TIERS: Tier[] = [
  {
    name: "Free trial",
    price: "$0",
    cadence: "for 14 days",
    pitch: "Real Instinctual. Three meetings. No commitment.",
    features: [
      "Up to 3 meetings",
      "All artifact archetypes",
      "Per-meeting export",
      "macOS only",
    ],
    cta: { label: "Start free trial", href: "#early-access" },
  },
  {
    name: "Team",
    price: "$48",
    cadence: "per seat / month",
    pitch: "For teams that meet more than they ship — and want that to flip.",
    features: [
      "Unlimited meetings",
      "Team memory layer",
      "Voice fingerprinting",
      "One-click deploy (Vercel, Modal, GitHub Actions)",
      "Slack + Linear integrations",
      "SOC 2 in progress",
    ],
    cta: { label: "Get early access", href: "#early-access" },
    highlight: true,
  },
  {
    name: "Enterprise",
    price: "Talk to us",
    pitch: "Custom contracts. Volume pricing. SSO + audit logs + DPA.",
    features: [
      "Everything in Team",
      "SAML SSO",
      "Audit logs",
      "Data residency (US / EU)",
      "Dedicated onboarding",
      "Quarterly business review",
    ],
    cta: { label: "Contact sales", href: "mailto:hameed.abdulmuhsin@gmail.com?subject=Instinctual%20Enterprise" },
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="section" aria-labelledby="pricing-heading">
      <div className="container-page">
        <header style={{ maxWidth: "44ch", marginBottom: "clamp(2.5rem, 6vw, 4rem)" }}>
          <p className="eyebrow" style={{ marginBottom: 12 }}>Pricing</p>
          <h2
            id="pricing-heading"
            className="headline"
            style={{ fontSize: "clamp(1.875rem, 4vw, 3rem)", margin: 0 }}
          >
            Priced like one engineer-hour saved per seat per week.
          </h2>
        </header>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 280px), 1fr))",
            gap: "clamp(1rem, 2vw, 1.5rem)",
          }}
        >
          {TIERS.map((t) => (
            <article
              key={t.name}
              style={{
                position: "relative",
                padding: "1.75rem 1.5rem 2rem",
                borderRadius: "var(--radius-xl)",
                border: t.highlight ? "1px solid rgba(255, 99, 99, 0.4)" : "1px solid var(--border-default)",
                background: t.highlight
                  ? "linear-gradient(180deg, rgba(255, 99, 99, 0.06) 0%, rgba(255, 99, 99, 0.02) 100%)"
                  : "linear-gradient(180deg, var(--bg-elevated) 0%, var(--bg-elevated-2) 100%)",
                boxShadow: t.highlight ? "0 0 0 1px rgba(255, 99, 99, 0.15), 0 24px 48px rgba(0,0,0,0.4)" : "var(--shadow-md)",
                display: "flex",
                flexDirection: "column",
                gap: 18,
              }}
            >
              {t.highlight && (
                <span
                  style={{
                    position: "absolute",
                    top: 14,
                    right: 14,
                    fontSize: 10,
                    fontWeight: 600,
                    letterSpacing: "0.12em",
                    textTransform: "uppercase",
                    color: "var(--accent)",
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  Recommended
                </span>
              )}
              <div>
                <h3
                  style={{
                    margin: 0,
                    fontSize: "var(--text-base)",
                    fontWeight: 500,
                    color: "var(--fg-primary)",
                    letterSpacing: "-0.012em",
                  }}
                >
                  {t.name}
                </h3>
                <p
                  style={{
                    margin: "10px 0 0",
                    fontSize: "var(--text-sm)",
                    color: "var(--fg-tertiary)",
                    minHeight: "2.4em",
                    letterSpacing: "-0.005em",
                  }}
                >
                  {t.pitch}
                </p>
              </div>
              <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                <span
                  style={{
                    fontSize: "var(--text-4xl)",
                    fontWeight: 500,
                    letterSpacing: "-0.025em",
                    color: "var(--fg-primary)",
                    fontFamily: "var(--font-display)",
                  }}
                >
                  {t.price}
                </span>
                {t.cadence && (
                  <span style={{ fontSize: "var(--text-sm)", color: "var(--fg-tertiary)" }}>
                    {t.cadence}
                  </span>
                )}
              </div>
              <ul
                style={{
                  listStyle: "none",
                  margin: 0,
                  padding: "0.5rem 0 1rem",
                  display: "grid",
                  gap: 10,
                  borderTop: "1px solid var(--border-subtle)",
                  paddingTop: "1.25rem",
                  flexGrow: 1,
                }}
              >
                {t.features.map((f) => (
                  <li
                    key={f}
                    style={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: 10,
                      fontSize: "var(--text-sm)",
                      color: "var(--fg-secondary)",
                      letterSpacing: "-0.005em",
                    }}
                  >
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 14 14"
                      fill="none"
                      style={{ flexShrink: 0, marginTop: 4 }}
                      aria-hidden
                    >
                      <path
                        d="M3 7.5l2.5 2.5L11 4"
                        stroke={t.highlight ? "var(--accent)" : "var(--fg-tertiary)"}
                        strokeWidth="1.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    {f}
                  </li>
                ))}
              </ul>
              <a
                href={t.cta.href}
                className={t.highlight ? "btn btn-accent" : "btn btn-secondary"}
                style={{ marginTop: "auto" }}
              >
                {t.cta.label}
              </a>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
