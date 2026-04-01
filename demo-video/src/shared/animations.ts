import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

/**
 * Fade-up animation matching the landing page's fadeUp variant.
 * Returns { opacity, transform } style object.
 */
export function useFadeUp(delay = 0) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame - delay, [0, fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const translateY = interpolate(frame - delay, [0, fps * 0.5], [24, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return {
    opacity,
    transform: `translateY(${translateY}px)`,
  };
}

/**
 * Spring-based entrance for cards and UI elements.
 */
export function useSpringIn(delay = 0) {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame: frame - delay,
    fps,
    config: { damping: 12, stiffness: 100 },
  });

  const opacity = interpolate(frame - delay, [0, fps * 0.3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return {
    opacity,
    transform: `scale(${scale})`,
  };
}

/**
 * Typewriter effect — returns substring of text up to current character.
 */
export function useTypewriter(text: string, startFrame = 0, charsPerFrame = 1.5) {
  const frame = useCurrentFrame();
  const elapsed = Math.max(0, frame - startFrame);
  const charCount = Math.min(Math.floor(elapsed * charsPerFrame), text.length);
  return text.substring(0, charCount);
}

/**
 * Progress bar that fills from 0 to 1 over a duration.
 */
export function useProgress(startFrame: number, durationFrames: number) {
  const frame = useCurrentFrame();
  return interpolate(frame, [startFrame, startFrame + durationFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
}

/**
 * Staggered entrance — returns delay in frames for item at given index.
 */
export function staggerDelay(index: number, staggerFrames = 8) {
  return index * staggerFrames;
}

/**
 * Fade out at end of scene.
 */
export function useFadeOut(sceneDurationFrames: number, fadeFrames = 15) {
  const frame = useCurrentFrame();
  return interpolate(
    frame,
    [sceneDurationFrames - fadeFrames, sceneDurationFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );
}
