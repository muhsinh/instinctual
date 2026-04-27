"use client";

import { useEffect, useRef, useState } from "react";
import { InstinctualIcon } from "./InstinctualIcon";

/**
 * Live interactive demo. Self-contained React component driven by a state
 * machine that simulates a meeting → spec → build → deploy flow in ~75s.
 *
 * Phases:
 *   idle      — Start demo card visible, nothing else.
 *   meeting   — Transcript ticker + panel forming spec. Clarification appears.
 *   building  — "Building" transition with progress bar.
 *   shipped   — Streamlit dashboard mock, deploy URL, "open" button.
 *
 * Two clarification branches converge to roughly equivalent end-states —
 * the visitor's choice changes the deployed dashboard's title/timezone but
 * not the artifact's overall shape. Demonstrates responsiveness without
 * making the visitor feel their choice was meaningless.
 *
 * No audio file is bundled; the mock is timer-driven. When real audio
 * exists, swap the setTimeout chain for an Audio() element + timeupdate
 * listener and the rest of the state machine is unchanged.
 */

type Phase = "idle" | "meeting" | "clarifying" | "building" | "shipped";
type Branch = "v2-sso" | "google-oauth";

const TRANSCRIPT_LINES: { speaker: string; line: string; t: number; specEffect?: string }[] = [
  { speaker: "Alex", line: "Okay so for Q4 we said we’d have a velocity dashboard ready by Friday.", t: 0 },
  { speaker: "Priya", line: "Right — PR throughput, deploy frequency, time-to-first-review.", t: 2400, specEffect: "scope-1" },
  { speaker: "Alex", line: "Last 90 days of data, broken out per repo.", t: 5200, specEffect: "scope-2" },
  { speaker: "Sam", line: "And p50 + p90 on the review latency, not just the mean.", t: 8000, specEffect: "scope-3" },
  { speaker: "Priya", line: "Streamlit + DuckDB on top of the GitHub API. Same stack as the v2 dashboard.", t: 11000, specEffect: "stack" },
  { speaker: "Alex", line: "Auth — should we do the same SSO as v2 or new Google OAuth?", t: 14500, specEffect: "open" },
  { speaker: "Sam", line: "Hmm. What's faster?", t: 17500 },
];

const TRANSCRIPT_TOTAL = 21500;
const BUILDING_MS = 6500;

