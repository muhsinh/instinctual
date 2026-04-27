"use client";

import { useCallback, useEffect, useState } from "react";
import { Slide, SlideEyebrow, SlideHeadline, SlideBody } from "../components/Slide";
import { Wordmark } from "../components/Wordmark";
import { MenuBarMock } from "../components/MenuBarMock";
import { InstinctualIcon } from "../components/InstinctualIcon";

/**
 * Pitch deck. 17 slides: original 15 + 2 PROMPT-2 extensions
 * (category map, financials). Traction slide is skipped — empty traction
 * is better than fake traction. The team slide is the v1 (single founder)
 * version per spec.
 *
 * Keyboard: ←/↑/PgUp = back, →/↓/Space/PgDn = forward, Home/End, Esc → "/".
 * Print: each .page-break section maps to one PDF page via the print
 * stylesheet in globals.css.
 */

const SLIDES: { id: string; render: () => React.ReactNode }[] = [
  { id: "title", render: TitleSlide },
  { id: "problem", render: ProblemSlide },
  { id: "broken", render: BrokenSlide },
  { id: "shift", render: ShiftSlide },
  { id: "product", render: ProductSlide },
  { id: "how", render: HowSlide },
  { id: "different", render: DifferentSlide },
  { id: "demo", render: DemoSlide },
  { id: "market", render: MarketSlide },
  { id: "why-now", render: WhyNowSlide },
  { id: "category-map", render: CategoryMapSlide }, // PROMPT 2 extension
  { id: "moat", render: MoatSlide },
  { id: "roadmap", render: RoadmapSlide },
  { id: "financials", render: FinancialsSlide }, // PROMPT 2 extension
  { id: "team", render: TeamSlide },
  { id: "ask", render: AskSlide },
  { id: "thanks", render: ThanksSlide },
];

export default function DeckPage() {
  const [index, setIndex] = useState(0);
  const total = SLIDES.length;

  const go = useCallback(
    (delta: number) => {
      setIndex((i) => Math.max(0, Math.min(total - 1, i + delta)));
    },
    [total],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === "PageDown" || e.key === " ") {
        e.preventDefault();
        go(+1);
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp" || e.key === "PageUp") {
        e.preventDefault();
        go(-1);
      } else if (e.key === "Home") {
        e.preventDefault();
        setIndex(0);
      } else if (e.key === "End") {
        e.preventDefault();
        setIndex(total - 1);
      } else if (e.key === "Escape") {
        window.location.href = "/";
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go, total]);

  return (
    <main
      style={{
        position: "fixed",
        inset: 0,
        background: "var(--bg-base)",
        overflow: "hidden",
      }}
    >
      <div
        style={{ position: "absolute", inset: 0 }}
        aria-roledescription="carousel"
        aria-label="Instinctual pitch deck"
      >
        {SLIDES.map((s, i) => (
          <Slide key={s.id} id={s.id} index={i} total={total} visible={i === index}>
            {s.render()}
          </Slide>
        ))}
      </div>

      {/* Slide indicator + nav */}
      <div
        className="no-print"
        style={{
          position: "fixed",
          bottom: 18,
          right: 24,
          display: "flex",
          alignItems: "center",
          gap: 14,
          fontFamily: "var(--font-mono)",
          fontSize: "var(--text-xs)",
          color: "var(--fg-tertiary)",
          letterSpacing: "0.04em",
          zIndex: 100,
        }}
      >
        <DeckButton ariaLabel="Previous slide" onClick={() => go(-1)} disabled={index === 0}>
          <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M7 2L3 5.5l4 3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </DeckButton>
        <span style={{ fontVariantNumeric: "tabular-nums" }}>
          {String(index + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}
        </span>
        <DeckButton ariaLabel="Next slide" onClick={() => go(+1)} disabled={index === total - 1}>
          <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M4 2l4 3.5L4 9" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </DeckButton>
      </div>

      {/* Top-left: wordmark links back */}
      <a
        href="/"
        className="no-print"
        style={{
          position: "fixed",
          top: 18,
          left: 24,
          color: "var(--fg-secondary)",
          zIndex: 100,
        }}
        aria-label="Back to instinctual.app"
      >
        <Wordmark size="sm" />
      </a>

      {/* Help text — bottom-left, very subtle */}
      <p
        className="no-print"
        style={{
          position: "fixed",
          bottom: 22,
          left: 24,
          margin: 0,
          fontSize: 10,
          fontFamily: "var(--font-mono)",
          color: "var(--fg-quaternary)",
          letterSpacing: "0.04em",
          zIndex: 100,
        }}
      >
        ← → · esc to exit
      </p>
    </main>
  );
}

