import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer, SectionTitle, LogoWatermark } from '../shared/components';
import { COLORS } from '../shared/constants';

/**
 * Scene 7: Value Assurance — Three-trajectory tracking
 *
 * Visual sequence:
 * 0-3s:   Title: "Did It Work?"
 * 3-8s:   Inaction line draws (red, dashed — declining)
 * 8-13s:  Expected line draws (blue, dashed — recovering)
 * 13-20s: Actual line draws (emerald, solid — growing month by month)
 * 20-25s: Verdict card appears: "On Track — actual exceeding expected"
 */
export const TrackingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Chart dimensions
  const chartX = 120;
  const chartY = 200;
  const chartW = 1680;
  const chartH = 500;

  // Data points (normalized 0-1 on Y axis)
  const months = ['M0', 'M1', 'M2', 'M3', 'M4', 'M5', 'M6'];
  const inaction =  [0.5, 0.45, 0.38, 0.32, 0.25, 0.18, 0.12]; // declining
  const expected =  [0.5, 0.55, 0.62, 0.68, 0.75, 0.80, 0.85]; // recovering
  const actual =    [0.5, 0.58, 0.65, 0.72, 0.78];              // growing (partial)

  const toSvgX = (i: number) => chartX + (i / (months.length - 1)) * chartW;
  const toSvgY = (v: number) => chartY + chartH - v * chartH;

  const toPath = (data: number[]) =>
    data.map((v, i) => `${i === 0 ? 'M' : 'L'} ${toSvgX(i)} ${toSvgY(v)}`).join(' ');

  // Line draw progress
  const inactionProgress = interpolate(frame, [fps * 3, fps * 8], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const expectedProgress = interpolate(frame, [fps * 8, fps * 13], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const actualProgress = interpolate(frame, [fps * 13, fps * 20], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Verdict
  const verdictOpacity = interpolate(frame, [fps * 20, fps * 21], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer className="p-16 relative">
      <SectionTitle subtitle="Three trajectories tell the whole story. What would have happened. What we predicted. What actually happened.">
        Did It Work?
      </SectionTitle>

      {/* Chart */}
      <svg width="1920" height="700" className="mt-4">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((v) => (
          <line
            key={v}
            x1={chartX} y1={toSvgY(v)}
            x2={chartX + chartW} y2={toSvgY(v)}
            stroke={COLORS.border} strokeWidth={1} strokeDasharray="4,8"
          />
        ))}

        {/* X axis labels */}
        {months.map((m, i) => (
          <text
            key={m}
            x={toSvgX(i)} y={chartY + chartH + 30}
            textAnchor="middle" fill={COLORS.muted}
            fontSize={18} fontFamily="Satoshi, system-ui"
          >
            {m}
          </text>
        ))}

        {/* Y axis labels */}
        <text x={chartX - 20} y={toSvgY(0.5)} textAnchor="end" fill={COLORS.muted} fontSize={16} fontFamily="Satoshi, system-ui">
          Baseline
        </text>
        <text x={chartX - 20} y={toSvgY(0.85)} textAnchor="end" fill={COLORS.muted} fontSize={16} fontFamily="Satoshi, system-ui">
          Target
        </text>

        {/* Inaction line (red, dashed) */}
        <path
          d={toPath(inaction)}
          fill="none" stroke={COLORS.red} strokeWidth={2.5}
          strokeDasharray="6,4"
          strokeDashoffset={0}
          pathLength={1}
          style={{ strokeDasharray: `${inactionProgress} ${1 - inactionProgress}` }}
        />

        {/* Expected line (blue, dashed) */}
        <path
          d={toPath(expected)}
          fill="none" stroke={COLORS.blue} strokeWidth={2.5}
          strokeDasharray="6,4"
          pathLength={1}
          style={{ strokeDasharray: `${expectedProgress} ${1 - expectedProgress}` }}
        />

        {/* Actual line (emerald, solid) */}
        <path
          d={toPath(actual)}
          fill="none" stroke={COLORS.emerald} strokeWidth={3}
          pathLength={1}
          style={{ strokeDasharray: `${actualProgress} ${1 - actualProgress}` }}
        />

        {/* Actual dots */}
        {actual.map((v, i) => {
          const dotOpacity = interpolate(
            frame,
            [fps * (13 + i * 1.5), fps * (13.5 + i * 1.5)],
            [0, 1],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          );
          return (
            <circle
              key={i}
              cx={toSvgX(i)} cy={toSvgY(v)} r={6}
              fill={COLORS.emerald} opacity={dotOpacity}
            />
          );
        })}

        {/* Measurement window line */}
        <line
          x1={toSvgX(6)} y1={chartY}
          x2={toSvgX(6)} y2={chartY + chartH}
          stroke={COLORS.border} strokeWidth={1} strokeDasharray="4,4"
        />
        <text
          x={toSvgX(6)} y={chartY - 10}
          textAnchor="middle" fill={COLORS.muted}
          fontSize={16} fontFamily="Satoshi, system-ui"
        >
          Measurement Window
        </text>
      </svg>

      {/* Legend */}
      <div className="flex gap-8 mt-2 ml-32">
        {[
          { color: COLORS.red, label: 'Inaction (what would happen)', dashed: true },
          { color: COLORS.blue, label: 'Expected (what we predicted)', dashed: true },
          { color: COLORS.emerald, label: 'Actual (what really happened)', dashed: false },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <div className="w-6 h-0.5" style={{
              backgroundColor: item.color,
              borderTop: item.dashed ? `2px dashed ${item.color}` : `2px solid ${item.color}`,
            }} />
            <span className="text-base" style={{ color: COLORS.muted }}>{item.label}</span>
          </div>
        ))}
      </div>

      {/* Verdict */}
      <div
        className="absolute bottom-16 right-16 rounded-xl border p-6 w-80"
        style={{
          opacity: verdictOpacity,
          backgroundColor: COLORS.card,
          borderColor: COLORS.emerald,
        }}
      >
        <div className="flex items-center gap-2 mb-2">
          <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.emerald }} />
          <span className="font-bold" style={{ color: COLORS.emerald }}>On Track</span>
        </div>
        <p className="text-base" style={{ color: COLORS.textSecondary }}>
          Actual margin recovery is exceeding expected trajectory. Month 4 actual: +2.8pp vs +2.5pp expected.
        </p>
        <p className="text-sm mt-2" style={{ color: COLORS.muted }}>
          Attribution: 72% solution impact (DiD)
        </p>
      </div>

      <LogoWatermark />
    </SceneContainer>
  );
};