export function InteractiveDemo() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [tIndex, setTIndex] = useState(0);
  const [branch, setBranch] = useState<Branch | null>(null);
  const [buildProgress, setBuildProgress] = useState(0);
  const startedAtRef = useRef<number>(0);
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clear = () => {
    timeoutsRef.current.forEach(clearTimeout);
    timeoutsRef.current = [];
  };
  useEffect(() => clear, []);

  function start() {
    clear();
    setPhase("meeting");
    setTIndex(0);
    setBranch(null);
    setBuildProgress(0);
    startedAtRef.current = performance.now();

    TRANSCRIPT_LINES.forEach((line, i) => {
      timeoutsRef.current.push(setTimeout(() => setTIndex(i + 1), line.t));
    });
    // Pause the meeting at the open question — wait for visitor input
    timeoutsRef.current.push(
      setTimeout(() => setPhase("clarifying"), TRANSCRIPT_LINES[5].t + 1200),
    );
  }

  function answer(b: Branch) {
    setBranch(b);
    setPhase("building");
    const interval = setInterval(() => {
      setBuildProgress((p) => {
        const next = p + 100 / (BUILDING_MS / 100);
        if (next >= 100) {
          clearInterval(interval);
          setTimeout(() => setPhase("shipped"), 250);
          return 100;
        }
        return next;
      });
    }, 100);
    timeoutsRef.current.push(interval as unknown as ReturnType<typeof setTimeout>);
  }

  function reset() {
    clear();
    setPhase("idle");
    setTIndex(0);
    setBranch(null);
    setBuildProgress(0);
  }

  return (
    <section
      id="live-demo"
      className="section"
      aria-labelledby="livedemo-heading"
      style={{ scrollMarginTop: 80 }}
    >
      <div className="container-page">
        <header style={{ maxWidth: "44ch", marginBottom: "clamp(2rem, 5vw, 3rem)" }}>
          <p className="eyebrow" style={{ marginBottom: 12 }}>Try it</p>
          <h2
            id="livedemo-heading"
            className="headline"
            style={{ fontSize: "clamp(1.875rem, 4vw, 3rem)", margin: 0 }}
          >
            Ninety seconds. No install. Click start.
          </h2>
        </header>

        <div
          className="demo-grid"
          aria-live="polite"
        >
          {/* Left pane — transcript / meeting feed */}
          <div className="demo-pane">
            <div className="demo-pane-header">
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span
                  style={{
                    width: 7, height: 7, borderRadius: "999px",
                    background: phase === "meeting" || phase === "clarifying" ? "var(--accent)" : "var(--fg-quaternary)",
                    boxShadow: phase === "meeting" || phase === "clarifying" ? "0 0 8px var(--accent-glow)" : "none",
                  }}
                />
                {phase === "idle" ? "Meeting · ready" : phase === "shipped" ? "Meeting · ended" : "Meeting · live"}
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 10.5, opacity: 0.7 }}>
                {phase === "idle" ? "00:00" : `00:${String(Math.min(75, Math.floor((tIndex / TRANSCRIPT_LINES.length) * 75))).padStart(2, "0")}`}
              </span>
            </div>
            <div className="demo-pane-body" style={{ position: "relative" }}>
              {phase === "idle" ? (
                <IdleState onStart={start} />
              ) : (
                <Transcript visibleCount={tIndex} />
              )}
            </div>
          </div>

          {/* Right pane — Instinctual panel + result */}
          <div className="demo-pane">
            <div className="demo-pane-header">
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <InstinctualIcon size={13} active={phase === "meeting" || phase === "clarifying"} color="var(--fg-secondary)" />
                {phaseLabel(phase)}
              </span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 10.5, opacity: 0.7 }}>
                {phase === "shipped" ? "deploy.instinctual.app" : phase === "building" ? `${Math.round(buildProgress)}%` : "5 agents"}
              </span>
            </div>
            <div className="demo-pane-body" style={{ position: "relative", overflow: "hidden" }}>
              {phase === "idle" && <IdlePanel />}
              {(phase === "meeting" || phase === "clarifying") && <PanelSpec tIndex={tIndex} />}
              {phase === "building" && <BuildingState progress={buildProgress} />}
              {phase === "shipped" && <DashboardArtifact branch={branch} />}

              {/* Clarification overlay */}
              <ClarificationOverlay
                visible={phase === "clarifying"}
                onAnswer={answer}
              />
            </div>
          </div>
        </div>

        {/* Reset button — only when not idle */}
        {phase !== "idle" && (
          <div style={{ display: "flex", justifyContent: "center", marginTop: 18 }}>
            <button
              onClick={reset}
              className="btn btn-secondary"
              style={{ padding: "0.5rem 0.95rem", fontSize: "var(--text-xs)" }}
            >
              Reset demo
            </button>
          </div>
        )}
      </div>

      <style>{styles}</style>
    </section>
  );
}

function phaseLabel(p: Phase) {
  switch (p) {
    case "idle": return "Instinctual · idle";
    case "meeting": return "Instinctual · listening";
    case "clarifying": return "Instinctual · waiting on you";
    case "building": return "Instinctual · building";
    case "shipped": return "Instinctual · shipped";
  }
}

function IdleState({ onStart }: { onStart: () => void }) {
  return (
    <div
      style={{
        height: "100%",
        minHeight: 320,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 14,
        padding: "2rem 1.25rem",
        textAlign: "center",
      }}
    >
      <span
        style={{
          fontSize: "var(--text-base)",
          color: "var(--fg-secondary)",
          maxWidth: "32ch",
          letterSpacing: "-0.005em",
        }}
      >
        Watch a real meeting turn into a deployed dashboard. Tap once to start —
        you’ll have a clarification to answer along the way.
      </span>
      <button onClick={onStart} className="btn btn-accent">
        Start demo
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
          <path d="M3 7h8m0 0L7.5 3.5M11 7l-3.5 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      <span
        style={{
          fontSize: "var(--text-xs)",
          color: "var(--fg-tertiary)",
          fontFamily: "var(--font-mono)",
          letterSpacing: "0.02em",
          marginTop: 2,
        }}
      >
        ~75 seconds · no audio · no install
      </span>
    </div>
  );
}

