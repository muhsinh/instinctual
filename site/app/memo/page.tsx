import type { Metadata } from "next";
import { Wordmark } from "../components/Wordmark";

export const metadata: Metadata = {
  title: "Why now / why us",
  description:
    "A long-form memo on why a meeting-to-working-tool product can exist now, why the category is empty, and why we're the team to fill it.",
  openGraph: {
    title: "Instinctual — Why now / why us",
    description:
      "A 2,000-word memo on Instinctual's thesis, the category map, and the team building it.",
  },
};

/**
 * Long-form essay. Designed for reading, not marketing scanning.
 * Wider line-height, narrower max-width (65ch), drop caps on section
 * openings, footnotes as hovers. Print stylesheet handles PDF export.
 */

export default function MemoPage() {
  return (
    <main>
      {/* Top bar */}
      <header
        className="no-print"
        style={{
          padding: "20px clamp(1.25rem, 5vw, 2.5rem)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid var(--border-subtle)",
        }}
      >
        <a href="/" style={{ color: "var(--fg-secondary)" }} aria-label="Back to Instinctual home">
          <Wordmark size="md" />
        </a>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <a href="/deck" style={{ fontSize: "var(--text-sm)", color: "var(--fg-secondary)" }}>
            Deck
          </a>
          <a href="/#early-access" className="btn btn-secondary" style={{ padding: "0.5rem 0.9rem" }}>
            Early access
          </a>
        </div>
      </header>

      <article
        className="container-prose memo"
        style={{
          paddingTop: "clamp(3rem, 8vh, 6rem)",
          paddingBottom: "clamp(4rem, 10vh, 7rem)",
        }}
      >
        <p
          className="eyebrow"
          style={{ marginBottom: 14 }}
        >
          Memo · {new Date().getFullYear()}
        </p>
        <h1
          className="headline"
          style={{
            fontSize: "clamp(2.25rem, 5vw, 3.75rem)",
            margin: 0,
            letterSpacing: "-0.035em",
            lineHeight: 1.05,
            maxWidth: "20ch",
          }}
        >
          Why now / why us.
        </h1>
        <p
          style={{
            marginTop: 18,
            fontSize: "var(--text-lg)",
            color: "var(--fg-secondary)",
            letterSpacing: "-0.005em",
            maxWidth: "55ch",
          }}
        >
          A 2,000-word read on Instinctual's thesis, the category, the product, the
          technical foundation, and the team. Written for investors and
          customers who want depth before a call.
        </p>
        <p
          className="eyebrow"
          style={{
            marginTop: 14,
            color: "var(--fg-quaternary)",
            fontFamily: "var(--font-mono)",
            textTransform: "none",
            letterSpacing: 0,
          }}
        >
          ~10 minute read · last updated {new Date().toLocaleDateString("en-US", { month: "long", year: "numeric" })}
        </p>

        <hr
          style={{
            margin: "clamp(2rem, 5vw, 3.5rem) 0",
            border: 0,
            borderTop: "1px solid var(--border-subtle)",
          }}
        />

        <Section heading="The thesis" id="thesis">
          <DropCap>M</DropCap>eetings produce decisions. Decisions produce
          backlogs. Backlogs produce drift. Two weeks after a thirty-minute
          conversation, an engineer is rebuilding the agreement from a Slack
          scroll, with the wrong scope, after one of the original participants
          has rotated to another team. This loop is the dominant cost of running
          a software org at scale, and it has been for forty years.
          <P>
            The shift now underway is that AI can compress
            decision-to-artifact from weeks to minutes. Real-time multimodal
            models can interpret meetings and screens cheaply. Agent
            orchestration can run parallel speculative builds. Enterprise AI
            budgets are unlimited but unstructured. The window to put a layer
            between meetings and shipped artifacts is open and shallow.
          </P>
          <P>
            Instinctual is that layer. A macOS menu bar app that listens to your
            meetings, watches what you're showing, and produces working
            artifacts — scheduled scripts, dashboards, Linear epics, structured
            spec docs — by the time the meeting ends. It is not a note-taker,
            and it is not an agent IDE. It is the orchestration surface that
            sits between the room and the artifact, doing the translation
            nobody has time to do.
          </P>
        </Section>

        <Section heading="Why now" id="why-now">
          <DropCap>T</DropCap>hree converging factors make this possible at
          this exact moment, and not eighteen months ago.
          <P>
            <strong>Real-time multimodal models matured.</strong> Interpreting a
            meeting plus a screen at 1–2 frames per second was research-grade
            cost a year ago and prohibitive in production. Today the per-meeting
            cost of full multimodal capture is sub-cent at consumer model
            quality. Anthropic, OpenAI, and Google all ship models with cached
            prompt prefixes that make this affordable at scale. The capability
            curve crossed the unit-economics curve in mid-2025.
          </P>
          <P>
            <strong>Agent orchestration crossed from research into shipping
            tools.</strong> Cursor 2.0 ships eight parallel agents on isolated
            VMs. Replit Agent 3 builds working apps in 36 minutes from typed
            prompts. The VS Code team published their workflow of running
            multiple agent sessions during meetings. The orchestration patterns
            (speculative parallelism, structured handoff between specialized
            agents, cost-bounded reasoning loops) are now well-understood
            engineering, not research bets. We can build on them.
          </P>
          <P>
            <strong>Enterprise AI budgets are unlimited but undisciplined.</strong>{" "}
            IDC projects $45B of global enterprise AI spend in 2025
            <Footnote n={1}>IDC, Worldwide AI Spending Guide, March 2025.</Footnote>,
            most of it going to seat-based tools without a plan for how those
            tools integrate with each other. CIOs have AI budget but no
            integration story. The first product that can sit between
            meetings and existing systems — and reliably produce something the
            team accepts — captures budget that's already allocated but
            undirected.
          </P>
          <P>
            None of these factors will be true forever. Models will commoditize.
            Capture will commoditize. The window for owning the orchestration
            layer above commodity inputs is roughly twelve to eighteen months.
            We're spending that window building defensible compounding assets,
            not chasing features.
          </P>
        </Section>

        <Section heading="The category" id="category">
          <DropCap>T</DropCap>he honest competitive picture is that three
          adjacent categories exist and a fourth — ours — is empty.
          <P>
            <strong>Note-takers</strong> own meeting capture. Granola raised
            $43M to $250M post in 2025
            <Footnote n={2}>TechCrunch, Granola Series B, 2025.</Footnote>{" "}
            and is becoming the data layer for the AI agent ecosystem.
            Otter, Fellow, and Sembly cover the long tail. They stop at notes
            and summaries. Microsoft Teams Facilitator generates Loop docs
            from meetings for free with any M365 Copilot license — strong on
            distribution, weak on output beyond markdown.
          </P>
          <P>
            <strong>Agent builders</strong> own code-from-typed-prompt. Cursor
            crossed $2B ARR in 2025
            <Footnote n={3}>The Information, Cursor revenue, 2025.</Footnote>{" "}
            with eight parallel agents per session. Replit, Lovable, and Bolt
            ship apps from natural-language briefs. They start from a typed
            prompt, which means a person had to translate the meeting into a
            prompt first — the exact translation work we want to eliminate.
          </P>
          <P>
            <strong>The empty quadrant</strong> is multimodal capture × working
            artifact output. Granola is deliberately audio-only. Cursor needs
            you to type. Nobody starts from a meeting and orchestrates
            concurrent build threads with screen context. That whitespace is
            empty because it's hard, not because nobody noticed.
            ScreenCaptureKit + multimodal models + agent orchestration is a
            three-leg stool that only became financially viable this year.
          </P>
        </Section>

        <Section heading="The product" id="product">
          <DropCap>I</DropCap>nstinct is a 28-pixel-tall icon in your menu
          bar. You start a meeting; the icon pulses. A panel slides down
          showing a structured spec forming as the conversation happens —
          decisions, scope, stack, open questions. Five agents work in
          parallel: Tagger filters the transcript, Builder drafts the
          artifact, Critic stress-tests feasibility, Clarifier surfaces
          one-tap questions when something is genuinely ambiguous, Synthesis
          classifies the meeting and routes to the right archetype.
          <P>
            <strong>Code as the artifact, not documents.</strong> When the
            meeting outcome is concrete (build a dashboard, write a cron job,
            structure a Linear epic), Instinctual generates working code via a
            Claude Code subprocess. When it isn't, you get a structured spec
            doc — but the code path is the lead. Note-takers stop at PRDs;
            we keep going until something runs.
          </P>
          <P>
            <strong>Screen-aware, not audio-only.</strong> ScreenCaptureKit
            captures both audio and 1–2fps video. A Vision agent interprets
            what's on screen — Figma, dashboards, code, docs — and feeds the
            Builder so artifacts are grounded in what the team actually saw,
            not just what they said. This is the single biggest capability
            gap vs. Granola, and it's structural: Granola is deliberately
            audio-only because their distribution depends on it.
          </P>
          <P>
            <strong>Multi-model orchestration during the meeting.</strong>{" "}
            Speculative parallel builds, ranked, revised, and converged
            before the meeting ends. The eager-build pattern means Builder
            fires by minute one and revises through the meeting; you never
            wait. Granola's API is read-after-the-fact; Cursor's agents start
            from a typed prompt; nobody else orchestrates concurrent build
            threads from a live meeting.
          </P>
        </Section>

        <Section heading="The technical foundation" id="tech">
          <DropCap>F</DropCap>ive things compound, and we're building each
          one as a first-class system, not a feature.
          <P>
            <strong>The five-agent loop</strong> with shared session state,
            mandatory prompt caching on every call, and a cost cap circuit
            breaker. Caveman-terse inter-agent communication; normal English
            to the user. Eager build. One active clarification at a time. All
            patterns we've validated in v0 and that survive contact with real
            meetings.
          </P>
          <P>
            <strong>The recipe layer.</strong> Each archetype (scheduled
            script, Streamlit dashboard, Linear epic, spec doc, design
            mockup) is a structured contract: classifier prompt, BuildPlan
            schema, Claude Code template, validation rules, deployment
            target. New archetypes are added by writing a new recipe file —
            no core code changes. This is the Skill pattern applied to our
            domain, and it's what lets the product grow without rewriting.
          </P>
          <P>
            <strong>The team memory layer.</strong> Postgres + pgvector
            storing per-team decision history, vocabulary, stack inference,
            voice fingerprints, and per-recipe acceptance rates. Queried at
            session start and injected into every agent's cached prefix.
            After ten meetings with the same team, Instinctual knows their
            stack, their conventions, their recurring projects — and
            produces artifacts that match the team, not generic ones.
          </P>
          <P>
            <strong>The corpus.</strong> Every session writes to{" "}
            <code className="code-voice">instinct.corpus</code>: anonymized
            transcript, classified archetype, generated artifact, accept /
            reject signal, deployment outcome. Designed like it will live for
            years and feed downstream RL/fine-tuning. After six months of
            usage, the routing decisions are backed by tens of thousands of
            meeting → artifact pairs no competitor can replicate.
          </P>
          <P>
            <strong>Active feasibility checking.</strong> Critic doesn't just
            stress-test against the meeting — it queries reality. Are the
            APIs being discussed actually accessible from the team's stack?
            Does the Linear workspace mentioned exist? When Critic finds a
            real blocker, it surfaces via Clarifier mid-meeting so the team
            can adjust before agreeing on something that won't work.
          </P>
        </Section>

        <Section heading="The roadmap" id="roadmap">
          <DropCap>v</DropCap>0 is shipping now: meeting → spec doc, single
          user, macOS only. v1 over the next twelve weeks adds five recipe
          archetypes, the Vision agent, team memory, voice fingerprinting,
          one-click deployment to Modal / Vercel / GitHub Actions, and
          multi-user session reconciliation. v2 in late 2026 is the bet:
          every team's meetings produce their tools, deployed continuously,
          and Instinctual is the orchestration surface for AI-native work
          across the org.
          <P>
            The phasing matters because some pieces compound only with time.
            Team memory needs accumulated meeting data. Deployment needs real
            customer credentials. Voice fingerprinting needs per-person
            sample sets. We're not trying to ship all of v1 in one push —
            we're sequencing for compounding leverage, not heroics.
          </P>
        </Section>

        <Section heading="Why us" id="why-us">
          <DropCap>I</DropCap>'m Abdul Hameed. I'm building Instinctual
          alone right now from a kitchen table, pre-seed, with nothing
          raised yet. This section will get longer once there's more
          to say without exaggerating; for now the honest version is
          short.
          <P>
            What I'll defend on a call: I've spent the last several years
            in and around AI engineering work, watching the same loop —
            a meeting that produces a decision, then weeks before
            anything ships. I've built variants of the meeting → working
            tool flow by hand more times than I can count, and the
            artifact that came out always lagged the conversation that
            produced it. The product I want to ship is the one that
            doesn't.
          </P>
          <P>
            What I won't claim in this memo: funding, advisors, or
            credentials I can't substantiate in a thirty-minute call.
            If a number or affiliation isn't in the deck or this memo,
            it doesn't exist yet.
          </P>
          <P>
            I'm hiring two founding engineers — macOS, Python/agents,
            full-stack — and looking for a small number of pre-seed
            investors with conviction in agents and developer tools.
            <a href="mailto:hameed.abdulmuhsin@gmail.com" style={{ color: "var(--fg-primary)" }}>
              {" "}If that's you, email me directly
            </a>
            . The sooner the better; we're building either way, but
            the right partners shorten the timeline meaningfully.
          </P>
        </Section>

        <hr
          style={{
            margin: "clamp(3rem, 6vw, 4rem) 0 2rem",
            border: 0,
            borderTop: "1px solid var(--border-subtle)",
          }}
        />

        <p
          style={{
            fontSize: "var(--text-sm)",
            color: "var(--fg-tertiary)",
            fontFamily: "var(--font-mono)",
            letterSpacing: 0,
          }}
        >
          <a href="mailto:hameed.abdulmuhsin@gmail.com" style={{ color: "var(--fg-secondary)" }}>hameed.abdulmuhsin@gmail.com</a> · <a href="/" style={{ color: "var(--fg-secondary)" }}>home</a> · <a href="/deck" style={{ color: "var(--fg-secondary)" }}>deck</a>
        </p>
      </article>

      <style>{memoStyles}</style>
    </main>
  );
}

