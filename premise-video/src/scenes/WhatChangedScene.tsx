import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import {
  SceneContainer,
  SectionTitle,
  AnimatedCard,
  ComparisonRow,
  LogoWatermark,
} from '../shared/components';
import { COLORS } from '../shared/constants';

const ROWS: { area: string; before: string; after: string }[] = [
  {
    area: 'Platform',
    before: 'SA→DA→SF pipeline',
    after: 'Full SA→DA→MA→SF→VA pipeline, production deployed',
  },
  {
    area: 'Positioning',
    before: 'Agentic consulting marketplace',
    after: 'AI Decision Intelligence — domain-agnostic',
  },
  {
    area: 'Corporate',
    before: 'No public presence',
    after: 'decision-studios.com + brand identity + 4 pages',
  },
  {
    area: 'Pricing',
    before: 'Theoretical $25K-$300K',
    after: '$15K-$25K pilots + incremental model under evaluation',
  },
  {
    area: 'ICP',
    before: 'Mid-market executives',
    after: 'Never-engaged mid-market ($50M-$500M)',
  },
  {
    area: 'Partners',
    before: 'BCG outreach planned',
    after: 'Tier 0 fractional CFOs now; Tier 1+ at 5+ customers',
  },
  {
    area: 'Primary Risk',
    before: 'Can we build this?',
    after: 'Commercial: can we close first 2 pilots?',
  },
];

export const WhatChangedScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Beat 1 (0-3s): SectionTitle (uses its own internal animation)
  const titleDelay = 0;

  // Beat 2 (3-20s): 7 rows with ~2.2s stagger
  const rowsStart = fps * 3;
  const rowStagger = fps * 2.2;

  // Beat 3 (20-24s): Bottom card
  const cardStart = fps * 20;
  const cardOpacity = interpolate(frame, [cardStart, cardStart + fps * 0.6], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cardY = interpolate(frame, [cardStart, cardStart + fps * 0.6], [16, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer>
      <div className="w-full h-full flex flex-col px-20 py-16 relative">

        {/* Section title */}
        <SectionTitle
          subtitle="What was theoretical in February is now deployed."
          delay={titleDelay}
        >
          Six Weeks of Execution
        </SectionTitle>

        {/* Comparison table */}
        <div className="mt-8 flex-1">
          {/* Static header row */}
          <div className="flex items-start pb-2" style={{ borderBottom: `1px solid ${COLORS.border}` }}>
            <div className="w-[18%] shrink-0">
              <span
                className="text-base font-semibold uppercase tracking-wider"
                style={{ color: COLORS.muted }}
              >
                Area
              </span>
            </div>
            <div className="w-[38%] shrink-0 pr-6">
              <span
                className="text-base font-semibold uppercase tracking-wider"
                style={{ color: COLORS.muted }}
              >
                February 2026
              </span>
            </div>
            <div className="w-[44%] shrink-0 pl-4">
              <span
                className="text-base font-semibold uppercase tracking-wider"
                style={{ color: COLORS.muted }}
              >
                March 2026
              </span>
            </div>
          </div>

          {/* Animated data rows */}
          {ROWS.map((row, i) => (
            <ComparisonRow
              key={row.area}
              area={row.area}
              before={row.before}
              after={row.after}
              delay={rowsStart + i * rowStagger}
            />
          ))}
        </div>

        {/* Bottom summary card */}
        <div
          style={{
            opacity: cardOpacity,
            transform: `translateY(${cardY}px)`,
            marginTop: '20px',
          }}
        >
          <div
            className="rounded-xl border p-5 text-center"
            style={{
              backgroundColor: COLORS.card,
              borderColor: COLORS.emerald,
            }}
          >
            <p className="text-2xl font-bold" style={{ color: COLORS.text }}>
              The technical risk is resolved. What remains is commercial execution.
            </p>
          </div>
        </div>

        <LogoWatermark />
      </div>
    </SceneContainer>
  );
};
