import React, { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { formatExecutive } from '../../utils/formatExecutive'

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
}

export interface KTIsIsNotData {
  where_is: IsIsNotItem[]
  where_is_not: IsIsNotItem[]
  what_is?: any[]
  what_is_not?: any[]
  when_is?: any[]
  when_is_not?: any[]
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
}

// Label a comparison basis for column headers / chips
const basisLabel = (c?: string): string => (c === 'budget' ? 'vs Budget' : 'vs Prior')

// Cross-basis tier chip (Phase 11I-D)
const TierChip: React.FC<{ tier?: string | null }> = ({ tier }) => {
  if (!tier || tier === 'healthy') return null
  const cfg: Record<string, { label: string; cls: string }> = {
    confirmed: { label: 'confirmed', cls: 'bg-red-950 text-red-300 border-red-800/60' },
    basis_specific: { label: 'artifact?', cls: 'bg-amber-950 text-amber-300 border-amber-800/60' },
    secondary_only: { label: '2nd-basis', cls: 'bg-blue-950 text-blue-300 border-blue-800/60' },
  }
  const c = cfg[tier]
  if (!c) return null
  return <span className={`px-1 py-px rounded text-[8px] font-medium border ${c.cls}`}>{c.label}</span>
}

// ─── IsIsNotExhibit — printed exhibit style, two-level expand ────────────────

