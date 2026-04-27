"use client";

import { useEffect, useState } from "react";

/**
 * Live spec preview rendered inside the menu bar panel. Content is the actual
 * streamlit_demo fixture from /backend/eval/fixtures/streamlit_demo/fixture.json
 * — same utterances, same ground-truth decisions, same archetype classification
 * the v1 Phase A pipeline uses in eval. The "BuildPlan" structure mirrors
 * StreamlitDashboardBuildPlan in /backend/instinct/recipes/streamlit_dashboard.py
 * (data_sources, charts, filters, layout, references).
 *
 * Animates over ~9s, holds 2.4s, resets. The motion is the entire point —
 * without motion this would be a screenshot of a generic dashboard spec.
 */

type Block =
  | { kind: "meta"; text: string }
  | { kind: "h"; text: string }
  | { kind: "li"; text: string; check?: boolean }
  | { kind: "field"; label: string; value: string }
  | { kind: "code"; text: string }
  | { kind: "ref"; text: string };

const SCRIPT: Block[] = [
  { kind: "meta", text: "streamlit_dashboard · 4 attendees · meeting in progress" },

  { kind: "h", text: "Decision" },
  { kind: "li", text: "Build a Streamlit dashboard for the activation funnel", check: true },
  { kind: "li", text: "Source data from the Postgres replica", check: true },
  { kind: "li", text: "A is the owner; draft by end of week", check: true },

  { kind: "h", text: "Charts" },
  { kind: "li", text: "Weekly activated users · bar chart" },
  { kind: "li", text: "Four-step onboarding funnel · funnel chart" },

  { kind: "h", text: "Filters · Layout" },
  { kind: "li", text: "Date range · country (sidebar layout)" },

  { kind: "h", text: "Stack · Deploy" },
  { kind: "code", text: "streamlit + postgres + modal" },

  { kind: "h", text: "Vision · references" },
  { kind: "ref", text: "existing analytics dashboard · sidebar layout · line chart of MAU" },
];

const VISIBLE_FRAMES = SCRIPT.length;
const FRAME_MS = 620;
const LOOP_PAUSE_MS = 2600;

export function LiveSpecPreview() {
  const [frame, setFrame] = useState(0);
  const [version, setVersion] = useState(1);

  useEffect(() => {
    let alive = true;
    let timeoutId: ReturnType<typeof setTimeout>;

    const tick = (next: number) => {
      if (!alive) return;
      if (next > VISIBLE_FRAMES) {
        timeoutId = setTimeout(() => {
          if (!alive) return;
          setFrame(0);
          setVersion((v) => v + 1);
          timeoutId = setTimeout(() => tick(1), 300);
        }, LOOP_PAUSE_MS);
        return;
      }
      setFrame(next);
      timeoutId = setTimeout(() => tick(next + 1), FRAME_MS);
    };

    timeoutId = setTimeout(() => tick(1), 600);
    return () => {
      alive = false;
      clearTimeout(timeoutId);
    };
  }, []);

  const visible = SCRIPT.slice(0, frame);

  return (
    <div
      key={`spec-${version}`}
      style={{
        fontFamily: "var(--font-body)",
        fontSize: 12.5,
        lineHeight: 1.55,
        color: "var(--fg-secondary)",
        position: "relative",
      }}
      aria-live="polite"
    >
      {visible.map((b, i) => (
        <SpecBlock key={i} block={b} index={i} />
      ))}
      {/* Caret while typing */}
      {frame > 0 && frame <= VISIBLE_FRAMES && (
        <span
          aria-hidden
          style={{
            display: "inline-block",
            width: 6,
            height: 12,
            marginLeft: 2,
            background: "var(--fg-secondary)",
            verticalAlign: "middle",
            animation: "blink 1s steps(2) infinite",
          }}
        />
      )}
      <style>{`
        @keyframes blink { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
        @keyframes specEnter {
          from { opacity: 0; transform: translateY(4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}

function SpecBlock({ block, index }: { block: Block; index: number }) {
  const baseStyle: React.CSSProperties = {
    animation: "specEnter 360ms cubic-bezier(0.22, 1, 0.36, 1) both",
    animationDelay: `${index === 0 ? 0 : 60}ms`,
  };

  switch (block.kind) {
    case "meta":
      return (
        <div
          style={{
            ...baseStyle,
            fontSize: 10.5,
            color: "var(--fg-tertiary)",
            fontFamily: "var(--font-mono)",
            marginBottom: 12,
          }}
        >
          {block.text}
        </div>
      );
    case "h":
      return (
        <div
          style={{
            ...baseStyle,
            fontSize: 9.5,
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            color: "var(--fg-tertiary)",
            fontWeight: 500,
            marginTop: 12,
            marginBottom: 4,
          }}
        >
          {block.text}
        </div>
      );
    case "li":
      return (
        <div
          style={{
            ...baseStyle,
            display: "flex",
            alignItems: "flex-start",
            gap: 8,
            paddingLeft: 0,
            marginBottom: 3,
          }}
        >
          <span
            aria-hidden
            style={{
              flexShrink: 0,
              marginTop: 5,
              width: 4,
              height: 4,
              borderRadius: "999px",
              background: block.check ? "var(--accent)" : "var(--fg-quaternary)",
              boxShadow: block.check ? "0 0 6px var(--accent-glow)" : "none",
            }}
          />
          <span
            style={{
              color: block.check ? "var(--fg-primary)" : "var(--fg-secondary)",
              fontSize: 12.5,
            }}
          >
            {block.text}
          </span>
        </div>
      );
    case "field":
      return (
        <div
          style={{
            ...baseStyle,
            display: "grid",
            gridTemplateColumns: "auto 1fr",
            gap: 10,
            fontSize: 11.5,
            marginBottom: 3,
          }}
        >
          <span style={{ color: "var(--fg-tertiary)", fontFamily: "var(--font-mono)" }}>{block.label}</span>
          <span style={{ color: "var(--fg-primary)" }}>{block.value}</span>
        </div>
      );
    case "code":
      return (
        <div
          style={{
            ...baseStyle,
            display: "inline-block",
            marginTop: 4,
            padding: "5px 9px",
            borderRadius: 5,
            background: "var(--bg-elevated-3)",
            border: "1px solid var(--border-subtle)",
            fontFamily: "var(--font-mono)",
            fontSize: 11,
            color: "var(--fg-primary)",
          }}
        >
          {block.text}
        </div>
      );
    case "ref":
      return (
        <div
          style={{
            ...baseStyle,
            display: "flex",
            alignItems: "flex-start",
            gap: 8,
            marginTop: 6,
            padding: "6px 10px",
            borderRadius: 5,
            background: "rgba(125, 211, 252, 0.06)",
            border: "1px solid rgba(125, 211, 252, 0.18)",
          }}
        >
          <span
            aria-hidden
            style={{
              flexShrink: 0,
              marginTop: 4,
              width: 5,
              height: 5,
              borderRadius: "999px",
              background: "var(--accent-cool)",
              boxShadow: "0 0 6px rgba(125, 211, 252, 0.4)",
            }}
          />
          <span style={{ fontSize: 11, color: "var(--fg-secondary)", letterSpacing: "-0.005em" }}>
            {block.text}
          </span>
        </div>
      );
  }
}
