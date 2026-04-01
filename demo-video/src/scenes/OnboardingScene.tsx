import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer, SectionTitle, LogoWatermark } from '../shared/components';
import { COLORS } from '../shared/constants';

/**
 * Scene 8: Onboarding — 5-Day Fast Start
 *
 * Visual sequence:
 * 0-3s:   Title: "Live in 5 Days"
 * 3-15s:  Timeline — 5 steps appear sequentially along a horizontal line
 * 15-18s: "No integration project. No 6-month rollout." closing message
 */
export const OnboardingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const steps = [
    { day: 'Day 1', label: 'Connect Data', detail: 'Point us at your data warehouse. We handle the rest.' },
    { day: 'Day 2', label: 'Map KPIs', detail: 'AI suggests KPIs from your schema. You confirm.' },
    { day: 'Day 3', label: 'Set Thresholds', detail: 'Define what "normal" looks like for each metric.' },
    { day: 'Day 4', label: 'Assign Principals', detail: 'Map decision-makers to business processes.' },
    { day: 'Day 5', label: 'Go Live', detail: 'First automated assessment runs. Situations surface.' },
  ];

  // Closing message
  const closingOpacity = interpolate(frame, [fps * 15, fps * 16], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer className="p-16 relative">
      <SectionTitle subtitle="From data connection to first automated assessment in one business week.">
        Live in 5 Days
      </SectionTitle>

      {/* Timeline */}
      <div className="mt-16 relative px-8">
        {/* Connecting line */}
        <div
          className="absolute top-8 left-24 right-24 h-0.5"
          style={{
            backgroundColor: COLORS.border,
            opacity: interpolate(frame, [fps * 3, fps * 4], [0, 1], {
              extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
            }),
          }}
        />

        {/* Steps */}
        <div className="flex justify-between relative">
          {steps.map((step, i) => {
            const start = fps * (3.5 + i * 2.2);
            const opacity = interpolate(frame, [start, start + fps * 0.5], [0, 1], {
              extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
            });
            const y = interpolate(frame, [start, start + fps * 0.5], [20, 0], {
              extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
            });

            const isLast = i === steps.length - 1;

            return (
              <div
                key={step.day}
                className="flex flex-col items-center text-center w-48"
                style={{ opacity, transform: `translateY(${y}px)` }}
              >
                {/* Circle */}
                <div
                  className="w-16 h-16 rounded-full flex items-center justify-center text-lg font-bold text-white mb-4"
                  style={{
                    backgroundColor: isLast ? COLORS.emerald : COLORS.accent,
                    boxShadow: isLast ? `0 0 24px ${COLORS.emerald}40` : 'none',
                  }}
                >
                  {i + 1}
                </div>

                {/* Day label */}
                <span
                  className="text-sm font-semibold uppercase tracking-wider mb-1"
                  style={{ color: isLast ? COLORS.emerald : COLORS.accentLight }}
                >
                  {step.day}
                </span>

                {/* Step name */}
                <span className="text-xl font-bold" style={{ color: COLORS.text }}>
                  {step.label}
                </span>

                {/* Detail */}
                <p className="text-base mt-2 leading-relaxed" style={{ color: COLORS.muted }}>
                  {step.detail}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Closing message */}
      <div
        className="mt-20 text-center"
        style={{ opacity: closingOpacity }}
      >
        <p className="text-4xl font-bold" style={{ color: COLORS.text }}>
          No integration project. No 6-month rollout.
        </p>
        <p className="text-2xl mt-3" style={{ color: COLORS.muted }}>
          Your existing data. Our analysis engine. Results in a week.
        </p>
      </div>

      <LogoWatermark />
    </SceneContainer>
  );
};
