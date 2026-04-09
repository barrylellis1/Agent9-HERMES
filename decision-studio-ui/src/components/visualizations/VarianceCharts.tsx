import React, { useMemo } from 'react'
import { IsIsNotItem } from '../../api/types'
import { IsIsNotExhibit, KTIsIsNotData } from './DivergingBarChart'

// VarianceBarList — stub kept for import compatibility.
// Internal rendering now delegates to IsIsNotExhibit.
export const VarianceBarList: React.FC<{
  items: IsIsNotItem[]
  maxDelta: number
  type: 'is' | 'isNot'
  title: string
}> = () => null

// VarianceSummary — shows the three headline numbers: total IS variance,
// IS NOT count, and net impact. No bar charts (those live in IsIsNotExhibit).
export const VarianceSummary: React.FC<{
  isItems: IsIsNotItem[]
  isNotItems: IsIsNotItem[]
  kpiName: string
}> = ({ isItems, isNotItems, kpiName }) => {
  const totalIsVariance = useMemo(() =>
    isItems.reduce((sum, item) => sum + (item.delta || 0), 0), [isItems])

  const totalIsNotVariance = useMemo(() =>
    isNotItems.reduce((sum, item) => sum + (item.delta || 0), 0), [isNotItems])

  const netImpact = totalIsVariance + totalIsNotVariance

  // Build a synthetic KTIsIsNotData to pass to IsIsNotExhibit
  const exhibitData: KTIsIsNotData = useMemo(() => ({
    where_is: isItems,
    where_is_not: isNotItems,
  }), [isItems, isNotItems])

  return (
    <div className="w-full space-y-4">
      {/* Three headline numbers */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
          <div className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Problem Variance</div>
          <div className="text-sm font-mono text-red-400">
            {totalIsVariance.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
          <div className="text-[10px] text-slate-600 mt-0.5">{isItems.length} areas</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
          <div className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Healthy Areas</div>
          <div className="text-sm font-mono text-emerald-600">
            {isNotItems.length}
          </div>
          <div className="text-[10px] text-slate-600 mt-0.5">IS NOT impacted</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
          <div className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Net Impact</div>
          <div className={`text-sm font-mono font-bold ${netImpact < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {netImpact > 0 ? '+' : ''}{netImpact.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
        </div>
      </div>

      {/* Full exhibit */}
      <IsIsNotExhibit data={exhibitData} kpiName={kpiName} />
    </div>
  )
}
