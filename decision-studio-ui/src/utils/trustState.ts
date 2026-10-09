/**
 * The one surface vocabulary for "how much should I trust this?".
 *
 * The registry keeps its full provenance ladder (theory_layer_design.md §4);
 * every decision-maker screen shows one of three states derived here, from
 * recorded fields only, with the detail behind a "Why" expand.
 *
 * Tested is reserved for a link that went through a Value Assurance verdict.
 * A measurement taken before the decision does not make something Tested.
 * Language cap: Tested copy says "held up", never "proved".
 */
export type TrustState = 'tested' | 'assumed' | 'calculated';

export interface TrustReading {
  state: TrustState;
  /** One plain sentence shown beside the state. */
  line: string;
  /** Only meaningful when state is 'tested'; false = the verdict went against it. */
  held?: boolean;
}

const LINK_SOURCE_LINE: Record<string, string> = {
  confirmed: 'Confirmed by your team.',
  template: 'Industry default, not yet checked against your data.',
  hitl_proposed: 'Suggested from past use, not yet confirmed.',
};

export function linkTrust(
  link: { basis?: string | null; causal_rung?: string | null; provenance?: string | null; hops?: number | null },
  /** The KPI being analysed. Pass null when the link is shown as a pair in its own right. */
  parentName: string | null,
): TrustReading {
  if (link.basis === 'accounting_identity') {
    if (parentName === null) {
      return { state: 'calculated', line: 'True by definition: one is calculated from the other.' };
    }
    const direct = link.hops == null || link.hops <= 1;
    return {
      state: 'calculated',
      line: direct
        ? `Part of how ${parentName} is calculated.`
        : `Feeds into how ${parentName} is calculated.`,
    };
  }
  if (link.causal_rung === 'intervention_tested') {
    return { state: 'tested', held: true, line: 'Held up when a past decision was measured.' };
  }
  return {
    state: 'assumed',
    line: LINK_SOURCE_LINE[link.provenance ?? ''] ?? 'Not yet tested.',
  };
}

const ASSUMPTION_SOURCE_LINE: Record<string, string> = {
  sa_assessment: 'Backed by the latest assessment.',
  ma_query: 'Backed by market research.',
  human_confirmation: 'Confirmed by a person.',
};

/**
 * A briefing assumption is a bet made before the decision, so it reads
 * Assumed even when it rests on a measurement ("grounded"); the line says
 * what backs it. Nothing here can be Tested until a graded outcome reaches
 * this payload.
 */
export function assumptionTrust(a: { grounded?: boolean; validated_by?: string | null }): TrustReading {
  if (a.grounded !== true) {
    return { state: 'assumed', line: "The model's reasoning, not yet measured." };
  }
  return {
    state: 'assumed',
    line: ASSUMPTION_SOURCE_LINE[a.validated_by ?? ''] ?? 'Backed by a measurement.',
  };
}

export function distanceInWords(hops: number | null | undefined): string | null {
  if (hops == null) return null;
  if (hops <= 1) return 'Direct link';
  if (hops === 2) return 'Two steps removed';
  return `${hops} steps removed`;
}
