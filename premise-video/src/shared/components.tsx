import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { COLORS } from './constants';

/**
 * Full-screen scene wrapper with dark background.
 */
export const SceneContainer: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = '' }) => (
  <div
    className={`w-full h-full flex flex-col font-satoshi ${className}`}
    style={{ backgroundColor: COLORS.bg, color: COLORS.text }}
  >
    {children}
  </div>
);

/**
 * Section title with accent underline.
 */
export const SectionTitle: React.FC<{
  children: React.ReactNode;
  subtitle?: string;
  delay?: number;
}> = ({ children, subtitle, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame - delay, [0, fps * 0.4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const y = interpolate(frame - delay, [0, fps * 0.4], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div style={{ opacity, transform: `translateY(${y}px)` }}>
      <h2 className="text-6xl font-bold tracking-tight" style={{ color: COLORS.text }}>
        {children}
      </h2>
      {subtitle && (
        <p className="text-2xl mt-3" style={{ color: COLORS.muted }}>
          {subtitle}
        </p>
      )}
      <div
        className="mt-4 h-1 w-24 rounded-full"
        style={{ backgroundColor: COLORS.accent }}
      />
    </div>
  );
};

/**
 * Animated card that springs in.
 */
export const AnimatedCard: React.FC<{
  children: React.ReactNode;
  delay?: number;
  className?: string;
  borderColor?: string;
}> = ({ children, delay = 0, className = '', borderColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame - delay, [0, fps * 0.3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const scale = interpolate(frame - delay, [0, fps * 0.4], [0.95, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      className={`rounded-xl border p-5 ${className}`}
      style={{
        opacity,
        transform: `scale(${scale})`,
        backgroundColor: COLORS.card,
        borderColor: borderColor || COLORS.border,
      }}
    >
      {children}
    </div>
  );
};

/**
 * Confidence badge — colored pill with label.
 */
export const ConfidenceBadge: React.FC<{
  level: 'strong' | 'improved' | 'conditional' | 'deferred' | 'addressed' | 'positive';
  label?: string;
}> = ({ level, label }) => {
  const colorMap = {
    strong: COLORS.emerald,
    improved: COLORS.emerald,
    positive: COLORS.emerald,
    conditional: COLORS.amber,
    deferred: COLORS.red,
    addressed: COLORS.blue,
  };
  const defaultLabels = {
    strong: 'Strong',
    improved: 'Improved',
    positive: 'Positive',
    conditional: 'Conditional',
    deferred: 'Deferred',
    addressed: 'Addressed',
  };
  const color = colorMap[level];
  const text = label || defaultLabels[level];

  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold"
      style={{ backgroundColor: `${color}20`, color }}
    >
      <span
        className="w-2 h-2 rounded-full"
        style={{ backgroundColor: color }}
      />
      {text}
    </span>
  );
};

/**
 * Comparison row — Area | Before | After with animated reveal.
 */
export const ComparisonRow: React.FC<{
  area: string;
  before: string;
  after: string;
  delay: number;
}> = ({ area, before, after, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame - delay, [0, fps * 0.3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const y = interpolate(frame - delay, [0, fps * 0.3], [12, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      className="flex items-start py-3"
      style={{
        opacity,
        transform: `translateY(${y}px)`,
        borderBottom: `1px solid ${COLORS.border}`,
      }}
    >
      <div className="w-[18%] shrink-0">
        <span className="text-lg font-semibold" style={{ color: COLORS.accentLight }}>
          {area}
        </span>
      </div>
      <div className="w-[38%] shrink-0 pr-6">
        <span className="text-lg" style={{ color: COLORS.muted }}>
          {before}
        </span>
      </div>
      <div
        className="w-[44%] shrink-0 pl-4"
        style={{ borderLeft: `2px solid ${COLORS.emerald}` }}
      >
        <span className="text-lg" style={{ color: COLORS.text }}>
          {after}
        </span>
      </div>
    </div>
  );
};

/**
 * Big number display — large numeral with label below.
 */
export const BigNumber: React.FC<{
  value: string;
  label: string;
  color?: string;
  delay?: number;
}> = ({ value, label, color = COLORS.text, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame - delay, [0, fps * 0.4], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const scale = interpolate(frame - delay, [0, fps * 0.4], [0.85, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      className="flex flex-col items-center text-center"
      style={{ opacity, transform: `scale(${scale})` }}
    >
      <span className="text-7xl font-bold" style={{ color }}>
        {value}
      </span>
      <span className="text-xl mt-2" style={{ color: COLORS.muted }}>
        {label}
      </span>
    </div>
  );
};

/**
 * Persistent logo watermark in bottom corner.
 */
export const LogoWatermark: React.FC = () => (
  <div className="absolute bottom-8 right-10 flex items-center gap-2" style={{ opacity: 0.5 }}>
    <div
      className="w-6 h-6 rounded-md flex items-center justify-center text-sm font-bold text-white"
      style={{ backgroundColor: COLORS.accent }}
    >
      DS
    </div>
    <span className="text-base font-medium" style={{ color: COLORS.muted }}>
      Decision Studio
    </span>
  </div>
);
