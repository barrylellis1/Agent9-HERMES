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

type TrendCard = {
  title: string;
  badgeLevel: 'strong' | 'improved' | 'conditional' | 'deferred' | 'addressed' | 'positive';
  badgeLabel: string;
  topBorderColor: string;
  description: string;
};

const TRENDS: TrendCard[] = [
  {
    title: 'Agent Infrastructure Explosion',
    badgeLevel: 'conditional',
    badgeLabel: 'Medium',
    topBorderColor: COLORS.amber,
    description: 'Orchestration commoditizes. Domain layer does not.',
  },
  {
    title: 'Consulting Firms Moving Faster',
    badgeLevel: 'strong',
    badgeLabel: 'Low for ICP',
    topBorderColor: COLORS.emerald,
    description: 'Building for $500M+ clients — not our market.',
  },
  {
    title: 'AI Finance Startup Wave',
    badgeLevel: 'conditional',
    badgeLabel: 'Medium',
    topBorderColor: COLORS.amber,
    description: 'Finance-only. Domain-agnostic is the gap.',
  },
  {
    title: 'Enterprise Buying Consolidation',
    badgeLevel: 'conditional',
    badgeLabel: 'Medium',
    topBorderColor: COLORS.amber,
    description: '$15K-$25K pilots bypass procurement.',
  },
  {
    title: 'LLM Cost Deflation',
    badgeLevel: 'positive',
    badgeLabel: 'Positive',
    topBorderColor: COLORS.emerald,
    description: '$1-$2 per full pipeline run. Margins strong.',
  },
];

export const MarketScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardsStart = fps * 3;
  const cardStagger = fps * 2.8;

  const calloutStart = fps * 20;
  const calloutOpacity = interpolate(frame, [calloutStart, calloutStart + fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const calloutY = interpolate(frame, [calloutStart, calloutStart + fps * 0.5], [16, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer>
      <div className="w-full h-full flex flex-col px-16 py-14 relative">
        {/* Section title — 0-3s */}
        <SectionTitle subtitle="Five forces reassessed after ICP and positioning shift.">
          Market Trends — Revised Risk
        </SectionTitle>

        {/* Five trend cards — 3-20s */}
        <div className="flex flex-row gap-4 mt-10 flex-1 items-start">
          {TRENDS.map((trend, i) => {
            const delay = cardsStart + i * cardStagger;
            return (
              <AnimatedCard
                key={trend.title}
                delay={delay}
                className="w-[340px] flex-shrink-0"
                borderColor={COLORS.border}
              >
                {/* Colored top border */}
                <div
                  style={{
                    height: '4px',
                    backgroundColor: trend.topBorderColor,
                    borderRadius: '2px',
                    marginBottom: '14px',
                    marginLeft: '-20px',
                    marginRight: '-20px',
                    marginTop: '-20px',
                    borderTopLeftRadius: '12px',
                    borderTopRightRadius: '12px',
                  }}
                />

                {/* Title + Badge row */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <p className="text-lg font-bold leading-snug" style={{ color: COLORS.text }}>
                    {trend.title}
                  </p>
                  <div className="shrink-0">
                    <ConfidenceBadge level={trend.badgeLevel} label={trend.badgeLabel} />
                  </div>
                </div>

                {/* Description */}
                <p className="text-base" style={{ color: COLORS.textSecondary }}>
                  {trend.description}
                </p>
              </AnimatedCard>
            );
          })}
        </div>

        {/* Callout — 20-22s */}
        <div
          className="mt-8 text-center"
          style={{
            opacity: calloutOpacity,
            transform: `translateY(${calloutY}px)`,
          }}
        >
          <p className="text-3xl font-bold" style={{ color: COLORS.text }}>
            The ICP revision made two of the five threats irrelevant.
          </p>
        </div>

        <LogoWatermark />
      </div>
    </SceneContainer>
  );
};
