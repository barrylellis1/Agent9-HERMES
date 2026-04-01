// Video dimensions and timing
export const VIDEO_WIDTH = 1920;
export const VIDEO_HEIGHT = 1080;
export const VIDEO_FPS = 30;

// Total duration in frames (~4:00 = 240 seconds)
export const TOTAL_DURATION_FRAMES = 240 * VIDEO_FPS; // 7200 frames

// Scene durations in seconds
export const SCENE_DURATIONS = {
  hero: 12,              // Brand intro + problem statement
  theProblem: 20,        // Three buyer-felt problems
  detection: 25,         // SA agent detecting KPI breach
  diagnosis: 25,         // DA agent dimensional analysis (trimmed)
  refinement: 20,        // HITL problem refinement with LLM assistance
  solutions: 30,         // SF multi-perspective debate + market context
  approval: 35,          // Executive briefing walkthrough + HITL approval
  tracking: 25,          // VA trajectory tracking
  onboarding: 18,        // 5-Day Fast Start
  closing: 10,           // CTA + contact
} as const;

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

// Brand colors
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
} as const;
