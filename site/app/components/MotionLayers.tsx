"use client";

import { useEffect } from "react";

/**
 * Three-layer motion system:
 *
 *   Layer A — AmbientMesh: gradient blobs animated via CSS keyframes,
 *             GPU-accelerated transforms only. Visible everywhere, always.
 *   Layer B — Scroll perspective on MenuBarMock — implemented in MenuBarMock.tsx
 *             (RAF-throttled scroll listener that updates CSS vars).
 *   Layer C — CursorMotion: lerps cursor position at ~60fps, writes
 *             --cursor-x / --cursor-y on document.documentElement so the mesh
 *             gradient origin tracks the cursor with ~250ms ease.
 *
 * All three respect prefers-reduced-motion. If the user opts out, Layers
 * B and C disable; Layer A freezes its keyframes.
 *
 * Performance notes:
 *   - Mesh uses transform + opacity only (GPU compositor).
 *   - Cursor lerp runs in a single rAF, no per-frame allocations.
 *   - The mesh has pointer-events: none so it never blocks input.
 */

export function AmbientMesh() {
  return (
    <div aria-hidden className="ambient-mesh">
      <div className="mesh-blob mesh-blob-coral" />
      <div className="mesh-blob mesh-blob-cool" />
      <div className="mesh-blob mesh-blob-deep" />
      {/* The cursor-tracking blob — its center follows --cursor-x/y */}
      <div className="mesh-blob mesh-blob-cursor" />
      <div className="mesh-grid" />
    </div>
  );
}

export function CursorMotion() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    // Disable on touch devices — no real cursor.
    if (window.matchMedia("(hover: none)").matches) return;

    const root = document.documentElement;
    let targetX = 50;
    let targetY = 28;
    let currentX = 50;
    let currentY = 28;
    let raf = 0;

    const handleMove = (e: PointerEvent) => {
      targetX = (e.clientX / window.innerWidth) * 100;
      targetY = (e.clientY / window.innerHeight) * 100;
    };

    const tick = () => {
      // ~250ms ease via 0.06 lerp factor at 60fps
      currentX += (targetX - currentX) * 0.06;
      currentY += (targetY - currentY) * 0.06;
      root.style.setProperty("--cursor-x", `${currentX.toFixed(2)}%`);
      root.style.setProperty("--cursor-y", `${currentY.toFixed(2)}%`);
      raf = requestAnimationFrame(tick);
    };

    window.addEventListener("pointermove", handleMove, { passive: true });
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", handleMove);
    };
  }, []);

  return null;
}