function DeckButton({
  children,
  ariaLabel,
  onClick,
  disabled,
}: {
  children: React.ReactNode;
  ariaLabel: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      aria-label={ariaLabel}
      onClick={onClick}
      disabled={disabled}
      style={{
        width: 28,
        height: 28,
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--border-default)",
        background: "var(--bg-elevated)",
        color: disabled ? "var(--fg-quaternary)" : "var(--fg-secondary)",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: disabled ? "default" : "pointer",
        opacity: disabled ? 0.5 : 1,
        transition: "background 150ms ease, color 150ms ease",
      }}
    >
      {children}
    </button>
  );
}

/* ─── Slides ─── */

function TitleSlide() {
  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", height: "100%" }}>
      <span />
      <div>
        <Wordmark size="xl" accent />
        <p
          style={{
            marginTop: "1.5rem",
            fontSize: "clamp(1.25rem, 2vw, 1.75rem)",
            color: "var(--fg-secondary)",
            maxWidth: "28ch",
            letterSpacing: "-0.012em",
            lineHeight: 1.3,
          }}
        >
          Your meetings should ship products, not tickets.
        </p>
      </div>
      <p
        style={{
          fontSize: "var(--text-xs)",
          fontFamily: "var(--font-mono)",
          color: "var(--fg-tertiary)",
          letterSpacing: "0.12em",
          textTransform: "uppercase",
          margin: 0,
        }}
      >
        Pitch deck · {new Date().getFullYear()} · macOS only · Private beta
      </p>
    </div>
  );
}

function ProblemSlide() {
  return (
    <>
      <SlideEyebrow>The problem</SlideEyebrow>
      <SlideHeadline size="xl">
        Meetings produce decisions. Then nothing happens for two weeks.
      </SlideHeadline>
    </>
  );
}

function BrokenSlide() {
  return (
    <>
      <SlideEyebrow>Why this is broken</SlideEyebrow>
      <SlideHeadline>
        By the time someone builds the thing, half the context is gone.
      </SlideHeadline>
      <SlideBody>
        Three engineers agree on a dashboard. Two weeks later, one engineer is
        re-building it from a Slack scroll, with the wrong scope, after one of
        the original three has left. Most "decision-to-build" loops in big
        companies look like this.
      </SlideBody>
    </>
  );
}

function ShiftSlide() {
  return (
    <>
      <SlideEyebrow>The shift</SlideEyebrow>
      <SlideHeadline size="xl">
        Meetings should produce artifacts, not tickets.
      </SlideHeadline>
    </>
  );
}

function ProductSlide() {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1.1fr)",
        gap: "clamp(2rem, 4vw, 4rem)",
        alignItems: "center",
        height: "100%",
      }}
    >
      <div>
        <SlideEyebrow>The product</SlideEyebrow>
        <SlideHeadline>
          A macOS menu bar app that listens, understands, and ships.
        </SlideHeadline>
        <SlideBody>
          Audio + screen capture during the meeting. Five agents draft the
          spec, stress-test feasibility, surface clarifications, and synthesize
          the result. By the time the meeting ends, you have a working draft.
        </SlideBody>
      </div>
      <MenuBarMock />
    </div>
  );
}

