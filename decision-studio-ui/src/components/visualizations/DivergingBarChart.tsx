import React, { useMemo, useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

// --- Types ---
export interface IsIsNotItem {
  dimension: string
  key: string
  current: number
  previous: number
  delta: number
  text?: string
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
}

// ─── IsIsNotExhibit — printed exhibit style, two-level expand ────────────────

export const IsIsNotExhibit: React.FC<IsIsNotExhibitProps> = ({
  data,
  kpiName = 'KPI',
}) => {
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

      // Sort: dimensions with problem areas first
      result.sort((a, b) => a.netIsVariance - b.netIsVariance)
      return result
    } catch (e) {
      console.error('IsIsNotExhibit: Error processing data', e)
      return []
    }
  }, [data])

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
      <div className="flex items-center justify-center h-24 text-slate-500 text-sm">
        No Is / Is Not data available
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
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-sm bg-red-600" />
            <span className="text-[10px] text-slate-500">Problem area</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-sm bg-emerald-700" />
            <span className="text-[10px] text-slate-500">Healthy</span>
          </div>
        </div>
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

                {/* Dimension name */}
                <span className="w-28 flex-shrink-0 text-[11px] uppercase tracking-wider text-slate-400 font-medium truncate">
                  {dim.dimension}
                </span>

                {/* Net IS variance */}
                <span className={`w-24 flex-shrink-0 text-right font-mono text-xs ${hasProblem ? 'text-red-400' : 'text-slate-600'}`}>
                  {hasProblem
                    ? dim.netIsVariance.toLocaleString(undefined, { maximumFractionDigits: 0 })
                    : '—'
                  }
                </span>

                {/* IS count badge */}
                <div className="flex items-center gap-2 ml-auto">
                  {hasProblem && (
                    <span className="text-[10px] px-2 py-0.5 bg-red-950 border border-red-900/60 text-red-400 rounded font-medium">
                      {dim.is.length} {dim.is.length === 1 ? 'problem area' : 'problem areas'}
                    </span>
                  )}
                  {hasHealthy && (
                    <span className="text-[10px] px-2 py-0.5 bg-emerald-950 border border-emerald-900/40 text-emerald-600 rounded font-medium">
                      {dim.isNot.length} healthy
                    </span>
                  )}
                  {!hasProblem && !hasHealthy && (
                    <span className="text-[10px] text-slate-600">no data</span>
                  )}
                </div>
              </button>

              {/* Level 2: Expanded item bars */}
              {isExpanded && (
                <div className="bg-slate-950/60 border-t border-slate-800/60 px-4 py-3 space-y-2">
                  {/* IS items — red bars */}
                  {dim.is.map((item, i) => {
                    const barPct = Math.max(4, Math.abs(item.delta || 0) / maxDelta * 100)
                    return (
                      <div key={`is-${item.key}-${i}`} className="flex items-center gap-3">
                        <div className="w-28 flex-shrink-0 text-xs text-slate-300 truncate" title={item.key}>
                          {item.key}
                        </div>
                        <div className="flex-1 h-4 bg-slate-900 rounded overflow-hidden">
                          <div
                            className="h-full bg-red-700 rounded"
                            style={{ width: `${barPct}%` }}
                          />
                        </div>
                        <span className="w-20 flex-shrink-0 text-right font-mono text-xs text-red-400">
                          {item.delta?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                        </span>
                      </div>
                    )
                  })}

                  {/* IS NOT items — green bars */}
                  {dim.isNot.map((item, i) => {
                    const absDelta = Math.abs(item.delta || 0)
                    const showCurrent = absDelta < 0.001 && (item.current || 0) !== 0
                    const barPct = showCurrent
                      ? Math.max(4, Math.abs(item.current) / maxDelta * 100)
                      : Math.max(4, absDelta / maxDelta * 100)
                    const displayVal = showCurrent
                      ? item.current?.toLocaleString(undefined, { maximumFractionDigits: 1 })
                      : (item.delta >= 0
                          ? `+${item.delta?.toLocaleString(undefined, { maximumFractionDigits: 0 })}`
                          : item.delta?.toLocaleString(undefined, { maximumFractionDigits: 0 }))

                    return (
                      <div key={`isnot-${item.key}-${i}`} className="flex items-center gap-3">
                        <div className="w-28 flex-shrink-0 text-xs text-slate-400 truncate" title={item.key}>
                          {item.key}
                        </div>
                        <div className="flex-1 h-4 bg-slate-900 rounded overflow-hidden">
                          <div
                            className="h-full bg-emerald-800 rounded"
                            style={{ width: `${barPct}%` }}
                          />
                        </div>
                        <span className="w-20 flex-shrink-0 text-right font-mono text-xs text-emerald-600">
                          {displayVal}
                        </span>
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
