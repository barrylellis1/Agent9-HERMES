/**
 * A neutral placeholder situation used to occupy the hero slot so real test subjects land
 * in the grid (KPITile). DashboardView sorts by severity: critical→0, high→1, medium→2.
 * Using severity='critical' with a large |percent_change| guarantees FILLER always sorts
 * first, regardless of what test subjects are in the list.
 */
export const FILLER_SITUATION = {
  situation_id: 'sit_filler_001',
  kpi_name: 'Operating Cash Flow',
  kpi_id: 'operating_cash_flow',
  kpi_value: {
    value: 12000000,
    unit: '$',
    currency: '$',
    percent_change: -99.9,
    comparison_type: 'yoy',
    inverse_logic: false,
    monthly_values: [
      { period: '2026-01', value: 2100000 },
      { period: '2026-02', value: 1900000 },
      { period: '2026-03', value: 2000000 },
      { period: '2026-04', value: 2200000 },
      { period: '2026-05', value: 1900000 },
      { period: '2026-06', value: 1900000 },
    ],
  },
  severity: 'critical',
  card_type: 'problem',
  direction: 'down',
  description: 'Filler hero situation — not under test',
  alert_type: 'threshold_breach',
  compound_alert: false,
  key_observations: ['Placeholder for hero slot'],
};
