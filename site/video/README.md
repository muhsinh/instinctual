# Instinctual demo video — production artifacts

This directory holds the planning artifacts for the 90-second product
demo video. **The video is not yet shot.** This is the package that makes
recording fast.

## Contents

- `treatment.md` — the creative brief: why this video exists, what it
  must accomplish, mood, tone, what to avoid.
- `shotlist.md` — the second-by-second shot list. Treat this as a recipe
  the editor can follow without further direction.
- `script-vo-alternative.md` — voiceover-free is the default. Voiceover
  alternatives provided here for international audiences or platforms
  where audio-on-by-default helps.
- `delivery-spec.md` — final delivery format requirements (codec, bitrate,
  captions, OG poster export).

## Recording day checklist

1. Mac with Instinctual v0 installed, signed in. Real account, real meeting.
2. Two participants on the call besides the user (recorded with consent;
   redact names in post if needed).
3. Quiet environment for the meeting audio. The video is the product
   talking — ambient room tone is fine, but no music in the background.
4. Display set to native resolution (no scaling). Dark mode on. Hide all
   notifications via Focus mode for the entire recording window.
5. Use ScreenFlow or QuickTime for the screen recording (separate audio
   track preferred). Frame rate 60fps to give post flexibility.
6. After recording: send raw files to whoever is editing (this directory
   is the brief).

## Delivery target

- Primary master: 1920×1080, H.264, 8 Mbps, 60fps, AAC stereo.
- Web variant: 1920×1080, H.264, 4 Mbps, captions burned-in optional.
- Hero embed: 1280×720 webm + mp4, lazy-loaded with poster frame.
- Captions: separate `.vtt` for both English and (later) Spanish.
- Poster frame: a single still from second 22 (panel mid-build), exported
  as PNG for use as the OG image and the `<video poster>`.
