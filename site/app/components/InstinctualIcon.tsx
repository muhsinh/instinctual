/**
 * The menu bar icon. Used in the MenuBarMock, the favicon, the OG image,
 * and the deck title slide. The motif: a soft squared rect with a centered
 * coral dot — the "i" tittle abstracted, with an active state that pulses.
 *
 * The active pulse is CSS-driven (.icon-pulse-target) so it can be
 * accelerated by cursor-proximity logic (Layer C). The inner circle
 * fades between full and 55% opacity by default; cursor proximity tightens
 * the duration by setting --pulse-dur on the element directly.
 */

export function InstinctualIcon({
  size = 18,
  active = false,
  color,
}: {
  size?: number;
  active?: boolean;
  color?: string;
}) {
  const stroke = color ?? "currentColor";
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 18 18"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
      style={{ flexShrink: 0 }}
    >
      <rect
        x="2.5"
        y="2.5"
        width="13"
        height="13"
        rx="3.5"
        stroke={stroke}
        strokeWidth="1.4"
        opacity={active ? 0.9 : 0.55}
      />
      <circle
        className={active ? "icon-pulse-target" : undefined}
        cx="9"
        cy="9"
        r={active ? 2.2 : 2}
        fill={active ? "var(--accent)" : stroke}
        opacity={active ? 1 : 0.85}
        style={
          active
            ? { filter: "drop-shadow(0 0 2px rgba(255, 99, 99, 0.65))" }
            : undefined
        }
      />
    </svg>
  );
}
