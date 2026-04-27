"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Four stages with viewport-triggered fade-in. Side-by-side on desktop,
 * stacked on mobile. Each stage's small SVG icon animates in via
 * IntersectionObserver — no scroll-triggered chaos.
 */

type Stage = {
  n: string;
  label: string;
  copy: string;
  icon: React.ReactNode;
};

const STAGES: Stage[] = [
  {
    n: "01",
    label: "Listen",
    copy: "Instinctual joins your meeting via screen recording. No bots, no integrations, no surprises.",
    icon: <ListenIcon />,
  },
  {
    n: "02",
    label: "Understand",
    copy: "Five agents work in parallel — tagging decisions, drafting the spec, stress-testing feasibility, surfacing clarifications, synthesizing the result.",
    icon: <UnderstandIcon />,
  },
  {
    n: "03",
    label: "Clarify",
    copy: "When something’s ambiguous, you get a one-tap question. Two seconds, no derail.",
    icon: <ClarifyIcon />,
  },
  {
    n: "04",
    label: "Ship",
    copy: "When the meeting ends, you have a working draft — not a backlog of follow-ups.",
    icon: <ShipIcon />,
  },
];

export function HowItWorks() {
  return (
    <section id="how" className="section" aria-labelledby="how-heading">
      <div className="container-page">
        <header style={{ maxWidth: "44ch", marginBottom: "clamp(2.5rem, 6vw, 4.5rem)" }}>
          <p className="eyebrow" style={{ marginBottom: 12 }}>How it works</p>
          <h2
            id="how-heading"
            className="headline"
            style={{ fontSize: "clamp(1.875rem, 4vw, 3rem)", margin: 0 }}
          >
            Four stages. All of them happen while the meeting is still happening.
          </h2>
        </header>

        <ol
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 240px), 1fr))",
            gap: "clamp(1.5rem, 3vw, 2.5rem)",
            listStyle: "none",
            margin: 0,
            padding: 0,
          }}
        >
          {STAGES.map((s, i) => (
            <StageCard key={s.n} stage={s} delay={i * 80} />
          ))}
        </ol>
      </div>
    </section>
  );
}

function StageCard({ stage, delay }: { stage: Stage; delay: number }) {
  const ref = useRef<HTMLLIElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          obs.disconnect();
        }
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.1 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <li
      ref={ref}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(8px)",
        transition: `opacity 480ms ${delay}ms cubic-bezier(0.22, 1, 0.36, 1), transform 480ms ${delay}ms cubic-bezier(0.22, 1, 0.36, 1)`,
        padding: "1.75rem 1.5rem",
        background: "linear-gradient(180deg, rgba(20, 17, 15, 0.6) 0%, rgba(20, 17, 15, 0.3) 100%)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 18,
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: "var(--text-xs)",
            color: "var(--fg-tertiary)",
            letterSpacing: "0.04em",
          }}
        >
          {stage.n}
        </span>
        <span style={{ color: "var(--fg-primary)", opacity: 0.85 }}>{stage.icon}</span>
      </div>
      <h3
        style={{
          fontSize: "var(--text-xl)",
          fontWeight: 500,
          letterSpacing: "-0.018em",
          margin: 0,
          color: "var(--fg-primary)",
        }}
      >
        {stage.label}
      </h3>
      <p
        style={{
          marginTop: 8,
          marginBottom: 0,
          fontSize: "var(--text-sm)",
          lineHeight: 1.55,
          color: "var(--fg-secondary)",
          letterSpacing: "-0.005em",
        }}
      >
        {stage.copy}
      </p>
    </li>
  );
}

/* ─── SVG icons — hand-tuned, distinctive, not generic ─── */

function ListenIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden>
      <rect x="3.5" y="6" width="21" height="13" rx="3" stroke="currentColor" strokeWidth="1.2" opacity="0.55" />
      {/* Waveform */}
      <line x1="8" y1="13" x2="8" y2="13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <line x1="11" y1="11" x2="11" y2="15" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <line x1="14" y1="9.5" x2="14" y2="16.5" stroke="var(--accent)" strokeWidth="1.6" strokeLinecap="round" />
      <line x1="17" y1="11" x2="17" y2="15" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <line x1="20" y1="12.5" x2="20" y2="13.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      <line x1="9" y1="22" x2="19" y2="22" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" opacity="0.4" />
    </svg>
  );
}

function UnderstandIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden>
      {/* Five agents = five concentric/orbiting nodes */}
      <circle cx="14" cy="14" r="2.4" fill="var(--accent)" />
      <circle cx="6.5" cy="9" r="1.6" stroke="currentColor" strokeWidth="1.2" />
      <circle cx="21.5" cy="9" r="1.6" stroke="currentColor" strokeWidth="1.2" />
      <circle cx="6.5" cy="19" r="1.6" stroke="currentColor" strokeWidth="1.2" />
      <circle cx="21.5" cy="19" r="1.6" stroke="currentColor" strokeWidth="1.2" />
      <line x1="8" y1="9.5" x2="12" y2="13" stroke="currentColor" strokeWidth="0.9" opacity="0.5" />
      <line x1="20" y1="9.5" x2="16" y2="13" stroke="currentColor" strokeWidth="0.9" opacity="0.5" />
      <line x1="8" y1="18.5" x2="12" y2="15" stroke="currentColor" strokeWidth="0.9" opacity="0.5" />
      <line x1="20" y1="18.5" x2="16" y2="15" stroke="currentColor" strokeWidth="0.9" opacity="0.5" />
    </svg>
  );
}

function ClarifyIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden>
      <rect x="4" y="7" width="20" height="11" rx="2" stroke="currentColor" strokeWidth="1.2" opacity="0.55" />
      <path d="M11 18l-2 3v-3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" opacity="0.55" />
      <text x="14" y="15" textAnchor="middle" fontSize="9" fontFamily="var(--font-mono)" fill="var(--accent)" fontWeight="600">?</text>
    </svg>
  );
}

function ShipIcon() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden>
      <path d="M5 9h13l5 5-5 5H5z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" opacity="0.55" />
      <path d="M9 14h6" stroke="var(--accent)" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M13 11.5l2.5 2.5L13 16.5" stroke="var(--accent)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
