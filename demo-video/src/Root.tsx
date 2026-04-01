import { Composition, Sequence } from 'remotion';
import { VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, SCENE_DURATIONS, TOTAL_DURATION_FRAMES, toFrames } from './shared/constants';
import './style.css';

// Scenes
import { HeroScene } from './scenes/HeroScene';
import { TheProblemScene } from './scenes/TheProblemScene';
import { DetectionScene } from './scenes/DetectionScene';
import { DiagnosisScene } from './scenes/DiagnosisScene';
import { RefinementScene } from './scenes/RefinementScene';
import { SolutionsScene } from './scenes/SolutionsScene';
import { ApprovalScene } from './scenes/ApprovalScene';
import { TrackingScene } from './scenes/TrackingScene';
import { OnboardingScene } from './scenes/OnboardingScene';
import { ClosingScene } from './scenes/ClosingScene';

/**
 * Full demo video — all 10 scenes sequenced.
 */
const DemoVideo: React.FC = () => {
  let offset = 0;

  const scenes = [
    { Component: HeroScene, duration: SCENE_DURATIONS.hero },
    { Component: TheProblemScene, duration: SCENE_DURATIONS.theProblem },
    { Component: DetectionScene, duration: SCENE_DURATIONS.detection },
    { Component: DiagnosisScene, duration: SCENE_DURATIONS.diagnosis },
    { Component: RefinementScene, duration: SCENE_DURATIONS.refinement },
    { Component: SolutionsScene, duration: SCENE_DURATIONS.solutions },
    { Component: ApprovalScene, duration: SCENE_DURATIONS.approval },
    { Component: TrackingScene, duration: SCENE_DURATIONS.tracking },
    { Component: OnboardingScene, duration: SCENE_DURATIONS.onboarding },
    { Component: ClosingScene, duration: SCENE_DURATIONS.closing },
  ];

  return (
    <>
      {scenes.map(({ Component, duration }, i) => {
        const from = offset;
        offset += toFrames(duration);
        return (
          <Sequence key={i} from={from} durationInFrames={toFrames(duration)}>
            <Component />
          </Sequence>
        );
      })}
    </>
  );
};

/**
 * Remotion Root — registers all compositions.
 */
export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Full video */}
      <Composition
        id="DemoVideo"
        component={DemoVideo}
        durationInFrames={TOTAL_DURATION_FRAMES}
        fps={VIDEO_FPS}
        width={VIDEO_WIDTH}
        height={VIDEO_HEIGHT}
      />

      {/* Individual scene previews for development */}
      <Composition id="Hero" component={HeroScene} durationInFrames={toFrames(SCENE_DURATIONS.hero)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="TheProblem" component={TheProblemScene} durationInFrames={toFrames(SCENE_DURATIONS.theProblem)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Detection" component={DetectionScene} durationInFrames={toFrames(SCENE_DURATIONS.detection)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Diagnosis" component={DiagnosisScene} durationInFrames={toFrames(SCENE_DURATIONS.diagnosis)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Refinement" component={RefinementScene} durationInFrames={toFrames(SCENE_DURATIONS.refinement)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Solutions" component={SolutionsScene} durationInFrames={toFrames(SCENE_DURATIONS.solutions)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Approval" component={ApprovalScene} durationInFrames={toFrames(SCENE_DURATIONS.approval)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Tracking" component={TrackingScene} durationInFrames={toFrames(SCENE_DURATIONS.tracking)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Onboarding" component={OnboardingScene} durationInFrames={toFrames(SCENE_DURATIONS.onboarding)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Closing" component={ClosingScene} durationInFrames={toFrames(SCENE_DURATIONS.closing)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
    </>
  );
};
