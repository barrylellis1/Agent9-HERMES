import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import {
  SceneContainer,
  SectionTitle,
  AnimatedCard,
  LogoWatermark,
} from '../shared/components';
import { COLORS } from '../shared/constants';

// ---------------------------------------------------------------------------
// Individual exit card content
// ---------------------------------------------------------------------------
interface ExitCardData {
  title: string;
  titleColor: string;
  valuation: string;
  valuationColor: string;
  valuationSize: string;
  arr: string;
  timeline: string;
  buyers: string;
  borderColor: string;
  annotation?: string;
}

const ExitCardContent: React.FC<ExitCardData> = ({
  title,
  titleColor,
  valuation,
  valuationColor,
  valuationSize,
  arr,
  timeline,
  buyers,
  borderColor,
  annotation,
}) => (
  <div
    style={{
      borderLeft: `4px solid ${borderColor}`,
      paddingLeft: '20px',
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
    }}
  >
    <div style={{ fontSize: '1.25rem', fontWeight: 700, color: titleColor }}>
      {title}
    </div>
    <div style={{ fontSize: valuationSize, fontWeight: 700, color: valuationColor, lineHeight: 1.1 }}>
      {valuation}
    </div>
    <div style={{ fontSize: '1rem', color: COLORS.textSecondary, marginTop: '4px' }}>
      {arr}
    </div>
    <div style={{ fontSize: '1rem', color: COLORS.muted }}>
      {timeline}
    </div>
    <div style={{ fontSize: '1rem', color: COLORS.muted }}>
      {buyers}
    </div>
    {annotation && (
      <div
        style={{
          fontSize: '0.875rem',
          color: COLORS.emerald,
          fontStyle: 'italic',
          marginTop: 'auto',
          paddingTop: '8px',
        }}
      >
        {annotation}
      </div>
    )}
  </div>
);

// ---------------------------------------------------------------------------
// Scene
// ---------------------------------------------------------------------------
export const ExitScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const bottomOpacity = interpolate(frame - fps * 16, [0, fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const cards: (ExitCardData & { delay: number; cardOpacity?: number })[] = [
    {
      title: 'Bootstrapped Acquisition',
      titleColor: COLORS.text,
      valuation: '$5M–$21M',
      valuationColor: COLORS.emerald,
      valuationSize: '2.5rem',
      arr: 'ARR: $600K–$1.4M',
      timeline: 'Month 24–36',
      buyers: 'PE roll-up, ERP vendor (Sage, Epicor)',
      borderColor: COLORS.emerald,
      annotation: '$1M ARR + 140% NRR → ~$22M valuation',
      delay: fps * 3,
    },
    {
      title: 'Funded Growth → Strategic',
      titleColor: COLORS.text,
      valuation: '$45M–$250M',
      valuationColor: COLORS.blue,
      valuationSize: '2.5rem',
      arr: 'ARR: $3M–$10M',
      timeline: 'Month 30–48',
      buyers: 'Salesforce, ServiceNow, Workday, SAP',
      borderColor: COLORS.blue,
      delay: fps * 5.5,
    },
    {
      title: 'PE Portfolio Play',
      titleColor: COLORS.text,
      valuation: '$60M–$300M',
      valuationColor: COLORS.purple,
      valuationSize: '2.5rem',
      arr: 'ARR: $5M–$15M',
      timeline: 'Month 36–60',
      buyers: 'PE firm or strategic at premium',
      borderColor: COLORS.purple,
      delay: fps * 8,
    },
    {
      title: 'Acqui-hire (Downside)',
      titleColor: COLORS.muted,
      valuation: '$1M–$5M',
      valuationColor: COLORS.muted,
      valuationSize: '2rem',
      arr: 'ARR: $180K–$360K',
      timeline: 'Month 24–30',
      buyers: 'AI startup, consulting firm',
      borderColor: COLORS.red,
      cardOpacity: 0.5,
      delay: fps * 10.5,
    },
  ];

  return (
    <SceneContainer>
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          padding: '56px 80px',
          position: 'relative',
        }}
      >
        <LogoWatermark />

        {/* Title */}
        <SectionTitle subtitle="The NRR multiplier changes the valuation category.">
          Exit Scenarios
        </SectionTitle>

        {/* 2×2 card grid */}
        <div
          style={{
            marginTop: '36px',
            flex: 1,
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gridTemplateRows: '1fr 1fr',
            gap: '20px',
          }}
        >
          {cards.map((card) => (
            <div
              key={card.title}
              style={card.cardOpacity !== undefined ? { opacity: card.cardOpacity } : undefined}
            >
              <AnimatedCard delay={card.delay}>
                <ExitCardContent {...card} />
              </AnimatedCard>
            </div>
          ))}
        </div>

        {/* Bottom line */}
        <div
          style={{
            opacity: bottomOpacity,
            textAlign: 'center',
            marginTop: '24px',
            paddingTop: '16px',
            borderTop: `1px solid ${COLORS.border}`,
          }}
        >
          <span style={{ fontSize: '1.25rem', color: COLORS.textSecondary }}>
            Month 12–18 decision point: stay bootstrapped, raise seed, or deepen PE relationship.
          </span>
        </div>
      </div>
    </SceneContainer>
  );
};
