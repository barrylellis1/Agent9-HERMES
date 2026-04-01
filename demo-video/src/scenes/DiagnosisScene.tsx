import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer, SectionTitle, AnimatedCard, LogoWatermark } from '../shared/components';
import { COLORS } from '../shared/constants';

/**
 * Scene 4: Deep Analysis — IS/IS NOT dimensional breakdown
 *
 * Visual sequence:
 * 0-3s:   Title: "Structured Diagnosis"
 * 3-10s:  IS/IS NOT table materializes row by row
 * 10-18s: SCQA framework card appears
 * 18-22s: Benchmark segments highlighted (control group vs replication)
 * 22-25s: "But first — let's interrogate this." transition
 */
export const DiagnosisScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const isIsNotRows = [
    { dimension: 'Region', is: 'Southeast, Midwest', isNot: 'Northeast, West', insight: 'Concentrated in 2 of 4 regions' },
    { dimension: 'Product', is: 'Premium Synthetics', isNot: 'Standard, Economy', insight: 'Premium line only' },
    { dimension: 'Customer', is: 'Industrial accounts', isNot: 'Retail, Fleet', insight: 'B2B segment specific' },
    { dimension: 'Time', is: 'Last 90 days', isNot: 'Prior period stable', insight: 'Recent deterioration' },
  ];

  // SCQA card at 10s
  const scqaOpacity = interpolate(frame, [fps * 10, fps * 11], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer className="p-16 relative">
      <SectionTitle subtitle="Kepner-Tregoe IS/IS NOT analysis isolates where the problem lives — and where it doesn't.">
        Structured Diagnosis
      </SectionTitle>

      {/* IS/IS NOT Table */}
      <div className="mt-10 max-w-5xl">
        <div className="grid grid-cols-4 gap-px rounded-lg overflow-hidden" style={{ backgroundColor: COLORS.border }}>
          {/* Header */}
          {['Dimension', 'IS (Affected)', 'IS NOT (Unaffected)', 'Insight'].map((h) => (
            <div
              key={h}
              className="px-4 py-3 text-lg font-semibold"
              style={{ backgroundColor: COLORS.surface, color: COLORS.accentLight }}
            >
              {h}
            </div>
          ))}
          {/* Rows */}
          {isIsNotRows.map((row, i) => {
            const rowStart = fps * (3.5 + i * 1.2);
            const rowOpacity = interpolate(frame, [rowStart, rowStart + fps * 0.4], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            return (
              <React.Fragment key={row.dimension}>
                {[row.dimension, row.is, row.isNot, row.insight].map((cell, j) => (
                  <div
                    key={j}
                    className="px-4 py-3 text-base"
                    style={{
                      opacity: rowOpacity,
                      backgroundColor: COLORS.card,
                      color: j === 1 ? COLORS.red : j === 2 ? COLORS.emerald : COLORS.text,
                    }}
                  >
                    {cell}
                  </div>
                ))}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* SCQA Framework */}
      <div className="mt-8 max-w-3xl" style={{ opacity: scqaOpacity }}>
        <AnimatedCard delay={fps * 10}>
          <h3 className="text-2xl font-bold mb-3" style={{ color: COLORS.accentLight }}>
            Diagnostic Summary (SCQA)
          </h3>
          <div className="space-y-2 text-base">
            <p><span className="font-semibold" style={{ color: COLORS.amber }}>Situation:</span>{' '}
              <span style={{ color: COLORS.textSecondary }}>Premium Synthetics gross margin in SE/MW declined 4.7pp over 90 days</span>
            </p>
            <p><span className="font-semibold" style={{ color: COLORS.amber }}>Complication:</span>{' '}
              <span style={{ color: COLORS.textSecondary }}>Industrial accounts facing raw material cost pass-through; competitor pricing pressure in these regions</span>
            </p>
            <p><span className="font-semibold" style={{ color: COLORS.amber }}>Question:</span>{' '}
              <span style={{ color: COLORS.textSecondary }}>How can we restore Premium Synthetics margin to 30%+ in affected regions within 90 days?</span>
            </p>
          </div>
        </AnimatedCard>
      </div>

      {/* Transition */}
      {frame > fps * 22 && (
        <div
          className="absolute bottom-20 left-0 right-0 text-center"
          style={{
            opacity: interpolate(frame, [fps * 22, fps * 23.5], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            }),
          }}
        >
          <p className="text-3xl font-medium" style={{ color: COLORS.accentLight }}>
            But first — let's interrogate this →
          </p>
        </div>
      )}

      <LogoWatermark />
    </SceneContainer>
  );
};