function IdlePanel() {
  return (
    <div
      style={{
        height: "100%",
        minHeight: 320,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "var(--fg-quaternary)",
        fontSize: "var(--text-sm)",
        fontFamily: "var(--font-mono)",
        letterSpacing: 0,
      }}
    >
      waiting for meeting to start…
    </div>
  );
}

function Transcript({ visibleCount }: { visibleCount: number }) {
  const visible = TRANSCRIPT_LINES.slice(0, visibleCount);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14, padding: "1rem 0.25rem" }}>
      {visible.map((l, i) => (
        <div
          key={i}
          style={{
            animation: "demoLineEnter 320ms cubic-bezier(0.22, 1, 0.36, 1) both",
            display: "grid",
            gridTemplateColumns: "auto 1fr",
            gap: 10,
            alignItems: "baseline",
          }}
        >
          <span
            style={{
              fontSize: "var(--text-xs)",
              fontFamily: "var(--font-mono)",
              fontWeight: 500,
              color: "var(--fg-tertiary)",
              textTransform: "uppercase",
              letterSpacing: "0.04em",
              minWidth: "5ch",
            }}
          >
            {l.speaker}
          </span>
          <span
            style={{
              fontSize: "var(--text-sm)",
              color: "var(--fg-primary)",
              lineHeight: 1.5,
              letterSpacing: "-0.005em",
            }}
          >
            {l.line}
          </span>
        </div>
      ))}
    </div>
  );
}

function PanelSpec({ tIndex }: { tIndex: number }) {
  // Reveal spec sections progressively as transcript advances.
  const showScope = tIndex >= 2;
  const showStack = tIndex >= 5;
  const showOpen = tIndex >= 6;

  return (
    <div style={{ padding: "1rem 0.5rem", fontSize: 12.5, color: "var(--fg-secondary)", lineHeight: 1.55 }}>
      <div className="spec-meta">Q4 dashboard sync · 4 attendees · live</div>

      <div className="spec-h">Decision</div>
      <SpecLi check>Build engineering velocity dashboard for Q4 review</SpecLi>
      <SpecLi check>Ship by Friday standup</SpecLi>

      {showScope && (
        <>
          <div className="spec-h">Scope</div>
          {tIndex >= 2 && <SpecLi>PR throughput per repo</SpecLi>}
          {tIndex >= 3 && <SpecLi>Last 90 days, broken out by repo</SpecLi>}
          {tIndex >= 4 && <SpecLi>Time-to-first-review · p50 + p90</SpecLi>}
        </>
      )}
      {showStack && (
        <>
          <div className="spec-h">Stack</div>
          <span className="spec-code">streamlit + duckdb + github-api</span>
        </>
      )}
      {showOpen && (
        <>
          <div className="spec-h">Open</div>
          <SpecLi>Auth — same SSO as v2 dashboard, or Google OAuth?</SpecLi>
        </>
      )}
    </div>
  );
}

function SpecLi({ children, check }: { children: React.ReactNode; check?: boolean }) {
  return (
    <div
      style={{
        display: "flex",
        gap: 8,
        marginBottom: 4,
        animation: "demoLineEnter 280ms cubic-bezier(0.22, 1, 0.36, 1) both",
      }}
    >
      <span
        aria-hidden
        style={{
          flexShrink: 0,
          marginTop: 7,
          width: 4,
          height: 4,
          borderRadius: "999px",
          background: check ? "var(--accent)" : "var(--fg-quaternary)",
          boxShadow: check ? "0 0 6px var(--accent-glow)" : "none",
        }}
      />
      <span style={{ color: check ? "var(--fg-primary)" : "var(--fg-secondary)" }}>{children}</span>
    </div>
  );
}

