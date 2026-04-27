"use client";

import { useEffect, useRef } from "react";
import { LiveSpecPreview } from "./LiveSpecPreview";
import { ClarificationBanner } from "./ClarificationBanner";
import { InstinctualIcon } from "./InstinctualIcon";
import { PipelineOverlay } from "./PipelineOverlay";

/**
 * The MenuBarMock is the hero's single dominant focal point — sized large
 * (~960px max-width) so it occupies most of the viewport. It carries:
 *
 *   - A faithful macOS menu bar strip with Instinctual active.
 *   - The animated LiveSpecPreview running the streamlit_demo fixture.
 *   - The ClarificationBanner appearing periodically.
 *   - The PipelineOverlay (collapsible model-routing display).
 *
 * Motion Layer B lives here: a RAF-throttled scroll listener writes
 * --mock-rotate-x / --mock-translate-y / --mock-scale CSS vars on the
 * stage element. The mock subtly tilts on the X axis and translates as
 * the user scrolls, like a deck card riding past. No transitions on the
 * transform — the RAF drives smooth updates directly.
 *
 * Cursor proximity (Layer C, icon side): we read the lerped cursor
 * position from --cursor-x/y and accelerate the icon pulse when the
 * cursor is near. Implemented as a separate RAF that updates the icon
 * element's --pulse-dur var.
 */

function AppleGlyph() {
  return (
    <svg width="11" height="13" viewBox="0 0 11 13" fill="none" aria-hidden style={{ opacity: 0.85 }}>
      <path
        d="M8.5 6.8c0-1.7 1.4-2.5 1.5-2.5-0.8-1.2-2.1-1.4-2.5-1.4-1.1-0.1-2.1 0.6-2.6 0.6-0.5 0-1.4-0.6-2.3-0.6-1.2 0-2.3 0.7-2.9 1.8-1.2 2.1-0.3 5.2 0.9 6.9 0.6 0.8 1.3 1.8 2.2 1.7 0.9 0 1.2-0.6 2.3-0.6 1.1 0 1.4 0.6 2.3 0.5 0.9 0 1.6-0.8 2.2-1.7 0.7-1 1-1.9 1-2 0 0-1.9-0.8-2-2.7zm-1.7-5C7.3 1.2 7.6 0.4 7.6 0c-0.7 0-1.5 0.5-2 1.1-0.4 0.5-0.8 1.3-0.7 2.1 0.7 0 1.4-0.4 1.9-1z"
        fill="currentColor"
      />
    </svg>
  );
}

function BatteryGlyph() {
  return (
    <svg width="22" height="10" viewBox="0 0 22 10" fill="none" aria-hidden style={{ opacity: 0.55 }}>
      <rect x="0.5" y="1.5" width="18" height="7" rx="1.5" stroke="currentColor" strokeWidth="0.8" fill="none" />
      <rect x="2" y="3" width="13" height="4" rx="0.5" fill="currentColor" />
      <rect x="20" y="4" width="1.2" height="2" rx="0.5" fill="currentColor" opacity="0.7" />
    </svg>
  );
}

function WifiGlyph() {
  return (
    <svg width="14" height="10" viewBox="0 0 14 10" fill="none" aria-hidden style={{ opacity: 0.65 }}>
      <path d="M7 8.4a1 1 0 100-2 1 1 0 000 2z" fill="currentColor" />
      <path d="M3.4 5.4a5 5 0 017.2 0" stroke="currentColor" strokeWidth="1" strokeLinecap="round" fill="none" />
      <path d="M1 3a8.5 8.5 0 0112 0" stroke="currentColor" strokeWidth="1" strokeLinecap="round" fill="none" />
    </svg>
  );
}

