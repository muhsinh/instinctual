import { Wordmark } from "./Wordmark";

/**
 * Minimal footer. Copyright, contact, social, links to deck/memo.
 * No newsletter sign-up, no logo soup, no gradient sweep.
 */

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer
      style={{
        marginTop: "clamp(4rem, 10vh, 7rem)",
        padding: "clamp(2rem, 5vw, 3.5rem) 0 2.5rem",
        borderTop: "1px solid var(--border-subtle)",
      }}
    >
      <div
        className="container-page"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 220px), 1fr))",
          gap: "2rem",
          alignItems: "start",
        }}
      >
        <div>
          <Wordmark size="md" />
          <p
            style={{
              marginTop: 14,
              maxWidth: "32ch",
              fontSize: "var(--text-sm)",
              color: "var(--fg-tertiary)",
              lineHeight: 1.55,
              letterSpacing: "-0.005em",
            }}
          >
            Instinctual listens to your meetings and builds the thing you’re
            talking about while you’re still talking about it.
          </p>
        </div>

        <FooterColumn label="Product">
          <FooterLink href="#how">How it works</FooterLink>
          <FooterLink href="#demo">Demo</FooterLink>
          <FooterLink href="#early-access">Early access</FooterLink>
          <FooterLink href="#pricing">Pricing</FooterLink>
        </FooterColumn>

        <FooterColumn label="Company">
          <FooterLink href="/memo">Why now / why us</FooterLink>
          <FooterLink href="/deck">Pitch deck</FooterLink>
          <FooterLink href="#security">Security & privacy</FooterLink>
          <FooterLink href="#team">Team</FooterLink>
        </FooterColumn>

        <FooterColumn label="Reach us">
          <FooterLink href="mailto:hameed.abdulmuhsin@gmail.com">hameed.abdulmuhsin@gmail.com</FooterLink>
          <FooterLink href="https://twitter.com/instinctapp" rel="noreferrer noopener" target="_blank">
            Twitter / X
          </FooterLink>
          <FooterLink href="https://github.com/instinct" rel="noreferrer noopener" target="_blank">
            GitHub
          </FooterLink>
          <FooterLink href="https://linkedin.com/company/instinct" rel="noreferrer noopener" target="_blank">
            LinkedIn
          </FooterLink>
        </FooterColumn>
      </div>

      <div
        className="container-page"
        style={{
          marginTop: "clamp(2.5rem, 6vw, 4rem)",
          paddingTop: "1.5rem",
          borderTop: "1px solid var(--border-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 16,
          flexWrap: "wrap",
        }}
      >
        <p
          style={{
            margin: 0,
            fontSize: "var(--text-xs)",
            color: "var(--fg-tertiary)",
            fontFamily: "var(--font-mono)",
            letterSpacing: "0.02em",
          }}
        >
          © {year} Instinctual. macOS only · Private beta.
        </p>
        <div style={{ display: "flex", gap: 18 }}>
          <a
            href="/privacy"
            style={{
              fontSize: "var(--text-xs)",
              color: "var(--fg-tertiary)",
              fontFamily: "var(--font-mono)",
              letterSpacing: "0.02em",
            }}
          >
            Privacy
          </a>
          <a
            href="/terms"
            style={{
              fontSize: "var(--text-xs)",
              color: "var(--fg-tertiary)",
              fontFamily: "var(--font-mono)",
              letterSpacing: "0.02em",
            }}
          >
            Terms
          </a>
        </div>
      </div>
    </footer>
  );
}

function FooterColumn({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p
        style={{
          margin: "0 0 14px",
          fontSize: "var(--text-xs)",
          letterSpacing: "0.12em",
          textTransform: "uppercase",
          color: "var(--fg-tertiary)",
          fontWeight: 500,
        }}
      >
        {label}
      </p>
      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 10 }}>
        {children}
      </ul>
    </div>
  );
}

function FooterLink({
  href,
  children,
  rel,
  target,
}: {
  href: string;
  children: React.ReactNode;
  rel?: string;
  target?: string;
}) {
  return (
    <li>
      <a
        href={href}
        rel={rel}
        target={target}
        style={{
          fontSize: "var(--text-sm)",
          color: "var(--fg-secondary)",
          letterSpacing: "-0.005em",
          transition: "color 150ms ease",
        }}
      >
        {children}
      </a>
    </li>
  );
}