function ClarificationOverlay({ visible, onAnswer }: { visible: boolean; onAnswer: (b: Branch) => void }) {
  return (
    <div
      style={{
        position: "absolute",
        left: 12, right: 12, bottom: 14,
        transform: visible ? "translateY(0)" : "translateY(140%)",
        opacity: visible ? 1 : 0,
        transition: "transform 420ms cubic-bezier(0.16, 1, 0.3, 1), opacity 220ms ease",
        pointerEvents: visible ? "auto" : "none",
      }}
    >
      <div
        style={{
          background: "linear-gradient(180deg, rgba(255, 99, 99, 0.18) 0%, rgba(255, 99, 99, 0.06) 100%)",
          border: "1px solid rgba(255, 99, 99, 0.4)",
          borderRadius: 10,
          padding: "12px 14px",
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
          boxShadow: "0 14px 28px rgba(0,0,0,0.4), 0 0 24px rgba(255, 99, 99, 0.2)",
        }}
      >
        <p
          style={{
            margin: "0 0 10px",
            fontSize: "var(--text-sm)",
            color: "var(--fg-primary)",
            letterSpacing: "-0.01em",
          }}
        >
          Auth — same SSO as the v2 dashboard, or Google OAuth?
        </p>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={() => onAnswer("v2-sso")}
            style={demoBtnStyle}
          >
            v2 SSO
          </button>
          <button
            onClick={() => onAnswer("google-oauth")}
            style={demoBtnStyle}
          >
            Google OAuth
          </button>
        </div>
      </div>
    </div>
  );
}

const demoBtnStyle: React.CSSProperties = {
  flex: 1,
  fontSize: "var(--text-xs)",
  fontWeight: 500,
  padding: "8px 12px",
  borderRadius: 6,
  background: "rgba(255, 255, 255, 0.08)",
  color: "var(--fg-primary)",
  border: "1px solid rgba(255, 255, 255, 0.15)",
  cursor: "pointer",
  transition: "background 150ms ease, border-color 150ms ease",
};

