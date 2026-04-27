/**
 * The Instinctual wordmark. Title case, tighter than default tracking.
 * The "I" carries a custom accent dot — the same dot used as the menu-bar
 * status indicator and the favicon. It's the one motif that travels across
 * every surface (site, deck, memo, app icon, video close).
 */

type Size = "sm" | "md" | "lg" | "xl";

const SIZES: Record<Size, { fontSize: string; gap: string }> = {
  sm: { fontSize: "1rem", gap: "0.02em" },
  md: { fontSize: "1.5rem", gap: "0.02em" },
  lg: { fontSize: "2.25rem", gap: "0.02em" },
  xl: { fontSize: "4rem", gap: "0.02em" },
};

export function Wordmark({ size = "md", accent = false }: { size?: Size; accent?: boolean }) {
  const { fontSize } = SIZES[size];
  return (
    <span
      aria-label="Instinctual"
      style={{
        fontFamily: "var(--font-display)",
        fontSize,
        fontWeight: 500,
        letterSpacing: "-0.035em",
        color: "var(--fg-primary)",
        display: "inline-flex",
        alignItems: "baseline",
        gap: 0,
      }}
    >
      <span style={{ position: "relative" }}>
        I<span
          aria-hidden
          style={{
            position: "absolute",
            top: "0.18em",
            left: "0.46em",
            width: "0.16em",
            height: "0.16em",
            borderRadius: "999px",
            background: accent ? "var(--accent)" : "var(--fg-primary)",
            boxShadow: accent ? "0 0 0.4em var(--accent-glow)" : "none",
          }}
        />
      </span>
      <span style={{ marginLeft: "-0.04em" }}>nstinctual</span>
    </span>
  );
}
