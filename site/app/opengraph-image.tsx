import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "Instinctual — Your meetings should ship products, not tickets.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/**
 * OG image generator. Renders a static-feeling OG card with the wordmark,
 * tagline, and a hint of the menu bar mock. No external assets — uses
 * system fonts and inline SVG.
 */
export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background:
            "radial-gradient(ellipse 80% 50% at 50% 0%, rgba(255, 99, 99, 0.10) 0%, transparent 60%), #0c0a09",
          color: "#f5f3f0",
          padding: "80px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          fontFamily: "system-ui, -apple-system, sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 16,
            fontSize: 36,
            fontWeight: 500,
            letterSpacing: "-0.035em",
          }}
        >
          {/* Mini icon */}
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: "transparent",
              border: "2px solid rgba(245, 243, 240, 0.7)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: 999,
                background: "#ff6363",
                boxShadow: "0 0 16px rgba(255, 99, 99, 0.6)",
              }}
            />
          </div>
          Instinctual
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div
            style={{
              fontSize: 80,
              fontWeight: 500,
              letterSpacing: "-0.04em",
              lineHeight: 1.05,
              maxWidth: 980,
              color: "#f5f3f0",
            }}
          >
            Your meetings should ship products, not tickets.
          </div>
          <div
            style={{
              fontSize: 28,
              color: "#a8a39c",
              maxWidth: 800,
              letterSpacing: "-0.005em",
              lineHeight: 1.35,
            }}
          >
            A macOS menu bar app that listens to your meetings and builds the
            thing you’re talking about while you’re still talking about it.
          </div>
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            color: "#6b6660",
            fontSize: 22,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}
        >
          <span>instinctual.app</span>
          <span>Now in private beta</span>
        </div>
      </div>
    ),
    { ...size },
  );
}
