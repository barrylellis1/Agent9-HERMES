import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import {
  SceneContainer,
  SectionTitle,
  LogoWatermark,
} from '../shared/components';
import { COLORS } from '../shared/constants';

type MoatBar = {
  color: string;
  label: string;
  detail: string;
};

const MOAT_BARS: MoatBar[] = [
  {
    color: COLORS.accent,
    label: 'Registry-Driven Domain Intelligence',
    detail: 'KPIs, principals, processes, glossary',
  },
  {
    color: COLORS.blue,
    label: 'Structured Analytical Methodology',
    detail: 'KT IS/IS NOT, SCQA, MBB perspectives',
  },
  {
    color: COLORS.emerald,
    label: 'Post-Decision Accountability',
    detail: 'VA three-trajectory tracking, DiD attribution',
  },
  {
    color: COLORS.amber,
    label: 'Real-Time Market Context',
    detail: 'Perplexity + Claude synthesis in every briefing',
  },
  {
    color: COLORS.purple,
    label: 'Full Audit Trail',
    detail: 'Detection → Diagnosis → Recommendation → Proof',
  },
];

export const MoatScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Beat A: 0-3s — SectionTitle
  // Beat B: 3-8s — commoditizes text + strikethrough
  const commoditizeTextStart = fps * 3;
  const commoditizeTextOpacity = interpolate(
    frame,
    [commoditizeTextStart, commoditizeTextStart + fps * 0.4],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );
  const commoditizeTextY = interpolate(
    frame,
    [commoditizeTextStart, commoditizeTextStart + fps * 0.4],
    [16, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Strikethrough animates 1s after text appears
  const strikeStart = commoditizeTextStart + fps * 1;
  const strikeScaleX = interpolate(frame, [strikeStart, strikeStart + fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Beat C: 8-17s — moat bars, 1.5s stagger starting at fps*8
  const barsStart = fps * 8;
  const barStagger = fps * 1.5;

  // Bottom line: 17-20s
  const bottomStart = fps * 17;
  const bottomOpacity = interpolate(frame, [bottomStart, bottomStart + fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const bottomY = interpolate(frame, [bottomStart, bottomStart + fps * 0.5], [16, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer>
      <div className="w-full h-full flex flex-col px-16 py-14 relative">
        {/* Section title — 0-3s */}
        <SectionTitle subtitle="It was never orchestration.">
          The Real Differentiator
        </SectionTitle>

        {/* Commoditizes text + strikethrough — 3-8s */}
        <div
          className="mt-10 relative inline-block self-start"
          style={{
            opacity: commoditizeTextOpacity,
            transform: `translateY(${commoditizeTextY}px)`,
          }}
        >
          <p className="text-2xl" style={{ color: COLORS.muted }}>
            AWS Bedrock Agents gives you orchestration.
          </p>
          {/* Strikethrough line */}
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: 0,
              height: '2px',
              width: '100%',
              backgroundColor: COLORS.red,
              transformOrigin: 'left center',
              transform: `scaleX(${strikeScaleX})`,
            }}
          />
        </div>

        {/* Moat bars — 8-17s */}
        <div className="flex flex-col gap-4 mt-10">
          {MOAT_BARS.map((bar, i) => {
            const delay = barsStart + i * barStagger;
            const barScaleX = interpolate(frame - delay, [0, fps * 0.5], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            const labelOpacity = interpolate(
              frame - delay,
              [fps * 0.3, fps * 0.6],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );

            return (
              <div
                key={bar.label}
                className="h-14 rounded-lg flex items-center px-5 gap-3"
                style={{
                  backgroundColor: `${bar.color}30`,
                  borderLeft: `4px solid ${bar.color}`,
                  transformOrigin: 'left center',
                  transform: `scaleX(${barScaleX})`,
                  // Prevent content from warping during scale by counter-scaling
                  // We render content inside a counter-scaled wrapper
                }}
              >
                <div
                  style={{
                    opacity: labelOpacity,
                    // Counter the scaleX so text doesn't stretch
                    transform: `scaleX(${barScaleX > 0 ? 1 / barScaleX : 1})`,
                    transformOrigin: 'left center',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  <span className="text-xl font-bold" style={{ color: COLORS.text }}>
                    {bar.label}
                  </span>
                  <span className="text-base" style={{ color: COLORS.muted }}>
                    {bar.detail}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Bottom line — 17-20s */}
        <div
          className="mt-auto pb-4 text-center"
          style={{
            opacity: bottomOpacity,
            transform: `translateY(${bottomY}px)`,
          }}
        >
          <p className="text-2xl font-semibold" style={{ color: COLORS.accentLight }}>
            Each layer reinforces the next. The combination is architecturally integrated.
          </p>
        </div>

        <LogoWatermark />
      </div>
    </SceneContainer>
  );
};
