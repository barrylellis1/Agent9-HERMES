import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import {
  SceneContainer,
  BigNumber,
  LogoWatermark,
} from '../shared/components';
import { COLORS } from '../shared/constants';

// ---------------------------------------------------------------------------
// Animated requirement line
// ---------------------------------------------------------------------------
const RequirementLine: React.FC<{
  marker: string;
  markerColor: string;
  text: string;
  delay: number;
}> = ({ marker, markerColor, text, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame - delay, [0, fps * 0.4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const y = interpolate(frame - delay, [0, fps * 0.4], [16, 0], {
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
        gap: '16px',
      }}
    >
      <span style={{ fontSize: '1.5rem', fontWeight: 700, color: markerColor, minWidth: '32px' }}>
        {marker}
      </span>
      <span style={{ fontSize: '1.5rem', color: COLORS.text }}>
        {text}
      </span>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Animated partner line
// ---------------------------------------------------------------------------
const PartnerLine: React.FC<{
  text: string;
  size: string;
  weight: number;
  color: string;
  delay: number;
}> = ({ text, size, weight, color, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame - delay, [0, fps * 0.4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const y = interpolate(frame - delay, [0, fps * 0.4], [12, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div style={{ opacity, transform: `translateY(${y}px)` }}>
      <span style={{ fontSize: size, fontWeight: weight, color }}>{text}</span>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Scene
// ---------------------------------------------------------------------------
export const ClosingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Logo block — Beat D (14-16s)
  const logoOpacity = interpolate(frame - fps * 14, [0, fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer>
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '64px 120px',
          position: 'relative',
          gap: '48px',
        }}
      >
        <LogoWatermark />

        {/* Beat A — Three requirement lines (0-4s, stagger 1.2s) */}
        <div
          style={{
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
            alignItems: 'flex-start',
          }}
        >
          <RequirementLine
            marker="✓"
            markerColor={COLORS.emerald}
            text="Demo video shipped"
            delay={0}
          />
          <RequirementLine
            marker="→"
            markerColor={COLORS.amber}
            text="First paying customer by September 2026"
            delay={fps * 1.2}
          />
          <RequirementLine
            marker="→"
            markerColor={COLORS.amber}
            text="2–3 documented ROI case studies by Month 12"
            delay={fps * 2.4}
          />
        </div>

        {/* Beat B — Large centered BigNumber (4-10s) */}
        <div style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
          <BigNumber
            value="September 2026"
            label="First paying customer. The only milestone that matters."
            color={COLORS.accent}
            delay={fps * 4}
          />
        </div>

        {/* Beat C — Two partner lines (10-14s, stagger 1.5s) */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            alignItems: 'center',
            textAlign: 'center',
          }}
        >
          <PartnerLine
            text="Tier 0 Fractional CFOs: adopt as a practitioner, not a partner."
            size="1.5rem"
            weight={600}
            color={COLORS.accentLight}
            delay={fps * 10}
          />
          <PartnerLine
            text="Use it. Document the outcome. That becomes the case study."
            size="1.5rem"
            weight={400}
            color={COLORS.textSecondary}
            delay={fps * 11.5}
          />
        </div>

        {/* Beat D — Logo block (14-16s) */}
        <div
          style={{
            opacity: logoOpacity,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                backgroundColor: COLORS.accent,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '1.125rem',
                fontWeight: 700,
                color: '#ffffff',
              }}
            >
              DS
            </div>
            <span style={{ fontSize: '3rem', fontWeight: 700, color: COLORS.text }}>
              Decision Studio
            </span>
          </div>
          <span style={{ fontSize: '1.25rem', color: COLORS.muted }}>
            decision-studios.com — Request a Conversation
          </span>
        </div>
      </div>
    </SceneContainer>
  );
};