function HowSlide() {
  const stages = [
    { n: "01", label: "Listen", body: "Audio + screen, no bots in the call." },
    { n: "02", label: "Understand", body: "Five agents in parallel." },
    { n: "03", label: "Clarify", body: "One-tap question, mid-meeting." },
    { n: "04", label: "Ship", body: "Working draft, deployable." },
  ];
  return (
    <>
      <SlideEyebrow>How it works</SlideEyebrow>
      <SlideHeadline size="md">
        Four stages. All while the meeting is still happening.
      </SlideHeadline>
      <div
        style={{
          marginTop: "clamp(2rem, 4vw, 3rem)",
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "clamp(1rem, 2vw, 1.5rem)",
        }}
      >
        {stages.map((s) => (
          <div
            key={s.n}
            style={{
              padding: "1.25rem 1rem",
              border: "1px solid var(--border-default)",
              borderRadius: "var(--radius-lg)",
              background: "var(--bg-elevated)",
            }}
          >
            <div style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-xs)", color: "var(--fg-tertiary)", letterSpacing: "0.04em" }}>{s.n}</div>
            <div style={{ marginTop: 12, fontSize: "var(--text-xl)", fontWeight: 500, color: "var(--fg-primary)", letterSpacing: "-0.018em" }}>{s.label}</div>
            <div style={{ marginTop: 8, fontSize: "var(--text-sm)", color: "var(--fg-secondary)", lineHeight: 1.5, letterSpacing: "-0.005em" }}>{s.body}</div>
          </div>
        ))}
      </div>
    </>
  );
}

function DifferentSlide() {
  const cols = [
    {
      head: "vs. note-takers",
      sub: "Granola, Otter, Fellow",
      body: "They stop at notes. We ship the thing."
    },
    {
      head: "vs. agent builders",
      sub: "Cursor, Replit, Lovable",
      body: "They start with a typed prompt. We start with the meeting."
    },
    {
      head: "vs. doing nothing",
      sub: "the status quo",
      body: "Decisions become backlog. Backlog becomes drift."
    },
  ];
  return (
    <>
      <SlideEyebrow>What's different</SlideEyebrow>
      <SlideHeadline size="md">
        Three categories meet here. Nobody else stands where we stand.
      </SlideHeadline>
      <div
        style={{
          marginTop: "clamp(2rem, 4vw, 3rem)",
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "clamp(1rem, 2vw, 1.75rem)",
        }}
      >
        {cols.map((c) => (
          <div
            key={c.head}
            style={{
              padding: "1.5rem",
              border: "1px solid var(--border-default)",
              borderRadius: "var(--radius-lg)",
              background: "var(--bg-elevated)",
            }}
          >
            <div style={{ fontSize: "var(--text-base)", fontWeight: 500, color: "var(--fg-primary)" }}>{c.head}</div>
            <div style={{ marginTop: 4, fontSize: "var(--text-xs)", color: "var(--fg-tertiary)", fontFamily: "var(--font-mono)" }}>{c.sub}</div>
            <div style={{ marginTop: 16, fontSize: "var(--text-base)", color: "var(--fg-secondary)", lineHeight: 1.5 }}>{c.body}</div>
          </div>
        ))}
      </div>
    </>
  );
}

function DemoSlide() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", height: "100%", justifyContent: "center", alignItems: "center" }}>
      <SlideEyebrow>Demo</SlideEyebrow>
      <div
        style={{
          width: "min(900px, 90%)",
          aspectRatio: "16 / 9",
          background: "linear-gradient(180deg, var(--bg-elevated) 0%, var(--bg-elevated-2) 100%)",
          border: "1px solid var(--border-default)",
          borderRadius: "var(--radius-xl)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          gap: 14,
        }}
      >
        <div
          style={{
            width: 78, height: 78, borderRadius: "var(--radius-full)",
            background: "var(--bg-elevated-3)", border: "1px solid var(--border-strong)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          <svg width="26" height="26" viewBox="0 0 22 22" fill="none">
            <path d="M7 5l11 6-11 6V5z" fill="var(--fg-primary)" fillOpacity="0.85" />
          </svg>
        </div>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "var(--text-sm)", letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--fg-tertiary)" }}>
          Demo · 90 seconds · instinctual.app/#live-demo
        </span>
      </div>
    </div>
  );
}

