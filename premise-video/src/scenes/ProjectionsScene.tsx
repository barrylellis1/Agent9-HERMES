import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import {
  SceneContainer,
  SectionTitle,
  BigNumber,
  LogoWatermark,
} from '../shared/components';
import { COLORS } from '../shared/constants';

// ---------------------------------------------------------------------------
// Animated table row
// ---------------------------------------------------------------------------
const TableRow: React.FC<{
  scenario: string;
  flat: string;
  incremental: string;
  multiplier: string;
  delay: number;
  highlight?: boolean;
}> = ({ scenario, flat, incremental, multiplier, delay, highlight = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame - delay, [0, fps * 0.4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const y = interpolate(frame - delay, [0, fps * 0.4], [14, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        opacity,
        transform: `translateY(${y}px)`,
        display: 'flex',
        alignItems: 'center',
        padding: '16px',
        borderBottom: `1px solid ${COLORS.border}`,
        backgroundColor: highlight ? `${COLORS.card}cc` : 'transparent',
        borderRadius: highlight ? '8px' : '0',
      }}
    >
      <div style={{ width: '18%', flexShrink: 0 }}>
        <span style={{ fontSize: '1.25rem', color: COLORS.text, fontWeight: 600 }}>
          {scenario}
        </span>
      </div>
      <div style={{ width: '30%', flexShrink: 0 }}>
        <span style={{ fontSize: '1.25rem', color: COLORS.textSecondary }}>
          {flat}
        </span>
      </div>
      <div style={{ width: '32%', flexShrink: 0 }}>
        <span style={{ fontSize: '1.25rem', color: COLORS.emerald, fontWeight: 700 }}>
          {incremental}
        </span>
      </div>
      <div style={{ width: '20%', flexShrink: 0 }}>
        <span style={{ fontSize: '1.25rem', color: COLORS.accentLight, fontWeight: 700 }}>
          {multiplier}
        </span>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Scene
// ---------------------------------------------------------------------------
export const ProjectionsScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Beat B — header row
  const headerOpacity = interpolate(frame - fps * 4, [0, fps * 0.3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Beat C — BigNumbers
  const bigNumberDelay1 = fps * 18;
  const bigNumberDelay2 = fps * 18.5;
  const bigNumberDelay3 = fps * 19;

  const bigNumOpacity = interpolate(frame - fps * 18, [0, fps * 0.4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Beat D — callout
  const calloutOpacity = interpolate(frame - fps * 22, [0, fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '64px 80px', position: 'relative' }}>
        <LogoWatermark />

        {/* Beat A — Title */}
        <SectionTitle subtitle="Three scenarios. Two pricing models. Same customer count.">
          18-Month Revenue Outlook
        </SectionTitle>

        {/* Beat B — Comparison Table */}
        <div style={{ marginTop: '40px', flex: 1 }}>
          {/* Header row */}
          <div
            style={{
              opacity: headerOpacity,
              display: 'flex',
              alignItems: 'center',
              padding: '12px 16px',
              backgroundColor: COLORS.surface,
              borderRadius: '8px 8px 0 0',
              borderBottom: `1px solid ${COLORS.border}`,
            }}
          >
            {[
              { label: 'Scenario', width: '18%' },
              { label: 'Flat SaaS (Month 24)', width: '30%' },
              { label: 'Incremental (Month 24)', width: '32%' },
              { label: 'Multiplier', width: '20%' },
            ].map(({ label, width }) => (
              <div key={label} style={{ width, flexShrink: 0 }}>
                <span
                  style={{
                    fontSize: '0.875rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.1em',
                    fontWeight: 600,
                    color: COLORS.muted,
                  }}
                >
                  {label}
                </span>
              </div>
            ))}
          </div>

          {/* Data rows — stagger starts at fps*5, 3s apart */}
          <TableRow
            scenario="Base"
            flat="$225K–$360K"
            incremental="$600K–$1.4M"
            multiplier="2.7–3.9×"
            delay={fps * 5}
            highlight={true}
          />
          <TableRow
            scenario="Upside"
            flat="$650K–$975K"
            incremental="$1.5M–$6M"
            multiplier="2.3–6.2×"
            delay={fps * 8}
          />
          <TableRow
            scenario="Downside"
            flat="$50K–$75K"
            incremental="$180K–$360K"
            multiplier="3.6–4.8×"
            delay={fps * 11}
          />
        </div>

        {/* Beat C — BigNumbers */}
        <div
          style={{
            opacity: bigNumOpacity,
            display: 'flex',
            justifyContent: 'space-around',
            gap: '48px',
            marginTop: '48px',
          }}
        >
          <BigNumber
            value="$600K–$1.4M"
            label="Base Case ARR, Month 24"
            color={COLORS.emerald}
            delay={bigNumberDelay1}
          />
          <BigNumber
            value="5–8"
            label="Tier 1 Customers"
            color={COLORS.blue}
            delay={bigNumberDelay2}
          />
          <BigNumber
            value="3–4×"
            label="Incremental vs Flat Lift"
            color={COLORS.amber}
            delay={bigNumberDelay3}
          />
        </div>

        {/* Beat D — Callout */}
        <div
          style={{
            opacity: calloutOpacity,
            textAlign: 'center',
            marginTop: '32px',
            paddingTop: '16px',
            borderTop: `1px solid ${COLORS.border}`,
          }}
        >
          <span
            style={{
              fontSize: '1.5rem',
              fontWeight: 600,
              color: COLORS.text,
            }}
          >
            $2M ARR at Month 30 is back in range under the upside scenario.
          </span>
        </div>
      </div>
    </SceneContainer>
  );
};
