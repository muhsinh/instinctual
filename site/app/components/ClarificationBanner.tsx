"use client";

import { useEffect, useState } from "react";

/**
 * Slides in from the bottom of the panel on a periodic schedule, holds for ~3s,
 * then dismisses itself. Mirrors how the real product surfaces a one-tap
 * question mid-meeting. The banner is the visible signal that the agents are
 * actively thinking, not just transcribing.
 */

const APPEAR_DELAY_MS = 5400;
const HOLD_MS = 3200;
const CYCLE_MS = 12_000;

// Clarifier-style questions adjacent to the streamlit_demo fixture's
// scope (activation funnel, sidebar filters, Postgres replica). Fixture
// expects 0 clarifications, but the hero benefits from showing one
// firing — it's the visible signal that the product is thinking, not
// just transcribing.
const QUESTIONS = [
  { q: "Date range default — last 30, 90, or all-time?", a: ["90", "All"] },
  { q: "Funnel break — drop-off counts or conversion %?", a: ["Counts", "%"] },
  { q: "Country list — top-10 from data or full?", a: ["Top 10", "Full"] },
];

export function ClarificationBanner() {
  const [phase, setPhase] = useState<"hidden" | "visible">("hidden");
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;

    const cycle = () => {
      if (!alive) return;
      timer = setTimeout(() => {
        if (!alive) return;
        setPhase("visible");
        timer = setTimeout(() => {
          if (!alive) return;
          setPhase("hidden");
          setIdx((i) => (i + 1) % QUESTIONS.length);
          timer = setTimeout(cycle, CYCLE_MS - APPEAR_DELAY_MS - HOLD_MS);
        }, HOLD_MS);
      }, APPEAR_DELAY_MS);
    };

    cycle();
    return () => { alive = false; clearTimeout(timer); };
  }, []);

  const { q, a } = QUESTIONS[idx];
  const visible = phase === "visible";

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: "absolute",
        left: 12,
        right: 12,
        bottom: 56,
        pointerEvents: "none",
        transform: visible ? "translateY(0)" : "translateY(140%)",
        opacity: visible ? 1 : 0,
        transition:
          "transform 420ms cubic-bezier(0.16, 1, 0.3, 1), opacity 220ms cubic-bezier(0.25, 1, 0.5, 1)",
      }}
    >
      <div
        style={{
          background: "linear-gradient(180deg, rgba(255, 99, 99, 0.16) 0%, rgba(255, 99, 99, 0.06) 100%)",
          border: "1px solid rgba(255, 99, 99, 0.35)",
          borderRadius: 8,
          padding: "10px 12px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 10,
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          boxShadow: "0 12px 28px rgba(0,0,0,0.4), 0 0 24px rgba(255, 99, 99, 0.18)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
          <span
            aria-hidden
            style={{
              flexShrink: 0,
              width: 6,
              height: 6,
              borderRadius: "999px",
              background: "var(--accent)",
              boxShadow: "0 0 10px var(--accent-glow)",
            }}
          />
          <span
            style={{
              fontSize: 12,
              color: "var(--fg-primary)",
              letterSpacing: "-0.01em",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {q}
          </span>
        </div>
        <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
          {a.map((label) => (
            <span
              key={label}
              style={{
                fontSize: 10.5,
                fontWeight: 500,
                padding: "3px 8px",
                borderRadius: 4,
                background: "rgba(255, 255, 255, 0.08)",
                color: "var(--fg-primary)",
                border: "1px solid rgba(255, 255, 255, 0.12)",
              }}
            >
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
