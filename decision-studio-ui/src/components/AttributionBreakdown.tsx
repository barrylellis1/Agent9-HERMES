import React from 'react';
import { Info } from 'lucide-react';

interface AttributionBreakdownProps {
  totalChange: number;
  attributableImpact: number;
  marketDrivenRecovery: number;
  seasonalComponent: number;
  controlGroupChange: number;
  expectedLower: number;
  expectedUpper: number;
  /** Control group description for the confidence note. Pass undefined when no control group. */
  controlGroupDescription?: string;
  /** e.g. "%" or "$M" — defaults to "%" */
  kpiUnit?: string;
}

// ─── Internal types ───────────────────────────────────────────────────────────

interface SegmentDef {
  key: string;
  label: string;
  value: number;
  barClass: string;
  valueClass: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatValue(value: number, unit: string): string {
  const sign = value >= 0 ? '+' : '';
  const formatted = Math.abs(value) < 10 ? value.toFixed(1) : value.toFixed(0);
  return `${sign}${formatted}${unit}`;
}

/**
 * Build bar segments. Only include segments whose absolute value > 0.
 * Returns an array ordered: attributable → market → seasonal → control.
 */
function buildSegments(props: AttributionBreakdownProps): SegmentDef[] {
  const all: SegmentDef[] = [
    {
      key: 'attributable',
      label: 'Attributable',
      value: props.attributableImpact,
      barClass: 'bg-emerald-500',
      valueClass: 'text-emerald-400',
    },
    {
      key: 'market',
      label: 'Market',
      value: props.marketDrivenRecovery,
      barClass: 'bg-blue-500',
      valueClass: 'text-blue-400',
    },
    {
      key: 'seasonal',
      label: 'Seasonal',
      value: props.seasonalComponent,
      barClass: 'bg-purple-500',
      valueClass: 'text-purple-400',
    },
    {
      key: 'control',
      label: 'Control adj.',
      value: props.controlGroupChange,
      barClass: 'bg-slate-500',
      valueClass: 'text-slate-400',
    },
  ];

  // Keep all segments visible even when 0 so users understand the breakdown
  return all;
}

// ─── Expected-range annotation ────────────────────────────────────────────────

interface RangeAnnotationProps {
  expectedLower: number;
  expectedUpper: number;
  totalChange: number;
  kpiUnit: string;
}

function RangeAnnotation({ expectedLower, expectedUpper, totalChange, kpiUnit }: RangeAnnotationProps) {
  // We render a simple bracket description rather than pixel-positioned overlays,
  // which keeps the component pure CSS / no external libs.
  const sign = (v: number) => (v >= 0 ? '+' : '');
  return (
    <div className="flex items-center gap-1.5 text-[10px] text-slate-500 mb-1">
      <span className="font-medium text-slate-400">Expected range:</span>
      <span>
        {sign(expectedLower)}
        {expectedLower.toFixed(1)}
        {kpiUnit} to {sign(expectedUpper)}
        {expectedUpper.toFixed(1)}
        {kpiUnit}
      </span>
      {totalChange >= expectedLower && totalChange <= expectedUpper ? (
        <span className="text-emerald-500 font-semibold">(within range)</span>
      ) : totalChange > expectedUpper ? (
        <span className="text-blue-400 font-semibold">(above range)</span>
      ) : (
        <span className="text-red-400 font-semibold">(below range)</span>
      )}
    </div>
  );
}

// ─── Stacked bar ─────────────────────────────────────────────────────────────

interface StackedBarProps {
  segments: SegmentDef[];
  totalAbsSum: number;
}

function StackedBar({ segments, totalAbsSum }: StackedBarProps) {
  if (totalAbsSum === 0) {
    return (
      <div className="h-6 w-full bg-slate-800 rounded-full flex items-center justify-center">
        <span className="text-[10px] text-slate-600">No change data</span>
      </div>
    );
  }

  return (
    <div className="h-6 w-full flex rounded-full overflow-hidden bg-slate-800 gap-[1px]">
      {segments.map((seg) => {
        const widthPct = totalAbsSum > 0 ? (Math.abs(seg.value) / totalAbsSum) * 100 : 0;
        if (widthPct === 0) return null;
        return (
          <div
            key={seg.key}
            title={`${seg.label}: ${seg.value >= 0 ? '+' : ''}${seg.value.toFixed(2)}`}
            className={`${seg.barClass} transition-all`}
            style={{ width: `${widthPct}%`, minWidth: widthPct > 0 ? '2px' : 0 }}
          />
        );
      })}
    </div>
  );
}

// ─── Legend row ───────────────────────────────────────────────────────────────

interface LegendProps {
  segments: SegmentDef[];
  kpiUnit: string;
}

function Legend({ segments, kpiUnit }: LegendProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
      {segments.map((seg) => (
        <div key={seg.key} className="flex flex-col gap-0.5">
          <div className="flex items-center gap-1.5">
            <div className={`w-2.5 h-2.5 rounded-sm flex-shrink-0 ${seg.barClass}`} />
            <span className="text-[10px] text-slate-500 uppercase tracking-wide">{seg.label}</span>
          </div>
          <span className={`text-sm font-semibold font-mono ${seg.valueClass}`}>
            {formatValue(seg.value, kpiUnit)}
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export const AttributionBreakdown: React.FC<AttributionBreakdownProps> = (props) => {
  const unit = props.kpiUnit ?? '%';
  const segments = buildSegments(props);

  // Sum of absolute values drives bar width proportions.
  const totalAbsSum = segments.reduce((acc, s) => acc + Math.abs(s.value), 0);

  const totalSign = props.totalChange >= 0 ? '+' : '';

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
          Attribution Breakdown
        </h4>
        <span
          className={`text-lg font-bold font-mono ${
            props.totalChange >= 0 ? 'text-emerald-400' : 'text-red-400'
          }`}
        >
          Total KPI change: {totalSign}
          {props.totalChange.toFixed(1)}
          {unit}
        </span>
      </div>

      {/* Expected range annotation */}
      <RangeAnnotation
        expectedLower={props.expectedLower}
        expectedUpper={props.expectedUpper}
        totalChange={props.totalChange}
        kpiUnit={unit}
      />

      {/* Stacked bar */}
      <StackedBar segments={segments} totalAbsSum={totalAbsSum} />

      {/* Legend */}
      <Legend segments={segments} kpiUnit={unit} />

      {/* Confidence / attribution note */}
      <div className="flex items-start gap-2 text-xs text-slate-500 pt-2 border-t border-slate-800">
        <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-slate-600" />
        {props.controlGroupDescription ? (
          <span>
            Attribution based on <span className="text-slate-400">{props.controlGroupDescription}</span> as
            control group (Difference-in-Differences method).
          </span>
        ) : (
          <span>
            No control group available &mdash; attribution is{' '}
            <span className="text-amber-500">directional only</span>. Interpret with caution.
          </span>
        )}
      </div>
    </div>
  );
};
