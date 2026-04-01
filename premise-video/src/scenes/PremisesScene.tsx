import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import {
  SceneContainer,
  SectionTitle,
  AnimatedCard,
  ConfidenceBadge,
  LogoWatermark,
} from '../shared/components';
import { COLORS } from '../shared/constants';

// ConfidenceBadge level type
type BadgeLevel = 'strong' | 'improved' | 'conditional' | 'deferred' | 'addressed' | 'positive';

interface PremiseCard {
  id: string;
  title: string;
  febLevel: BadgeLevel;
  febLabel: string;
  marLevel: BadgeLevel;
  marLabel: string;
  verdict: string;
  borderColor: string;
  boxShadow?: string;
}

interface NewPremiseCard {
  id: string;
  title: string;
  level: BadgeLevel;
  label?: string;
  verdict: string;
  borderColor: string;
  boxShadow?: string;
}

const ORIGINAL_PREMISES: PremiseCard[] = [
  {
    id: 'P1',
    title: 'No Marketplace Exists',
    febLevel: 'deferred',
    febLabel: 'Eroding',
    marLevel: 'conditional',
    marLabel: 'Repositioned',
    verdict: 'Addressed — no longer the pitch',
    borderColor: COLORS.amber,
  },
  {
    id: 'P2',
    title: 'Firms Slow to Adopt AI',
    febLevel: 'conditional',
    febLabel: 'Half True',
    marLevel: 'conditional',
    marLabel: 'Unchanged',
    verdict: 'Not a factor for revised ICP',
    borderColor: COLORS.amber,
  },
  {
    id: 'P3',
    title: 'Mid-Market Will Buy',
    febLevel: 'conditional',
    febLabel: 'Conditional',
    marLevel: 'improved',
    marLabel: 'Improved',
    verdict: 'Deployed product + 30-year career credibility',
    borderColor: COLORS.emerald,
  },
  {
    id: 'P4',
    title: 'Debate = Durable Moat',
    febLevel: 'conditional',
    febLabel: 'Closing',
    marLevel: 'conditional',
    marLabel: 'Deeper',
    verdict: 'Registry + VA + MA make combination harder',
    borderColor: COLORS.amber,
  },
  {
    id: 'P5',
    title: 'Partners Encode IP',
    febLevel: 'deferred',
    febLabel: 'Unlikely',
    marLevel: 'deferred',
    marLabel: 'Deferred',
    verdict: 'Correctly deferred — Tier 0 first',
    borderColor: COLORS.red,
  },
  {
    id: 'P6',
    title: '$100K+ ACV Pre-Rev',
    febLevel: 'deferred',
    febLabel: 'Unrealistic',
    marLevel: 'addressed',
    marLabel: 'Addressed',
    verdict: '$15K-$25K pilots accepted',
    borderColor: COLORS.emerald,
  },
  {
    id: 'P7',
    title: 'Bootstrapped $2M ARR',
    febLevel: 'conditional',
    febLabel: 'Narrow',
    marLevel: 'conditional',
    marLabel: 'Revised',
    verdict: '$600K-$1.4M base under incremental pricing',
    borderColor: COLORS.amber,
  },
];

const NEW_PREMISES: NewPremiseCard[] = [
  {
    id: 'P8',
    title: 'Never-Engaged ICP',
    level: 'strong',
    verdict: 'No incumbent to displace; they never hired MBB',
    borderColor: COLORS.emerald,
    boxShadow: `0 0 16px ${COLORS.emerald}30`,
  },
  {
    id: 'P9',
    title: 'VA Tracking is Defensible',
    level: 'strong',
    verdict: 'No competitor offers three-trajectory DiD tracking',
    borderColor: COLORS.emerald,
    boxShadow: `0 0 16px ${COLORS.emerald}30`,
  },
  {
    id: 'P10',
    title: '5-Day Onboarding = Moat',
    level: 'strong',
    verdict: 'Template library compounds; switching costs from Day 1',
    borderColor: COLORS.emerald,
    boxShadow: `0 0 16px ${COLORS.emerald}30`,
  },
  {
    id: 'P11',
    title: 'Usage-Based Pricing',
    level: 'conditional',
    label: 'Plausible',
    verdict: 'Needs demo feedback validation',
    borderColor: COLORS.amber,
  },
  {
    id: 'P12',
    title: 'Outcome-Based Component',
    level: 'conditional',
    label: 'Plausible',
    verdict: 'VA trajectory = invoice justification',
    borderColor: COLORS.amber,
  },
];