function Section({
  heading,
  id,
  children,
}: {
  heading: string;
  id: string;
  children: React.ReactNode;
}) {
  return (
    <section
      id={id}
      style={{ marginBottom: "clamp(2.5rem, 6vw, 4rem)", scrollMarginTop: "5rem" }}
    >
      <h2
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "clamp(1.5rem, 2.5vw, 2rem)",
          fontWeight: 500,
          letterSpacing: "-0.025em",
          color: "var(--fg-primary)",
          margin: "0 0 1.25rem",
        }}
      >
        {heading}
      </h2>
      <div className="memo-prose">{children}</div>
    </section>
  );
}

function DropCap({ children }: { children: React.ReactNode }) {
  return (
    <span
      style={{
        float: "left",
        fontFamily: "var(--font-display)",
        fontSize: "3.5em",
        lineHeight: 0.85,
        marginRight: "0.12em",
        marginTop: "0.05em",
        color: "var(--accent)",
        fontWeight: 500,
        letterSpacing: "-0.04em",
      }}
    >
      {children}
    </span>
  );
}

function P({ children }: { children: React.ReactNode }) {
  return <p style={{ marginBlock: "1.1em" }}>{children}</p>;
}

function Footnote({ n, children }: { n: number; children: React.ReactNode }) {
  return (
    <sup
      tabIndex={0}
      style={{
        position: "relative",
        marginLeft: 2,
        cursor: "help",
        fontFamily: "var(--font-mono)",
        fontSize: "0.7em",
        color: "var(--accent)",
        fontWeight: 500,
      }}
      className="footnote"
    >
      [{n}]
      <span
        className="footnote-popover"
        role="note"
        style={{
          position: "absolute",
          top: "calc(100% + 6px)",
          left: 0,
          minWidth: 240,
          maxWidth: 320,
          padding: "10px 12px",
          background: "var(--bg-elevated-2)",
          border: "1px solid var(--border-default)",
          borderRadius: 6,
          fontSize: 12,
          fontWeight: 400,
          fontFamily: "var(--font-body)",
          color: "var(--fg-secondary)",
          letterSpacing: 0,
          lineHeight: 1.5,
          zIndex: 50,
          boxShadow: "var(--shadow-md)",
        }}
      >
        {children}
      </span>
    </sup>
  );
}

const memoStyles = `
  .memo-prose {
    font-size: clamp(1.05rem, 1.4vw, 1.18rem);
    line-height: 1.75;
    color: var(--fg-primary);
    letter-spacing: -0.005em;
  }
  .memo-prose strong { color: var(--fg-primary); font-weight: 600; }
  .memo-prose a { color: var(--accent); text-decoration: underline; text-decoration-color: rgba(255, 99, 99, 0.3); text-underline-offset: 2px; }
  .memo-prose a:hover { text-decoration-color: var(--accent); }

  .footnote .footnote-popover {
    opacity: 0;
    transform: translateY(-4px);
    pointer-events: none;
    transition: opacity 150ms ease, transform 150ms ease;
  }
  .footnote:hover .footnote-popover, .footnote:focus .footnote-popover, .footnote:focus-visible .footnote-popover {
    opacity: 1;
    transform: translateY(0);
    pointer-events: auto;
  }
`;
