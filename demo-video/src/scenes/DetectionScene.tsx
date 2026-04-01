import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer, SectionTitle, KPITile, AnimatedCard, LogoWatermark } from '../shared/components';
import { COLORS } from '../shared/constants';
import { staggerDelay } from '../shared/animations';

/**
 * Scene 3: Situation Awareness — KPI breach detection
 *
 * Visual sequence:
 * 0-3s:  Title: "Continuous Monitoring" with subtitle
 * 3-10s: Grid of KPI tiles appears — most green, one turns red (Gross Margin)
 * 10-18s: Situation card materializes from the red KPI
 * 18-25s: Card details expand: severity, affected dimensions, recommended action
 */
export const DetectionScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const kpis = [
    { name: 'Revenue', value: '$12.4M', change: '+3.2%', status: 'healthy' as const },
    { name: 'Gross Margin', value: '28.1%', change: '-4.7%', status: 'critical' as const },
    { name: 'COGS Ratio', value: '71.9%', change: '+2.1%', status: 'warning' as const },
    { name: 'Operating Income', value: '$2.1M', change: '+1.8%', status: 'healthy' as const },
    { name: 'Net Cash Flow', value: '$890K', change: '-0.5%', status: 'healthy' as const },
    { name: 'Customer Count', value: '1,247', change: '+12', status: 'opportunity' as const },
  ];

  // Situation card appears at 10s
  const cardOpacity = interpolate(frame, [fps * 10, fps * 11], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cardScale = interpolate(frame, [fps * 10, fps * 11.5], [0.9, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Card details expand at 14s
  const detailsOpacity = interpolate(frame, [fps * 14, fps * 15], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer className="p-16 relative">
      <SectionTitle subtitle="Your KPIs are scanned continuously. When something breaks threshold, you know immediately.">
        Continuous Monitoring
      </SectionTitle>

      {/* KPI Grid */}
      <div className="grid grid-cols-3 gap-4 mt-12 max-w-4xl">
        {kpis.map((kpi, i) => (
          <KPITile
            key={kpi.name}
            {...kpi}
            delay={fps * 3 + staggerDelay(i, 6)}
          />
        ))}
      </div>

      {/* Situation Card */}
      <div
        className="absolute right-16 top-1/2 -translate-y-1/2 w-[420px]"
        style={{ opacity: cardOpacity, transform: `scale(${cardScale})` }}
      >
        <AnimatedCard className="border-l-4" delay={fps * 10}>
          <div style={{ borderLeftColor: COLORS.red }}>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.red }} />
              <span className="text-lg font-semibold" style={{ color: COLORS.red }}>
                CRITICAL — Situation Detected
              </span>
            </div>
            <h3 className="text-2xl font-bold" style={{ color: COLORS.text }}>
              Gross Margin Below Threshold
            </h3>
            <p className="text-lg mt-2" style={{ color: COLORS.muted }}>
              Gross Margin dropped to 28.1%, breaching the 30% threshold.
              Decline accelerating over past 3 months.
            </p>

            {/* Expandable details */}
            <div className="mt-4 pt-4 border-t" style={{ opacity: detailsOpacity, borderColor: COLORS.border }}>
              <div className="flex justify-between text-base mb-2">
                <span style={{ color: COLORS.muted }}>Severity</span>
                <span className="font-medium" style={{ color: COLORS.red }}>High</span>
              </div>
              <div className="flex justify-between text-base mb-2">
                <span style={{ color: COLORS.muted }}>Affected Dimensions</span>
                <span className="font-medium" style={{ color: COLORS.text }}>Region, Product, Customer</span>
              </div>
              <div className="flex justify-between text-base">
                <span style={{ color: COLORS.muted }}>Next Step</span>
                <span className="font-medium" style={{ color: COLORS.accentLight }}>Deep Analysis →</span>
              </div>
            </div>
          </div>
        </AnimatedCard>
      </div>

      <LogoWatermark />
    </SceneContainer>
  );
};
