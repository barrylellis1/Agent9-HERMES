import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer, LogoWatermark } from '../shared/components';
import { COLORS } from '../shared/constants';

/**
 * Scene 2: The Problem — Three buyer-felt pain points
 *
 * Visual sequence:
 * 0-3s:   "Sound familiar?" headline fades in
 * 3-8s:   Problem 1 card: "Your BI tools show what happened. Not what to do."
 * 8-13s:  Problem 2 card: "Every decision is a fire drill of spreadsheets and meetings."
 * 13-18s: Problem 3 card: "You never know if the decision actually worked."
 * 18-20s: Fade to next scene
 */
export const TheProblemScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const problems = [
    {
      number: '01',
      headline: 'Your BI tools show what happened.',
      subtext: 'Not what to do about it.',
      detail: 'Dashboards surface symptoms. You still need analysts, meetings, and weeks to find root causes.',
    },
    {
      number: '02',
      headline: 'Every decision is a fire drill.',
      subtext: 'Spreadsheets, slide decks, and war rooms.',
      detail: 'By the time you align on a recommendation, the window for action has narrowed.',
    },
    {
      number: '03',
      headline: 'You never know if it worked.',
      subtext: 'Decisions vanish into the operational void.',
      detail: 'No one tracks whether the approved solution actually moved the KPI. Accountability ends at approval.',
    },
  ];

  return (
    <SceneContainer className="items-center justify-center relative">
      {/* Headline */}
      <p
        className="text-3xl font-medium mb-16 tracking-wide"
        style={{
          color: COLORS.muted,
          opacity: interpolate(frame, [0, fps * 0.5], [0, 1], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
          }),
        }}
      >
        Sound familiar?
      </p>

      {/* Three problem cards */}
      <div className="flex gap-8 px-20">
        {problems.map((p, i) => {
          const start = fps * (3 + i * 5);
          const opacity = interpolate(frame, [start, start + fps * 0.6], [0, 1], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
          });
          const y = interpolate(frame, [start, start + fps * 0.6], [30, 0], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
          });

          return (
            <div
              key={p.number}
              className="flex-1 rounded-xl border p-8"
              style={{
                opacity,
                transform: `translateY(${y}px)`,
                backgroundColor: COLORS.card,
                borderColor: COLORS.border,
              }}
            >
              <span
                className="text-6xl font-bold"
                style={{ color: COLORS.accent, opacity: 0.3 }}
              >
                {p.number}
              </span>
              <h3 className="text-3xl font-bold mt-4" style={{ color: COLORS.text }}>
                {p.headline}
              </h3>
              <p className="text-2xl font-medium mt-1" style={{ color: COLORS.accentLight }}>
                {p.subtext}
              </p>
              <p className="text-lg mt-4 leading-relaxed" style={{ color: COLORS.muted }}>
                {p.detail}
              </p>
            </div>
          );
        })}
      </div>

      <LogoWatermark />
    </SceneContainer>
  );
};
