import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer, LogoWatermark } from '../shared/components';
import { COLORS } from '../shared/constants';

/**
 * Scene 1: Brand intro + problem statement
 *
 * Visual sequence:
 * 0-1s:  Fade in Decision Studio logo (centered, large)
 * 1-4s:  Logo shrinks to top-left, tagline appears: "AI Decision Intelligence"
 * 4-8s:  Three problem lines appear sequentially (from landing page):
 *        "You're always reacting, never anticipating."
 *        "Your data tells you what happened. Not what to do about it."
 *        "By the time you act, the window has closed."
 * 8-12s: Transition text: "What if your data could think?"
 */
export const HeroScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Phase 1: Logo entrance (0-1s)
  const logoScale = interpolate(frame, [0, fps], [1.5, 1], {
    extrapolateRight: 'clamp',
  });
  const logoOpacity = interpolate(frame, [0, fps * 0.3], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Phase 2: Logo moves up, tagline appears (1-4s)
  const logoY = interpolate(frame, [fps, fps * 2], [0, -280], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const taglineOpacity = interpolate(frame, [fps * 2, fps * 2.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Phase 3: Problem lines (4-8s)
  const problems = [
    "You're always reacting, never anticipating.",
    "Your data tells you what happened. Not what to do about it.",
    "By the time you act, the window has closed.",
  ];

  // Phase 4: Transition (8-12s)
  const transitionOpacity = interpolate(frame, [fps * 8.5, fps * 9.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer className="items-center justify-center relative">
      {/* Logo */}
      <div
        className="flex flex-col items-center"
        style={{
          opacity: logoOpacity,
          transform: `scale(${logoScale}) translateY(${logoY}px)`,
        }}
      >
        <div className="flex items-center gap-4">
          <div
            className="w-16 h-16 rounded-xl flex items-center justify-center text-2xl font-bold text-white"
            style={{ backgroundColor: COLORS.accent }}
          >
            DS
          </div>
          <h1 className="text-7xl font-bold tracking-tight" style={{ color: COLORS.text }}>
            Decision Studio
          </h1>
        </div>
        <p
          className="text-4xl mt-4 tracking-wide"
          style={{ color: COLORS.accentLight, opacity: taglineOpacity }}
        >
          AI Decision Intelligence
        </p>
      </div>

      {/* Problem statements */}
      <div className="absolute top-[55%] flex flex-col items-center gap-6 px-20">
        {problems.map((problem, i) => {
          const start = fps * (4 + i * 1.3);
          const opacity = interpolate(frame, [start, start + fps * 0.5], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const y = interpolate(frame, [start, start + fps * 0.5], [16, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return (
            <p
              key={i}
              className="text-3xl text-center"
              style={{
                opacity,
                transform: `translateY(${y}px)`,
                color: COLORS.textSecondary,
              }}
            >
              {problem}
            </p>
          );
        })}
      </div>

      {/* Transition */}
      <div
        className="absolute bottom-32 text-center"
        style={{ opacity: transitionOpacity }}
      >
        <p className="text-5xl font-bold" style={{ color: COLORS.text }}>
          What if your data could think?
        </p>
      </div>

      <LogoWatermark />
    </SceneContainer>
  );
};
