import React, { useState, useMemo } from 'react';
import { LinePath } from '@visx/shape';
import { scaleLinear } from '@visx/scale';
import { curveMonotoneX } from '@visx/curve';
import { ParentSize } from '@visx/responsive';
import { motion } from 'framer-motion';

export interface TrajectoryChartProps {
  inactionTrend: number[];
  expectedTrend: number[];
  actualTrend: number[];
  actualTrendDates: string[];
  approvedAt: string;
  measurementWindowDays: number;
  inactionHorizonMonths: number;
  kpiName?: string;
}

interface TooltipState {
  x: number;
  y: number;
  monthIndex: number;
}

// Humanize a raw KPI ID like "lub_gross_margin_pct" → "Gross Margin Pct"
function humanizeKpiId(raw: string): string {
  // Strip common prefix patterns: one segment followed by an underscore that starts the real name
  // e.g. "lub_gross_margin_pct" → "gross_margin_pct", "lube_gross_margin" → "gross_margin"
  const withoutPrefix = raw.replace(/^[a-z]{2,5}_/, '');
  return withoutPrefix
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Draws a single animating line via a framer-motion path length trick
interface AnimatedLineProps {
  d: string;
  stroke: string;
  strokeWidth?: number;
  strokeDasharray?: string;
  strokeOpacity?: number;
}

const AnimatedLine: React.FC<AnimatedLineProps> = ({
  d,
  stroke,
  strokeWidth = 2,
  strokeDasharray,
  strokeOpacity,
}) => (
  <motion.path
    d={d}
    fill="none"
    stroke={stroke}
    strokeWidth={strokeWidth}
    strokeDasharray={strokeDasharray}
    strokeOpacity={strokeOpacity}
    initial={{ pathLength: 0, opacity: 0 }}
    animate={{ pathLength: 1, opacity: strokeOpacity ?? 1 }}
    transition={{ duration: 1.2, ease: 'easeInOut' }}
  />
);

// ─── Inner chart — rendered inside ParentSize ─────────────────────────────────

interface InnerChartProps extends TrajectoryChartProps {
  width: number;
  height: number;
}

const MARGIN = { top: 16, right: 16, bottom: 28, left: 44 };

const InnerChart: React.FC<InnerChartProps> = ({
  inactionTrend,
  expectedTrend,
  actualTrend,
  measurementWindowDays,
  inactionHorizonMonths,
  width,
  height,
}) => {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const innerWidth = width - MARGIN.left - MARGIN.right;
  const innerHeight = height - MARGIN.top - MARGIN.bottom;

  // Total months on the x-axis is inactionHorizonMonths
  const totalMonths = inactionHorizonMonths || Math.max(inactionTrend.length - 1, 1);

  // Measurement window in months (approximate: days / 30)
  const measurementWindowMonths = measurementWindowDays / 30;

  // Combine all values to determine y domain
  const allValues = [
    ...inactionTrend,
    ...expectedTrend,
    ...actualTrend,
  ].filter((v) => v !== undefined && v !== null && !isNaN(v));

  const rawMin = allValues.length > 0 ? Math.min(...allValues) : 0;
  const rawMax = allValues.length > 0 ? Math.max(...allValues) : 1;
  const padding = (rawMax - rawMin) * 0.1 || 1;
  const yMin = rawMin - padding;
  const yMax = rawMax + padding;

  const xScale = useMemo(
    () =>
      scaleLinear({
        domain: [0, totalMonths],
        range: [0, innerWidth],
      }),
    [totalMonths, innerWidth]
  );

  const yScale = useMemo(
    () =>
      scaleLinear({
        domain: [yMin, yMax],
        range: [innerHeight, 0],
      }),
    [yMin, yMax, innerHeight]
  );

  // Build point arrays for each series
  const inactionPoints = inactionTrend.map((v, i) => ({
    x: (i / Math.max(inactionTrend.length - 1, 1)) * totalMonths,
    y: v,
  }));

  const expectedPoints = expectedTrend.map((v, i) => ({
    x: (i / Math.max(expectedTrend.length - 1, 1)) * measurementWindowMonths,
    y: v,
  }));

  const actualPoints = actualTrend.map((v, i) => ({
    x: i,
    y: v,
  }));

  // X position of the measurement window boundary marker
  const evalX = xScale(measurementWindowMonths);

  // Y-axis tick generation (5 ticks)
  const yTicks = useMemo(() => {
    const count = 5;
    return Array.from({ length: count }, (_, i) => {
      const val = yMin + (i / (count - 1)) * (yMax - yMin);
      return { val, y: yScale(val) };
    });
  }, [yMin, yMax, yScale]);

  // X-axis labels (M0 … Mn)
  const xLabels = useMemo(() => {
    const labels: { label: string; x: number }[] = [];
    for (let m = 0; m <= totalMonths; m++) {
      labels.push({ label: `M${m}`, x: xScale(m) });
    }
    return labels;
  }, [totalMonths, xScale]);

  // Tooltip hover: figure out which month is closest to cursor x
  const handleMouseMove = (e: React.MouseEvent<SVGRectElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const relX = e.clientX - rect.left;
    const monthFloat = xScale.invert(relX);
    const month = Math.round(monthFloat);
    const clampedMonth = Math.max(0, Math.min(totalMonths, month));
    setTooltip({ x: xScale(clampedMonth), y: relX, monthIndex: clampedMonth });
  };

  const getValueAtMonth = (points: { x: number; y: number }[], month: number): number | null => {
    if (points.length === 0) return null;
    // Find closest point by x (already in month units)
    let closest = points[0];
    let minDist = Math.abs(points[0].x - month);
    for (const p of points) {
      const dist = Math.abs(p.x - month);
      if (dist < minDist) {
        minDist = dist;
        closest = p;
      }
    }
    // Only return a value if we're close enough (within 0.75 months)
    return minDist <= 0.75 ? closest.y : null;
  };

  return (
    <div className="relative">
      <svg
        width={width}
        height={height}
        style={{ overflow: 'visible' }}
      >
        <g transform={`translate(${MARGIN.left},${MARGIN.top})`}>
          {/* Grid lines + Y axis ticks */}
          {yTicks.map(({ val, y }) => (
            <g key={val}>
              <line
                x1={0}
                x2={innerWidth}
                y1={y}
                y2={y}
                stroke="#1e293b"
                strokeWidth={1}
              />
              <text
                x={-6}
                y={y}
                dy="0.35em"
                textAnchor="end"
                fill="#64748b"
                fontSize={9}
              >
                {val.toFixed(1)}
              </text>
            </g>
          ))}

          {/* X axis labels */}
          {xLabels.map(({ label, x }) => (
            <text
              key={label}
              x={x}
              y={innerHeight + 16}
              textAnchor="middle"
              fill="#64748b"
              fontSize={9}
            >
              {label}
            </text>
          ))}

          {/* Measurement window vertical boundary line */}
          {measurementWindowMonths < totalMonths && (
            <line
              x1={evalX}
              x2={evalX}
              y1={0}
              y2={innerHeight}
              stroke="#475569"
              strokeWidth={1}
              strokeDasharray="4,3"
            />
          )}
          {measurementWindowMonths < totalMonths && (
            <text
              x={evalX + 4}
              y={8}
              fill="#475569"
              fontSize={8}
            >
              eval
            </text>
          )}

          {/* Inaction line — red faded dots */}
          {inactionPoints.length >= 2 && (
            <AnimatedLine
              d={
                inactionPoints
                  .map((p, i) =>
                    `${i === 0 ? 'M' : 'L'}${xScale(p.x).toFixed(1)},${yScale(p.y).toFixed(1)}`
                  )
                  .join(' ')
              }
              stroke="#ef4444"
              strokeWidth={1.5}
              strokeDasharray="3,4"
              strokeOpacity={0.5}
            />
          )}

          {/* Expected line — slate solid */}
          {expectedPoints.length >= 2 && (
            <AnimatedLine
              d={
                expectedPoints
                  .map((p, i) =>
                    `${i === 0 ? 'M' : 'L'}${xScale(p.x).toFixed(1)},${yScale(p.y).toFixed(1)}`
                  )
                  .join(' ')
              }
              stroke="#475569"
              strokeWidth={1.5}
            />
          )}

          {/* Actual line — white solid with dot markers */}
          {actualPoints.length >= 2 && (
            <>
              <LinePath
                data={actualPoints}
                x={(p) => xScale(p.x) ?? 0}
                y={(p) => yScale(p.y) ?? 0}
                stroke="#ffffff"
                strokeWidth={2}
                curve={curveMonotoneX}
              />
              {actualPoints.map((p, i) => (
                <circle
                  key={i}
                  cx={xScale(p.x)}
                  cy={yScale(p.y)}
                  r={4}
                  fill="#ffffff"
                  stroke="#0f172a"
                  strokeWidth={1.5}
                />
              ))}
            </>
          )}

          {/* Invisible hover target */}
          <rect
            x={0}
            y={0}
            width={innerWidth}
            height={innerHeight}
            fill="transparent"
            onMouseMove={handleMouseMove}
            onMouseLeave={() => setTooltip(null)}
          />

          {/* Tooltip vertical line */}
          {tooltip && (
            <line
              x1={tooltip.x}
              x2={tooltip.x}
              y1={0}
              y2={innerHeight}
              stroke="#94a3b8"
              strokeWidth={1}
              strokeDasharray="3,2"
              pointerEvents="none"
            />
          )}
        </g>
      </svg>

      {/* Tooltip box — positioned as a DOM overlay */}
      {tooltip && (() => {
        const inactionVal = getValueAtMonth(inactionPoints, tooltip.monthIndex);
        const expectedVal = getValueAtMonth(expectedPoints, tooltip.monthIndex);
        const actualVal = getValueAtMonth(actualPoints, tooltip.monthIndex);
        const hasAny = inactionVal !== null || expectedVal !== null || actualVal !== null;
        if (!hasAny) return null;

        const boxLeft = MARGIN.left + tooltip.x + 8;

        return (
          <motion.div
            key={tooltip.monthIndex}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute pointer-events-none bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs shadow-xl z-10"
            style={{ top: MARGIN.top, left: boxLeft }}
          >
            <div className="text-slate-400 font-medium mb-1.5">M{tooltip.monthIndex}</div>
            {inactionVal !== null && (
              <div className="flex items-center gap-2 mb-0.5">
                <span className="w-3 h-0.5 bg-red-500 opacity-50 inline-block" />
                <span className="text-slate-400">Inaction</span>
                <span className="text-red-400 font-mono ml-auto pl-3">{inactionVal.toFixed(2)}</span>
              </div>
            )}
            {expectedVal !== null && (
              <div className="flex items-center gap-2 mb-0.5">
                <span className="w-3 h-0.5 bg-slate-500 inline-block" />
                <span className="text-slate-400">Expected</span>
                <span className="text-slate-300 font-mono ml-auto pl-3">{expectedVal.toFixed(2)}</span>
              </div>
            )}
            {actualVal !== null && (
              <div className="flex items-center gap-2">
                <span className="w-3 h-0.5 bg-white inline-block" />
                <span className="text-slate-400">Actual</span>
                <span className="text-white font-mono ml-auto pl-3">{actualVal.toFixed(2)}</span>
              </div>
            )}
          </motion.div>
        );
      })()}
    </div>
  );
};

// ─── Public component ─────────────────────────────────────────────────────────

const CHART_HEIGHT = 240;

export const TrajectoryChart: React.FC<TrajectoryChartProps> = (props) => {
  const hasData = props.actualTrend.length > 1;

  return (
    <div className="bg-slate-950 border border-slate-700 rounded-xl p-4">
      {/* Header */}
      {props.kpiName && (
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          {humanizeKpiId(props.kpiName)} — Value Trajectory
        </div>
      )}

      {/* Empty state */}
      {!hasData ? (
        <div className="flex items-center justify-center h-40 text-slate-500 text-sm">
          First measurement period in progress
        </div>
      ) : (
        <ParentSize>
          {({ width }) => (
            <InnerChart
              {...props}
              width={width || 400}
              height={CHART_HEIGHT}
            />
          )}
        </ParentSize>
      )}

      {/* Legend */}
      <div className="flex items-center gap-6 mt-3 pt-3 border-t border-slate-800">
        <div className="flex items-center gap-1.5">
          <svg width={20} height={8}>
            <line x1={0} y1={4} x2={20} y2={4} stroke="#ef4444" strokeOpacity={0.5} strokeWidth={1.5} strokeDasharray="3,4" />
          </svg>
          <span className="text-[10px] text-slate-500">Inaction</span>
        </div>
        <div className="flex items-center gap-1.5">
          <svg width={20} height={8}>
            <line x1={0} y1={4} x2={20} y2={4} stroke="#475569" strokeWidth={1.5} />
          </svg>
          <span className="text-[10px] text-slate-500">Expected</span>
        </div>
        <div className="flex items-center gap-1.5">
          <svg width={20} height={8}>
            <line x1={0} y1={4} x2={20} y2={4} stroke="#ffffff" strokeWidth={2} />
          </svg>
          <span className="text-[10px] text-slate-400">Actual</span>
        </div>
      </div>
    </div>
  );
};
