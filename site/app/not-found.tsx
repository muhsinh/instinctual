import { Wordmark } from "./components/Wordmark";

export default function NotFound() {
  return (
    <main
      style={{
        minHeight: "100dvh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "1.25rem",
        padding: "clamp(2rem, 5vw, 4rem)",
        textAlign: "center",
      }}
    >
      <Wordmark size="md" />
      <h1
        className="headline"
        style={{
          fontSize: "clamp(2.5rem, 6vw, 4.5rem)",
          margin: 0,
          letterSpacing: "-0.04em",
        }}
      >
        404 · Out of frame.
      </h1>
      <p
        style={{
          fontSize: "var(--text-base)",
          color: "var(--fg-secondary)",
          maxWidth: "44ch",
          margin: 0,
        }}
      >
        The page you’re looking for moved or never existed. The site has
        only a few real surfaces — try one of these.
      </p>
      <div style={{ display: "flex", gap: 12, marginTop: "0.5rem", flexWrap: "wrap", justifyContent: "center" }}>
        <a href="/" className="btn btn-accent">
          Home
        </a>
        <a href="/deck" className="btn btn-secondary">
          Deck
        </a>
        <a href="/memo" className="btn btn-secondary">
          Memo
        </a>
      </div>
      <p
        style={{
          marginTop: "2rem",
          fontSize: "var(--text-xs)",
          color: "var(--fg-tertiary)",
          fontFamily: "var(--font-mono)",
          letterSpacing: "0.04em",
        }}
      >
        404 · instinctual.app
      </p>
    </main>
  );
}
