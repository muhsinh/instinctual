# Demo video — delivery spec

## Master file

- **Format.** ProRes 422 HQ master, 1920×1080, 60fps, 16-bit color.
- **Duration.** 1:30 (00:00:00 to 00:01:30 hard-out).
- **Audio.** Stereo, 48kHz, 24-bit. Two channels: meeting audio (1) and
  ambient pad / SFX (2). Master with -14 LUFS integrated for web
  delivery; -23 LUFS for broadcast if ever needed.
- **Color space.** Rec. 709, full range. No HDR variants for v0.

## Web delivery (this site)

Three encoded variants, served via `<video>` with `<source>` fallbacks
in priority order:

1. **AV1 / WebM**, 1920×1080, ~3.5 Mbps. Modern browsers, smallest
   file. Target: ~50MB.
2. **H.264 / MP4**, 1920×1080, 5 Mbps. Universal fallback. Target:
   ~70MB.
3. **H.264 / MP4 mobile**, 1280×720, 2.5 Mbps. Bandwidth fallback.
   Target: ~30MB.

All three: `+faststart` so playback can begin before full download.
Lazy-loaded via Intersection Observer when the hero scrolls in.

## Poster frame

Single still from second 22 (panel mid-build, banner already visible).
Export as `1920×1080.png`. Used as:

- `<video poster>` attribute on the hero embed.
- `og-image.png` for social shares (resize to 1200×630).
- The "Demo coming soon" placeholder image once the demo placeholder
  swaps out.

## Captions

- `en.vtt` — English, sentence-level cues, no emoji.
- Burn-in version of captions on the web variant only (master + social
  uploads use sidecar VTT for accessibility).

## Social cuts

Generate three social variants from the master:

1. **Square 1:1 cut**, 1080×1080, 60s. Used for LinkedIn, Instagram.
   Drops the building beat (0:38–0:60), keeps the meeting → deployed
   transition.
2. **Vertical 9:16 cut**, 1080×1920, 30s. Used for X (formerly
   Twitter), TikTok. Cold open + deployed beat only. Captions
   burned-in.
3. **Hero loop**, 1920×1080, 12s, silent. Loops on the website hero
   above the menu bar mock. Just the panel forming the spec doc.

## File naming

```
instinct-demo-v1-master.mov           # master
instinct-demo-v1-web-1080.webm        # web AV1
instinct-demo-v1-web-1080.mp4         # web H.264
instinct-demo-v1-web-720.mp4          # web mobile
instinct-demo-v1-poster.png           # poster + OG
instinct-demo-v1-social-square.mp4    # 1:1 60s
instinct-demo-v1-social-vertical.mp4  # 9:16 30s
instinct-demo-v1-hero-loop.mp4        # 12s silent loop
instinct-demo-v1-captions-en.vtt      # captions
```

## Where they go

- `/site/public/video/` for the web variants and poster.
- `/site/public/captions/` for the VTT.
- The square + vertical social cuts go into a separate `/social/`
  drop folder; the website doesn't host them.
- The master + project files go to long-term archive (Backblaze B2
  bucket, `instinct-archive/video/`). Don't commit the master to git;
  it's gigabytes.
