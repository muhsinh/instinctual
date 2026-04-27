import { MenuBarMock } from "./MenuBarMock";
import { Wordmark } from "./Wordmark";

/**
 * Hero — single focal point per scroll position. Copy lives in a compact
 * column at the top of the viewport; the MenuBarMock dominates below it
 * at ~960px max-width (about 65% of a 1440px viewport).
 *
 * The hero takes 100dvh on the first viewport. The mock is sized so it's
 * either fully visible above the fold (on tall viewports) or partially
 * hidden so the scroll cue draws the user down (on shorter viewports).
 *
 * No ambient gradient is rendered here — the page-wide AmbientMesh
 * (Layer A) and CursorMotion (Layer C) provide the background. The mock
 * itself runs Layer B (scroll perspective) internally.
 */

export function Hero() {
  return (
    <header
      className="site-hero"
      style={{
        position: "relative",
        minHeight: "100dvh",
        display: "flex",
        flexDirection: "column",
        alignItems: "stretch",
      }}
    >
      {/* Top nav */}
      <nav
        aria-label="Primary"
        className="site-nav"
        style={{
          padding: "20px clamp(1.25rem, 5vw, 2.5rem)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexShrink: 0,
        }}
      >
        <Wordmark size="md" />
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <a
            href="/memo"
            style={{
              fontSize: "var(--text-sm)",
              color: "var(--fg-secondary)",
              letterSpacing: "-0.01em",
            }}
          >
            Memo
          </a>
          <a
            href="/deck"
            style={{
              fontSize: "var(--text-sm)",
              color: "var(--fg-secondary)",
              letterSpacing: "-0.01em",
            }}
          >
            Deck
          </a>
          <a
            href="#early-access"
            className="btn btn-secondary nav-cta"
            style={{ padding: "0.5rem 0.9rem" }}
          >
            Early access
          </a>
        </div>
      </nav>

      {/* Hero content — single-column vertical layout, mock is the focal point */}
      <div
        className="container-page hero-content"
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          gap: "clamp(2.5rem, 5vh, 4.5rem)",
          paddingBlock: "clamp(2rem, 5vh, 4.5rem)",
        }}
      >
        {/* Compact text column at top — does not compete for attention */}
        <div
          style={{
            width: "100%",
            maxWidth: "min(100%, 880px)",
            minWidth: 0,
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "1.4rem",
          }}
        >
          <span className="pill">
            <span className="pill-dot" />
            Now in private beta
          </span>

          <h1
            className="headline"
            style={{
              fontSize: "clamp(1.625rem, 6.4vw, 4.5rem)",
              margin: 0,
              maxWidth: "14ch",
              width: "100%",
              letterSpacing: "-0.04em",
              lineHeight: 1.04,
            }}
          >
            Your meetings should ship products, not tickets.
          </h1>

          <p
            style={{
              fontSize: "clamp(0.95rem, 1.5vw, 1.2rem)",
              lineHeight: 1.45,
              color: "var(--fg-secondary)",
              maxWidth: "min(100%, 40ch)",
              width: "100%",
              margin: 0,
              letterSpacing: "-0.005em",
              overflowWrap: "anywhere",
            }}
          >
            Instinctual listens to your meetings and builds the thing you’re
            talking about while you’re still talking about it.
          </p>

          <div
            style={{
              display: "flex",
              gap: 12,
              flexWrap: "wrap",
              justifyContent: "center",
              marginTop: "0.4rem",
            }}
          >
            <a href="#early-access" className="btn btn-accent">
              Get early access
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
                <path
                  d="M3 7h8m0 0L7.5 3.5M11 7l-3.5 3.5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </a>
            <a href="#live-demo" className="btn btn-secondary">
              See it in action
            </a>
          </div>
        </div>

        {/* MenuBarMock — the focal point. Sized to dominate the viewport. */}
        <div
          style={{
            width: "100%",
            display: "flex",
            justifyContent: "center",
          }}
        >
          <MenuBarMock />
        </div>
      </div>

      {/* Bottom strip: macOS / quiet credibility line + scroll cue */}
      <div
        className="hero-foot no-print"
        style={{
          padding: "0 clamp(1.25rem, 5vw, 2.5rem) 24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 20,
          flexShrink: 0,
          flexWrap: "wrap",
        }}
      >
        <p
          style={{
            margin: 0,
            fontSize: "var(--text-xs)",
            color: "var(--fg-tertiary)",
            fontFamily: "var(--font-mono)",
            letterSpacing: "0.04em",
            maxWidth: "32ch",
            minWidth: 0,
          }}
        >
          macOS · audio + screen · no bots
        </p>
        <a
          href="#live-demo"
          aria-label="Scroll to live demo"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            fontSize: "var(--text-xs)",
            fontFamily: "var(--font-mono)",
            color: "var(--fg-tertiary)",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}
        >
          Scroll
          <span aria-hidden className="hero-scroll-cue">
            <svg width="14" height="20" viewBox="0 0 14 20" fill="none">
              <rect x="1" y="1" width="12" height="18" rx="6" stroke="currentColor" strokeWidth="1" opacity="0.55" />
              <circle cx="7" cy="6" r="1.4" fill="currentColor" />
            </svg>
          </span>
        </a>
      </div>

      <style>{`
        .hero-scroll-cue circle {
          animation: scrollDot 2.4s var(--ease-in-out) infinite;
        }
        @keyframes scrollDot {
          0%, 100% { transform: translateY(0); opacity: 1; }
          50% { transform: translateY(4px); opacity: 0.4; }
        }
      `}</style>
    </header>
  );
}
