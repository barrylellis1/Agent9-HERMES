import React, { useState, useMemo, useCallback } from 'react';
import { LinePath } from '@visx/shape';
import { scaleLinear, scalePoint } from '@visx/scale';
import { curveMonotoneX } from '@visx/curve';
import { ParentSize } from '@visx/responsive';
import { localPoint } from '@visx/event';
import { motion } from 'framer-motion';
import { CAUSAL_SECONDARY_HUES, CAUSAL_PRIMARY_HUE } from '../../utils/causalColors';

/**
 * Indexed multi-line trend comparison — plots a primary KPI alongside its
 * causal-neighbour KPIs, each normalized to "% change from the first period
 * shown," so a decision-maker can visually spot co-movement/divergence
 * before choosing which causal driver to reframe around (Phase 20
 * prototype). Deliberately NOT a node-link/force-graph — see
 * docs/architecture/theory_layer_design.md §7 for why that form is
 * out of scope here (its own pre-mortem: "the new spider chart").
 *
 * Values are shown RAW (not sign-flipped for inverse-logic KPIs like COGS,
 * where "up" is bad) — the mechanism/complication text carries that
 * interpretation. A silently-transformed axis would mislead a reader who
 * trusts the chart without reading the caption.
 *
 * Colors: dataviz skill categorical slots 1–3 (blue/orange/aqua, dark-mode
 * steps), validated against this app's actual bg-slate-950 (#020617)
 * surface — see the validator run in this feature's design conversation.
 * Primary series uses ink-white, not a categorical hue, so "the KPI you're
 * framing" is never confused with "a candidate being compared to it."
 * Imported from utils/causalColors.ts (not redefined here) so this chart's
 * colors and FramingGateCard's compact list always agree — §14 decision 8.
 */

const SECONDARY_HUES = CAUSAL_SECONDARY_HUES;
const PRIMARY_HUE = CAUSAL_PRIMARY_HUE;
const MAX_SECONDARY_SERIES = 3; // dataviz skill: adjacent-pairlist categorical caps clean comparison at 3 for a multi-line form

export interface TrendSeries {
  kpiId: string;
  label: string;
  isPrimary?: boolean;
  /** One value per period, already indexed to "% change from periods[0]" (0 at the first period). */
  indexedValues: (number | null)[];
}

export interface CausalTrendChartProps {
  /** Period labels shared by every series, e.g. ["Dec", "Jan", ..., "Aug"]. */
  periods: string[];
  /** Primary series first (isPrimary=true), then up to MAX_SECONDARY_SERIES causal neighbours. */
  series: TrendSeries[];
  height?: number;
}

interface TooltipState {
  periodIndex: number;
  x: number;
}

function seriesColor(s: TrendSeries, secondaryIndex: number): string {
  if (s.isPrimary) return PRIMARY_HUE;
  return SECONDARY_HUES[secondaryIndex % SECONDARY_HUES.length];
}

function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  const sign = v > 0 ? '+' : '';
  return `${sign}${v.toFixed(1)}%`;
}

