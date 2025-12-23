import React, { useMemo, useState } from 'react'
import { motion } from 'framer-motion'

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

interface DivergingBarChartProps {
  data: KTIsIsNotData
  kpiName?: string
  width?: number
}

export const DivergingBarChart: React.FC<DivergingBarChartProps> = ({ 
  data, 
  kpiName = "KPI",
  width = 600
}) => {
  const [hoveredItem, setHoveredItem] = useState<IsIsNotItem | null>(null)

  // Processed data type
  interface ProcessedDimension {
    dimension: string
    is: IsIsNotItem[]
    isNot: IsIsNotItem[]
  }

  // Process data into grouped format by dimension
  const processedData: ProcessedDimension[] = useMemo(() => {
    if (!data) return []
    
    try {
      const dimensionMap = new Map<string, { is: IsIsNotItem[], isNot: IsIsNotItem[], isKeys: Set<string> }>()
      
      // Process "where_is" items (problem areas) FIRST
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
          text: item.text
        })
        dimData.isKeys.add(key)
      })
      
      // Process "where_is_not" items (healthy areas) - SKIP if key already in "is"
      const whereIsNot = Array.isArray(data.where_is_not) ? data.where_is_not : []
      whereIsNot.forEach((item: any) => {
        if (!item || !item.dimension) return
        if (!dimensionMap.has(item.dimension)) {
          dimensionMap.set(item.dimension, { is: [], isNot: [], isKeys: new Set() })
        }
        const dimData = dimensionMap.get(item.dimension)!
        const key = item.key || 'Unknown'
        // Deduplicate: skip if this key is already in the ISSUE list
        if (dimData.isKeys.has(key)) return
        dimData.isNot.push({
          dimension: item.dimension || '',
          key,
          current: parseFloat(item.current) || 0,
          previous: parseFloat(item.previous) || 0,
          delta: parseFloat(item.delta) || 0,
          text: item.text
        })
      })
      
      const result: ProcessedDimension[] = []
      dimensionMap.forEach((items: { is: IsIsNotItem[], isNot: IsIsNotItem[], isKeys: Set<string> }, dimension: string) => {
        result.push({
          dimension,
          is: items.is,
          isNot: items.isNot
        })
      })
      return result
    } catch (e) {
      console.error('DivergingBarChart: Error processing data', e, data)
      return []
    }
  }, [data])

  // Find max absolute delta for scaling
  const maxDelta = useMemo(() => {
    let max = 0
    processedData.forEach(dim => {
      dim.is.forEach(item => {
        max = Math.max(max, Math.abs(item.delta || 0))
      })
      dim.isNot.forEach(item => {
        max = Math.max(max, Math.abs(item.delta || 0))
      })
    })
    return max || 1
  }, [processedData])

  // Early return for missing/invalid data
  if (!data) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-500 text-sm">
        No data provided
      </div>
    )
  }

  if (processedData.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-500 text-sm">
        No Is/Is Not data available
      </div>
    )
  }

  const barMaxWidth = (width - 200) / 2 // Half width for each side

  return (
    <div className="w-full" style={{ maxWidth: width }}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4 px-2">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-xs text-slate-400">Problem Areas (IS)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-emerald-500" />
            <span className="text-xs text-slate-400">Healthy Areas (IS NOT)</span>
          </div>
        </div>
        <span className="text-xs text-slate-500">{kpiName} Variance</span>
      </div>

      {/* Chart */}
      <div className="space-y-4">
        {processedData.map((dimData, dimIdx) => (
          <div key={dimData.dimension} className="bg-slate-900/50 rounded-lg p-3 border border-slate-800">
            {/* Dimension Label */}
            <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              {dimData.dimension}
            </div>
            
            {/* Bars Container */}
            <div className="space-y-2">
              {/* IS items (Problem - Red, Left side negative) */}
              {dimData.is.map((item, idx) => {
                const barWidth = Math.abs(item.delta || 0) / maxDelta * barMaxWidth
                const isHovered = hoveredItem?.key === item.key && hoveredItem?.dimension === item.dimension
                
                return (
                  <motion.div
                    key={`is-${item.key}-${idx}`}
                    className="flex items-center gap-2"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: dimIdx * 0.1 + idx * 0.05 }}
                    onMouseEnter={() => setHoveredItem(item)}
                    onMouseLeave={() => setHoveredItem(null)}
                  >
                    {/* Label */}
                    <div className="w-24 text-right text-xs text-slate-300 truncate" title={item.key}>
                      {item.key}
                    </div>
                    
                    {/* Bar Container */}
                    <div className="flex-1 flex items-center">
                      {/* Left side (IS - Problem) */}
                      <div className="flex-1 flex justify-end">
                        <motion.div
                          className={`h-5 rounded-l ${isHovered ? 'bg-red-400' : 'bg-red-500'} flex items-center justify-end pr-2`}
                          initial={{ width: 0 }}
                          animate={{ width: barWidth }}
                          transition={{ duration: 0.5, delay: dimIdx * 0.1 + idx * 0.05 }}
                        >
                          {barWidth > 40 && (
                            <span className="text-[10px] text-white font-medium">
                              {item.delta?.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                            </span>
                          )}
                        </motion.div>
                      </div>
                      
                      {/* Center Line */}
                      <div className="w-px h-6 bg-slate-600" />
                      
                      {/* Right side (empty for IS items) */}
                      <div className="flex-1" />
                    </div>
                    
                    {/* Status Badge */}
                    <div className="w-16 text-left">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-900/30 text-red-400 border border-red-900/50">
                        ISSUE
                      </span>
                    </div>
                  </motion.div>
                )
              })}
              
              {/* IS NOT items (Healthy - Green, Right side positive) */}
              {dimData.isNot.map((item, idx) => {
                const barWidth = Math.abs(item.delta || 0) / maxDelta * barMaxWidth
                const isHovered = hoveredItem?.key === item.key && hoveredItem?.dimension === item.dimension
                
                return (
                  <motion.div
                    key={`isnot-${item.key}-${idx}`}
                    className="flex items-center gap-2"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: dimIdx * 0.1 + idx * 0.05 + 0.2 }}
                    onMouseEnter={() => setHoveredItem(item)}
                    onMouseLeave={() => setHoveredItem(null)}
                  >
                    {/* Label */}
                    <div className="w-24 text-right text-xs text-slate-400 truncate" title={item.key}>
                      {item.key}
                    </div>
                    
                    {/* Bar Container */}
                    <div className="flex-1 flex items-center">
                      {/* Left side (empty for IS NOT items) */}
                      <div className="flex-1" />
                      
                      {/* Center Line */}
                      <div className="w-px h-6 bg-slate-600" />
                      
                      {/* Right side (IS NOT - Healthy) */}
                      <div className="flex-1 flex justify-start">
                        <motion.div
                          className={`h-5 rounded-r ${isHovered ? 'bg-emerald-400' : 'bg-emerald-500'} flex items-center justify-start pl-2`}
                          initial={{ width: 0 }}
                          animate={{ width: barWidth || 20 }}
                          transition={{ duration: 0.5, delay: dimIdx * 0.1 + idx * 0.05 + 0.2 }}
                        >
                          {(barWidth || 20) > 40 && (
                            <span className="text-[10px] text-white font-medium">
                              {item.delta?.toLocaleString(undefined, { maximumFractionDigits: 0 }) || 'OK'}
                            </span>
                          )}
                        </motion.div>
                      </div>
                    </div>
                    
                    {/* Status Badge */}
                    <div className="w-16 text-left">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-900/30 text-emerald-400 border border-emerald-900/50">
                        OK
                      </span>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Tooltip */}
      {hoveredItem && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 bg-slate-800 border border-slate-700 rounded-lg p-3"
        >
          <div className="text-xs text-slate-400 mb-1">{hoveredItem.dimension}</div>
          <div className="font-bold text-white mb-2">{hoveredItem.key}</div>
          <div className="grid grid-cols-3 gap-4 text-xs">
            <div>
              <span className="text-slate-500 block">Previous</span>
              <span className="text-slate-200">{hoveredItem.previous?.toLocaleString() || 'N/A'}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Current</span>
              <span className="text-slate-200">{hoveredItem.current?.toLocaleString() || 'N/A'}</span>
            </div>
            <div>
              <span className="text-slate-500 block">Delta</span>
              <span className={hoveredItem.delta < 0 ? 'text-red-400' : 'text-emerald-400'}>
                {hoveredItem.delta > 0 ? '+' : ''}{hoveredItem.delta?.toLocaleString() || 'N/A'}
              </span>
            </div>
          </div>
          {hoveredItem.text && (
            <div className="mt-2 text-xs text-slate-400 italic border-t border-slate-700 pt-2">
              {hoveredItem.text}
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
