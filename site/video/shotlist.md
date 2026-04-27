# Demo video — shot list

90 seconds. Six visual beats. Time-coded for the editor; record more
than you need at each beat and trim down.

## Beat 1 — Cold open · 0:00–0:05

**Visual.** Tight macro on the menu bar. The Instinctual icon is dim. A
soft chime (~6dB below room tone) plays. The icon activates: the dot
turns coral, gains a soft glow, begins a slow 2.4-second pulse. The
panel slides down beneath the icon over 220ms — Mac sheet animation,
not custom. "Listening" appears in the strip with a live timer at
00:00.

**Audio.** Room tone. The chime is the only deliberate sound.

**Don't.** No title card. No "Instinctual presents." Cold open means cold.

## Beat 2 — Meeting in progress · 0:05–0:30

**Visual.** Wide shot establishing context: the menu bar with active
icon at top, the panel below it, the meeting window (Zoom, Meet, or
similar) in the background. The user is the camera POV — we're seeing
what they're seeing, including periodic eye contact with their meeting
participants on screen.

**The conversation we're recording.** Three engineers discussing
building an internal velocity dashboard for engineering Q4 review. Real
discussion, real disagreement, real terms ("p50", "DuckDB", "the v2
dash"). 25 seconds of real meeting audio. No script.

**The panel is the lead.** As the meeting progresses, the spec doc
forms in the panel — section by section. Decision header populates with
two checked items. Scope header populates with three bullets, one per
sentence of new requirement. Stack section appears with `streamlit +
duckdb + github-api`. Open section appears with the auth question.

**Cuts.** Maximum two cuts in this 25-second beat. Long takes carry
the cadence; short cuts ruin it.

**Audio.** Real meeting audio. No music yet.

## Beat 3 — Clarification banner · 0:30–0:38

**Visual.** Around the 30-second mark, a clarification banner slides up
from the bottom of the panel. The banner reads: "Auth — same SSO as the
v2 dashboard, or Google OAuth?" with two pill buttons: "v2 SSO" and
"Google".

The user, mid-conversation with their meeting, glances at the panel,
moves the cursor to the panel (1-1.5s of cursor motion — make it feel
deliberate), taps "v2 SSO". The banner dismisses with a soft slide-down
+ fade. The "Open" section in the spec doc updates to a checked item:
"Auth — v2 SSO (chose at 0:32)."

**Why this beat matters.** This is the only point in the video where the
product is not just transcribing. It's the moment intelligence shows.
Don't rush it.

**Audio.** Soft whoosh on banner appearance (~80ms, low volume). Soft
click on tap. Otherwise meeting audio continues.

## Beat 4 — Meeting end → Building · 0:38–0:60

**Visual.** The meeting window closes (Cmd+W or red dot, your call).
The Instinctual panel transitions: "Listening" becomes "Building" in the
panel header strip. The panel body re-renders as a build progress view
with five steps, each animating from pending → active → done as the
build advances. A thin coral progress bar fills under the header.

The five build steps (text appears in mono, one per step):
1. `Synthesis · classify recipe → streamlit_dashboard`
2. `Builder · scaffold streamlit app`
3. `Builder · wire DuckDB + GitHub API`
4. `Critic · feasibility passes (3/3)`
5. `Deploy · push to Modal`

Total build duration: 22 seconds of screen time, compressed from real
build time. Don't fake this. If the real build takes 90 seconds, that's
fine — speed-ramp the recording 4x and live with it.

**Audio.** Ambient pad enters here, lightly. Subtle "step complete"
sound on each build step (a clean `tick`, ~10dB below pad). No music
beat. No drop.

## Beat 5 — Deployed · 0:60–0:80

**Visual.** Build completes. The panel transitions to a "Shipped" view:
the deployed dashboard URL appears in a rounded green-tinted block:
`velocity-v2.instinctual.app`. The user taps "Open ↗". Cut to the deployed
dashboard rendering in a real browser — the Streamlit dashboard with
PR throughput KPIs, deploy frequency, p50/p90 review latency, real
charts, real numbers from the GitHub API.

The user clicks one of the charts. It's real. It works.

**Cuts.** Two cuts: panel → browser opening, browser → user clicking.
Both held long enough to read.

**Audio.** Pad continues. No celebration — calm satisfaction, not
fireworks.

## Beat 6 — The timestamp · 0:80–0:88

**Visual.** Cut to text on a black background, in the site's display
type. Two lines, large:

> Meeting ended at 2:47.
> Tool live at 2:51.

Beat. (1.5s.)

> This is real.

The "is" is in coral; everything else is in fg-primary.

**Audio.** Pad sustains, no music change. The text lands without
emphasis — the timestamp does the work.

## Beat 7 — Closing card · 0:88–0:90

**Visual.** Wordmark + tagline + URL. White on black, no animation
beyond a 200ms fade-in.

> **Instinctual**
> Your meetings should ship products, not tickets.
> instinctual.app

**Audio.** Pad fades out under the wordmark. End on silence, not on a
button-press sound.

---

## Cuts summary

Total cuts: **6** (count them: cold open hold, meeting wide, clarify
beat, building transition, deployed → browser, timestamp card,
closing). Eight is the maximum tolerance. Anything more reads as
nervous editing.

## Captioning

Burn-in captions for accessibility on the web embed only. Master
delivers without burn-in; captions ride as a `.vtt` sidecar. The
captions cover the meeting audio in beat 2 and the click cues in
beats 3 and 5. The text-on-screen beats (6 and 7) don't need captions.
