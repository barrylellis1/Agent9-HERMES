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
    area: 'Product',
    before: 'Spots problems and recommends fixes — live in production',
    after: 'Now also tracks whether approved fixes actually worked — full loop closed',
  },
  {
    area: 'Client Data',
    before: 'One demo dataset (bicycle retailer)',
    after: 'Second industry added (industrial lubricants) — shows it works across domains',
  },
  {
    area: 'Briefings',
    before: 'Results visible in the app only',
    after: 'Automated email summaries delivered to executives on demand',
  },
  {
    area: 'Website',
    before: 'decision-studios.com live, brand + 4 pages',
    after: 'Same — no new pages; focus was on product, not marketing',
  },
  {
    area: 'Pricing',
    before: '$15K–$25K pilot projects being evaluated',
    after: 'Unchanged — waiting for first demo to validate',
  },
  {
    area: 'Target Customer',
    before: 'Mid-size companies ($50M–$500M) with no big consulting firm on retainer',
    after: 'Unchanged — still the right profile',
  },
  {
    area: 'Biggest Risk',
    before: 'Can we build a product that actually works?',
    after: 'Can we get two paying pilots? Product risk is resolved.',
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
          subtitle="One month of focused building. Here is what moved."
          delay={titleDelay}
        >
          March to April — What Changed
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
                March 2026
              </span>
            </div>
            <div className="w-[44%] shrink-0 pl-4">
              <span
                className="text-base font-semibold uppercase tracking-wider"
                style={{ color: COLORS.muted }}
              >
                April 2026
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
              The product works end-to-end. The next question is: can we close the first two clients?
            </p>
          </div>
        </div>

        <LogoWatermark />
      </div>
    </SceneContainer>
  );
};
