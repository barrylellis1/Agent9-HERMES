import React, { useMemo } from 'react'
import { motion } from 'framer-motion'
import { TrendingDown, TrendingUp } from 'lucide-react'
import { IsIsNotItem } from '../../api/types'

// Simple horizontal bar chart for one side (IS or IS-NOT)
export const VarianceBarList: React.FC<{
  items: IsIsNotItem[]
  maxDelta: number
  type: 'is' | 'isNot'
  title: string
}> = ({ items, maxDelta, type, title }) => {
  const isProblematic = type === 'is'
  const barColor = isProblematic ? 'bg-red-500' : 'bg-emerald-500'
  const textColor = isProblematic ? 'text-red-400' : 'text-emerald-400'
  const bgColor = isProblematic ? 'bg-red-500/10' : 'bg-emerald-500/10'
  const borderColor = isProblematic ? 'border-red-500/20' : 'border-emerald-500/20'

  // Group by dimension
  const grouped = useMemo(() => {
    const map = new Map<string, IsIsNotItem[]>()
    items.forEach(item => {
      if (!map.has(item.dimension)) map.set(item.dimension, [])
      map.get(item.dimension)!.push(item)
    })
    return Array.from(map.entries())
  }, [items])

  if (items.length === 0) {
    return (
      <div className={`flex-1 ${bgColor} border ${borderColor} rounded-lg p-4`}>
        <h4 className={`text-sm font-bold ${textColor} uppercase tracking-wider mb-3 flex items-center gap-2`}>
          {isProblematic ? <TrendingDown className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
          {title}
        </h4>
        <div className="text-slate-500 text-sm italic">No items in this category</div>
      </div>
    )
  }

  return (
    <div className={`flex-1 ${bgColor} border ${borderColor} rounded-lg p-4`}>
      <h4 className={`text-sm font-bold ${textColor} uppercase tracking-wider mb-3 flex items-center gap-2`}>
        {isProblematic ? <TrendingDown className="w-4 h-4" /> : <TrendingUp className="w-4 h-4" />}
        {title}
        <span className="text-xs font-normal text-slate-500">({items.length} items)</span>
      </h4>
      
      <div className="space-y-4">
        {grouped.map(([dimension, dimItems]) => (
          <div key={dimension}>
            <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">{dimension}</div>
            <div className="space-y-1.5">
              {dimItems.map((item, idx) => {
                const barWidth = Math.min(100, Math.abs(item.delta || 0) / maxDelta * 100)
                const formattedDelta = item.delta >= 0 
                  ? `+${item.delta.toLocaleString()}` 
                  : item.delta.toLocaleString()
                
                return (
                  <motion.div
                    key={`${item.key}-${idx}`}
                    initial={{ opacity: 0, x: isProblematic ? -20 : 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    className="flex items-center gap-3"
                  >
                    <div className="w-28 text-xs text-slate-300 truncate" title={item.key}>
                      {item.key}
                    </div>
                    <div className="flex-1 h-5 bg-slate-800/50 rounded overflow-hidden relative">
                      <motion.div
                        className={`h-full ${barColor} rounded`}
                        initial={{ width: 0 }}
                        animate={{ width: `${barWidth}%` }}
                        transition={{ duration: 0.5, delay: idx * 0.03 }}
                      />
                    </div>
                    <div className={`w-20 text-xs font-mono ${textColor} text-right`}>
                      {formattedDelta}
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// Summary stats in the center
export const VarianceSummary: React.FC<{
  isItems: IsIsNotItem[]
  isNotItems: IsIsNotItem[]
  kpiName: string
}> = ({ isItems, isNotItems, kpiName }) => {
  const totalIsVariance = useMemo(() => 
    isItems.reduce((sum, item) => sum + (item.delta || 0), 0), [isItems])
  
  const totalIsNotVariance = useMemo(() => 
    isNotItems.reduce((sum, item) => sum + (item.delta || 0), 0), [isNotItems])

  const avgIsVariance = isItems.length > 0 ? totalIsVariance / isItems.length : 0
  const avgIsNotVariance = isNotItems.length > 0 ? totalIsNotVariance / isNotItems.length : 0

  return (
    <div className="w-48 flex flex-col items-center justify-center px-4 border-x border-slate-700">
      <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Summary</div>
      <div className="text-lg font-bold text-white mb-1">{kpiName}</div>
      
      <div className="w-full space-y-3 mt-4">
        <div className="bg-slate-800/50 rounded p-2">
          <div className="text-[10px] text-slate-500 uppercase">Problem Areas</div>
          <div className="text-sm font-mono text-red-400">
            {totalIsVariance.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-600">
            {isItems.length} items • avg {avgIsVariance.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
        </div>
        
        <div className="bg-slate-800/50 rounded p-2">
          <div className="text-[10px] text-slate-500 uppercase">Healthy Areas</div>
          <div className="text-sm font-mono text-emerald-400">
            {totalIsNotVariance >= 0 ? '+' : ''}{totalIsNotVariance.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-600">
            {isNotItems.length} items • avg {avgIsNotVariance.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
        </div>

        <div className="bg-slate-800/50 rounded p-2 border border-slate-700">
          <div className="text-[10px] text-slate-500 uppercase">Net Impact</div>
          <div className={`text-sm font-mono font-bold ${(totalIsVariance + totalIsNotVariance) < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
            {(totalIsVariance + totalIsNotVariance).toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  )
}
