/**
 * Formats large numbers into executive-readable strings with sign and magnitude suffix.
 *
 * Examples:
 *   -189051582       → "-$189.1M"
 *   +150369071.62    → "+$150.4M"
 *   -42400000        → "-$42.4M"
 *   1500             → "+$1.5K"
 *   -950             → "-$950"
 *   0                → "$0"
 *
 * @param value     Raw numeric value
 * @param currency  Currency prefix (default "$"). Pass "" to omit.
 * @param forceSign If true, always show + on positive values (default true)
 */
export function formatExecutive(
  value: number,
  currency = '$',
  forceSign = true,
): string {
  if (!isFinite(value)) return '—';

  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : forceSign && value > 0 ? '+' : '';

  if (abs >= 1_000_000_000) {
    return `${sign}${currency}${(abs / 1_000_000_000).toFixed(1)}B`;
  }
  if (abs >= 1_000_000) {
    return `${sign}${currency}${(abs / 1_000_000).toFixed(1)}M`;
  }
  if (abs >= 1_000) {
    return `${sign}${currency}${(abs / 1_000).toFixed(1)}K`;
  }
  return `${sign}${currency}${abs.toLocaleString()}`;
}

/**
 * Compact variant — no sign, no currency prefix. For axis labels and sparklines.
 *   189051582 → "189.1M"
 *   42400     → "42.4K"
 */
export function formatCompact(value: number): string {
  return formatExecutive(Math.abs(value), '', false);
}
