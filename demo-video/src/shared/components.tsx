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
}> = ({ children, delay = 0, className = '' }) => {
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
      className={`rounded-xl border p-6 ${className}`}
      style={{
        opacity,
        transform: `scale(${scale})`,
        backgroundColor: COLORS.card,
        borderColor: COLORS.border,
      }}
    >
      {children}
    </div>
  );
};

/**
 * Pipeline node — colored circle with label.
 */
export const PipelineNode: React.FC<{
  label: string;
  color: string;
  active?: boolean;
  delay?: number;
}> = ({ label, color, active = false, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame - delay, [0, fps * 0.3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const glow = active ? `0 0 20px ${color}40` : 'none';

  return (
    <div
      className="flex flex-col items-center gap-2"
      style={{ opacity }}
    >
      <div
        className="w-16 h-16 rounded-full flex items-center justify-center text-white text-base font-bold"
        style={{ backgroundColor: color, boxShadow: glow }}
      />
      <span className="text-lg font-medium" style={{ color: COLORS.textSecondary }}>
        {label}
      </span>
    </div>
  );
};

/**
 * KPI tile matching the app's situation card style.
 */
export const KPITile: React.FC<{
  name: string;
  value: string;
  change: string;
  status: 'critical' | 'warning' | 'healthy' | 'opportunity';
  delay?: number;
}> = ({ name, value, change, status, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame - delay, [0, fps * 0.3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const statusColors = {
    critical: COLORS.red,
    warning: COLORS.amber,
    healthy: COLORS.emerald,
    opportunity: COLORS.emerald,
  };

  return (
    <div
      className="rounded-lg border p-4"
      style={{
        opacity,
        backgroundColor: COLORS.surface,
        borderColor: COLORS.border,
        borderLeftWidth: 3,
        borderLeftColor: statusColors[status],
      }}
    >
      <p className="text-base" style={{ color: COLORS.muted }}>{name}</p>
      <p className="text-3xl font-bold mt-1" style={{ color: COLORS.text }}>{value}</p>
      <p className="text-base mt-1" style={{ color: statusColors[status] }}>{change}</p>
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