function MarketSlide() {
  return (
    <>
      <SlideEyebrow>The market</SlideEyebrow>
      <SlideHeadline>
        ~4M PMs, TPMs, and engineering leads in the US. Every one of them is in
        meetings their company can't act on fast enough.
      </SlideHeadline>
      <div style={{ marginTop: "clamp(2rem, 4vw, 3rem)", display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "clamp(1rem, 2vw, 2rem)" }}>
        {[
          { n: "4M", label: "US PMs / TPMs / eng leads", sub: "BLS estimate" },
          { n: "$45B", label: "Global enterprise AI spend, 2025", sub: "IDC" },
          { n: "15h", label: "Hours / week / PM in meetings", sub: "Atlassian survey" },
        ].map((stat) => (
          <div key={stat.n}>
            <div
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(2.5rem, 5vw, 4rem)",
                fontWeight: 500,
                letterSpacing: "-0.03em",
                color: "var(--fg-primary)",
                lineHeight: 1,
              }}
            >
              {stat.n}
            </div>
            <div style={{ marginTop: 10, fontSize: "var(--text-base)", color: "var(--fg-secondary)" }}>{stat.label}</div>
            <div style={{ marginTop: 6, fontSize: "var(--text-xs)", color: "var(--fg-quaternary)", fontFamily: "var(--font-mono)" }}>{stat.sub}</div>
          </div>
        ))}
      </div>
      <p style={{ marginTop: "clamp(1.5rem, 3vw, 2rem)", fontSize: "var(--text-xs)", color: "var(--fg-quaternary)", fontFamily: "var(--font-mono)", letterSpacing: 0 }}>
        Estimates. Source data linked in the memo.
      </p>
    </>
  );
}

function WhyNowSlide() {
  const factors = [
    { head: "Real-time multimodal models", body: "Meetings + screens are now interpretable cheaply enough to do live.", evidence: "GPT-5, Gemini 2 multimodal · sub-cent per meeting-second" },
    { head: "Agent orchestration matured", body: "Parallel speculative builds aren't research anymore — they're shipping.", evidence: "Cursor 2.0 · 8 parallel agents · Replit Agent 3 · 36-min apps" },
    { head: "Enterprise AI budget without discipline", body: "Companies have unlimited spend, no integration story.", evidence: "$45B AI spend · most goes to seats, not orchestration" },
  ];
  return (
    <>
      <SlideEyebrow>Why now</SlideEyebrow>
      <SlideHeadline size="md">
        Three converging factors. The window is open and shallow.
      </SlideHeadline>
      <div style={{ marginTop: "clamp(2rem, 4vw, 3rem)", display: "grid", gap: "1.25rem" }}>
        {factors.map((f) => (
          <div
            key={f.head}
            style={{
              padding: "1.25rem 1.5rem",
              border: "1px solid var(--border-default)",
              borderRadius: "var(--radius-lg)",
              background: "var(--bg-elevated)",
              display: "grid",
              gridTemplateColumns: "minmax(0, 1.2fr) minmax(0, 1.6fr) minmax(0, 1fr)",
              gap: "1.5rem",
              alignItems: "baseline",
            }}
          >
            <div style={{ fontSize: "var(--text-lg)", fontWeight: 500, color: "var(--fg-primary)", letterSpacing: "-0.012em" }}>{f.head}</div>
            <div style={{ fontSize: "var(--text-base)", color: "var(--fg-secondary)" }}>{f.body}</div>
            <div style={{ fontSize: "var(--text-xs)", color: "var(--fg-tertiary)", fontFamily: "var(--font-mono)", letterSpacing: 0 }}>{f.evidence}</div>
          </div>
        ))}
      </div>
    </>
  );
}