function BuildingState({ progress }: { progress: number }) {
  const steps = [
    { label: "Synthesis · classify recipe", at: 8 },
    { label: "Builder · scaffold streamlit app", at: 26 },
    { label: "Builder · wire DuckDB + GitHub API", at: 48 },
    { label: "Critic · feasibility passes", at: 68 },
    { label: "Deploy · push to Modal", at: 88 },
  ];
  const passed = steps.filter((s) => progress >= s.at);

  return (
    <div style={{ padding: "1.5rem 0.75rem", display: "flex", flexDirection: "column", gap: 14 }}>
      <div
        style={{
          height: 4,
          borderRadius: 2,
          background: "var(--bg-elevated-3)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progress}%`,
            background: "linear-gradient(90deg, var(--accent) 0%, var(--accent-hover) 100%)",
            boxShadow: "0 0 8px var(--accent-glow)",
            transition: "width 100ms linear",
          }}
        />
      </div>
      <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 10 }}>
        {steps.map((s, i) => {
          const done = progress >= s.at;
          const active = !done && (i === passed.length);
          return (
            <li
              key={s.label}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                fontSize: "var(--text-sm)",
                color: done ? "var(--fg-primary)" : active ? "var(--fg-secondary)" : "var(--fg-quaternary)",
                fontFamily: "var(--font-mono)",
                letterSpacing: 0,
                transition: "color 200ms ease",
              }}
            >
              <span
                aria-hidden
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: "999px",
                  background: done ? "var(--accent)" : "transparent",
                  border: done ? "none" : `1px solid ${active ? "var(--accent)" : "var(--fg-quaternary)"}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  animation: active ? "demoSpin 1.2s linear infinite" : "none",
                }}
              >
                {done && (
                  <svg width="7" height="7" viewBox="0 0 7 7" fill="none">
                    <path d="M1 4l1.5 1.5L6 1.5" stroke="#1a0e0e" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
                {active && !done && (
                  <span style={{ width: 4, height: 4, borderRadius: "999px", background: "var(--accent)" }} />
                )}
              </span>
              {s.label}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function DashboardArtifact({ branch }: { branch: Branch | null }) {
  const title = branch === "google-oauth" ? "Engineering Velocity · Google" : "Engineering Velocity · v2 SSO";
  return (
    <div
      style={{
        padding: "0.75rem 0.5rem",
        animation: "demoLineEnter 360ms cubic-bezier(0.22, 1, 0.36, 1) both",
      }}
    >
      <div
        style={{
          background: "var(--bg-elevated-3)",
          border: "1px solid var(--border-default)",
          borderRadius: 8,
          padding: "10px 12px 14px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "var(--fg-primary)", letterSpacing: "-0.01em" }}>
            {title}
          </span>
          <span style={{ fontSize: 10, color: "var(--fg-tertiary)", fontFamily: "var(--font-mono)" }}>
            last 90 days
          </span>
        </div>

        {/* Three KPI tiles */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginBottom: 12 }}>
          {[
            { label: "PRs / week", val: "47.2", delta: "+12%" },
            { label: "Deploy / day", val: "8.1", delta: "+24%" },
            { label: "p50 review", val: "1h 12m", delta: "−18%" },
          ].map((k) => (
            <div
              key={k.label}
              style={{
                background: "var(--bg-elevated-2)",
                border: "1px solid var(--border-subtle)",
                borderRadius: 6,
                padding: "8px 10px",
              }}
            >
              <div style={{ fontSize: 9, color: "var(--fg-tertiary)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                {k.label}
              </div>
              <div style={{ fontSize: 18, fontWeight: 500, color: "var(--fg-primary)", letterSpacing: "-0.025em", marginTop: 2 }}>
                {k.val}
              </div>
              <div style={{ fontSize: 10, color: "var(--success)", fontFamily: "var(--font-mono)" }}>{k.delta}</div>
            </div>
          ))}
        </div>

        {/* Tiny bar chart */}
        <div style={{ display: "flex", alignItems: "flex-end", gap: 3, height: 56 }}>
          {[42, 55, 38, 64, 50, 71, 60, 82, 68, 79, 91, 88].map((v, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                height: `${v}%`,
                background: "linear-gradient(180deg, var(--accent) 0%, rgba(255, 99, 99, 0.4) 100%)",
                borderRadius: "2px 2px 0 0",
                opacity: 0.5 + (v / 200),
              }}
            />
          ))}
        </div>
        <div
          style={{
            marginTop: 8,
            fontSize: 9,
            color: "var(--fg-tertiary)",
            fontFamily: "var(--font-mono)",
            letterSpacing: "0.02em",
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <span>weeks ago: 12</span>
          <span>now</span>
        </div>
      </div>

      <div
        style={{
          marginTop: 14,
          padding: "10px 12px",
          background: "linear-gradient(180deg, rgba(74, 222, 128, 0.08), rgba(74, 222, 128, 0.02))",
          border: "1px solid rgba(74, 222, 128, 0.3)",
          borderRadius: 8,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
          <span
            aria-hidden
            style={{
              width: 6, height: 6, borderRadius: "999px",
              background: "var(--success)",
              boxShadow: "0 0 6px rgba(74, 222, 128, 0.5)",
              flexShrink: 0,
            }}
          />
          <span
            style={{
              fontSize: 11,
              color: "var(--fg-primary)",
              fontFamily: "var(--font-mono)",
              letterSpacing: 0,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            deployed · velocity-{branch === "google-oauth" ? "g" : "v2"}.instinctual.app
          </span>
        </div>
        <a
          href="#"
          onClick={(e) => e.preventDefault()}
          style={{
            fontSize: 11,
            fontWeight: 500,
            color: "var(--fg-primary)",
            padding: "4px 10px",
            borderRadius: 4,
            background: "rgba(255,255,255,0.06)",
            border: "1px solid rgba(255,255,255,0.12)",
          }}
        >
          Open ↗
        </a>
      </div>
    </div>
  );
}

const styles = `
  .demo-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    border-radius: var(--radius-xl);
  }
  @media (max-width: 760px) {
    .demo-grid { grid-template-columns: 1fr; }
  }
  .demo-pane {
    background: linear-gradient(180deg, var(--bg-elevated) 0%, var(--bg-elevated-2) 100%);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: var(--shadow-md);
    min-height: 420px;
    display: flex;
    flex-direction: column;
  }
  .demo-pane-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-subtle);
    font-size: 11.5px;
    color: var(--fg-secondary);
    letter-spacing: -0.005em;
    background: rgba(0,0,0,0.15);
  }
  .demo-pane-body {
    flex: 1;
    padding: 12px 14px;
    overflow-y: auto;
  }
  .spec-meta { font-size: 10.5px; color: var(--fg-tertiary); font-family: var(--font-mono); margin-bottom: 12px; letter-spacing: 0; }
  .spec-h { font-size: 9.5px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--fg-tertiary); font-weight: 500; margin-top: 12px; margin-bottom: 5px; }
  .spec-code { display: inline-block; padding: 5px 9px; border-radius: 5px; background: var(--bg-elevated-3); border: 1px solid var(--border-subtle); font-family: var(--font-mono); font-size: 11px; color: var(--fg-primary); margin-top: 4px; }

  @keyframes demoLineEnter {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes demoSpin {
    to { transform: rotate(360deg); }
  }
`;
