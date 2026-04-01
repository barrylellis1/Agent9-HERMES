import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import {
  SceneContainer,
  SectionTitle,
  AnimatedCard,
  LogoWatermark,
} from '../shared/components';
import { COLORS } from '../shared/constants';

// Beat A: billing components
type PricingComponent = {
  name: string;
  price: string;
  description: string;
  borderColor: string;
  badge?: { text: string; color: string };
};

const PRICING_COMPONENTS: PricingComponent[] = [
  {
    name: 'Onboarding',
    price: '$5K-$15K',
    description: 'per data product (one-time)',
    borderColor: COLORS.accent,
  },
  {
    name: 'Base Platform',
    price: '$3K/month',
    description: 'Dashboard, registries, 50 NL queries',
    borderColor: COLORS.accent,
  },
  {
    name: 'KPI Monitoring',
    price: '$300/KPI/mo',
    description: 'First 10 included in base',
    borderColor: COLORS.emerald,
    badge: { text: '37-53% of revenue', color: COLORS.emerald },
  },
  {
    name: 'Assessment Credits',
    price: '$750 each',
    description: '4/month included; additional on-demand',
    borderColor: COLORS.blue,
  },
  {
    name: 'Solution Tracking',
    price: '$500/quarter',
    description: 'Per VA-tracked solution',
    borderColor: COLORS.purple,
  },
];

// Beat B: revenue tiers
type RevenueTier = {
  name: string;
  revenue: string;
  revenueColor: string;
  examples: string;
  detail: string;
  borderColor: string;
  opacity?: number;
};

const REVENUE_TIERS: RevenueTier[] = [
  {
    name: 'Mid-Market / Single Domain',
    revenue: '$100K-$150K/yr',
    revenueColor: COLORS.emerald,
    examples: 'Valvoline, Hess, Pilgrim\'s Pride',
    detail: '20-30 KPIs • 6-8 assessments/mo',
    borderColor: COLORS.emerald,
  },
  {
    name: 'Large Enterprise / Multi-Division',
    revenue: '$350K-$650K/yr',
    revenueColor: COLORS.blue,
    examples: 'Whirlpool, Panasonic, McKesson',
    detail: '50-100 KPIs • 15-25 assessments/mo',
    borderColor: COLORS.blue,
  },
  {
    name: 'Global Enterprise / Partner-Led',
    revenue: '$1.2M-$2.8M/yr',
    revenueColor: COLORS.purple,
    examples: 'ExxonMobil, Shell, Roche',
    detail: '200-500 KPIs • Year 3+',
    borderColor: COLORS.purple,
    opacity: 0.6,
  },
];

export const PricingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Beat A: 0-12s
  const componentsStart = fps * 3;
  const componentStagger = fps * 1.5;

  // Beat B: 12-26s
  const dividerStart = fps * 12;
  const dividerOpacity = interpolate(frame, [dividerStart, dividerStart + fps * 0.4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const tiersStart = fps * 13;
  const tierStagger = fps * 3.5;

  // Beat C: 26-28s
  const statusStart = fps * 26;
  const statusOpacity = interpolate(frame, [statusStart, statusStart + fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const statusY = interpolate(frame, [statusStart, statusStart + fps * 0.5], [12, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer>
      <div className="w-full h-full flex flex-col px-16 py-12 relative">
        {/* Section title — 0-3s */}
        <SectionTitle subtitle="Cost drivers map to billing axes.">
          Pricing Architecture
        </SectionTitle>

        {/* Beat A: 5 components in 2-column grid — 3-12s */}
        {/* 3 left column, 2 right column via CSS grid */}
        <div
          className="mt-8"
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gridTemplateRows: 'auto auto auto',
            gap: '12px',
          }}
        >
          {PRICING_COMPONENTS.map((component, i) => {
            const delay = componentsStart + i * componentStagger;
            return (
              <AnimatedCard
                key={component.name}
                delay={delay}
                borderColor={component.borderColor}
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <p className="text-xl font-bold" style={{ color: COLORS.text }}>
                    {component.name}
                  </p>
                  {component.badge && (
                    <span
                      className="inline-flex items-center rounded-full px-2 py-0.5 text-sm font-semibold shrink-0"
                      style={{
                        backgroundColor: `${component.badge.color}20`,
                        color: component.badge.color,
                      }}
                    >
                      {component.badge.text}
                    </span>
                  )}
                </div>
                <p className="text-3xl font-bold" style={{ color: COLORS.accentLight }}>
                  {component.price}
                </p>
                <p className="text-base mt-1" style={{ color: COLORS.muted }}>
                  {component.description}
                </p>
              </AnimatedCard>
            );
          })}
        </div>

        {/* Beat B: divider — 12-13s */}
        <div
          className="mt-6 mb-4"
          style={{
            opacity: dividerOpacity,
            height: '1px',
            backgroundColor: COLORS.border,
          }}
        />

        {/* Beat B: three tier columns — 13-26s */}
        <div className="flex flex-row gap-5 flex-1">
          {REVENUE_TIERS.map((tier, i) => {
            const delay = tiersStart + i * tierStagger;
            return (
              <div
                key={tier.name}
                className="flex-1"
                style={{ opacity: tier.opacity ?? 1 }}
              >
                <AnimatedCard
                  delay={delay}
                  className="h-full"
                  borderColor={tier.borderColor}
                >
                  {/* Left accent border */}
                  <div
                    style={{
                      borderLeft: `4px solid ${tier.borderColor}`,
                      paddingLeft: '14px',
                    }}
                  >
                    <p className="text-xl font-bold mb-2" style={{ color: COLORS.text }}>
                      {tier.name}
                    </p>
                    <p
                      className="font-bold mb-2"
                      style={{ fontSize: '2.25rem', color: tier.revenueColor, lineHeight: 1.1 }}
                    >
                      {tier.revenue}
                    </p>
                    <p
                      className="text-base mb-3"
                      style={{ color: COLORS.muted, fontStyle: 'italic' }}
                    >
                      {tier.examples}
                    </p>
                    <p className="text-lg" style={{ color: COLORS.textSecondary }}>
                      {tier.detail}
                    </p>
                  </div>
                </AnimatedCard>
              </div>
            );
          })}
        </div>

        {/* Beat C: status note — 26-28s */}
        <div
          className="mt-4 text-center"
          style={{
            opacity: statusOpacity,
            transform: `translateY(${statusY}px)`,
          }}
        >
          <p className="text-xl" style={{ color: COLORS.muted, fontStyle: 'italic' }}>
            Three models being tested. Demo feedback question: "Which would you take to your CFO?"
          </p>
        </div>

        <LogoWatermark />
      </div>
    </SceneContainer>
  );
};
