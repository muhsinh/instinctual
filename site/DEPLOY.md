# Deploy

The production build is green. Vercel deploy requires `vercel login` which
is interactive, so it has to run in your terminal. Steps:

```bash
# from /Users/muh/instinctual/site/
npm i -g vercel              # if not already installed
vercel                       # auth + link the project (preview URL)
vercel --prod                # push to production
```

The first `vercel` run prompts for: scope (your account), project name
(suggest: `instinct-site`), framework (auto-detected as Next.js), root
dir (`.`). Accept defaults except project name.

## Environment variables

Optional. Set once in the Vercel dashboard under Settings → Environment
Variables, or via `vercel env add`:

- `EARLY_ACCESS_WEBHOOK` — Slack/Discord/HTTP webhook URL. Each early
  access submission is forwarded as JSON. Leave unset to silently
  accept submissions (visible in Vercel logs only).

## Custom domain

Once deployed:

```bash
vercel domains add instinctual.app   # or your chosen domain
```

Then in Vercel dashboard → Domains, point your DNS:

- `A` record → `76.76.21.21`
- `CNAME` for `www` → `cname.vercel-dns.com`

## Build characteristics

- **6 routes**, all under 120KB First Load JS.
- `/`, `/deck`, `/memo`, `/_not-found` prerender as static.
- `/api/early-access` is a dynamic Route Handler.
- `/opengraph-image` runs on the edge runtime.

## What's not deployed yet

- The 90-second product video — record using `video/shotlist.md` then
  drop the encoded files in `public/video/` and replace the placeholder
  in `app/components/DemoSection.tsx`.
- Real form storage — current API endpoint forwards to a webhook only.
  For a database, swap in Neon or Supabase: see comments in
  `app/api/early-access/route.ts`.
- A real product photo on the team page — the `HM` initials tile in
  `app/components/Team.tsx` swaps out for an `<Image>` once a photo
  exists.
