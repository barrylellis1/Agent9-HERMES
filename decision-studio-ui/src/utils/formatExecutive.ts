/**
 * Formats large integers/floats as executive-readable strings.
 *
 * Two call signatures are supported:
 *
 * Options-object form (preferred for new code):
 *   formatExecutive(-189051582)                         → "-$189.1M"
 *   formatExecutive(150369071.62, { showSign: true })   → "+$150.4M"
 *   formatExecutive(0.185, { isPercent: true })         → "18.5%"
 *   formatExecutive(450000)                             → "$450.0K"
 *   formatExecutive(-12500)                             → "-$12.5K"
 *   formatExecutive(5200000)                            → "$5.2M"
 *
 * Legacy positional form (preserved for existing call sites):
 *   formatExecutive(value, '$', false)
 *   formatExecutive(value, '', false)
 */

interface FormatExecutiveOptions {
  showSign?:  boolean;   // show + for positive values (default false)
  isPercent?: boolean;   // format as percentage instead of currency (default false)
  unit?:      string;    // currency/unit prefix override (default '$')
}

// Overload 1 — new options-object form
export function formatExecutive(value: number, options?: FormatExecutiveOptions): string;
// Overload 2 — legacy positional form used by existing call sites
export function formatExecutive(value: number, currency?: string, forceSign?: boolean): string;

// Implementation — handles both overloads
export function formatExecutive(
  value: number,
  optionsOrCurrency?: FormatExecutiveOptions | string,
  forceSignLegacy?: boolean,
): string {
  if (!isFinite(value)) return '—';

  // ── Resolve arguments from whichever overload was used ──
  let showSign: boolean;
  let isPercent: boolean;
  let unit: string;

  if (typeof optionsOrCurrency === 'object' || optionsOrCurrency === undefined) {
    // Options-object form
    const opts = optionsOrCurrency ?? {};
    showSign  = opts.showSign  ?? false;
    isPercent = opts.isPercent ?? false;
    unit      = opts.unit      ?? '$';
  } else {
    // Legacy positional form: formatExecutive(value, currency?, forceSign?)
    unit      = optionsOrCurrency ?? '$';
    showSign  = forceSignLegacy   ?? true;   // legacy default was forceSign=true
    isPercent = false;
  }

  // ── Percentage branch ──
  if (isPercent) {
    const sign = showSign && value > 0 ? '+' : '';
    return `${sign}${(value * 100).toFixed(1)}%`;
  }

  // ── Currency / magnitude branch ──
  const abs  = Math.abs(value);
  const sign = value < 0 ? '-' : showSign && value > 0 ? '+' : '';

  let formatted: string;
  if (abs >= 1_000_000_000) {
    formatted = `${unit}${(abs / 1_000_000_000).toFixed(1)}B`;
  } else if (abs >= 1_000_000) {
    formatted = `${unit}${(abs / 1_000_000).toFixed(1)}M`;
  } else if (abs >= 1_000) {
    formatted = `${unit}${(abs / 1_000).toFixed(1)}K`;
  } else {
    formatted = `${unit}${abs.toFixed(0)}`;
  }

  return `${sign}${formatted}`;
}

/**
 * Compact variant — no sign, no currency prefix. For axis labels and sparklines.
 *   189051582 → "189.1M"
 *   42400     → "42.4K"
 */
export function formatCompact(value: number): string {
  return formatExecutive(Math.abs(value), '', false);
}
