import React, { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { formatExecutive } from '../../utils/formatExecutive'
import { formatDimLabel } from '../../utils/briefingUtils'

// --- Types ---
export interface IsIsNotItem {
  dimension: string
  key: string
  current: number
  previous: number
  delta: number
  text?: string
  segment_type?: 'problem' | 'opportunity'
  // Phase 11I-D segment matrix — second comparison basis + cross-basis tier
  secondary_delta?: number | null
  basis_agreement?: 'confirmed' | 'basis_specific' | 'secondary_only' | 'healthy' | null
  // Governed business-glossary display label for `dimension` (e.g.
  // "Customer Region" for "customer_region"), resolved server-side by DA via
  // A9_Data_Governance_Agent.resolve_dimension_label(). Absent — not a
  // mechanical guess — when the glossary has no entry yet for this field;
  // see formatDimLabel for the client-side fallback used in that case.
  dimension_label?: string
}

export interface KTIsIsNotData {
  where_is: IsIsNotItem[]
  where_is_not: IsIsNotItem[]
  what_is?: any[]
  what_is_not?: any[]
  when_is?: any[]
  when_is_not?: any[]
  /**
   * Per-dimension overall movement as the WAREHOUSE computed it (GROUP BY ROLLUP),
   * keyed by dimension name. Never derived here.
   *
   * This header used to sum the member deltas, printing -53pp for a KPI whose
   * enterprise move was about -5pp; summing the margin LEVELS the same way gives
   * 452.95% against a true 29.43%. A ratio's members cannot be added — the total
   * has to be re-aggregated from the components, which only the query can do.
   * Absent means render no total rather than deriving one.
   */
  dimension_totals?: Record<string, { current?: number | null; previous?: number | null; delta?: number | null; source?: string }>
}

interface IsIsNotExhibitProps {
  data: KTIsIsNotData
  kpiName?: string
  width?: number
  analysisMode?: 'problem' | 'opportunity' | 'mixed'
  // Phase 11I-D segment matrix
  matrixRan?: boolean
  comparator?: 'previous' | 'budget'
  comparatorSecondary?: 'previous' | 'budget'
  /** Lower is better (costs): budget words read "over / under budget". */
  inverseLogic?: boolean
  /** The card's period comparison (e.g. "ytd_vs_pytd"), so "previous" is named as the reader knows it. */
  periodComparison?: string | null
}

// ── Plain words for the two comparisons (owner, 2026-10-29) ──────────────────
// The chips used to read "both" / "one only" / "other only", which a principal could not
// decode, and "one only" was explained as "possibly a timing effect". Each row now says
// what its two numbers say, built from the numbers themselves, so the words can never
// disagree with the figures beside them.

/** What "previous" means on this card, in a reader's words. */
export const priorWords = (periodComparison?: string | null): string => {
  const k = (periodComparison || '').toLowerCase()
  if (k === 'ltm_vs_prior_ltm') return 'the prior 12 months'
  if (k === 'mtd_vs_py_mtd' || k === 'month_vs_py_month') return 'the same month last year'
  if (k === 'qtd_vs_py_qtd' || k === 'quarter_vs_py_quarter') return 'the same quarter last year'
  if (k === 'ytd_vs_pytd' || k === 'year_vs_prev_year' || k === 'yoy') return 'last year'
  if (k === 'qtd_vs_prev_qtd' || k === 'quarter_vs_prev_quarter' || k === 'qoq') return 'last quarter'
  if (k === 'mtd_vs_prev_mtd' || k === 'month_vs_prev_month' || k === 'mom') return 'last month'
  return 'the prior period'
}

interface BasisWords {
  /** "budget" or e.g. "last year": the object of "above / below". */
  name: string
  /** Column heading: "vs Budget", "vs last year". */
  heading: string
  /** In a sentence: "the budget", "last year". */
  phrase: string
}

const basisWords = (c: string | undefined, prior: string): BasisWords =>
  c === 'budget'
    ? { name: 'budget', heading: 'vs Budget', phrase: 'the budget' }
    : { name: prior, heading: `vs ${prior}`, phrase: prior }

/** "below" / "above" (or "under" / "over" budget for a cost); "level with" at zero. */
const sideWord = (delta: number, isBudget: boolean, inverse: boolean): string => {
  if (Math.abs(delta) < 1e-9) return 'level with'
  if (isBudget && inverse) return delta > 0 ? 'over' : 'under'
  return delta > 0 ? 'above' : 'below'
}

/** One row's two comparisons: "below budget, above last year"; "below budget and last year". */
export const comparisonPhrase = (
  delta: number,
  secondaryDelta: number | null | undefined,
  main: BasisWords,
  other: BasisWords,
  mainIsBudget: boolean,
  inverse: boolean,
  joiner: ', ' | ' but ' = ', ',
): string | null => {
  if (secondaryDelta == null) return null
  const a = sideWord(delta, mainIsBudget, inverse)
  const b = sideWord(secondaryDelta, !mainIsBudget, inverse)
  return a === b ? `${a} ${main.name} and ${other.name}` : `${a} ${main.name}${joiner}${b} ${other.name}`
}

// Cross-basis tier chip (Phase 11I-D): the colour still comes from the tier the analysis
// computed (red = worse on both, amber = worse on the main comparison only, blue = worse on
// the other only); the words come from the row's numbers.
const TierChip: React.FC<{ tier?: string | null; text?: string | null }> = ({ tier, text }) => {
  if (!tier || tier === 'healthy' || !text) return null
  const cfg: Record<string, string> = {
    confirmed: 'bg-severity-critical/20 text-severity-critical border-severity-critical/60',
    basis_specific: 'bg-severity-warning/20 text-severity-warning border-severity-warning/60',
    secondary_only: 'bg-blue-950 text-blue-300 border-blue-800/60',
  }
  const cls = cfg[tier]
  if (!cls) return null
  return <span className={`px-1.5 py-px rounded text-[10px] font-medium border whitespace-nowrap ${cls}`}>{text}</span>
}

// ─── IsIsNotExhibit — printed exhibit style, two-level expand ────────────────

export const IsIsNotExhibit: React.FC<IsIsNotExhibitProps> = ({
  data,
  kpiName = 'KPI',
  analysisMode = 'problem',
  matrixRan = false,
  comparator,
  comparatorSecondary,
  inverseLogic = false,
  periodComparison,
}) => {
  const isOpportunity = analysisMode === 'opportunity'
  const isMixed = analysisMode === 'mixed'
  const [expandedDimensions, setExpandedDimensions] = useState<Set<string>>(new Set())

  // The total comes from the backend or not at all. There is deliberately no
  // client-side fallback: any arithmetic here would be the bug this replaced.
  const totals = data?.dimension_totals ?? {}

  // A ratio KPI's deltas are percentage POINTS, not currency. formatExecutive
  // defaults to a '$' prefix, which is how "-7.86pp" reached a CFO as "-$7".
  const isRatioKpi = /%|percent|margin|rate|ratio|yield/i.test(kpiName || '')
  const fmtDelta = (v: number): string =>
    isRatioKpi
      ? `${v >= 0 ? '+' : ''}${v.toFixed(2)}pp`
      : formatExecutive(v, '$', true)

  const prior = priorWords(periodComparison)
  const mainWords = basisWords(comparator, prior)
  const otherWords = basisWords(comparatorSecondary, prior)
  const mainIsBudget = comparator === 'budget'
  const phraseFor = (item: IsIsNotItem, joiner: ', ' | ' but ' = ', ') =>
    comparisonPhrase(item.delta || 0, item.secondary_delta, mainWords, otherWords, mainIsBudget, inverseLogic, joiner)

  const toggleDimension = (dim: string) => {
    setExpandedDimensions(prev => {
      const next = new Set(prev)
      if (next.has(dim)) next.delete(dim)
      else next.add(dim)
      return next
    })
  }

  // Group items by dimension
  interface ProcessedDimension {
    dimension: string
    /** Governed glossary term when the backend resolved one, else a
     *  mechanical Title Case fallback (formatDimLabel) — never the raw
     *  "CUSTOMER_REGION"-style field name a reader would have to decode. */
    dimensionLabel: string
    is: IsIsNotItem[]
    isNot: IsIsNotItem[]
    /** Null when the deltas are not additive — show no total rather than a wrong one. */
    netIsVariance: number | null
    /** Most extreme single member delta — from CONFIRMED (bad on both bases)
     *  members when any exist, else from all members. Meaningful whether or
     *  not deltas are additive, so ordering never depends on a sum we may not
     *  be allowed to take. */
    sortKey: number
    /** True when sortKey was computed from confirmed-tier segments only
     *  (dual-basis matrix mode, at least one segment confirmed) — drives the
     *  column caption/tooltip wording so a reader knows which claim is being
     *  made. */
    sortKeyIsConfirmedOnly: boolean
  }

  const processedData: ProcessedDimension[] = useMemo(() => {
    if (!data) return []

    try {
      const dimensionMap = new Map<string, { is: IsIsNotItem[]; isNot: IsIsNotItem[]; isKeys: Set<string> }>()

      const whereIs = Array.isArray(data.where_is) ? data.where_is : []
      whereIs.forEach((item: any) => {
        if (!item || !item.dimension) return
        if (!dimensionMap.has(item.dimension)) {
          dimensionMap.set(item.dimension, { is: [], isNot: [], isKeys: new Set() })
        }
        const dimData = dimensionMap.get(item.dimension)!
        const key = item.key || 'Unknown'
        dimData.is.push({
          dimension: item.dimension || '',
          key,
          current: parseFloat(item.current) || 0,
          previous: parseFloat(item.previous) || 0,
          delta: parseFloat(item.delta) || 0,
          text: item.text,
          segment_type: item.segment_type,
          secondary_delta: item.secondary_delta ?? null,
          basis_agreement: item.basis_agreement ?? null,
          dimension_label: item.dimension_label,
        })
        dimData.isKeys.add(key)
      })

      const whereIsNot = Array.isArray(data.where_is_not) ? data.where_is_not : []
      whereIsNot.forEach((item: any) => {
        if (!item || !item.dimension) return
        if (!dimensionMap.has(item.dimension)) {
          dimensionMap.set(item.dimension, { is: [], isNot: [], isKeys: new Set() })
        }
        const dimData = dimensionMap.get(item.dimension)!
        const key = item.key || 'Unknown'
        if (dimData.isKeys.has(key)) return
        dimData.isNot.push({
          dimension: item.dimension || '',
          key,
          current: parseFloat(item.current) || 0,
          previous: parseFloat(item.previous) || 0,
          delta: parseFloat(item.delta) || 0,
          text: item.text,
          secondary_delta: item.secondary_delta ?? null,
          basis_agreement: item.basis_agreement ?? null,
          dimension_label: item.dimension_label,
        })
      })

      const result: ProcessedDimension[] = []
      dimensionMap.forEach((items, dimension) => {
        // Read, never computed. `items.is.reduce(...)` here is exactly what
        // produced -53pp against a ~-5pp enterprise move.
        const t = totals[dimension]
        const netIsVariance = typeof t?.delta === 'number' ? t.delta : null
        const deltas = items.is.map(i => i.delta || 0)
        // In dual-basis (11I-D matrix) mode, prefer CONFIRMED segments (bad on
        // BOTH bases — the genuine problem, per DA's own
        // _build_situation_complication_facts framing) over ones merely
        // worse on the main comparison only (the old "one only" chip, once
        // read as a timing quirk; now said plainly). Found live 2026-08-24:
        // Customer Region's largest RAW delta was North America at -$17.1M,
        // worse on budget only (it's actually +$2.8M vs the secondary basis) —
        // that single number was both the row's headline "Largest driver"
        // AND the dimension's sort-order key, burying International and
        // Europe underneath it despite both being tagged "confirmed" at a
        // fraction of the magnitude. Ranking by raw size alone, blind to the
        // tier the matrix itself computed, contradicted what the matrix was
        // built to establish. Falls back to all deltas when no item in this
        // dimension carries a confirmed tag — including the common case where
        // basis_agreement is absent entirely (single-basis analyses have no
        // tier to prefer, and every delta already means the same thing).
        const confirmedDeltas = items.is
          .filter(i => i.basis_agreement === 'confirmed')
          .map(i => i.delta || 0)
        const rankingDeltas = confirmedDeltas.length ? confirmedDeltas : deltas
        const sortKey = rankingDeltas.length
          ? (isOpportunity ? Math.max(...rankingDeltas) : Math.min(...rankingDeltas))
          : 0
        const sortKeyIsConfirmedOnly = confirmedDeltas.length > 0
        // Every item sharing this raw `dimension` carries the same
        // dimension_label (it's resolved per-field server-side, not
        // per-segment) — take it from whichever item has it.
        const glossaryLabel = items.is.find(i => i.dimension_label)?.dimension_label
          ?? items.isNot.find(i => i.dimension_label)?.dimension_label
        result.push({
          dimension,
          dimensionLabel: glossaryLabel || formatDimLabel(dimension),
          is: items.is,
          isNot: items.isNot,
          netIsVariance,
          sortKey,
          sortKeyIsConfirmedOnly,
        })
      })

      // Sort: opportunity mode → most positive first; problem/mixed → most negative
      // first. Keyed on the most extreme MEMBER, not on a sum — ordering must not
      // depend on an addition that is invalid for a ratio KPI.
      result.sort((a, b) => isOpportunity
        ? b.sortKey - a.sortKey
        : a.sortKey - b.sortKey)
      return result
    } catch (e) {
      console.error('IsIsNotExhibit: Error processing data', e)
      return []
    }
  }, [data, isOpportunity, totals])

  // Global max delta for bar scaling within expanded sections
  const maxDelta = useMemo(() => {
    let max = 0
    processedData.forEach(dim => {
      dim.is.forEach(item => { max = Math.max(max, Math.abs(item.delta || 0)) })
      dim.isNot.forEach(item => { max = Math.max(max, Math.abs(item.delta || 0)) })
    })
    return max || 1
  }, [processedData])

  // "Every segment shown is below budget but above last year." Only when every cross-checked
  // segment reads the same; otherwise the rows speak for themselves.
  const sharedPattern = useMemo(() => {
    if (!matrixRan) return null
    const phrases: string[] = []
    processedData.forEach(dim => {
      ;[...dim.is, ...dim.isNot].forEach(item => {
        const p = phraseFor(item, ' but ')
        if (p) phrases.push(p)
      })
    })
    if (phrases.length < 2) return null
    return phrases.every(p => p === phrases[0]) ? phrases[0] : null
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [processedData, matrixRan, comparator, comparatorSecondary, inverseLogic, periodComparison])

  if (!data || processedData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-24 gap-1 text-slate-500 text-sm">
        {isOpportunity || isMixed
          ? <>
              <span>Dimensional breakdown not available for this KPI</span>
              <span className="text-xs text-slate-600">Detected at aggregate level — segment-level data requires dimensional SQL support</span>
            </>
          : 'No Is / Is Not data available'
        }
      </div>
    )
  }

  return (
    <div className="w-full">
      {/* Exhibit header */}
      <div className="flex items-center justify-between mb-3 px-1">
        <span className="text-[10px] uppercase tracking-widest text-slate-500 font-medium">
          {kpiName} — Is / Is Not Analysis
        </span>
        <div className="flex items-center gap-4">
          {isMixed ? (
            <>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-sm bg-severity-critical" />
                <span className="text-[10px] text-slate-500">Problem area</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-sm bg-severity-opportunity" />
                <span className="text-[10px] text-slate-500">Opportunity</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-sm ${isOpportunity ? 'bg-severity-opportunity' : 'bg-severity-critical'}`} />
                <span className="text-[10px] text-slate-500">{isOpportunity ? 'Leading segment' : 'Problem area'}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-sm bg-slate-600" />
                <span className="text-[10px] text-slate-500">{isOpportunity ? 'Unrealised potential' : 'Healthy'}</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Phase 11I-D: two comparisons per segment, said plainly (owner, 2026-10-29) */}
      {matrixRan && (
        <div className="mb-2 space-y-1 px-1" data-testid="two-comparisons-note">
          <p className="text-[11px] text-slate-400">
            Each segment is compared with {mainWords.phrase} and with {otherWords.phrase}.
          </p>
          {sharedPattern && (
            <p className="text-xs text-slate-200 font-medium" data-testid="shared-pattern">
              Every segment shown is {sharedPattern}.
            </p>
          )}
        </div>
      )}

      {/* Column caption — once, not repeated per row. Names what the number in
          each row actually is (see the rationale on that span below): the
          largest single-segment driver, not a repeated dimension-wide total.
          In matrix mode the actual per-row answer varies — some dimensions
          have a confirmed segment to prefer, some don't — so the caption
          says "confirmed where available" rather than promising every row
          is confirmed; the per-row chip (see below) is what tells you which
          case a given row is in. */}
      <div className="flex items-center gap-3 px-4 pb-1">
        <span className="w-3.5 flex-shrink-0" />
        <span className="w-36 flex-shrink-0 text-[9px] uppercase tracking-widest text-slate-600">Dimension</span>
        <span className="w-32 flex-shrink-0 text-right text-[9px] uppercase tracking-widest text-slate-600 whitespace-nowrap">
          {matrixRan ? `Largest driver, ${mainWords.heading}` : 'Largest driver'}
        </span>
      </div>

      {/* Dimension rows */}
      <div className="border border-slate-800 rounded-lg overflow-hidden">
        {processedData.map((dim, idx) => {
          const isExpanded = expandedDimensions.has(dim.dimension)
          const hasProblem = dim.is.length > 0
          const hasHealthy = dim.isNot.length > 0

          return (
            <div key={dim.dimension} className={idx > 0 ? 'border-t border-slate-800' : ''}>
              {/* Level 1: Dimension summary row */}
              <button
                onClick={() => toggleDimension(dim.dimension)}
                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-800/40 transition-colors text-left"
              >
                {/* Expand indicator */}
                <span className="flex-shrink-0 text-slate-600">
                  {isExpanded
                    ? <ChevronDown className="w-3.5 h-3.5" />
                    : <ChevronRight className="w-3.5 h-3.5" />
                  }
                </span>

                {/* Dimension name — governed glossary term when the backend
                    resolved one (see IsIsNotItem.dimension_label), else a
                    mechanical Title Case fallback. Widened from w-28 and no
                    longer force-uppercased: that width/casing fit raw column
                    names like "CUSTOMER_REGION" (which is exactly why they
                    were truncating mid-word, e.g. "CUSTOMER_REGI…"), not real
                    English phrases like "Customer Region". The raw technical
                    field name is still available on hover for a Framer who
                    wants it. */}
                <span
                  className="w-36 flex-shrink-0 text-[11px] tracking-wide text-slate-400 font-medium truncate"
                  title={dim.dimension}
                >
                  {dim.dimensionLabel}
                </span>

                {/* Largest single-segment driver — NOT the dimension rollup total.
                    Was showing dim.netIsVariance here, which is the SAME rollup
                    figure re-derived for every dimension (it's a full-partition
                    total, mathematically identical across any GROUP BY slicing of
                    the same data) — so every row showed the identical number
                    (e.g. "-$3.0M" repeated across all 7 dimensions), telling a
                    reader nothing about which dimension actually concentrates the
                    variance. dim.sortKey (the most extreme single member delta,
                    already computed above for row ORDERING) is what genuinely
                    varies per dimension and answers "how bad is the worst segment
                    here" — showing it is what makes the existing sort order
                    legible, not just a hidden implementation detail. The rollup
                    total is still available, in the tooltip, correctly framed. */}
                <div
                  className="w-32 flex-shrink-0 flex items-center justify-end gap-1"
                  title={[
                    dim.sortKeyIsConfirmedOnly
                      ? `Largest gap among the segments here that are worse than both ${mainWords.phrase} and ${otherWords.phrase}. Segments worse on only one comparison are left out of this figure, even when their gap is larger.`
                      : matrixRan
                        ? `No segment here is worse than both ${mainWords.phrase} and ${otherWords.phrase}; this is the largest gap ${mainWords.heading}.`
                        : 'Largest single-segment driver in this dimension.',
                    dim.netIsVariance == null
                      ? 'No dimension-level rollup total was supplied (a ratio KPI\'s segments cannot be summed to derive one).'
                      : `Dimension-wide rollup total: ${fmtDelta(dim.netIsVariance)} (computed across all segments, not the sum of the rows below).`,
                  ].join(' ')}
                >
                  <span
                    className={`font-mono text-xs ${
                      hasProblem
                        ? isMixed
                          ? (dim.sortKey < 0 ? 'text-severity-critical' : 'text-severity-opportunity')
                          : isOpportunity ? 'text-severity-opportunity' : 'text-severity-critical'
                        : 'text-slate-600'
                    }`}
                  >
                    {!hasProblem ? '—' : fmtDelta(dim.sortKey)}
                  </span>
                </div>
                {matrixRan && hasProblem && (() => {
                  const driver = dim.is.find(i => (i.delta || 0) === dim.sortKey)
                  return driver ? (
                    <span className="flex-shrink-0 hidden md:inline">
                      <TierChip tier={driver.basis_agreement} text={phraseFor(driver)} />
                    </span>
                  ) : null
                })()}

                {/* IS count badges */}
                <div className="flex items-center gap-2 ml-auto">
                  {isMixed && hasProblem ? (() => {
                    const probCt = dim.is.filter(i => i.segment_type !== 'opportunity').length
                    const oppCt = dim.is.filter(i => i.segment_type === 'opportunity').length
                    return (
                      <>
                        {probCt > 0 && (
                          <span className="text-[10px] px-2 py-0.5 rounded font-medium bg-severity-critical/20 border border-severity-critical/60 text-severity-critical">
                            {probCt} problem
                          </span>
                        )}
                        {oppCt > 0 && (
                          <span className="text-[10px] px-2 py-0.5 rounded font-medium bg-severity-opportunity/20 border border-severity-opportunity/60 text-severity-opportunity">
                            {oppCt} opportunity
                          </span>
                        )}
                      </>
                    )
                  })() : (
                    <>
                      {hasProblem && (
                        <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${isOpportunity ? 'bg-severity-opportunity/20 border border-severity-opportunity/60 text-severity-opportunity' : 'bg-severity-critical/20 border border-severity-critical/60 text-severity-critical'}`}>
                          {dim.is.length} {isOpportunity ? 'leading' : (dim.is.length === 1 ? 'problem area' : 'problem areas')}
                        </span>
                      )}
                      {hasHealthy && (
                        <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${isOpportunity ? 'bg-severity-warning/20 border border-severity-warning/40 text-severity-warning' : 'bg-severity-opportunity/20 border border-severity-opportunity/40 text-severity-opportunity'}`}>
                          {dim.isNot.length} {isOpportunity ? 'unrealised' : 'healthy'}
                        </span>
                      )}
                    </>
                  )}
                  {!hasProblem && !hasHealthy && (
                    <span className="text-[10px] text-slate-600">no data</span>
                  )}
                </div>
              </button>

              {/* Level 2: Expanded item bars */}
              {isExpanded && (
                <div className="bg-slate-950/60 border-t border-slate-800/60 px-4 py-3 space-y-2">
                  {matrixRan && (
                    <div className="flex items-center gap-3 text-[9px] uppercase tracking-widest text-slate-500">
                      <span className="w-28 flex-shrink-0" />
                      <span className="flex-1" />
                      <span className="w-20 flex-shrink-0 text-right">{mainWords.heading}</span>
                      <span className="w-20 flex-shrink-0 text-right">{otherWords.heading}</span>
                      <span className="w-44 flex-shrink-0" />
                    </div>
                  )}
                  {/* IS items — red bars (problem) or green bars (opportunity leaders); mixed: color by segment_type */}
                  {dim.is.map((item, i) => {
                    const barPct = Math.max(4, Math.abs(item.delta || 0) / maxDelta * 100)
                    const isOppItem = isMixed ? item.segment_type === 'opportunity' : isOpportunity
                    return (
                      <div key={`is-${item.key}-${i}`} className="flex items-center gap-3">
                        <div className="w-28 flex-shrink-0 text-xs text-slate-300 truncate" title={item.key}>
                          {item.key}
                        </div>
                        <div className="flex-1 h-4 bg-slate-900 rounded overflow-hidden">
                          <div
                            className={`h-full rounded ${isOppItem ? 'bg-severity-opportunity' : 'bg-severity-critical'}`}
                            style={{ width: `${barPct}%` }}
                          />
                        </div>
                        <span className={`w-20 flex-shrink-0 text-right font-mono text-xs ${isOppItem ? 'text-severity-opportunity' : 'text-severity-critical'}`}>
                          {fmtDelta(item.delta || 0)}
                        </span>
                        {matrixRan && (
                          <>
                            <span className="w-20 flex-shrink-0 text-right font-mono text-[11px] text-slate-400" title={otherWords.heading}>
                              {item.secondary_delta != null ? fmtDelta(item.secondary_delta) : '—'}
                            </span>
                            <span className="w-44 flex-shrink-0"><TierChip tier={item.basis_agreement} text={phraseFor(item)} /></span>
                          </>
                        )}
                      </div>
                    )
                  })}

                  {/* IS NOT items — green bars (healthy) or amber bars (replication targets) */}
                  {dim.isNot.map((item, i) => {
                    const absDelta = Math.abs(item.delta || 0)
                    const showCurrent = absDelta < 0.001 && (item.current || 0) !== 0
                    const barPct = showCurrent
                      ? Math.max(4, Math.abs(item.current) / maxDelta * 100)
                      : Math.max(4, absDelta / maxDelta * 100)
                    const displayVal = showCurrent
                      ? (isRatioKpi ? `${(item.current || 0).toFixed(2)}%` : formatExecutive(item.current || 0, '$', false))
                      : fmtDelta(item.delta || 0)

                    return (
                      <div key={`isnot-${item.key}-${i}`} className="flex items-center gap-3">
                        <div className="w-28 flex-shrink-0 text-xs text-slate-400 truncate" title={item.key}>
                          {item.key}
                        </div>
                        <div className="flex-1 h-4 bg-slate-900 rounded overflow-hidden">
                          <div
                            className={`h-full rounded ${isOpportunity ? 'bg-severity-warning' : 'bg-severity-opportunity'}`}
                            style={{ width: `${barPct}%` }}
                          />
                        </div>
                        <span className={`w-20 flex-shrink-0 text-right font-mono text-xs ${isOpportunity ? 'text-severity-warning' : 'text-severity-opportunity'}`}>
                          {displayVal}
                        </span>
                        {matrixRan && (
                          <>
                            <span className="w-20 flex-shrink-0 text-right font-mono text-[11px] text-slate-500" title={otherWords.heading}>
                              {item.secondary_delta != null ? fmtDelta(item.secondary_delta) : '—'}
                            </span>
                            <span className="w-44 flex-shrink-0"><TierChip tier={item.basis_agreement} text={phraseFor(item)} /></span>
                          </>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

// Keep DivergingBarChart as alias so existing imports in DeepFocusView don't break
export const DivergingBarChart = IsIsNotExhibit