function CategoryMapSlide() {
  // 2x2 plot. Y axis: Output (notes ↔ working artifacts). X: Capture (audio-only ↔ multimodal).
  const PLOT = [
    { label: "Granola", x: 0.18, y: 0.22 },
    { label: "Otter", x: 0.10, y: 0.15 },
    { label: "MS Facilitator", x: 0.30, y: 0.30 },
    { label: "Cursor", x: 0.55, y: 0.78 },
    { label: "Replit Agent", x: 0.50, y: 0.85 },
    { label: "Instinctual", x: 0.86, y: 0.90, accent: true },
  ];
  return (
    <>
      <SlideEyebrow>The category map</SlideEyebrow>
      <SlideHeadline size="md">
        Multimodal capture × working-artifact output is empty. Until us.
      </SlideHeadline>
      <div
        style={{
          marginTop: "clamp(2rem, 4vw, 2.5rem)",
          display: "grid",
          gridTemplateColumns: "auto 1fr",
          gap: "1rem",
          alignItems: "stretch",
          height: "min(420px, 50vh)",
        }}
      >
        {/* Y axis label */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--fg-tertiary)",
            fontSize: "var(--text-xs)",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            fontFamily: "var(--font-mono)",
            writingMode: "vertical-rl",
            transform: "rotate(180deg)",
          }}
        >
          Output: notes → working tools
        </div>
        {/* Plot */}
        <div style={{ position: "relative", border: "1px solid var(--border-default)", borderRadius: "var(--radius-lg)", background: "var(--bg-elevated)" }}>
          {/* Crosshairs */}
          <div style={{ position: "absolute", left: 0, right: 0, top: "50%", borderTop: "1px dashed var(--border-default)" }} />
          <div style={{ position: "absolute", top: 0, bottom: 0, left: "50%", borderLeft: "1px dashed var(--border-default)" }} />
          {/* Quadrant labels */}
          <span style={{ position: "absolute", top: 10, right: 14, fontSize: 10, color: "var(--accent)", fontFamily: "var(--font-mono)", letterSpacing: "0.04em" }}>Empty until Instinctual</span>
          <span style={{ position: "absolute", top: 10, left: 14, fontSize: 10, color: "var(--fg-quaternary)", fontFamily: "var(--font-mono)" }}>typed → tools</span>
          <span style={{ position: "absolute", bottom: 10, left: 14, fontSize: 10, color: "var(--fg-quaternary)", fontFamily: "var(--font-mono)" }}>audio → notes</span>
          <span style={{ position: "absolute", bottom: 10, right: 14, fontSize: 10, color: "var(--fg-quaternary)", fontFamily: "var(--font-mono)" }}>multimodal → notes</span>

          {PLOT.map((p) => (
            <div
              key={p.label}
              style={{
                position: "absolute",
                left: `calc(${p.x * 100}% - 6px)`,
                top: `calc(${(1 - p.y) * 100}% - 6px)`,
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              <span
                style={{
                  width: p.accent ? 14 : 10,
                  height: p.accent ? 14 : 10,
                  borderRadius: "999px",
                  background: p.accent ? "var(--accent)" : "var(--fg-secondary)",
                  boxShadow: p.accent ? "0 0 14px var(--accent-glow)" : "none",
                  border: p.accent ? "2px solid rgba(255, 99, 99, 0.3)" : "none",
                }}
              />
              <span
                style={{
                  fontSize: p.accent ? "var(--text-sm)" : "var(--text-xs)",
                  color: p.accent ? "var(--fg-primary)" : "var(--fg-tertiary)",
                  fontWeight: p.accent ? 600 : 400,
                  whiteSpace: "nowrap",
                  letterSpacing: p.accent ? "-0.01em" : 0,
                }}
              >
                {p.label}
              </span>
            </div>
          ))}
        </div>
        {/* X axis label */}
        <span />
        <div
          style={{
            color: "var(--fg-tertiary)",
            fontSize: "var(--text-xs)",
            letterSpacing: "0.12em",
            textTransform: "uppercase",
            fontFamily: "var(--font-mono)",
            textAlign: "center",
            paddingTop: 6,
          }}
        >
          Capture: audio-only → multimodal
        </div>
      </div>
    </>
  );
}

function MoatSlide() {
  return (
    <>
      <SlideEyebrow>The moat</SlideEyebrow>
      <SlideHeadline>
        Orchestration layer above the model layer. Per-team meeting corpus below it. Both compound.
      </SlideHeadline>
      <SlideBody>
        Models commoditize. Meeting capture commoditizes. The compounding asset
        is the orchestration policy that turns a meeting into the right artifact
        — and the per-team corpus that sharpens it. Twelve months in, no
        competitor can replicate either without a year of usage data they don't
        have.
      </SlideBody>
    </>
  );
}