export function MenuBarMock() {
  const stageRef = useRef<HTMLDivElement>(null);
  const iconRef = useRef<HTMLSpanElement>(null);

  /* Layer B — scroll-driven perspective */
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const stage = stageRef.current;
    if (!stage) return;

    let raf = 0;
    let ticking = false;

    const update = () => {
      const rect = stage.getBoundingClientRect();
      const wh = window.innerHeight;
      const elementCenter = rect.top + rect.height / 2;
      const viewportCenter = wh / 2;
      // -1 (above viewport) to +1 (below). Clamp.
      const offset = Math.max(-1, Math.min(1, (elementCenter - viewportCenter) / wh));
      // Subtle: 4° max tilt, 28px max translate, 0.97-1 scale.
      const rotateX = -offset * 3.5;
      const translateY = offset * 28;
      const scale = 1 - Math.abs(offset) * 0.025;
      stage.style.setProperty("--mock-rotate-x", `${rotateX.toFixed(2)}deg`);
      stage.style.setProperty("--mock-translate-y", `${translateY.toFixed(2)}px`);
      stage.style.setProperty("--mock-scale", `${scale.toFixed(4)}`);
      ticking = false;
    };

    const onScroll = () => {
      if (!ticking) {
        raf = requestAnimationFrame(update);
        ticking = true;
      }
    };

    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);

  /* Layer C — icon-pulse cursor proximity */
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (window.matchMedia("(hover: none)").matches) return;

    const icon = iconRef.current;
    if (!icon) return;

    let raf = 0;
    let targetDur = 2400;
    let currentDur = 2400;
    let lastClientX = -9999;
    let lastClientY = -9999;

    const onMove = (e: PointerEvent) => {
      lastClientX = e.clientX;
      lastClientY = e.clientY;
    };

    const tick = () => {
      const rect = icon.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dist = Math.hypot(lastClientX - cx, lastClientY - cy);
      // 0 (far) → 1 (very close). Anything > 320px reads as "not near".
      const proximity = Math.max(0, Math.min(1, 1 - dist / 320));
      // Closer cursor → faster pulse: 2400ms (default) → 900ms (very close).
      targetDur = 2400 - proximity * 1500;
      currentDur += (targetDur - currentDur) * 0.08;
      icon.style.setProperty("--pulse-dur", `${Math.round(currentDur)}ms`);
      raf = requestAnimationFrame(tick);
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    raf = requestAnimationFrame(tick);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onMove);
    };
  }, []);

  return (
    <div
      ref={stageRef}
      className="menu-bar-stage"
      role="img"
      aria-label="Instinctual running in the macOS menu bar — panel open showing a Streamlit dashboard spec being built in real time during a meeting"
      style={{
        position: "relative",
        width: "100%",
        maxWidth: 960,
        marginInline: "auto",
        userSelect: "none",
      }}
    >
      <div className="menu-bar-stage-inner" style={{ position: "relative" }}>
        {/* Faint glow under the panel — independent of the global mesh */}
        <div
          aria-hidden
          style={{
            position: "absolute",
            inset: "-40px -60px",
            background:
              "radial-gradient(ellipse 60% 40% at 50% 30%, rgba(255, 99, 99, 0.10) 0%, transparent 60%)",
            filter: "blur(40px)",
            zIndex: 0,
            pointerEvents: "none",
          }}
        />

        {/* Menu bar strip */}
        <div
          style={{
            position: "relative",
            height: 30,
            borderRadius: "10px 10px 0 0",
            background: "linear-gradient(180deg, rgba(20, 17, 15, 0.92) 0%, rgba(20, 17, 15, 0.78) 100%)",
            border: "1px solid var(--border-default)",
            borderBottom: "none",
            backdropFilter: "blur(24px)",
            WebkitBackdropFilter: "blur(24px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 12px",
            fontSize: 11.5,
            color: "var(--fg-secondary)",
            fontFamily: "var(--font-body)",
            letterSpacing: "-0.005em",
          }}
        >
          <div style={{ display: "flex", gap: 14, alignItems: "center", minWidth: 0, overflow: "hidden" }}>
            <AppleGlyph />
            <span style={{ fontWeight: 600, color: "var(--fg-primary)" }}>Zoom</span>
            <span className="menubar-hide-narrow" style={{ opacity: 0.6 }}>Meeting</span>
            <span className="menubar-hide-narrow" style={{ opacity: 0.6 }}>View</span>
            <span className="menubar-hide-narrow" style={{ opacity: 0.6 }}>Window</span>
          </div>
          <div style={{ display: "flex", gap: 12, alignItems: "center", flexShrink: 0 }}>
            <span className="menubar-hide-narrow" style={{ display: "inline-flex" }}><BatteryGlyph /></span>
            <span className="menubar-hide-narrow" style={{ display: "inline-flex" }}><WifiGlyph /></span>
            <span
              ref={iconRef}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                padding: "3px 7px",
                marginInline: -2,
                borderRadius: 5,
                background: "var(--accent-muted)",
                color: "var(--fg-primary)",
                position: "relative",
              }}
            >
              <InstinctualIcon size={14} active color="var(--fg-primary)" />
              <span style={{ fontSize: 11, fontWeight: 500, letterSpacing: "-0.005em" }}>
                Listening · 14:32
              </span>
            </span>
            <span className="menubar-hide-narrow" style={{ opacity: 0.55, fontVariantNumeric: "tabular-nums" }}>2:47 PM</span>
          </div>
        </div>

        {/* The panel */}
        <div
          style={{
            position: "relative",
            background: "linear-gradient(180deg, var(--bg-elevated) 0%, var(--bg-elevated-2) 100%)",
            border: "1px solid var(--border-default)",
            borderRadius: "0 10px 16px 16px",
            boxShadow: "var(--shadow-panel)",
            overflow: "hidden",
            minHeight: 420,
          }}
        >
          {/* Panel header */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "16px 20px",
              borderBottom: "1px solid var(--border-subtle)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 12, minWidth: 0, flex: "1 1 auto" }}>
              <InstinctualIcon size={18} active color="var(--fg-primary)" />
              <div style={{ display: "flex", flexDirection: "column", lineHeight: 1.15, minWidth: 0, flex: "1 1 auto" }}>
                <span
                  style={{
                    fontSize: 14.5,
                    fontWeight: 500,
                    color: "var(--fg-primary)",
                    letterSpacing: "-0.012em",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  Activation funnel dashboard
                </span>
                <span
                  style={{
                    fontSize: 11,
                    color: "var(--fg-tertiary)",
                    fontFamily: "var(--font-mono)",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  meeting · 4 attendees · synthesis → streamlit_dashboard
                </span>
              </div>
            </div>
            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <button
                aria-label="Pause"
                style={{
                  width: 24, height: 24, borderRadius: 6,
                  display: "inline-flex", alignItems: "center", justifyContent: "center",
                  color: "var(--fg-tertiary)",
                  background: "transparent",
                }}
              >
                <svg width="10" height="10" viewBox="0 0 9 9" fill="none">
                  <rect x="1.5" y="1" width="2" height="7" rx="0.5" fill="currentColor" />
                  <rect x="5.5" y="1" width="2" height="7" rx="0.5" fill="currentColor" />
                </svg>
              </button>
            </div>
          </div>

          {/* Live spec preview (animated) */}
          <div style={{ padding: "20px 22px 28px", minHeight: 320 }}>
            <LiveSpecPreview />
          </div>

          {/* Clarification banner — appears periodically over the panel */}
          <ClarificationBanner />

          {/* Pipeline overlay — collapsible "real product" debug panel */}
          <PipelineOverlay />

          {/* Footer status strip */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "12px 20px",
              borderTop: "1px solid var(--border-subtle)",
              background: "rgba(0,0,0,0.2)",
              fontSize: 11,
              color: "var(--fg-tertiary)",
              fontFamily: "var(--font-mono)",
            }}
          >
            <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
              <span
                style={{
                  width: 6, height: 6, borderRadius: "999px",
                  background: "var(--success)",
                  boxShadow: "0 0 6px rgba(74, 222, 128, 0.5)",
                }}
              />
              5 agents · synthesizing
            </span>
            <span>Builder revising · v3 · 0.18 USD</span>
          </div>
        </div>
      </div>
    </div>
  );
}
