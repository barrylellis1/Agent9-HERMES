/**
 * RangeBar — a low-high range positioned on a shared 0-max scale, for the
 * compact option rows (2026-08-28 compact-brief restructure, mirroring the
 * reference mockup's hatched range visualization).
 *
 * CSS `<div>`-based, matching the bar convention already established in
 * `DivergingBarChart.tsx` (track: `bg-slate-900/950 rounded overflow-hidden`,
 * fill: an absolutely/proportionally sized inner div) — not SVG. This app has
 * no precedent for an SVG chart primitive at this scale; introducing one here
 * would be a second bar-drawing convention to maintain alongside the first.
 *
 * Print: hidden outright. A CSS gradient/hatch fill is not reliable in
 * browser print output, and it isn't the substance anyway — the caller
 * (CompactOptionRow) renders the low/high number as ordinary text next to
 * this bar, and that text is what survives to paper. See
 * docs/architecture/executive_briefing_redesign.md and the 2026-08-28
 * plan note on print parity for the reasoning.
 */
interface RangeBarProps {
  low: number;
  high: number;
  max: number;
  /** 'recommended' gets the opportunity token; 'dominated' renders faint,
   *  matching the reduced-opacity treatment the row itself already carries;
   *  'default' is a neutral slate fill. */
  tone: 'recommended' | 'default' | 'dominated';
}

const TONE_FILL: Record<RangeBarProps['tone'], string> = {
  recommended: 'bg-severity-opportunity',
  default: 'bg-slate-400',
  dominated: 'bg-slate-500',
};

export function RangeBar({ low, high, max, tone }: RangeBarProps) {
  if (!(max > 0) || !Number.isFinite(low) || !Number.isFinite(high)) return null;

  const clamp = (v: number) => Math.min(100, Math.max(0, (v / max) * 100));
  const left = clamp(Math.min(low, high));
  const right = clamp(Math.max(low, high));
  const width = Math.max(right - left, 1.5); // stays visible even for a near-zero range

  return (
    <div
      className={`print:hidden relative h-1.5 w-full rounded-full bg-slate-800 overflow-hidden ${
        tone === 'dominated' ? 'opacity-50' : ''
      }`}
      data-testid="range-bar"
      data-low={low}
      data-high={high}
      data-max={max}
    >
      {/* Hatch texture under the solid fill — CSS-only, no image asset. */}
      <div
        className={`absolute inset-y-0 rounded-full ${TONE_FILL[tone]} opacity-30`}
        style={{
          left: `${left}%`,
          width: `${width}%`,
          backgroundImage:
            'repeating-linear-gradient(135deg, currentColor 0px, currentColor 2px, transparent 2px, transparent 5px)',
        }}
      />
      <div
        className={`absolute inset-y-0 rounded-full ${TONE_FILL[tone]}`}
        style={{ left: `${left}%`, width: `${width}%` }}
      />
    </div>
  );
}