function RoadmapSlide() {
  const milestones = [
    { tag: "v0", date: "Shipping now", body: "Meeting → spec doc. macOS only. Single user." },
    { tag: "v1", date: "Q1 2026 · 12 weeks", body: "Five archetypes. Vision agent. Team memory. One-click deploy. Multi-user reconciliation." },
    { tag: "v2", date: "Late 2026", body: "The bet — every team's meetings produce their tools. Orchestration layer for AI-native work." },
  ];
  return (
    <>
      <SlideEyebrow>Roadmap</SlideEyebrow>
      <SlideHeadline size="md">
        Three steps. Each step earns the next.
      </SlideHeadline>
      <ol style={{ listStyle: "none", margin: "clamp(2rem, 4vw, 3rem) 0 0", padding: 0, display: "grid", gap: "1rem" }}>
        {milestones.map((m) => (
          <li
            key={m.tag}
            style={{
              display: "grid",
              gridTemplateColumns: "auto auto 1fr",
              alignItems: "baseline",
              gap: "1.5rem",
              padding: "1.25rem 1.5rem",
              border: "1px solid var(--border-default)",
              borderRadius: "var(--radius-lg)",
              background: "var(--bg-elevated)",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "var(--text-xs)",
                color: "var(--accent)",
                letterSpacing: "0.04em",
                fontWeight: 600,
              }}
            >
              {m.tag}
            </span>
            <span style={{ fontSize: "var(--text-sm)", color: "var(--fg-tertiary)", fontFamily: "var(--font-mono)", letterSpacing: 0, whiteSpace: "nowrap" }}>{m.date}</span>
            <span style={{ fontSize: "var(--text-base)", color: "var(--fg-secondary)", letterSpacing: "-0.005em" }}>{m.body}</span>
          </li>
        ))}
      </ol>
    </>
  );
}

function FinancialsSlide() {
  return (
    <>
      <SlideEyebrow>Financials</SlideEyebrow>
      <SlideHeadline size="md">
        Pre-seed: $1.5M for 18 months of runway. Two engineers, two pilot deals.
      </SlideHeadline>
      <div
        style={{
          marginTop: "clamp(2rem, 4vw, 2.5rem)",
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: "clamp(1rem, 2vw, 2rem)",
        }}
      >
        <FinCard heading="Use of funds">
          <FinRow label="Founding engineers (2)" value="$640k" sub="comp + equity-acceleration ramp" />
          <FinRow label="Compute" value="$220k" sub="Anthropic + OpenAI + infra" />
          <FinRow label="Pilot delivery" value="$120k" sub="customer success, on-site setup" />
          <FinRow label="Legal + admin + buffer" value="$520k" sub="incl. SOC 2 audit, 6-month runway extension" />
        </FinCard>
        <FinCard heading="Milestones to seed">
          <FinRow label="10 paying teams" value="Q3 '26" sub="100+ engineers covered by Instinctual" />
          <FinRow label="$30k MRR" value="Q4 '26" sub="$48 / seat / month, 600 seats" />
          <FinRow label="Two enterprise pilots" value="Q1 '27" sub="LOIs in hand, deployed in production" />
          <FinRow label="Seed raise" value="$8M @ $40M" sub="targets close 18 months from pre-seed" />
        </FinCard>
      </div>
    </>
  );
}

function FinCard({ heading, children }: { heading: string; children: React.ReactNode }) {
  return (
    <div style={{ padding: "1.5rem", border: "1px solid var(--border-default)", borderRadius: "var(--radius-lg)", background: "var(--bg-elevated)" }}>
      <div
        style={{
          fontSize: "var(--text-xs)",
          letterSpacing: "0.12em",
          textTransform: "uppercase",
          color: "var(--fg-tertiary)",
          fontWeight: 500,
          marginBottom: 16,
        }}
      >
        {heading}
      </div>
      <div style={{ display: "grid", gap: 12 }}>{children}</div>
    </div>
  );
}

