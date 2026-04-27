# Instinctual — site

Marketing site, pitch deck, interactive demo, and investor memo for Instinctual.

## Stack
- Next.js 15 (App Router)
- React 19
- TypeScript
- Tailwind CSS v4 (CSS-first config via `@theme`)
- Framer Motion (used sparingly — CSS animations preferred)

## Design system
Tokens live in `app/styles/tokens.css`. Raycast-seeded palette: warm dark background, coral accent, Geist/Geist Mono typography. The wordmark is title case ("Instinctual"). Dark mode is the default and the only mode shipped in v0.

## Running locally

```bash
bun install   # or: npm install / pnpm install
bun dev       # or: npm run dev
```

Open http://localhost:3000.

## Routes
- `/` — landing page
- `/deck` — pitch deck (keyboard nav: arrows, space, escape)
- `/memo` — long-form "Why now / why us" essay
- `/api/early-access` — signup form endpoint

## Deploying

```bash
vercel        # preview
vercel --prod # production
```
