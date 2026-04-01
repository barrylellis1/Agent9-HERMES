import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer } from '../shared/components';
import { COLORS } from '../shared/constants';

/**
 * Scene 9: Closing — CTA
 *
 * Visual sequence:
 * 0-3s:  Pipeline recap (6 colored dots in a line)
 * 3-6s:  "From detection to proof. Automatically."
 * 6-10s: CTA: "Request a Conversation" + decision-studios.com
 */
export const ClosingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const pipelineNodes = [
    { label: 'Monitor', color: '#3b82f6' },
    { label: 'Detect', color: '#ef4444' },
    { label: 'Diagnose', color: '#f59e0b' },
    { label: 'Recommend', color: '#8b5cf6' },
    { label: 'Decide', color: '#4f46e5' },
    { label: 'Prove', color: '#10b981' },
  ];

  const taglineOpacity = interpolate(frame, [fps * 3, fps * 4], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  const ctaOpacity = interpolate(frame, [fps * 6, fps * 7], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer className="items-center justify-center relative">
      {/* Pipeline dots */}
      <div className="flex items-center gap-4">
        {pipelineNodes.map((node, i) => {
          const delay = i * 4;
          const opacity = interpolate(frame, [delay, delay + fps * 0.3], [0, 1], {
            extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
          });
          return (
            <React.Fragment key={node.label}>
              <div className="flex flex-col items-center gap-2" style={{ opacity }}>
                <div
                  className="w-14 h-14 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: node.color }}
                />
                <span className="text-lg font-medium" style={{ color: COLORS.textSecondary }}>
                  {node.label}
                </span>
              </div>
              {i < pipelineNodes.length - 1 && (
                <div
                  className="w-12 h-0.5 -mt-6"
                  style={{
                    backgroundColor: COLORS.border,
                    opacity: interpolate(frame, [delay + 4, delay + fps * 0.3 + 4], [0, 1], {
                      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
                    }),
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Tagline */}
      <p
        className="text-5xl font-bold mt-16 tracking-tight"
        style={{ opacity: taglineOpacity, color: COLORS.text }}
      >
        From detection to proof. Automatically.
      </p>

      {/* CTA */}
      <div className="mt-12 flex flex-col items-center gap-4" style={{ opacity: ctaOpacity }}>
        <div
          className="px-10 py-4 rounded-lg text-2xl font-semibold text-white"
          style={{ backgroundColor: COLORS.accent }}
        >
          Request a Conversation
        </div>
        <p className="text-2xl" style={{ color: COLORS.accentLight }}>
          decision-studios.com
        </p>
      </div>

      {/* Logo */}
      <div className="absolute bottom-12 flex items-center gap-3">
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
