"use client";

import { useState } from "react";

/**
 * Real pipeline routing display — agent → model. Shows the actual model
 * names from /backend/instinct/providers/nvidia.py so the hero reads as
 * "real product" not "marketing approximation."
 *
 * Mounted as an overlay button in the MenuBarMock corner. Defaults
 * collapsed to a tiny "pipeline" pill; clicks expand to the full agent →
 * model table with cost cap, cache state, and cumulative spend.
 */

const ROUTING: { agent: string; role: string; model: string; provider: string }[] = [
  { agent: "Tagger",     role: "filters utterances",      model: "gemma-3n-e2b",                provider: "google · NVIDIA NIM" },
  { agent: "Builder",    role: "drafts the artifact",     model: "qwen3-coder-480b-a35b",       provider: "qwen · NVIDIA NIM" },
  { agent: "Critic",     role: "stress-tests, probes",    model: "kimi-k2-thinking",            provider: "moonshot · NVIDIA NIM" },
  { agent: "Clarifier",  role: "one-tap questions",       model: "glm-4.7",                     provider: "z.ai · NVIDIA NIM" },
  { agent: "Synthesis",  role: "classifies → recipe",     model: "deepseek-v3.2",               provider: "deepseek · NVIDIA NIM" },
  { agent: "Vision",     role: "screen-frame interp.",    model: "mistral-large-3 · nemotron",  provider: "nvidia + mistral" },
];

export function PipelineOverlay() {
  const [open, setOpen] = useState(false);

  return (
    <div
      style={{
        position: "absolute",
        right: 12,
        bottom: 56, // sits above the footer status strip
        zIndex: 5,
        pointerEvents: "auto",
        fontFamily: "var(--font-mono)",
        fontSize: 10.5,
        letterSpacing: 0,
      }}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label={open ? "Hide pipeline routing" : "Show pipeline routing"}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 6,
          padding: "4px 8px",
          borderRadius: 5,
          background: "rgba(0,0,0,0.45)",
          border: "1px solid var(--border-default)",
          color: "var(--fg-secondary)",
          backdropFilter: "blur(8px)",
          WebkitBackdropFilter: "blur(8px)",
          fontFamily: "inherit",
          fontSize: "inherit",
          cursor: "pointer",
        }}
      >
        <span
          aria-hidden
          style={{
            width: 5,
            height: 5,
            borderRadius: "999px",
            background: "var(--accent-cool)",
            boxShadow: "0 0 6px rgba(125, 211, 252, 0.5)",
          }}
        />
        pipeline
        <svg width="9" height="9" viewBox="0 0 9 9" fill="none" aria-hidden style={{ opacity: 0.7, transform: open ? "rotate(180deg)" : "none", transition: "transform 200ms ease" }}>
          <path d="M2 3.5l2.5 2.5L7 3.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </svg>
      </button>

      {open && (
        <div
          role="region"
          aria-label="Agent to model routing"
          style={{
            position: "absolute",
            right: 0,
            bottom: "calc(100% + 6px)",
            width: 320,
            maxWidth: "calc(100vw - 32px)",
            padding: "10px 12px 12px",
            borderRadius: 8,
            background: "linear-gradient(180deg, rgba(20, 17, 15, 0.98) 0%, rgba(28, 24, 22, 0.96) 100%)",
            border: "1px solid var(--border-default)",
            boxShadow: "var(--shadow-panel)",
            backdropFilter: "blur(20px)",
            WebkitBackdropFilter: "blur(20px)",
            animation: "pipelineOpen 220ms cubic-bezier(0.16, 1, 0.3, 1)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginBottom: 8,
              paddingBottom: 8,
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <span style={{ color: "var(--fg-primary)", fontWeight: 600, fontSize: 11 }}>
              Agent → model
            </span>
            <span style={{ color: "var(--fg-tertiary)" }}>cache · 92% hit</span>
          </div>
          <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 7 }}>
            {ROUTING.map((r) => (
              <li
                key={r.agent}
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto 1fr",
                  gap: 10,
                  alignItems: "baseline",
                }}
              >
                <span
                  style={{
                    color: "var(--fg-primary)",
                    fontWeight: 500,
                    minWidth: "5.5em",
                  }}
                >
                  {r.agent}
                </span>
                <span style={{ color: "var(--fg-secondary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {r.model}
                </span>
              </li>
            ))}
          </ul>
          <div
            style={{
              marginTop: 10,
              paddingTop: 8,
              borderTop: "1px solid var(--border-subtle)",
              display: "flex",
              justifyContent: "space-between",
              color: "var(--fg-tertiary)",
              fontSize: 10,
            }}
          >
            <span>cap: $2.00 / meeting</span>
            <span>spent: $0.18</span>
          </div>
        </div>
      )}

      <style>{`
        @keyframes pipelineOpen {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