function FinRow({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr auto", alignItems: "baseline", gap: 12, paddingBottom: 10, borderBottom: "1px solid var(--border-subtle)" }}>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontSize: "var(--text-sm)", color: "var(--fg-primary)", letterSpacing: "-0.005em" }}>{label}</div>
        <div style={{ fontSize: "var(--text-xs)", color: "var(--fg-quaternary)", fontFamily: "var(--font-mono)", letterSpacing: 0, marginTop: 2 }}>{sub}</div>
      </div>
      <div style={{ fontSize: "var(--text-base)", fontFamily: "var(--font-mono)", color: "var(--fg-primary)", fontVariantNumeric: "tabular-nums" }}>{value}</div>
    </div>
  );
}

function TeamSlide() {
  return (
    <>
      <SlideEyebrow>Team</SlideEyebrow>
      <SlideHeadline size="md">
        One founder shipping. Pre-seed. Hiring two.
      </SlideHeadline>
      <div
        style={{
          marginTop: "clamp(2rem, 4vw, 3rem)",
          display: "grid",
          gridTemplateColumns: "auto 1fr",
          gap: "1.75rem",
          alignItems: "start",
          padding: "1.75rem",
          border: "1px solid var(--border-default)",
          borderRadius: "var(--radius-lg)",
          background: "var(--bg-elevated)",
          maxWidth: 760,
        }}
      >
        <div
          style={{
            width: 96, height: 96,
            borderRadius: "var(--radius-lg)",
            background: "linear-gradient(135deg, var(--bg-elevated-2), var(--bg-elevated-3))",
            border: "1px solid var(--border-default)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontFamily: "var(--font-display)", fontSize: "1.875rem", fontWeight: 500,
            letterSpacing: "-0.02em", color: "var(--fg-secondary)",
          }}
        >AH</div>
        <div>
          <div style={{ fontSize: "var(--text-2xl)", fontWeight: 500, letterSpacing: "-0.018em", color: "var(--fg-primary)" }}>Abdul Hameed</div>
          <div style={{ marginTop: 4, fontSize: "var(--text-sm)", fontFamily: "var(--font-mono)", color: "var(--fg-tertiary)" }}>Founder</div>
          <p style={{ marginTop: 14, fontSize: "var(--text-base)", color: "var(--fg-secondary)", lineHeight: 1.55, letterSpacing: "-0.005em" }}>
            Building Instinctual because the same meeting kept happening —
            somebody describing a tool they needed, nobody having time to
            build it. The tool should build itself. Pre-seed, shipping now.
          </p>
        </div>
      </div>
      <p style={{ marginTop: "1.5rem", fontSize: "var(--text-sm)", color: "var(--fg-tertiary)", fontFamily: "var(--font-mono)", letterSpacing: 0 }}>
        Hiring founding engineers (macOS, Python/agents, full-stack) — hameed.abdulmuhsin@gmail.com
      </p>
    </>
  );
}

function AskSlide() {
  return (
    <>
      <SlideEyebrow>The ask</SlideEyebrow>
      <SlideHeadline size="lg">
        Raising $1.5M pre-seed. Two engineering hires. Five enterprise pilots in 18 months.
      </SlideHeadline>
      <SlideBody>
        Nothing raised yet. Talking to a small number of pre-seed investors
        with agent and dev-tools conviction. If that's you and you want
        depth, the memo at <a href="/memo" style={{ color: "var(--fg-primary)" }}>/memo</a> is the deeper read.
      </SlideBody>
    </>
  );
}

function ThanksSlide() {
  return (
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "flex-start", height: "100%" }}>
      <Wordmark size="xl" accent />
      <p
        style={{
          marginTop: "1.5rem",
          fontSize: "clamp(1.25rem, 2vw, 1.75rem)",
          color: "var(--fg-secondary)",
          letterSpacing: "-0.012em",
        }}
      >
        Thank you.
      </p>
      <p
        style={{
          marginTop: "2.5rem",
          fontSize: "var(--text-base)",
          color: "var(--fg-tertiary)",
          fontFamily: "var(--font-mono)",
          letterSpacing: 0,
        }}
      >
        hameed.abdulmuhsin@gmail.com
      </p>
      <div style={{ marginTop: 36 }}>
        <InstinctualIcon size={32} active color="var(--fg-secondary)" />
      </div>
    </div>
  );
}
