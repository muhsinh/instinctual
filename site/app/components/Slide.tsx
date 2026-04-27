"use client";

import { ReactNode } from "react";

/**
 * Single full-viewport slide. Used by /deck. Print stylesheet maps each
 * slide to a single PDF page. Keyboard nav + slide indicator live in the
 * deck page itself, not here.
 */

export function Slide({
  id,
  index,
  total,
  visible,
  children,
  background,
}: {
  id: string;
  index: number;
  total: number;
  visible: boolean;
  children: ReactNode;
  background?: string;
}) {
  return (
    <section
      id={id}
      role="group"
      aria-roledescription="slide"
      aria-label={`Slide ${index + 1} of ${total}`}
      className="page-break"
      style={{
        position: "absolute",
        inset: 0,
        opacity: visible ? 1 : 0,
        pointerEvents: visible ? "auto" : "none",
        transition: "opacity 220ms ease",
        background: background ?? "var(--bg-base)",
        display: "flex",
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          padding: "clamp(2rem, 5vw, 4.5rem)",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          maxWidth: "1200px",
          marginInline: "auto",
        }}
      >
        {children}
      </div>
    </section>
  );
}

export function SlideEyebrow({ children }: { children: ReactNode }) {
  return (
    <p
      className="eyebrow"
      style={{ marginBottom: "clamp(1.5rem, 3vw, 2.5rem)", marginTop: 0 }}
    >
      {children}
    </p>
  );
}

export function SlideHeadline({
  children,
  size = "lg",
}: {
  children: ReactNode;
  size?: "md" | "lg" | "xl";
}) {
  const fontSize = size === "xl" ? "clamp(3rem, 7vw, 6rem)" : size === "lg" ? "clamp(2rem, 5vw, 4.25rem)" : "clamp(1.75rem, 3.5vw, 2.5rem)";
  return (
    <h2
      className="headline"
      style={{
        fontSize,
        lineHeight: 1.05,
        margin: 0,
        maxWidth: "22ch",
        letterSpacing: "-0.035em",
      }}
    >
      {children}
    </h2>
  );
}

export function SlideBody({ children }: { children: ReactNode }) {
  return (
    <p
      style={{
        marginTop: "clamp(1rem, 2.5vw, 1.75rem)",
        marginBottom: 0,
        fontSize: "clamp(1.05rem, 1.75vw, 1.5rem)",
        lineHeight: 1.4,
        color: "var(--fg-secondary)",
        maxWidth: "52ch",
        letterSpacing: "-0.005em",
      }}
    >
      {children}
    </p>
  );
}
