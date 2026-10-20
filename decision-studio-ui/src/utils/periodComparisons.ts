/**
 * The comparison a KPI threshold row is judged on (Phase 26, step 2).
 *
 * The ten period comparisons mirror src/analysis/period_comparisons.py. A to-date comparison
 * sets two partial spans of equal elapsed length side by side; a complete-period comparison
 * sets two finished periods of equal length side by side. The plan and alert rows are not
 * period comparisons and keep their names.
 *
 * yoy / qoq / mom are the names rows had before the rename. A row may still hold one until
 * its client's registry is re-seeded; the backend reads each as the comparison it has always
 * meant (yoy = YTD vs previous year YTD), and the editors show it as that so a reader is not
 * misled and an untouched row is saved unchanged.
 */

export interface ComparisonOption {
  value: string;
  label: string;
}

export interface ComparisonGroup {
  group: string;
  options: ComparisonOption[];
}

export const THRESHOLD_COMPARISON_GROUPS: ComparisonGroup[] = [
  {
    group: 'To date',
    options: [
      { value: 'mtd_vs_prev_mtd', label: 'MTD vs previous MTD' },
      { value: 'mtd_vs_py_mtd', label: 'MTD vs previous year MTD' },
      { value: 'qtd_vs_prev_qtd', label: 'QTD vs previous QTD' },
      { value: 'qtd_vs_py_qtd', label: 'QTD vs previous year QTD' },
      { value: 'ytd_vs_pytd', label: 'YTD vs previous year YTD' },
    ],
  },
  {
    group: 'Complete period',
    options: [
      { value: 'month_vs_prev_month', label: 'Month vs previous month' },
      { value: 'month_vs_py_month', label: 'Month vs same month previous year' },
      { value: 'quarter_vs_prev_quarter', label: 'Quarter vs previous quarter' },
      { value: 'quarter_vs_py_quarter', label: 'Quarter vs same quarter previous year' },
      { value: 'year_vs_prev_year', label: 'Year vs previous year' },
    ],
  },
  {
    group: 'Rolling',
    options: [
      { value: 'ltm_vs_prior_ltm', label: 'LTM vs Prior LTM' },
    ],
  },
  {
    group: 'Plan and alerts',
    options: [
      { value: 'budget', label: 'Actual vs budget' },
      { value: 'plan_variance', label: 'Plan variance' },
      { value: 'projected_breach', label: 'Projected breach' },
      { value: 'acceleration', label: 'Acceleration' },
      { value: 'target', label: 'Against target' },
      { value: 'greater_than', label: 'Greater than' },
      { value: 'less_than', label: 'Less than' },
    ],
  },
];

/** Old row names and the comparison each is read as. */
export const LEGACY_COMPARISONS: Record<string, string> = {
  yoy: 'ytd_vs_pytd',
  qoq: 'quarter_vs_prev_quarter',
  mom: 'month_vs_prev_month',
};

/** The default comparison for a new threshold row: the one every scan reads today. */
export const DEFAULT_THRESHOLD_COMPARISON = 'ytd_vs_pytd';

const LABELS: Record<string, string> = Object.fromEntries(
  THRESHOLD_COMPARISON_GROUPS.flatMap(g => g.options.map(o => [o.value, o.label])),
);

/** A comparison name in words. An old name reads as its comparison, marked as the old name. */
export function comparisonLabel(value: string | null | undefined): string {
  const v = String(value ?? '').trim().toLowerCase();
  if (LABELS[v]) return LABELS[v];
  const current = LEGACY_COMPARISONS[v];
  if (current) return `${LABELS[current]} (old name "${v}")`;
  return v || 'Not set';
}

/** True when the editor's list has no entry for this value, so it must add one to show it. */
export function needsExtraOption(value: string | null | undefined): boolean {
  const v = String(value ?? '').trim().toLowerCase();
  return v !== '' && !LABELS[v];
}
