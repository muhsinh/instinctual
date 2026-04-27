/**
 * Motion system. Codified easings + durations so animations stay consistent
 * across the hero, interactive demo, and deck. Motion is earned, not
 * decorative — a thing moves because it conveys information.
 */

export const easing = {
  outQuint: [0.22, 1, 0.36, 1] as const,
  outQuart: [0.25, 1, 0.5, 1] as const,
  outExpo: [0.16, 1, 0.3, 1] as const,
  inOut: [0.65, 0, 0.35, 1] as const,
  spring: [0.34, 1.56, 0.64, 1] as const,
};

export const duration = {
  instant: 0.08,
  fast: 0.15,
  base: 0.24,
  slow: 0.42,
  slower: 0.72,
  slowest: 1.2,
};

/** Used for spec-doc characters appearing one-by-one. */
export const typewriter = {
  charDelayMs: 18,
  lineDelayMs: 220,
};

/** Used for clarification banner slide-in. */
export const banner = {
  enter: { duration: duration.slow, ease: easing.outExpo },
  exit: { duration: duration.base, ease: easing.outQuart },
};

/** Used for spec doc updating in the live panel. */
export const specUpdate = {
  enter: { duration: duration.slow, ease: easing.outQuint },
  fade: { duration: duration.base, ease: easing.outQuart },
};

/** Used for menu bar icon pulse. */
export const pulse = {
  duration: 2.4,
  ease: easing.inOut,
};