export const PremisesScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Beat A: 0-18s
  const titleDelay = 0;
  const premisesStart = fps * 3;
  const premiseStagger = fps * 1.8;

  // Beat B: 18-30s
  const bannerStart = fps * 18;
  const bannerScaleX = interpolate(frame, [bannerStart, bannerStart + fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const bannerOpacity = interpolate(frame, [bannerStart, bannerStart + fps * 0.3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const newPremisesStart = fps * 19;
  const newPremiseStagger = fps * 1.8;

  return (
    <SceneContainer>
      <div className="w-full h-full flex flex-col px-16 py-12 relative overflow-hidden">

        {/* Beat A — show until frame < fps*18 so it doesn't overlap beat B */}
        {frame < fps * 18 + fps * 0.5 && (
          <>
            {/* Section title */}
            <SectionTitle
              subtitle="Seven assumptions stress-tested against six weeks of execution."
              delay={titleDelay}
            >
              Core Premises — Reassessed
            </SectionTitle>

            {/* 7-card grid: 4 top row, 3 bottom row */}
            <div className="mt-8 flex flex-col gap-4 flex-1">
              {/* Top row — 4 cards */}
              <div className="grid grid-cols-4 gap-4">
                {ORIGINAL_PREMISES.slice(0, 4).map((p, i) => {
                  const delay = premisesStart + i * premiseStagger;
                  return (
                    <AnimatedCard
                      key={p.id}
                      delay={delay}
                      borderColor={p.borderColor}
                    >
                      <div className="flex flex-col gap-2">
                        <span
                          className="text-base font-bold"
                          style={{ color: COLORS.accentLight }}
                        >
                          {p.id}
                        </span>
                        <span
                          className="text-lg font-semibold leading-tight"
                          style={{ color: COLORS.text }}
                        >
                          {p.title}
                        </span>
                        <div className="flex flex-wrap gap-2 mt-1">
                          <div className="flex flex-col items-start gap-1">
                            <span className="text-xs uppercase tracking-wide" style={{ color: COLORS.muted }}>
                              Feb
                            </span>
                            <ConfidenceBadge level={p.febLevel} label={p.febLabel} />
                          </div>
                          <div className="flex flex-col items-start gap-1">
                            <span className="text-xs uppercase tracking-wide" style={{ color: COLORS.muted }}>
                              Mar
                            </span>
                            <ConfidenceBadge level={p.marLevel} label={p.marLabel} />
                          </div>
                        </div>
                        <p className="text-sm mt-1" style={{ color: COLORS.muted }}>
                          {p.verdict}
                        </p>
                      </div>
                    </AnimatedCard>
                  );
                })}
              </div>

              {/* Bottom row — 3 cards */}
              <div className="grid grid-cols-3 gap-4">
                {ORIGINAL_PREMISES.slice(4).map((p, i) => {
                  const delay = premisesStart + (4 + i) * premiseStagger;
                  return (
                    <AnimatedCard
                      key={p.id}
                      delay={delay}
                      borderColor={p.borderColor}
                    >
                      <div className="flex flex-col gap-2">
                        <span
                          className="text-base font-bold"
                          style={{ color: COLORS.accentLight }}
                        >
                          {p.id}
                        </span>
                        <span
                          className="text-lg font-semibold leading-tight"
                          style={{ color: COLORS.text }}
                        >
                          {p.title}
                        </span>
                        <div className="flex flex-wrap gap-2 mt-1">
                          <div className="flex flex-col items-start gap-1">
                            <span className="text-xs uppercase tracking-wide" style={{ color: COLORS.muted }}>
                              Feb
                            </span>
                            <ConfidenceBadge level={p.febLevel} label={p.febLabel} />
                          </div>
                          <div className="flex flex-col items-start gap-1">
                            <span className="text-xs uppercase tracking-wide" style={{ color: COLORS.muted }}>
                              Mar
                            </span>
                            <ConfidenceBadge level={p.marLevel} label={p.marLabel} />
                          </div>
                        </div>
                        <p className="text-sm mt-1" style={{ color: COLORS.muted }}>
                          {p.verdict}
                        </p>
                      </div>
                    </AnimatedCard>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {/* Beat B — NEW banner + 5 new cards */}
        {frame >= bannerStart && (
          <div className="absolute inset-0 flex flex-col px-16 py-12">
            {/* "NEW" sweep banner */}
            <div
              className="w-full rounded-xl flex items-center justify-center py-4 mb-8"
              style={{
                opacity: bannerOpacity,
                backgroundColor: COLORS.accent,
                transformOrigin: 'left center',
                transform: `scaleX(${bannerScaleX})`,
              }}
            >
              <span className="text-2xl font-bold text-white tracking-wide">
                New Premises — March 2026
              </span>
            </div>

            {/* 5 new premise cards in a horizontal row */}
            <div className="grid grid-cols-5 gap-4 flex-1">
              {NEW_PREMISES.map((p, i) => {
                const delay = newPremisesStart + i * newPremiseStagger;
                return (
                  // Outer div carries the box shadow; AnimatedCard handles opacity/scale
                  <div
                    key={p.id}
                    style={p.boxShadow ? { boxShadow: p.boxShadow } : undefined}
                    className="rounded-xl"
                  >
                    <AnimatedCard
                      delay={delay}
                      borderColor={p.borderColor}
                      className="h-full"
                    >
                      <div className="flex flex-col gap-2 h-full">
                        <span
                          className="text-base font-bold"
                          style={{ color: COLORS.accentLight }}
                        >
                          {p.id}
                        </span>
                        <span
                          className="text-lg font-semibold leading-tight"
                          style={{ color: COLORS.text }}
                        >
                          {p.title}
                        </span>
                        <div className="mt-1">
                          <ConfidenceBadge level={p.level} label={p.label} />
                        </div>
                        <p className="text-sm mt-2" style={{ color: COLORS.muted }}>
                          {p.verdict}
                        </p>
                      </div>
                    </AnimatedCard>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <LogoWatermark />
      </div>
    </SceneContainer>
  );
};
