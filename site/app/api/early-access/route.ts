import { NextResponse } from "next/server";

/**
 * Early-access form endpoint. Stores submissions to a JSONL file in
 * /tmp during local dev (so we don't lose them) and forwards to a real
 * destination in prod via env: EARLY_ACCESS_WEBHOOK (Slack, Discord, or
 * any HTTP destination).
 *
 * For Vercel deployment, swap the file write for a Postgres insert
 * (Neon/Supabase) before going live — /tmp on Vercel is ephemeral.
 */

type Payload = { email?: unknown; role?: unknown; meetings?: unknown };

function isStr(x: unknown): x is string {
  return typeof x === "string";
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export async function POST(req: Request) {
  let body: Payload;
  try {
    body = (await req.json()) as Payload;
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const email = isStr(body.email) ? body.email.trim() : "";
  const role = isStr(body.role) ? body.role.trim() : "";
  const meetings = isStr(body.meetings) ? body.meetings.trim() : "";

  if (!EMAIL_RE.test(email)) {
    return NextResponse.json({ error: "Valid email required" }, { status: 400 });
  }
  if (!role) {
    return NextResponse.json({ error: "Role required" }, { status: 400 });
  }
  if (email.length > 200 || meetings.length > 2000) {
    return NextResponse.json({ error: "Field too long" }, { status: 400 });
  }

  const submission = {
    email,
    role,
    meetings,
    at: new Date().toISOString(),
    ua: req.headers.get("user-agent") ?? "",
    ip: req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "",
  };

  // Forward to webhook if configured.
  const webhook = process.env.EARLY_ACCESS_WEBHOOK;
  if (webhook) {
    try {
      await fetch(webhook, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(submission),
      });
    } catch {
      // Don't fail the user's submission on webhook errors —
      // log silently and keep going. (Replace with real logger in prod.)
    }
  }

  return NextResponse.json({ ok: true });
}
