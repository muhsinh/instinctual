/**
 * Programmatic mirror of tokens.css. Use these for dynamic styles only —
 * static styles should reference the CSS variables directly so a single
 * source of truth (tokens.css) drives everything.
 */

export const color = {
  bgBase: "var(--bg-base)",
  bgElevated: "var(--bg-elevated)",
  bgElevated2: "var(--bg-elevated-2)",
  bgElevated3: "var(--bg-elevated-3)",
  bgOverlay: "var(--bg-overlay)",

  fgPrimary: "var(--fg-primary)",
  fgSecondary: "var(--fg-secondary)",
  fgTertiary: "var(--fg-tertiary)",
  fgQuaternary: "var(--fg-quaternary)",

  borderSubtle: "var(--border-subtle)",
  borderDefault: "var(--border-default)",
  borderStrong: "var(--border-strong)",

  accent: "var(--accent)",
  accentHover: "var(--accent-hover)",
  accentMuted: "var(--accent-muted)",
  accentGlow: "var(--accent-glow)",
  accentCool: "var(--accent-cool)",

  success: "var(--success)",
  warning: "var(--warning)",
  danger: "var(--danger)",
} as const;

export const font = {
  display: "var(--font-display)",
  body: "var(--font-body)",
  mono: "var(--font-mono)",
} as const;

export const radius = {
  xs: "var(--radius-xs)",
  sm: "var(--radius-sm)",
  md: "var(--radius-md)",
  lg: "var(--radius-lg)",
  xl: "var(--radius-xl)",
  "2xl": "var(--radius-2xl)",
  "3xl": "var(--radius-3xl)",
  full: "var(--radius-full)",
} as const;

export const shadow = {
  xs: "var(--shadow-xs)",
  sm: "var(--shadow-sm)",
  md: "var(--shadow-md)",
  lg: "var(--shadow-lg)",
  panel: "var(--shadow-panel)",
  glow: "var(--shadow-glow)",
} as const;
