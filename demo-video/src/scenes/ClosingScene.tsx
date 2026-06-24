import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer } from '../shared/components';
import { COLORS } from '../shared/constants';

/**
 * Scene 9: Closing — extended CTA (28 seconds)
 *
 * 0–5s:   Pipeline nodes appear one by one with connector lines
 * 5–10s:  "From detection to proof." lands
 * 10–14s: "Automatically." fades in beneath it
 * 14–19s: Supporting line — "First assessment in your environment within a week."
 * 19–28s: CTA button + domain + logo breathe with gentle pulse
 */
export const ClosingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const fi = (start: number, end: number, from: number, to: number) =>
    interpolate(frame, [fps * start, fps * end], [from, to], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });

  const pipelineNodes = [
    { label: 'Monitor',   color: '#3b82f6' },
    { label: 'Detect',    color: '#ef4444' },
    { label: 'Diagnose',  color: '#f59e0b' },
    { label: 'Recommend', color: '#8b5cf6' },
    { label: 'Decide',    color: '#4f46e5' },
    { label: 'Prove',     color: '#10b981' },
  ];

  // Stagger each node: node i appears at i*0.6s
  const nodeDelay = 0.6;
  const lastNodeTime = (pipelineNodes.length - 1) * nodeDelay + 0.4;

  // Main tagline: "From detection to proof."
  const tagline1Opacity = fi(lastNodeTime, lastNodeTime + 1, 0, 1);
  const tagline1Y = fi(lastNodeTime, lastNodeTime + 1, 20, 0);

  // "Automatically." — half a beat after the main tagline
  const tagline2Opacity = fi(lastNodeTime + 1.2, lastNodeTime + 2.2, 0, 1);
  const tagline2Y = fi(lastNodeTime + 1.2, lastNodeTime + 2.2, 20, 0);

  // Supporting line
  const supportOpacity = fi(14, 15.5, 0, 1);
  const supportY = fi(14, 15.5, 16, 0);

  // CTA block
  const ctaOpacity = fi(19, 21, 0, 1);
  const ctaScale = fi(19, 21, 0.92, 1);

  // Gentle pulse on CTA button after it appears (cycles every 3s)
  const pulsePhase = ((frame - fps * 21) / (fps * 3)) % 1;
  const buttonGlow = frame > fps * 21
    ? 0.15 + 0.12 * Math.sin(pulsePhase * Math.PI * 2)
    : 0;

  // Logo
  const logoOpacity = fi(19, 22, 0, 1);

  return (
    <SceneContainer className="items-center justify-center relative overflow-hidden">

      {/* Subtle radial glow behind the tagline */}
      <div
        style={{
          position: 'absolute',
          top: '30%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 900,
          height: 500,
          borderRadius: '50%',
          background: `radial-gradient(ellipse, rgba(79,70,229,0.12) 0%, transparent 70%)`,
          opacity: fi(5, 11, 0, 1),
          pointerEvents: 'none',
        }}
      />

      {/* Pipeline nodes */}
      <div className="flex items-center gap-5">
        {pipelineNodes.map((node, i) => {
          const t = i * nodeDelay;
          const nodeOpacity = fi(t, t + 0.4, 0, 1);
          const nodeScale = fi(t, t + 0.4, 0.6, 1);
          const connectorOpacity = fi(t + 0.2, t + 0.6, 0, 1);
          return (
            <React.Fragment key={node.label}>
              <div
                className="flex flex-col items-center gap-3"
                style={{ opacity: nodeOpacity, transform: `scale(${nodeScale})` }}
              >
                <div
                  className="w-16 h-16 rounded-full flex items-center justify-center"
                  style={{
                    backgroundColor: node.color,
                    boxShadow: `0 0 24px ${node.color}55`,
                  }}
                />
                <span
                  className="text-base font-semibold tracking-wide uppercase"
                  style={{ color: COLORS.textSecondary, letterSpacing: '0.08em' }}
                >
                  {node.label}
                </span>
              </div>
              {i < pipelineNodes.length - 1 && (
                <div
                  className="w-14 h-0.5 -mt-7"
                  style={{
                    background: `linear-gradient(to right, ${node.color}88, ${pipelineNodes[i + 1].color}88)`,
                    opacity: connectorOpacity,
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Main tagline */}
      <div className="mt-20 text-center" style={{ lineHeight: 1.1 }}>
        <p
          className="text-6xl font-bold tracking-tight"
          style={{
            color: COLORS.text,
            opacity: tagline1Opacity,
            transform: `translateY(${tagline1Y}px)`,
          }}
        >
          From detection to proof.
        </p>
        <p
          className="text-6xl font-bold tracking-tight mt-2"
          style={{
            color: COLORS.accentLight,
            opacity: tagline2Opacity,
            transform: `translateY(${tagline2Y}px)`,
          }}
        >
          Automatically.
        </p>
      </div>

      {/* Supporting line */}
      <p
        className="mt-8 text-2xl font-normal text-center"
        style={{
          color: COLORS.textSecondary,
          opacity: supportOpacity,
          transform: `translateY(${supportY}px)`,
          maxWidth: 700,
        }}
      >
        First assessment in your environment within a week.
      </p>

      {/* CTA block */}
      <div
        className="mt-14 flex flex-col items-center gap-5"
        style={{ opacity: ctaOpacity, transform: `scale(${ctaScale})` }}
      >
        <div
          className="px-14 py-5 rounded-xl text-2xl font-semibold text-white"
          style={{
            backgroundColor: COLORS.accent,
            boxShadow: `0 0 ${40 + buttonGlow * 200}px rgba(79,70,229,${0.45 + buttonGlow})`,
            transition: 'none',
          }}
        >
          Request a Conversation
        </div>
        <p className="text-2xl font-medium" style={{ color: COLORS.accentLight }}>
          decision-studios.com
        </p>
      </div>

      {/* Logo */}
      <div
        className="absolute bottom-12 flex items-center gap-3"
        style={{ opacity: logoOpacity }}
      >
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold text-white"
          style={{ backgroundColor: COLORS.accent }}
        >
          DS
        </div>
        <span className="text-2xl font-semibold" style={{ color: COLORS.text }}>
          Decision Studio
        </span>
      </div>
    </SceneContainer>
  );
};
