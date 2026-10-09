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
  parentName: string,
): TrustReading {
  if (link.basis === 'accounting_identity') {
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

export function distanceInWords(hops: number | null | undefined): string | null {
  if (hops == null) return null;
  if (hops <= 1) return 'Direct link';
  if (hops === 2) return 'Two steps removed';
  return `${hops} steps removed`;
}
