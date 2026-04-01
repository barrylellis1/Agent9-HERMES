import { Composition, Sequence } from 'remotion';
import { VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, SCENE_DURATIONS, TOTAL_DURATION_FRAMES, toFrames } from './shared/constants';
import './style.css';

// Scenes
import { OpeningScene } from './scenes/OpeningScene';
import { WhatChangedScene } from './scenes/WhatChangedScene';
import { PremisesScene } from './scenes/PremisesScene';
import { MarketScene } from './scenes/MarketScene';
import { MoatScene } from './scenes/MoatScene';
import { PricingScene } from './scenes/PricingScene';
import { ProjectionsScene } from './scenes/ProjectionsScene';
import { ExitScene } from './scenes/ExitScene';
import { ClosingScene } from './scenes/ClosingScene';

/**
 * Full premise challenge video — all 9 scenes sequenced.
 */
const PremiseVideo: React.FC = () => {
  let offset = 0;

  const scenes = [
    { Component: OpeningScene, duration: SCENE_DURATIONS.opening },
    { Component: WhatChangedScene, duration: SCENE_DURATIONS.whatChanged },
    { Component: PremisesScene, duration: SCENE_DURATIONS.premises },
    { Component: MarketScene, duration: SCENE_DURATIONS.market },
    { Component: MoatScene, duration: SCENE_DURATIONS.moat },
    { Component: PricingScene, duration: SCENE_DURATIONS.pricing },
    { Component: ProjectionsScene, duration: SCENE_DURATIONS.projections },
    { Component: ExitScene, duration: SCENE_DURATIONS.exit },
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
        id="PremiseVideo"
        component={PremiseVideo}
        durationInFrames={TOTAL_DURATION_FRAMES}
        fps={VIDEO_FPS}
        width={VIDEO_WIDTH}
        height={VIDEO_HEIGHT}
      />

      {/* Individual scene previews for development */}
      <Composition id="Opening" component={OpeningScene} durationInFrames={toFrames(SCENE_DURATIONS.opening)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="WhatChanged" component={WhatChangedScene} durationInFrames={toFrames(SCENE_DURATIONS.whatChanged)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Premises" component={PremisesScene} durationInFrames={toFrames(SCENE_DURATIONS.premises)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Market" component={MarketScene} durationInFrames={toFrames(SCENE_DURATIONS.market)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Moat" component={MoatScene} durationInFrames={toFrames(SCENE_DURATIONS.moat)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Pricing" component={PricingScene} durationInFrames={toFrames(SCENE_DURATIONS.pricing)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Projections" component={ProjectionsScene} durationInFrames={toFrames(SCENE_DURATIONS.projections)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Exit" component={ExitScene} durationInFrames={toFrames(SCENE_DURATIONS.exit)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
      <Composition id="Closing" component={ClosingScene} durationInFrames={toFrames(SCENE_DURATIONS.closing)} fps={VIDEO_FPS} width={VIDEO_WIDTH} height={VIDEO_HEIGHT} />
    </>
  );
};
