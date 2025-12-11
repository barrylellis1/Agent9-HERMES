import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { scaleLinear, scaleBand } from '@visx/scale'
import { Play, Pause } from 'lucide-react'

// --- Types ---
interface Distribution {
  id: string
  label: string
  data: number[] // Raw values
}

interface Snapshot {
  date: string
  distributions: Distribution[]
}

interface RidgelineScannerProps {
  history: Snapshot[]
  width?: number
  height?: number
}

// --- Component ---
export const RidgelineScanner: React.FC<RidgelineScannerProps> = ({ 
  history, 
  width = 800, 
  height = 400 
}) => {
  const [timeIndex, setTimeIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)

  // Auto-play effect
  React.useEffect(() => {
    if (!isPlaying) return
    const timer = setInterval(() => {
      setTimeIndex(prev => (prev + 1) % history.length)
    }, 800) // Speed of animation
    return () => clearInterval(timer)
  }, [isPlaying, history.length])

  // Get current data snapshot
  const currentSnapshot = history[timeIndex]
  
  // Dimensions
  const margin = { top: 40, right: 20, bottom: 40, left: 100 }
  const xMax = width - margin.left - margin.right
  const yMax = height - margin.top - margin.bottom

  // Scales
  const xScale = useMemo(() => scaleLinear({
    domain: [-1, 1], // Margin variance range (-100% to +100%)
    range: [0, xMax],
  }), [xMax])

  const yScale = useMemo(() => scaleBand({
    domain: currentSnapshot.distributions.map(d => d.id),
    range: [0, yMax],
    padding: 0.2,
  }), [currentSnapshot, yMax])

  // Color logic (Dynamic Gradient based on distribution shape)
  // We'll use Framer Motion to animate the SVG paths
  
  return (
    <div className="w-full h-full flex flex-col text-slate-200">
      
      {/* 1. The Visualization Area */}
      <div className="flex-1 relative">
        <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
          <g transform={`translate(${margin.left}, ${margin.top})`}>
            
            {/* Grid Lines */}
            <line x1={xScale(0)} x2={xScale(0)} y1={0} y2={yMax} stroke="#334155" strokeWidth={2} strokeDasharray="4 4" />
            <text x={xScale(0)} y={-10} textAnchor="middle" fill="#94a3b8" fontSize={12}>Target (0%)</text>
            
            <text x={xScale(-0.5)} y={-10} textAnchor="middle" fill="#ef4444" fontSize={10}>-50%</text>
            <text x={xScale(0.5)} y={-10} textAnchor="middle" fill="#10b981" fontSize={10}>+50%</text>

            <AnimatePresence mode="popLayout">
              {currentSnapshot.distributions.map((dist) => {
                // Generate path data for the density curve
                // For this MVP, we fake a KDE by just drawing a smooth curve through bins
                // In a real app, we'd use d3-array's bin() or a kernel density estimator
                const bins = histogram(dist.data, 20)
                const pathData = generatePath(bins, xScale, yScale.bandwidth())

                return (
                  <g key={dist.id} transform={`translate(0, ${yScale(dist.id)})`}>
                    
                    {/* Row Label */}
                    <text 
                      x={-15} 
                      y={yScale.bandwidth() / 2} 
                      textAnchor="end" 
                      dominantBaseline="middle" 
                      fill="#e2e8f0" 
                      fontSize={14} 
                      fontWeight={500}
                    >
                      {dist.label}
                    </text>

                    {/* The Animated Ridge */}
                    <motion.path
                      initial={{ d: pathData }}
                      animate={{ d: pathData }}
                      transition={{ 
                        type: "spring", 
                        stiffness: 100, 
                        damping: 20 
                      }}
                      d={pathData}
                      fill="url(#gradient-ridge)"
                      stroke="rgba(255,255,255,0.5)"
                      strokeWidth={1}
                      fillOpacity={0.8}
                      filter="drop-shadow(0px 4px 4px rgba(0,0,0,0.5))"
                    />
                  </g>
                )
              })}
            </AnimatePresence>
            
            {/* Gradient Definition */}
            <defs>
              <linearGradient id="gradient-ridge" x1="0" x2="1" y1="0" y2="0">
                <stop offset="0%" stopColor="#ef4444" stopOpacity="0.6" /> {/* Red (Negative) */}
                <stop offset="45%" stopColor="#3b82f6" stopOpacity="0.4" /> {/* Blue (Neutral) */}
                <stop offset="55%" stopColor="#3b82f6" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#10b981" stopOpacity="0.6" /> {/* Green (Positive) */}
              </linearGradient>
            </defs>

          </g>
        </svg>
      </div>

      {/* 2. The Time Machine Controls */}
      <div className="h-16 border-t border-slate-700 mt-4 flex items-center gap-4 px-2">
        <button 
          onClick={() => setIsPlaying(!isPlaying)}
          className="w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-500 flex items-center justify-center text-white transition-colors"
        >
          {isPlaying ? <Pause size={18} /> : <Play size={18} fill="currentColor" />}
        </button>

        <div className="flex-1 flex flex-col justify-center">
          <div className="flex justify-between text-xs text-slate-400 mb-2">
            <span>Timeline</span>
            <span className="font-mono text-blue-400">{currentSnapshot.date}</span>
          </div>
          <input 
            type="range" 
            min={0} 
            max={history.length - 1} 
            value={timeIndex}
            onChange={(e) => {
              setIsPlaying(false)
              setTimeIndex(parseInt(e.target.value))
            }}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
          />
        </div>
      </div>
    </div>
  )
}

// --- Helper: Simple Histogram Generator ---
function histogram(data: number[], binCount: number) {
  const min = -1, max = 1
  const step = (max - min) / binCount
  const bins = Array(binCount).fill(0)
  
  data.forEach(v => {
    const binIndex = Math.floor((v - min) / step)
    if (binIndex >= 0 && binIndex < binCount) {
      bins[binIndex]++
    }
  })
  
  // Normalize and smooth
  return bins.map((count, i) => ({
    x: min + (i * step),
    y: count / data.length
  }))
}

// --- Helper: Path Generator ---
function generatePath(bins: {x: number, y: number}[], xScale: any, height: number) {
  // SVG Path command
  let d = `M ${xScale(bins[0].x)} ${height}` // Start bottom-left
  
  bins.forEach(bin => {
    const x = xScale(bin.x)
    const y = height - (bin.y * height * 3) // Scale up height for visibility
    d += ` L ${x} ${y}`
  })
  
  d += ` L ${xScale(bins[bins.length-1].x)} ${height} Z` // Close path
  return d
}