export const IsIsNotExhibit: React.FC<IsIsNotExhibitProps> = ({
  data,
  kpiName = 'KPI',
  analysisMode = 'problem',
  matrixRan = false,
  comparator,
  comparatorSecondary,
}) => {
  const isOpportunity = analysisMode === 'opportunity'
  const isMixed = analysisMode === 'mixed'
  const [expandedDimensions, setExpandedDimensions] = useState<Set<string>>(new Set())

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
    is: IsIsNotItem[]
    isNot: IsIsNotItem[]
    netIsVariance: number
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
        })
      })

      const result: ProcessedDimension[] = []
      dimensionMap.forEach((items, dimension) => {
        const netIsVariance = items.is.reduce((sum, i) => sum + (i.delta || 0), 0)
        result.push({
          dimension,
          is: items.is,
          isNot: items.isNot,
          netIsVariance,
        })
      })

      // Sort: opportunity mode → most positive first; problem/mixed → most negative first
      result.sort((a, b) => isOpportunity
        ? b.netIsVariance - a.netIsVariance
        : a.netIsVariance - b.netIsVariance)
      return result
    } catch (e) {
      console.error('IsIsNotExhibit: Error processing data', e)
      return []
    }
  }, [data, isOpportunity])

  // Global max delta for bar scaling within expanded sections
  const maxDelta = useMemo(() => {
    let max = 0
    processedData.forEach(dim => {
      dim.is.forEach(item => { max = Math.max(max, Math.abs(item.delta || 0)) })
      dim.isNot.forEach(item => { max = Math.max(max, Math.abs(item.delta || 0)) })
    })
    return max || 1
  }, [processedData])

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
                <div className="w-2 h-2 rounded-sm bg-red-600" />
                <span className="text-[10px] text-slate-500">Problem area</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-sm bg-emerald-600" />
                <span className="text-[10px] text-slate-500">Opportunity</span>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-sm ${isOpportunity ? 'bg-emerald-600' : 'bg-red-600'}`} />
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

      {/* Phase 11I-D: two-basis matrix banner — explains the second delta column + tiers */}
      {matrixRan && (
        <div className="mb-2 flex items-center flex-wrap gap-x-4 gap-y-1 text-[10px] text-slate-500">
          <span>Each segment cross-checked on two bases:</span>
          <span className="font-mono text-slate-400">{basisLabel(comparator)}</span>
          <span className="font-mono text-slate-400">{basisLabel(comparatorSecondary)}</span>
          <span className="flex items-center gap-1"><TierChip tier="confirmed" /> bad on both</span>
          <span className="flex items-center gap-1"><TierChip tier="basis_specific" /> likely timing artifact</span>
          <span className="flex items-center gap-1"><TierChip tier="secondary_only" /> only 2nd basis</span>
        </div>
      )}

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

                {/* Dimension name */}
                <span className="w-28 flex-shrink-0 text-[11px] uppercase tracking-wider text-slate-400 font-medium truncate">
                  {dim.dimension}
                </span>

                {/* Net IS variance */}
                <span className={`w-24 flex-shrink-0 text-right font-mono text-xs ${
                  hasProblem
                    ? isMixed
                      ? (dim.netIsVariance < 0 ? 'text-red-400' : 'text-emerald-400')
                      : isOpportunity ? 'text-emerald-400' : 'text-red-400'
                    : 'text-slate-600'
                }`}>
                  {hasProblem
                    ? dim.netIsVariance.toLocaleString(undefined, { maximumFractionDigits: 0 })
                    : '—'
                  }
                </span>

                {/* IS count badges */}
                <div className="flex items-center gap-2 ml-auto">
                  {isMixed && hasProblem ? (() => {
                    const probCt = dim.is.filter(i => i.segment_type !== 'opportunity').length
                    const oppCt = dim.is.filter(i => i.segment_type === 'opportunity').length
                    return (
                      <>
                        {probCt > 0 && (
                          <span className="text-[10px] px-2 py-0.5 rounded font-medium bg-red-950 border border-red-900/60 text-red-400">
                            {probCt} problem
                          </span>
                        )}
                        {oppCt > 0 && (
                          <span className="text-[10px] px-2 py-0.5 rounded font-medium bg-emerald-950 border border-emerald-900/60 text-emerald-400">
                            {oppCt} opportunity
                          </span>
                        )}
                      </>
                    )
                  })() : (
                    <>
                      {hasProblem && (
                        <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${isOpportunity ? 'bg-emerald-950 border border-emerald-900/60 text-emerald-400' : 'bg-red-950 border border-red-900/60 text-red-400'}`}>
                          {dim.is.length} {isOpportunity ? 'leading' : (dim.is.length === 1 ? 'problem area' : 'problem areas')}
                        </span>
                      )}
                      {hasHealthy && (
                        <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${isOpportunity ? 'bg-amber-950 border border-amber-900/40 text-amber-600' : 'bg-emerald-950 border border-emerald-900/40 text-emerald-600'}`}>
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
                            className={`h-full rounded ${isOppItem ? 'bg-emerald-700' : 'bg-red-700'}`}
                            style={{ width: `${barPct}%` }}
                          />
                        </div>
                        <span className={`w-20 flex-shrink-0 text-right font-mono text-xs ${isOppItem ? 'text-emerald-400' : 'text-red-400'}`}>
                          {formatExecutive(item.delta || 0)}
                        </span>
                        {matrixRan && (
                          <>
                            <span className="w-20 flex-shrink-0 text-right font-mono text-[11px] text-slate-400" title={basisLabel(comparatorSecondary)}>
                              {item.secondary_delta != null ? formatExecutive(item.secondary_delta) : '—'}
                            </span>
                            <span className="w-16 flex-shrink-0"><TierChip tier={item.basis_agreement} /></span>
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
                      ? formatExecutive(item.current || 0, '$', false)
                      : formatExecutive(item.delta || 0)

                    return (
                      <div key={`isnot-${item.key}-${i}`} className="flex items-center gap-3">
                        <div className="w-28 flex-shrink-0 text-xs text-slate-400 truncate" title={item.key}>
                          {item.key}
                        </div>
                        <div className="flex-1 h-4 bg-slate-900 rounded overflow-hidden">
                          <div
                            className={`h-full rounded ${isOpportunity ? 'bg-amber-800' : 'bg-emerald-800'}`}
                            style={{ width: `${barPct}%` }}
                          />
                        </div>
                        <span className={`w-20 flex-shrink-0 text-right font-mono text-xs ${isOpportunity ? 'text-amber-600' : 'text-emerald-600'}`}>
                          {displayVal}
                        </span>
                        {matrixRan && (
                          <>
                            <span className="w-20 flex-shrink-0 text-right font-mono text-[11px] text-slate-500" title={basisLabel(comparatorSecondary)}>
                              {item.secondary_delta != null ? formatExecutive(item.secondary_delta) : '—'}
                            </span>
                            <span className="w-16 flex-shrink-0"><TierChip tier={item.basis_agreement} /></span>
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
