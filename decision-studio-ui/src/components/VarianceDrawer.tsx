import React, { useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronUp, ChevronDown, TrendingDown, TrendingUp, BarChart3 } from 'lucide-react'

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

interface TimeframeMapping {
  current: string
  previous: string
}

interface VarianceDrawerProps {
  data: KTIsIsNotData | null
  kpiName?: string
  timeframeMapping?: TimeframeMapping | null
  comparisonType?: string  // 'previous' | 'budget' | 'yoy' | 'qoq' | 'mom'
  isOpen: boolean
  onToggle: () => void
}

// Simple horizontal bar chart for one side (IS or IS-NOT)
const VarianceBarList: React.FC<{
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
const VarianceSummary: React.FC<{
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

export const VarianceDrawer: React.FC<VarianceDrawerProps> = ({
  data,
  kpiName = "KPI",
  timeframeMapping,
  comparisonType,
  isOpen,
  onToggle
}) => {
  // Process and deduplicate data
  const processedData = useMemo(() => {
    const emptyResult = { isItems: [] as IsIsNotItem[], isNotItems: [] as IsIsNotItem[], maxDelta: 1 };
    if (!data) return emptyResult;
    
    const isKeys = new Set<string>();
    const isArr: IsIsNotItem[] = [];
    const isNotArr: IsIsNotItem[] = [];
    
    // Process IS items first
    const whereIs = data.where_is || [];
    for (const item of whereIs) {
      if (!item?.dimension) continue;
      const key = `${item.dimension}:${item.key || 'Unknown'}`;
      isKeys.add(key);
      isArr.push({
        dimension: item.dimension,
        key: item.key || 'Unknown',
        current: item.current || 0,
        previous: item.previous || 0,
        delta: item.delta || 0,
        text: item.text
      });
    }
    
    // Process IS-NOT items, skip duplicates
    const whereIsNot = data.where_is_not || [];
    for (const item of whereIsNot) {
      if (!item?.dimension) continue;
      const key = `${item.dimension}:${item.key || 'Unknown'}`;
      if (isKeys.has(key)) continue;
      isNotArr.push({
        dimension: item.dimension,
        key: item.key || 'Unknown',
        current: item.current || 0,
        previous: item.previous || 0,
        delta: item.delta || 0,
        text: item.text
      });
    }
    
    // Calculate max delta for scaling
    let max = 1;
    for (const item of [...isArr, ...isNotArr]) {
      max = Math.max(max, Math.abs(item.delta || 0));
    }
    
    return { isItems: isArr, isNotItems: isNotArr, maxDelta: max };
  }, [data]);

  const { isItems, isNotItems, maxDelta } = processedData;

  const hasData = isItems.length > 0 || isNotItems.length > 0

  return (
    <>
      {/* Toggle Button - Always visible at bottom */}
      <motion.button
        onClick={onToggle}
        className={`fixed bottom-0 left-1/2 -translate-x-1/2 z-[60] px-6 py-2 rounded-t-lg font-medium text-sm flex items-center gap-2 transition-colors ${
          isOpen 
            ? 'bg-slate-800 text-white border-t border-x border-slate-700' 
            : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg'
        }`}
        whileHover={{ y: -2 }}
        whileTap={{ y: 0 }}
      >
        <BarChart3 className="w-4 h-4" />
        Variance Analysis
        {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        {!isOpen && hasData && (
          <span className="ml-1 px-1.5 py-0.5 bg-red-500 text-white text-[10px] rounded-full">
            {isItems.length}
          </span>
        )}
      </motion.button>

      {/* Drawer Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 30, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-[55] bg-slate-900 border-t border-slate-700 shadow-2xl"
            style={{ height: '45vh', minHeight: '300px', maxHeight: '500px' }}
          >
            {/* Drawer Header */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm">
              <div className="flex items-center gap-3">
                <BarChart3 className="w-5 h-5 text-blue-400" />
                <h3 className="text-lg font-semibold text-white">Variance Analysis</h3>
                <span className="text-sm text-slate-500">|</span>
                <span className="text-sm text-slate-400">{kpiName}</span>
                {/* Timeframe Info */}
                {timeframeMapping && (
                  <>
                    <span className="text-sm text-slate-500">|</span>
                    <span className="text-xs px-2 py-1 bg-slate-800 rounded text-slate-300">
                      <span className="text-slate-500">Comparing:</span> {timeframeMapping.current} <span className="text-slate-500">vs</span> {timeframeMapping.previous}
                    </span>
                  </>
                )}
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <span className="text-slate-400">Problem Areas (IS)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-emerald-500" />
                    <span className="text-slate-400">Healthy Areas (IS NOT)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Drawer Content */}
            <div className="h-[calc(100%-56px)] overflow-auto p-4">
              {!hasData ? (
                <div className="flex items-center justify-center h-full text-slate-500">
                  No variance data available. Run Deep Analysis first.
                </div>
              ) : (
                <div className="flex gap-4 h-full">
                  {/* IS (Problem Areas) - Left */}
                  <VarianceBarList
                    items={isItems}
                    maxDelta={maxDelta}
                    type="is"
                    title="Problem Areas (IS)"
                  />
                  
                  {/* Summary - Center */}
                  <VarianceSummary
                    isItems={isItems}
                    isNotItems={isNotItems}
                    kpiName={kpiName}
                  />
                  
                  {/* IS-NOT (Healthy Areas) - Right */}
                  <VarianceBarList
                    items={isNotItems}
                    maxDelta={maxDelta}
                    type="isNot"
                    title="Healthy Areas (IS NOT)"
                  />
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Backdrop when open */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.3 }}
            exit={{ opacity: 0 }}
            onClick={onToggle}
            className="fixed inset-0 bg-black z-[45]"
          />
        )}
      </AnimatePresence>
    </>
  )
}

export default VarianceDrawer
