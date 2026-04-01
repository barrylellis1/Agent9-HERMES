// Video dimensions and timing
export const VIDEO_WIDTH = 1920;
export const VIDEO_HEIGHT = 1080;
export const VIDEO_FPS = 30;

// Scene durations in seconds
export const SCENE_DURATIONS = {
  opening: 14,
  whatChanged: 24,
  premises: 30,
  market: 22,
  moat: 20,
  pricing: 28,
  projections: 24,
  exit: 18,
  closing: 16,
} as const;

// Total duration in frames
export const TOTAL_DURATION_FRAMES = Object.values(SCENE_DURATIONS).reduce(
  (sum, d) => sum + d * VIDEO_FPS, 0
); // 196s = 5880 frames

// Convert seconds to frames
export const toFrames = (seconds: number) => seconds * VIDEO_FPS;

// Scene start frames (cumulative)
export const SCENE_STARTS = Object.entries(SCENE_DURATIONS).reduce(
  (acc, [key, duration], index) => {
    const entries = Object.entries(SCENE_DURATIONS);
    const start = entries
      .slice(0, index)
      .reduce((sum, [, d]) => sum + toFrames(d), 0);
    return { ...acc, [key]: start };
  },
  {} as Record<keyof typeof SCENE_DURATIONS, number>
);

// Brand colors — same as demo-video + additions
export const COLORS = {
  bg: '#020617',
  surface: '#0f172a',
  card: '#1e293b',
  border: '#334155',
  muted: '#64748b',
  text: '#f8fafc',
  textSecondary: '#cbd5e1',
  accent: '#4f46e5',
  accentLight: '#818cf8',
  emerald: '#10b981',
  amber: '#f59e0b',
  red: '#ef4444',
  blue: '#3b82f6',
  purple: '#8b5cf6',
  teal: '#14b8a6',
} as const;
