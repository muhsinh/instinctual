/**
 * Placeholder for the 90s product video. The site spec calls for a styled
 * video frame with "Demo coming soon" rather than a fake video. Once the
 * real recording exists, swap the inner content for a <video> element with
 * proper poster, captions, and reduced-motion handling.
 */

export function DemoSection() {
  return (
    <section id="demo" className="section" aria-labelledby="demo-heading">
      <div className="container-page">
        <header
          style={{
            maxWidth: "44ch",
            marginBottom: "clamp(2rem, 5vw, 3.5rem)",
          }}
        >
          <p className="eyebrow" style={{ marginBottom: 12 }}>See it</p>
          <h2
            id="demo-heading"
            className="headline"
            style={{ fontSize: "clamp(1.875rem, 4vw, 3rem)", margin: 0 }}
          >
            Ninety seconds. One real meeting. One working tool at the end.
          </h2>
        </header>

        <div
          style={{
            position: "relative",
            aspectRatio: "16 / 9",
            background:
              "linear-gradient(180deg, var(--bg-elevated) 0%, var(--bg-elevated-2) 100%)",
            border: "1px solid var(--border-default)",
            borderRadius: "var(--radius-xl)",
            overflow: "hidden",
            boxShadow: "var(--shadow-lg)",
          }}
          aria-label="Product demo video — coming soon"
        >
          {/* Faint ambient glow inside the frame */}
          <div
            aria-hidden
            style={{
              position: "absolute",
              inset: 0,
              background:
                "radial-gradient(ellipse at 50% 60%, rgba(255, 99, 99, 0.08) 0%, transparent 60%)",
            }}
          />

          {/* Centered "play" placeholder */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 14,
              color: "var(--fg-secondary)",
            }}
          >
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: "var(--radius-full)",
                background: "var(--bg-elevated-3)",
                border: "1px solid var(--border-strong)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "var(--shadow-md)",
              }}
            >
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden>
                <path
                  d="M7 5l11 6-11 6V5z"
                  fill="var(--fg-primary)"
                  fillOpacity="0.85"
                />
              </svg>
            </div>
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "var(--text-xs)",
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                color: "var(--fg-tertiary)",
              }}
            >
              Demo coming soon
            </span>
            <span
              style={{
                fontSize: "var(--text-sm)",
                color: "var(--fg-secondary)",
                maxWidth: "32ch",
                textAlign: "center",
                marginInline: "auto",
                paddingInline: "1.5rem",
              }}
            >
              Try the live interactive demo above for now.
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
