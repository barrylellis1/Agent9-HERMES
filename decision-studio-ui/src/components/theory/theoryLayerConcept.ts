/**
 * Illustrative payload for the "KPI Drivers" concept image on the public site.
 *
 * This is a concept of the finished product, not a client's data. The KPI and
 * driver names are generic, the values are invented, and nothing here is read
 * from a registry. Shown with a "Concept" badge wherever it appears.
 */
import type { TheoryLayerPayload } from '../../api/client';

export const conceptKpiDrivers: TheoryLayerPayload = {
  kpi_id: 'margin_rate',
  kpi_name: 'Margin rate',
  client_id: 'concept',
  spine: {
    nodes: [
      { kpi_id: 'margin_rate', name: 'Margin rate', unit: '%', unit_class: 'ratio',
        additive_across_dimensions: false, aggregation_method: 'ratio', scope_eligible: null,
        value: 34.2, prior_value: 36.1 },
      { kpi_id: 'gross_profit', name: 'Gross profit', unit: '$', unit_class: 'currency',
        additive_across_dimensions: true, aggregation_method: 'sum', scope_eligible: null,
        value: 4120000, prior_value: 4380000 },
      { kpi_id: 'net_revenue', name: 'Net revenue', unit: '$', unit_class: 'currency',
        additive_across_dimensions: true, aggregation_method: 'sum', scope_eligible: null,
        value: 12050000, prior_value: 12130000 },
      { kpi_id: 'cost_of_goods', name: 'Cost of goods', unit: '$', unit_class: 'currency',
        additive_across_dimensions: true, aggregation_method: 'sum', scope_eligible: null,
        value: 7930000, prior_value: 7750000 },
      // Drivers that appear in the variance bridge.
      { kpi_id: 'premium_mix', name: 'Premium mix', unit: '%', unit_class: 'ratio',
        additive_across_dimensions: false, aggregation_method: 'ratio', scope_eligible: null,
        value: 27.5, prior_value: 25.9 },
      { kpi_id: 'freight_cost', name: 'Freight cost', unit: '%', unit_class: 'ratio',
        additive_across_dimensions: false, aggregation_method: 'ratio', scope_eligible: null,
        value: 6.8, prior_value: 6.0 },
      { kpi_id: 'price_realisation', name: 'Price realisation', unit: '%', unit_class: 'ratio',
        additive_across_dimensions: false, aggregation_method: 'ratio', scope_eligible: null,
        value: 101.4, prior_value: 101.3 },
    ],
    edges: [
      { parent_kpi_id: 'margin_rate', child_kpi_id: 'gross_profit', operation: 'ratio', sign: 1, weight_kpi_id: 'net_revenue' },
      { parent_kpi_id: 'gross_profit', child_kpi_id: 'net_revenue', operation: 'linear', sign: 1, weight_kpi_id: null },
      { parent_kpi_id: 'gross_profit', child_kpi_id: 'cost_of_goods', operation: 'linear', sign: -1, weight_kpi_id: null },
    ],
    reconciliation: { ok: true, detail: null },
    variance_bridge: {
      prior_value: 36.1,
      current_value: 34.2,
      total_move: -1.9,
      effects: [
        { kpi_id: 'premium_mix', effect: -1.1 },
        { kpi_id: 'freight_cost', effect: -0.9 },
        { kpi_id: 'price_realisation', effect: 0.1 },
      ],
      residual: 0,
      exact: true,
      note: null,
    },
  },
  causal_edges: [
    {
      kpi_id: 'margin_rate', related_kpi_id: 'premium_mix',
      kpi_name: 'Margin rate', related_kpi_name: 'Premium mix',
      basis: 'causal_estimate',
      mechanism: 'Premium products carry a higher margin per unit than the core range.',
      lag_periods: 0, causal_rung: 'intervention_tested', provenance: 'va_validated',
      confidence: 'high', causal_direction: 'positive', hops: 1, verdict: 'held_up',
    },
    {
      kpi_id: 'margin_rate', related_kpi_id: 'freight_cost',
      kpi_name: 'Margin rate', related_kpi_name: 'Freight cost',
      basis: 'causal_estimate',
      mechanism: 'Higher freight cost lowers margin unless it is passed on to customers.',
      lag_periods: 0, causal_rung: 'intervention_hypothesized', provenance: 'template',
      confidence: 'medium', causal_direction: 'negative', hops: 1, verdict: null,
    },
    {
      kpi_id: 'margin_rate', related_kpi_id: 'price_realisation',
      kpi_name: 'Margin rate', related_kpi_name: 'Price realisation',
      basis: 'causal_estimate',
      mechanism: 'Realised price per unit moves margin directly.',
      lag_periods: 0, causal_rung: 'correlational', provenance: 'confirmed',
      confidence: 'medium', causal_direction: 'positive', hops: 1, verdict: null,
    },
    {
      kpi_id: 'margin_rate', related_kpi_id: 'gross_profit',
      kpi_name: 'Margin rate', related_kpi_name: 'Gross profit',
      basis: 'accounting_identity', mechanism: null, lag_periods: null,
      causal_rung: null, provenance: 'identity', confidence: null,
      causal_direction: 'positive', hops: 1, verdict: null,
    },
    {
      kpi_id: 'margin_rate', related_kpi_id: 'net_revenue',
      kpi_name: 'Margin rate', related_kpi_name: 'Net revenue',
      basis: 'accounting_identity', mechanism: null, lag_periods: null,
      causal_rung: null, provenance: 'identity', confidence: null,
      causal_direction: 'positive', hops: 2, verdict: null,
    },
    {
      kpi_id: 'margin_rate', related_kpi_id: 'cost_of_goods',
      kpi_name: 'Margin rate', related_kpi_name: 'Cost of goods',
      basis: 'accounting_identity', mechanism: null, lag_periods: null,
      causal_rung: null, provenance: 'identity', confidence: null,
      causal_direction: 'negative', hops: 2, verdict: null,
    },
  ],
  ports: [
    {
      id: 'raw_material_index', name: 'Raw material index', port_type: 'market',
      linked_kpi_id: 'margin_rate', linked_kpi_name: 'Margin rate',
      lag_periods: 1, buffer_description: 'Supplier contracts reset each quarter.',
      current_signal: 'Rising for three months', source: 'market_signal',
    },
  ],
  epistemic_summary: {
    identities: 3,
    causal_claims: 3,
    tested: 1,
    asserted: 1,
    template: 1,
    density_gate_passed: false,
  },
  values_included: true,
  notes: ['Illustrative values for a concept view. Not a client’s results.'],
};
