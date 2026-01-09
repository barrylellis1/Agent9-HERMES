import React, { useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { scaleLinear } from '@visx/scale'

// --- Types ---
export interface SnowflakeAttribute {
  id: string
  label: string
  value: number
  delta: number
  deltaPct: number // 0.1 for 10%
}

export interface SnowflakeDimension {
  id: string
  label: string
  attributes: SnowflakeAttribute[]
}

interface SnowflakeScannerProps {
  data: SnowflakeDimension[]
  width?: number
  height?: number
  kpiName?: string
}

export const SnowflakeScanner: React.FC<SnowflakeScannerProps> = ({ 
  data, 
  width = 600, 
  height = 600,
  kpiName = "KPI"
}) => {
  const [hoveredNode, setHoveredNode] = useState<SnowflakeAttribute | null>(null)

  // Layout Constants
  const centerX = width / 2
  const centerY = height / 2
  const maxRadius = Math.min(width, height) / 2 - 60 // Padding for labels
  
  // Scales
  // Map Variance % (-0.5 to 0.5) to Radius (0 to maxRadius)
  // But strictly: Center of chart = -MaxVariance? Or Center = Target?
  // Let's do: Middle Ring = 0%. Inner = -50%. Outer = +50%.
  const varianceDomain = useMemo(() => [-0.5, 0.5] as const, [])
  const radiusScale = useMemo(() => scaleLinear({
    domain: varianceDomain,
    range: [40, maxRadius] // Don't go to absolute 0 center, leave a hole
  }), [maxRadius, varianceDomain])

  // Helper to get coordinates
  const getCoords = (angle: number, variance: number) => {
    // Clamp variance
    const v = Math.max(varianceDomain[0], Math.min(varianceDomain[1], variance))
    const r = radiusScale(v)
    return {
      x: centerX + r * Math.cos(angle - Math.PI / 2), // Subtract PI/2 to start at 12 o'clock
      y: centerY + r * Math.sin(angle - Math.PI / 2)
    }
  }

  if (!data || data.length === 0) {
    return <div className="flex items-center justify-center h-full text-slate-500">No data for Snowflake visualization</div>
  }

  const angleStep = (2 * Math.PI) / data.length

  return (
    <div className="relative flex items-center justify-center" style={{ width, height }}>
      <svg width={width} height={height} className="overflow-visible">
        {/* 1. Grid Rings */}
        {[0, -0.25, 0.25, -0.5, 0.5].map((tick, i) => {
          const r = radiusScale(tick)
          const isZero = tick === 0
          return (
            <g key={i}>
              <circle 
                cx={centerX} 
                cy={centerY} 
                r={r} 
                fill="none" 
                stroke={isZero ? "#64748b" : "#334155"} 
                strokeWidth={isZero ? 2 : 1} 
                strokeDasharray={isZero ? "0" : "4 4"}
                opacity={0.5}
              />
              <text 
                x={centerX + 5} 
                y={centerY - r + 12} 
                fill={isZero ? "#94a3b8" : "#475569"} 
                fontSize={10}
              >
                {tick === 0 ? "Target" : `${tick > 0 ? '+' : ''}${tick * 100}%`}
              </text>
            </g>
          )
        })}

        {/* 2. Dimension Spokes */}
        {data.map((dim, i) => {
          const angle = i * angleStep
          const endX = centerX + maxRadius * Math.cos(angle - Math.PI / 2)
          const endY = centerY + maxRadius * Math.sin(angle - Math.PI / 2)
          
          return (
            <g key={dim.id}>
              <line 
                x1={centerX} 
                y1={centerY} 
                x2={endX} 
                y2={endY} 
                stroke="#334155" 
                strokeWidth={1} 
              />
              {/* Label */}
              <text
                x={endX + (Math.cos(angle - Math.PI/2) * 20)}
                y={endY + (Math.sin(angle - Math.PI/2) * 20)}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="#e2e8f0"
                fontSize={12}
                fontWeight="bold"
              >
                {dim.label}
              </text>
            </g>
          )
        })}

        {/* 3. Attribute Nodes */}
        {data.map((dim, i) => {
          const angle = i * angleStep
          
          return (
            <g key={`nodes-${dim.id}`}>
              {dim.attributes.map((attr, j) => {
                const coords = getCoords(angle, attr.deltaPct)
                const isPositive = attr.deltaPct >= 0
                const color = isPositive ? "#10b981" : "#ef4444" // Green/Red
                const isHovered = hoveredNode?.id === attr.id
                
                return (
                  <motion.g 
                    key={attr.id}
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: isHovered ? 1.5 : 1 }}
                    transition={{ delay: i * 0.1 + j * 0.05 }}
                    onMouseEnter={() => setHoveredNode(attr)}
                    onMouseLeave={() => setHoveredNode(null)}
                    style={{ cursor: 'pointer' }}
                  >
                    <circle
                      cx={coords.x}
                      cy={coords.y}
                      r={isHovered ? 8 : 5}
                      fill={color}
                      fillOpacity={0.8}
                      stroke="#fff"
                      strokeWidth={1}
                    />
                  </motion.g>
                )
              })}
            </g>
          )
        })}
      </svg>

      {/* Tooltip Overlay */}
      <AnimatePresence>
        {hoveredNode && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="absolute z-10 bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl pointer-events-none"
            style={{ 
              top: height / 2 + 50, // Position it centrally or dynamically
              left: width / 2 - 100,
              width: 200
            }}
          >
            <div className="text-xs text-slate-400 mb-1">{kpiName} Performance</div>
            <div className="font-bold text-white mb-1">{hoveredNode.label}</div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">Value:</span>
              <span className="text-slate-200">{hoveredNode.value.toLocaleString()}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-slate-500">Variance:</span>
              <span className={`${hoveredNode.deltaPct >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {hoveredNode.deltaPct > 0 ? '+' : ''}{(hoveredNode.deltaPct * 100).toFixed(1)}%
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
