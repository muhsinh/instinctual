"use client";

import { useState } from "react";

/**
 * Early-access form. Posts to /api/early-access (Next Route Handler).
 * Three fields: email, role, what-meetings. Inline success state on submit.
 *
 * Validation is intentionally lightweight on the client (HTML required +
 * type=email). Real validation happens server-side; this is enterprise
 * basic hygiene, not a replacement for the API endpoint's checks.
 */

const ROLES = ["PM / TPM", "Engineering", "Founder / Exec", "Designer", "Other"];

type Status = "idle" | "submitting" | "success" | "error";

export function EarlyAccess() {
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("submitting");
    setError(null);
    const fd = new FormData(e.currentTarget);
    const payload = {
      email: String(fd.get("email") ?? ""),
      role: String(fd.get("role") ?? ""),
      meetings: String(fd.get("meetings") ?? ""),
    };
    try {
      const res = await fetch("/api/early-access", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error ?? `Request failed (${res.status})`);
      }
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Something went wrong");
    }
  }

  return (
    <section id="early-access" className="section" aria-labelledby="ea-heading">
      <div className="container-narrow">
        <header style={{ marginBottom: "clamp(2rem, 5vw, 3rem)", textAlign: "left" }}>
          <p className="eyebrow" style={{ marginBottom: 12 }}>Early access</p>
          <h2
            id="ea-heading"
            className="headline"
            style={{ fontSize: "clamp(1.875rem, 4vw, 2.75rem)", margin: 0 }}
          >
            We’re onboarding teams one at a time.
          </h2>
          <p
            style={{
              marginTop: "1rem",
              fontSize: "var(--text-base)",
              color: "var(--fg-secondary)",
              maxWidth: "52ch",
              letterSpacing: "-0.005em",
            }}
          >
            Tell us a little about your team. We read every submission and reach out within
            a few days if there’s a fit.
          </p>
        </header>

        {status === "success" ? (
          <SuccessState />
        ) : (
          <form
            onSubmit={handleSubmit}
            style={{
              display: "grid",
              gap: 14,
              padding: "1.5rem",
              borderRadius: "var(--radius-xl)",
              border: "1px solid var(--border-default)",
              background: "var(--bg-elevated)",
            }}
            aria-busy={status === "submitting"}
          >
            <Field label="Work email" htmlFor="email">
              <input
                required
                id="email"
                name="email"
                type="email"
                placeholder="you@team.com"
                autoComplete="email"
                style={inputStyle}
              />
            </Field>

            <Field label="Role" htmlFor="role">
              <select required id="role" name="role" defaultValue="" style={inputStyle}>
                <option value="" disabled>
                  Select a role…
                </option>
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="What kind of meetings do you want this for?" htmlFor="meetings">
              <textarea
                id="meetings"
                name="meetings"
                rows={3}
                placeholder="Standups, design reviews, customer calls, exec syncs…"
                style={{ ...inputStyle, resize: "vertical", minHeight: 88, fontFamily: "var(--font-body)" }}
              />
            </Field>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                marginTop: 6,
                flexWrap: "wrap",
              }}
            >
              <button
                type="submit"
                className="btn btn-accent"
                disabled={status === "submitting"}
                style={{ opacity: status === "submitting" ? 0.7 : 1 }}
              >
                {status === "submitting" ? "Sending…" : "Request early access"}
              </button>
              {status === "error" && error && (
                <span style={{ fontSize: "var(--text-sm)", color: "var(--accent)" }}>{error}</span>
              )}
              <span
                style={{
                  marginLeft: "auto",
                  fontSize: "var(--text-xs)",
                  color: "var(--fg-tertiary)",
                  fontFamily: "var(--font-mono)",
                  letterSpacing: "0.02em",
                }}
              >
                We’ll never share your email.
              </span>
            </div>
          </form>
        )}
      </div>
    </section>
  );
}

function Field({ label, htmlFor, children }: { label: string; htmlFor: string; children: React.ReactNode }) {
  return (
    <label htmlFor={htmlFor} style={{ display: "grid", gap: 6 }}>
      <span
        style={{
          fontSize: "var(--text-xs)",
          letterSpacing: "0.04em",
          textTransform: "uppercase",
          color: "var(--fg-tertiary)",
          fontWeight: 500,
        }}
      >
        {label}
      </span>
      {children}
    </label>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.7rem 0.85rem",
  borderRadius: "var(--radius-md)",
  background: "var(--bg-elevated-2)",
  border: "1px solid var(--border-default)",
  color: "var(--fg-primary)",
  fontSize: "var(--text-sm)",
  fontFamily: "var(--font-body)",
  letterSpacing: "-0.005em",
  outline: "none",
  transition: "border-color 150ms ease, background 150ms ease",
};

function SuccessState() {
  return (
    <div
      role="status"
      style={{
        padding: "2rem 1.5rem",
        borderRadius: "var(--radius-xl)",
        border: "1px solid rgba(74, 222, 128, 0.35)",
        background: "linear-gradient(180deg, rgba(74, 222, 128, 0.05), rgba(74, 222, 128, 0.02))",
        textAlign: "center",
      }}
    >
      <div
        style={{
          margin: "0 auto 14px",
          width: 38,
          height: 38,
          borderRadius: "var(--radius-full)",
          background: "rgba(74, 222, 128, 0.15)",
          border: "1px solid rgba(74, 222, 128, 0.4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "var(--success)",
        }}
        aria-hidden
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path
            d="M3.5 8.5l3 3 6-6.5"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <h3
        style={{
          margin: 0,
          fontSize: "var(--text-xl)",
          fontWeight: 500,
          letterSpacing: "-0.018em",
          color: "var(--fg-primary)",
        }}
      >
        You’re on the list.
      </h3>
      <p
        style={{
          marginTop: 8,
          marginBottom: 18,
          fontSize: "var(--text-sm)",
          color: "var(--fg-secondary)",
          letterSpacing: "-0.005em",
        }}
      >
        We’ll reach out within a few days. In the meantime, here’s the deck.
      </p>
      <a href="/deck" className="btn btn-secondary">
        View the deck
      </a>
    </div>
  );
}
