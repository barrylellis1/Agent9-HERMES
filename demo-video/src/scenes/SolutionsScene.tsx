import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer, SectionTitle, AnimatedCard, LogoWatermark } from '../shared/components';
import { COLORS } from '../shared/constants';

/**
 * Scene 6: Solution Finder — MBB-caliber multi-perspective debate + market context
 *
 * Visual sequence:
 * 0-3s:   Title: "The Strategy Council" with MBB framing subtitle
 * 3-12s:  Three persona cards appear (Operations, Financial, Strategic)
 * 12-16s: Market context overlay — competitor & market signals from MA agent
 * 16-22s: Cards show competing recommendations with visible disagreement
 * 22-27s: Synthesis card materializes — unified recommendation with trade-offs
 * 27-30s: Transition
 */
export const SolutionsScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const personas = [
    {
      name: 'Operations Perspective',
      firmStyle: 'Supply chain & process optimization',
      color: '#3b82f6',
      recommendation: 'Renegotiate supplier contracts for SE/MW raw materials. Switch to regional suppliers with shorter lead times.',
      impact: '+2.8pp margin recovery',
      timeline: '60 days',
      risk: 'Supply continuity during transition',
    },
    {
      name: 'Financial Perspective',
      firmStyle: 'Pricing strategy & P&L restructuring',
      color: '#10b981',
      recommendation: 'Implement tiered pricing for industrial accounts. Premium tier absorbs cost increase; standard tier holds.',
      impact: '+3.5pp margin recovery',
      timeline: '30 days',
      risk: 'Customer churn on premium tier',
    },
    {
      name: 'Strategic Perspective',
      firmStyle: 'Value proposition & market positioning',
      color: '#8b5cf6',
      recommendation: 'Bundle Premium Synthetics with maintenance contracts. Shifts value perception from price to total cost of ownership.',
      impact: '+4.1pp effective margin',
      timeline: '90 days',
      risk: 'Requires sales team retraining',
    },
  ];

  // Market context overlay at 12s
  const marketOpacity = interpolate(frame, [fps * 12, fps * 13], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Synthesis appears at 22s
  const synthOpacity = interpolate(frame, [fps * 22, fps * 23], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer className="p-16 relative">
      <SectionTitle subtitle="Three AI perspectives — each applying the analytical frameworks used by top-tier strategy firms — analyze independently, then debate. Disagreement is visible, not hidden.">
        The Strategy Council
      </SectionTitle>

      {/* Three persona cards */}
      <div className="flex gap-5 mt-8">
        {personas.map((persona, i) => {
          const start = fps * (3.5 + i * 2.5);
          return (
            <AnimatedCard key={persona.name} delay={start} className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: persona.color }}
                />
                <span className="text-lg font-bold" style={{ color: persona.color }}>
                  {persona.name}
                </span>
              </div>
              <p className="text-sm mb-3 italic" style={{ color: COLORS.muted }}>
                {persona.firmStyle}
              </p>
              <p className="text-base leading-relaxed" style={{ color: COLORS.textSecondary }}>
                {persona.recommendation}
              </p>
              <div className="mt-4 pt-3 border-t space-y-1" style={{ borderColor: COLORS.border }}>
                <div className="flex justify-between text-sm">
                  <span style={{ color: COLORS.muted }}>Expected Impact</span>
                  <span className="font-semibold" style={{ color: COLORS.emerald }}>{persona.impact}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span style={{ color: COLORS.muted }}>Timeline</span>
                  <span style={{ color: COLORS.text }}>{persona.timeline}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span style={{ color: COLORS.muted }}>Key Risk</span>
                  <span style={{ color: COLORS.amber }}>{persona.risk}</span>
                </div>
              </div>
            </AnimatedCard>
          );
        })}
      </div>

      {/* Market Context — enriched by Market Analysis agent */}
      <div
        className="mt-4 flex gap-3 items-start"
        style={{ opacity: marketOpacity }}
      >
        <div
          className="rounded-xl border p-4 flex-1"
          style={{ backgroundColor: COLORS.surface, borderColor: COLORS.border }}
        >
          <div className="flex items-center gap-2 mb-2">
            <div
              className="w-5 h-5 rounded-md flex items-center justify-center"
              style={{ backgroundColor: `${COLORS.blue}20` }}
            >
              <span className="text-sm" style={{ color: COLORS.blue }}>MA</span>
            </div>
            <span className="text-base font-bold" style={{ color: COLORS.blue }}>
              Market Intelligence
            </span>
            <span className="text-sm ml-auto" style={{ color: COLORS.muted }}>
              Sources: Perplexity web search + Claude synthesis
            </span>
          </div>
          <div className="flex gap-8">
            <div className="text-sm" style={{ color: COLORS.textSecondary }}>
              <span className="font-semibold" style={{ color: COLORS.amber }}>Competitor:</span>{' '}
              ChemCorp launched economy-tier synthetic in SE — 15% undercut on price
            </div>
            <div className="text-sm" style={{ color: COLORS.textSecondary }}>
              <span className="font-semibold" style={{ color: COLORS.amber }}>Market:</span>{' '}
              Raw material index forecast to plateau Q4 — cost pressure temporary
            </div>
            <div className="text-sm" style={{ color: COLORS.textSecondary }}>
              <span className="font-semibold" style={{ color: COLORS.amber }}>Signal:</span>{' '}
              3 of 5 industry peers pursuing value-bundling strategy
            </div>
          </div>
        </div>
      </div>

      {/* Synthesis */}
      <div className="mt-6 max-w-4xl" style={{ opacity: synthOpacity }}>
        <AnimatedCard delay={fps * 22}>
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-white"
              style={{ backgroundColor: COLORS.accent }}>
              ∑
            </div>
            <span className="text-2xl font-bold" style={{ color: COLORS.accentLight }}>
              Synthesized Recommendation
            </span>
            <span className="text-sm ml-2 px-2 py-0.5 rounded-full" style={{ backgroundColor: `${COLORS.blue}20`, color: COLORS.blue }}>
              Market-enriched
            </span>
          </div>
          <p className="text-base leading-relaxed" style={{ color: COLORS.textSecondary }}>
            <strong style={{ color: COLORS.text }}>Phase 1 (30 days):</strong> Implement tiered pricing for industrial accounts.{' '}
            <strong style={{ color: COLORS.text }}>Phase 2 (60 days):</strong> Parallel supplier renegotiation for raw materials.{' '}
            <strong style={{ color: COLORS.text }}>Phase 3 (90 days):</strong> Pilot bundled maintenance contracts in SE region.
          </p>
          <p className="text-sm mt-2 italic" style={{ color: COLORS.muted }}>
            Note: Bundling strategy aligns with industry trend (3/5 peers). Cost pressure likely temporary per raw material forecast — aggressive supplier renegotiation may yield short-term leverage.
          </p>
          <div className="flex gap-6 mt-4 pt-3 border-t" style={{ borderColor: COLORS.border }}>
            <div className="text-center">
              <p className="text-2xl font-bold" style={{ color: COLORS.emerald }}>+3.8pp</p>
              <p className="text-sm" style={{ color: COLORS.muted }}>Expected Recovery</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold" style={{ color: COLORS.text }}>90 days</p>
              <p className="text-sm" style={{ color: COLORS.muted }}>Measurement Window</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold" style={{ color: COLORS.amber }}>Medium</p>
              <p className="text-sm" style={{ color: COLORS.muted }}>Overall Risk</p>
            </div>
          </div>
        </AnimatedCard>
      </div>

      <LogoWatermark />
    </SceneContainer>
  );
};
