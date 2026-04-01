import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer, LogoWatermark } from '../shared/components';
import { COLORS } from '../shared/constants';

export const OpeningScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Beat 1 (0-2s): Logo fades in centered
  const logoOpacity = interpolate(frame, [0, fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Beat 2 (2-5s): Logo moves up, title/subtitle fade in
  const logoMoveStart = fps * 2;
  const logoMoveEnd = fps * 5;
  const logoY = interpolate(frame, [logoMoveStart, logoMoveEnd], [0, -200], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const titleOpacity = interpolate(frame, [logoMoveStart + fps * 0.3, logoMoveEnd], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const titleY = interpolate(frame, [logoMoveStart + fps * 0.3, logoMoveEnd], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const subtitleOpacity = interpolate(frame, [logoMoveStart + fps * 0.7, logoMoveEnd + fps * 0.3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const barOpacity = interpolate(frame, [logoMoveStart + fps, logoMoveEnd + fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const barScaleX = interpolate(frame, [logoMoveStart + fps, logoMoveEnd + fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Beat 3 (5-11s): Three questions stagger 1.8s apart
  const questions = [
    'Is the market real?',
    'Does the product hold up?',
    'Can this become a business?',
  ];
  const questionsStart = fps * 5;
  const questionStagger = fps * 1.8;

  // Beat 4 (11-14s): Answer line fades in
  const answerStart = fps * 11;
  const answerOpacity = interpolate(frame, [answerStart, answerStart + fps * 0.6], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const answerY = interpolate(frame, [answerStart, answerStart + fps * 0.6], [20, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer>
      {/* Centered layout */}
      <div className="w-full h-full flex flex-col items-center justify-center relative">

        {/* Logo block — moves up after 2s */}
        <div
          className="flex flex-col items-center gap-4 absolute"
          style={{
            opacity: logoOpacity,
            transform: `translateY(${logoY}px)`,
          }}
        >
          <div
            className="w-16 h-16 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: COLORS.accent }}
          >
            <span className="text-2xl font-bold text-white">DS</span>
          </div>
          <span className="font-bold tracking-tight" style={{ fontSize: '4.5rem', color: COLORS.text }}>
            Decision Studio
          </span>
        </div>

        {/* Title + subtitle + bar — appear starting at 2s */}
        <div className="flex flex-col items-center gap-3 mt-[-60px]">
          <div style={{ opacity: titleOpacity, transform: `translateY(${titleY}px)` }}>
            <h1
              className="font-bold tracking-tight text-center"
              style={{ fontSize: '3rem', color: COLORS.text }}
            >
              Business Premise Challenge
            </h1>
          </div>

          <div style={{ opacity: subtitleOpacity }}>
            <p className="text-2xl text-center" style={{ color: COLORS.muted }}>
              March 2026 — 18-Month Stress Test
            </p>
          </div>

          {/* Thin accent bar */}
          <div
            style={{
              opacity: barOpacity,
              width: '120px',
              height: '3px',
              borderRadius: '9999px',
              backgroundColor: COLORS.accent,
              transformOrigin: 'left center',
              transform: `scaleX(${barScaleX})`,
              marginTop: '4px',
            }}
          />
        </div>

        {/* Questions — staggered */}
        <div className="flex flex-col items-center gap-5 mt-12">
          {questions.map((q, i) => {
            const start = questionsStart + i * questionStagger;
            const qOpacity = interpolate(frame, [start, start + fps * 0.5], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            const qY = interpolate(frame, [start, start + fps * 0.5], [16, 0], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });

            return (
              <div
                key={i}
                style={{
                  opacity: qOpacity,
                  transform: `translateY(${qY}px)`,
                }}
              >
                <p
                  className="text-3xl text-center"
                  style={{ color: COLORS.accentLight }}
                >
                  {q}
                </p>
              </div>
            );
          })}
        </div>

        {/* Answer line */}
        <div
          className="mt-10 px-16 text-center"
          style={{
            opacity: answerOpacity,
            transform: `translateY(${answerY}px)`,
          }}
        >
          <p className="text-4xl font-bold" style={{ color: COLORS.text }}>
            We stress-tested every assumption. Here is what we found.
          </p>
        </div>

        <LogoWatermark />
      </div>
    </SceneContainer>
  );
};