function ChartInner({ width, height, periods, series }: Omit<CausalTrendChartProps, 'height'> & { width: number; height: number }) {
  const [tooltip, setTooltip] = useState<TooltipState | null>(null);

  const margin = { top: 16, right: 46, bottom: 28, left: 44 };
  const innerWidth = Math.max(0, width - margin.left - margin.right);
  const innerHeight = Math.max(0, height - margin.top - margin.bottom);

  const xScale = useMemo(
    () => scalePoint<string>({ domain: periods, range: [0, innerWidth], padding: 0.05 }),
    [periods, innerWidth],
  );

  const yDomain = useMemo(() => {
    const all = series.flatMap(s => s.indexedValues.filter((v): v is number => v !== null && !Number.isNaN(v)));
    const lo = Math.min(0, ...all);
    const hi = Math.max(0, ...all);
    const pad = Math.max(1, (hi - lo) * 0.12);
    return [lo - pad, hi + pad] as [number, number];
  }, [series]);

  const yScale = useMemo(
    () => scaleLinear<number>({ domain: yDomain, range: [innerHeight, 0] }),
    [yDomain, innerHeight],
  );

  const secondaries = series.filter(s => !s.isPrimary);
  const primary = series.find(s => s.isPrimary) ?? null;
  const orderedForRender = primary ? [...secondaries, primary] : secondaries; // primary drawn last (on top)

  const handleMove = useCallback(
    (event: React.PointerEvent<SVGRectElement>) => {
      const point = localPoint(event);
      if (!point) return;
      const xInner = point.x - margin.left;
      // Snap to nearest period — the crosshair finds the X, not a raw pixel.
      const step = innerWidth / Math.max(1, periods.length - 1);
      const idx = Math.round(xInner / step);
      const clamped = Math.min(periods.length - 1, Math.max(0, idx));
      setTooltip({ periodIndex: clamped, x: xScale(periods[clamped]) ?? 0 });
    },
    [innerWidth, periods, xScale, margin.left],
  );

  const yTicks = yScale.ticks(5);
  // Sparse x ticks — every other period once there are more than ~6, so labels don't collide.
  const xTickEvery = periods.length > 6 ? 2 : 1;

  return (
    <svg width={width} height={height}>
      <g transform={`translate(${margin.left},${margin.top})`}>
        {/* Gridlines — solid hairline, recessive, never dashed */}
        {yTicks.map(t => (
          <line
            key={`grid-${t}`}
            x1={0}
            x2={innerWidth}
            y1={yScale(t)}
            y2={yScale(t)}
            stroke={t === 0 ? '#383835' : '#2c2c2a'}
            strokeWidth={1}
          />
        ))}

        {/* Y axis labels — muted ink, never the series color */}
        {yTicks.map(t => (
          <text key={`ytick-${t}`} x={-8} y={yScale(t)} dy="0.32em" textAnchor="end" fontSize={10} fill="#898781">
            {t > 0 ? `+${t}%` : `${t}%`}
          </text>
        ))}

        {/* X axis labels */}
        {periods.map((p, i) =>
          i % xTickEvery === 0 ? (
            <text key={`xtick-${p}`} x={xScale(p) ?? 0} y={innerHeight + 18} textAnchor="middle" fontSize={10} fill="#898781">
              {p}
            </text>
          ) : null,
        )}

        {/* Lines — 2px, round join/cap, secondaries first so primary renders on top.
            `defined` breaks the path across nulls rather than interpolating through
            a fabricated value — missing data must read as a gap, never as "no change." */}
        {orderedForRender.map(s => {
          const secondaryIdx = secondaries.indexOf(s);
          const color = seriesColor(s, secondaryIdx);
          const pathPoints = periods.map((p, i) => ({ x: xScale(p) ?? 0, v: s.indexedValues[i] }));
          const lastDefinedIdx = (() => {
            for (let i = s.indexedValues.length - 1; i >= 0; i--) {
              if (s.indexedValues[i] !== null && s.indexedValues[i] !== undefined) return i;
            }
            return -1;
          })();
          return (
            <motion.g key={s.kpiId}>
              <LinePath
                data={pathPoints}
                x={d => d.x}
                y={d => yScale(d.v ?? 0)}
                defined={d => d.v !== null && d.v !== undefined}
                curve={curveMonotoneX}
                stroke={color}
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {/* End marker + end-label — at the LAST DEFINED point, not necessarily the
                  last period (a series with a trailing gap should still show its last
                  real value, not silently vanish). Label is the value only — the legend
                  above already carries the series name (skill: "Lines -> value at the end"). */}
              {lastDefinedIdx >= 0 && (() => {
                const lastVal = s.indexedValues[lastDefinedIdx] as number;
                const cx = xScale(periods[lastDefinedIdx]) ?? 0;
                const cy = yScale(lastVal);
                return (
                  <>
                    <circle cx={cx} cy={cy} r={5} fill="#020617" />
                    <circle cx={cx} cy={cy} r={4} fill={color} />
                    <text x={cx + 9} y={cy} dy="0.32em" fontSize={11} fill={s.isPrimary ? '#ffffff' : '#c3c2b7'} fontWeight={s.isPrimary ? 600 : 400}>
                      {fmtPct(lastVal)}
                    </text>
                  </>
                );
              })()}
            </motion.g>
          );
        })}

        {/* Crosshair + hover hit target — one tooltip lists every series at that X */}
        <rect width={innerWidth} height={innerHeight} fill="transparent" onPointerMove={handleMove} onPointerLeave={() => setTooltip(null)} />
        {tooltip && (
          <>
            <line x1={tooltip.x} x2={tooltip.x} y1={0} y2={innerHeight} stroke="#c3c2b7" strokeWidth={1} strokeOpacity={0.5} />
            <foreignObject x={Math.min(tooltip.x + 10, innerWidth - 210)} y={4} width={210} height={30 + series.length * 22}>
              <div className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-xs shadow-lg pointer-events-none">
                <div className="text-slate-500 mb-1">{periods[tooltip.periodIndex]}</div>
                {series.map(s => {
                  const secondaryIdx = secondaries.indexOf(s);
                  const color = seriesColor(s, secondaryIdx);
                  const v = s.indexedValues[tooltip.periodIndex];
                  return (
                    <div key={s.kpiId} className="flex items-center gap-1.5 leading-tight py-0.5 whitespace-nowrap">
                      <span className="inline-block w-3 h-0.5 shrink-0" style={{ backgroundColor: color }} />
                      <span className="text-white font-medium shrink-0">{fmtPct(v)}</span>
                      <span className="text-slate-400 truncate">{s.label}</span>
                    </div>
                  );
                })}
              </div>
            </foreignObject>
          </>
        )}
      </g>
    </svg>
  );
}

export function CausalTrendChart({ periods, series, height = 220 }: CausalTrendChartProps) {
  const capped = useMemo(() => {
    const primary = series.filter(s => s.isPrimary);
    const secondaries = series.filter(s => !s.isPrimary).slice(0, MAX_SECONDARY_SERIES);
    return [...primary, ...secondaries];
  }, [series]);

  return (
    <div className="space-y-2">
      {/* Legend — always present for >=2 series, the dependable identity channel */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
        {capped.map(s => {
          const secondaries = capped.filter(x => !x.isPrimary);
          const color = seriesColor(s, secondaries.indexOf(s));
          return (
            <div key={s.kpiId} className="flex items-center gap-1.5">
              <span className="inline-block w-3 h-0.5" style={{ backgroundColor: color }} />
              <span className={s.isPrimary ? 'text-white font-medium' : 'text-slate-400'}>{s.label}</span>
            </div>
          );
        })}
      </div>
      <div style={{ height }}>
        <ParentSize>{({ width }) => (width > 0 ? <ChartInner width={width} height={height} periods={periods} series={capped} /> : null)}</ParentSize>
      </div>
    </div>
  );
}
