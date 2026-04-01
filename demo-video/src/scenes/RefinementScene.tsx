import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer, SectionTitle, AnimatedCard, LogoWatermark } from '../shared/components';
import { COLORS } from '../shared/constants';

/**
 * Scene 5: Problem Refinement — HITL conversational interrogation with LLM
 *
 * Visual sequence:
 * 0-3s:   Title: "Interrogate the Analysis"
 * 3-7s:   Chat bubble from user: "Which industrial accounts are driving the decline?"
 * 7-11s:  System response: data table with top 3 accounts + margin delta
 * 11-14s: Second user question: "Is this correlated with the raw material price spike in Q3?"
 * 14-18s: System response: correlation chart snippet + "Yes — 87% correlation..."
 * 18-20s: Suggested follow-ups appear as chips → transition
 */
export const RefinementScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Chat messages appear sequentially
  const msg1Opacity = interpolate(frame, [fps * 3, fps * 3.5], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const msg1Y = interpolate(frame, [fps * 3, fps * 3.5], [20, 0], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Typewriter for first question
  const q1Text = 'Which industrial accounts are driving the decline?';
  const q1Chars = Math.min(
    Math.floor(Math.max(0, (frame - fps * 3.5)) * 1.8),
    q1Text.length
  );

  // Response 1
  const resp1Opacity = interpolate(frame, [fps * 7, fps * 7.5], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Second question
  const msg2Opacity = interpolate(frame, [fps * 11, fps * 11.5], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });
  const q2Text = 'Is this correlated with the raw material price spike in Q3?';
  const q2Chars = Math.min(
    Math.floor(Math.max(0, (frame - fps * 11.5)) * 1.8),
    q2Text.length
  );

  // Response 2
  const resp2Opacity = interpolate(frame, [fps * 14, fps * 14.5], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Suggested follow-ups
  const suggestionsOpacity = interpolate(frame, [fps * 18, fps * 18.5], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  const accounts = [
    { name: 'Meridian Manufacturing', region: 'SE', delta: '-6.2pp' },
    { name: 'Great Lakes Industrial', region: 'MW', delta: '-5.8pp' },
    { name: 'Southern Fabricators Inc.', region: 'SE', delta: '-4.1pp' },
  ];

  const suggestions = [
    'Show me competitor pricing in SE region',
    'What would happen if we held pricing?',
    'Break down by product SKU',
  ];

  return (
    <SceneContainer className="p-16 relative">
      <SectionTitle subtitle="Ask follow-up questions in natural language. The system queries live data to answer.">
        Interrogate the Analysis
      </SectionTitle>

      <div className="mt-8 max-w-4xl space-y-4">
        {/* User question 1 */}
        <div
          className="flex justify-end"
          style={{ opacity: msg1Opacity, transform: `translateY(${msg1Y}px)` }}
        >
          <div
            className="rounded-2xl rounded-br-sm px-5 py-3 max-w-lg"
            style={{ backgroundColor: COLORS.accent }}
          >
            <p className="text-lg font-medium text-white">
              {q1Text.substring(0, q1Chars)}
              {q1Chars < q1Text.length && (
                <span className="inline-block w-0.5 h-4 ml-0.5 align-middle" style={{ backgroundColor: 'white' }} />
              )}
            </p>
          </div>
        </div>

        {/* System response 1 — data table */}
        <div style={{ opacity: resp1Opacity }}>
          <AnimatedCard delay={fps * 7} className="ml-0 max-w-lg">
            <div className="flex items-center gap-2 mb-3">
              <div
                className="w-5 h-5 rounded-md flex items-center justify-center text-sm font-bold text-white"
                style={{ backgroundColor: COLORS.accent }}
              >
                DS
              </div>
              <span className="text-base font-semibold" style={{ color: COLORS.accentLight }}>
                Live Data Query
              </span>
              <span className="text-base" style={{ color: COLORS.muted }}>• 1.2s</span>
            </div>
            <table className="w-full text-base">
              <thead>
                <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                  {['Account', 'Region', 'Margin Δ'].map((h) => (
                    <th key={h} className="text-left py-1.5 font-semibold" style={{ color: COLORS.muted }}>
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {accounts.map((acct, i) => {
                  const rowDelay = fps * (7.5 + i * 0.3);
                  const rowOpacity = interpolate(frame, [rowDelay, rowDelay + fps * 0.2], [0, 1], {
                    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
                  });
                  return (
                    <tr key={acct.name} style={{ opacity: rowOpacity }}>
                      <td className="py-1.5" style={{ color: COLORS.text }}>{acct.name}</td>
                      <td className="py-1.5" style={{ color: COLORS.textSecondary }}>{acct.region}</td>
                      <td className="py-1.5 font-semibold" style={{ color: COLORS.red }}>{acct.delta}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="text-sm mt-2" style={{ color: COLORS.muted }}>
              Top 3 of 14 affected accounts • Sorted by margin impact
            </p>
          </AnimatedCard>
        </div>

        {/* User question 2 */}
        <div className="flex justify-end" style={{ opacity: msg2Opacity }}>
          <div
            className="rounded-2xl rounded-br-sm px-5 py-3 max-w-lg"
            style={{ backgroundColor: COLORS.accent }}
          >
            <p className="text-lg font-medium text-white">
              {q2Text.substring(0, q2Chars)}
              {q2Chars < q2Text.length && (
                <span className="inline-block w-0.5 h-4 ml-0.5 align-middle" style={{ backgroundColor: 'white' }} />
              )}
            </p>
          </div>
        </div>

        {/* System response 2 — correlation insight */}
        <div style={{ opacity: resp2Opacity }}>
          <AnimatedCard delay={fps * 14} className="ml-0 max-w-lg">
            <div className="flex items-center gap-2 mb-3">
              <div
                className="w-5 h-5 rounded-md flex items-center justify-center text-sm font-bold text-white"
                style={{ backgroundColor: COLORS.accent }}
              >
                DS
              </div>
              <span className="text-base font-semibold" style={{ color: COLORS.accentLight }}>
                Correlation Analysis
              </span>
              <span className="text-base" style={{ color: COLORS.muted }}>• 2.1s</span>
            </div>
            <div className="flex items-center gap-4">
              {/* Mini correlation indicator */}
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center text-lg font-bold"
                style={{ backgroundColor: `${COLORS.red}20`, color: COLORS.red }}
              >
                87%
              </div>
              <div className="flex-1">
                <p className="text-lg" style={{ color: COLORS.text }}>
                  <strong>Strong correlation confirmed.</strong>
                </p>
                <p className="text-base mt-1" style={{ color: COLORS.textSecondary }}>
                  Raw material index rose 12.3% in Q3. Pass-through lag of 45-60 days aligns with margin decline onset in SE/MW industrial accounts.
                </p>
              </div>
            </div>
          </AnimatedCard>
        </div>

        {/* Suggested follow-ups */}
        <div className="flex gap-2 mt-2" style={{ opacity: suggestionsOpacity }}>
          {suggestions.map((s, i) => {
            const chipDelay = fps * (18.2 + i * 0.2);
            const chipOpacity = interpolate(frame, [chipDelay, chipDelay + fps * 0.2], [0, 1], {
              extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
            });
            return (
              <div
                key={s}
                className="rounded-full border px-4 py-2 text-sm"
                style={{
                  opacity: chipOpacity,
                  borderColor: COLORS.border,
                  color: COLORS.accentLight,
                  backgroundColor: COLORS.surface,
                }}
              >
                {s}
              </div>
            );
          })}
        </div>
      </div>

      <LogoWatermark />
    </SceneContainer>
  );
};
