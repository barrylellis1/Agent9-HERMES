import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer, LogoWatermark } from '../shared/components';
import { COLORS } from '../shared/constants';

/**
 * Scene 7: Executive Decision Briefing + HITL Approval
 *
 * Page-flip approach: each briefing section fades in/out in the same viewport area.
 * Persistent header stays on top; page counter tracks progress.
 *
 * Pages (each ~3s visible):
 * 0-3s:   Header + urgency metrics (stays visible)
 * 3-6s:   Page 1: Executive Summary
 * 6-9s:   Page 2: Situation Analysis + Root Cause
 * 9-12s:  Page 3: Key Question + Assumptions
 * 12-15s: Page 4: Market Intelligence
 * 15-18s: Page 5: Independent Firm Proposals
 * 18-21s: Page 6: Strategic Options Table
 * 21-24s: Page 7: Recommended Option
 * 24-27s: Page 8: Implementation Roadmap + Risk
 * 27-30s: Dim document → Approval overlay
 * 30-33s: Click → Confirmation
 * 33-35s: Decision registered details
 */
export const ApprovalScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Header fade-in
  const headerOpacity = interpolate(frame, [0, fps * 0.5], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  // Page visibility helper: fade in over 0.4s, hold, fade out over 0.4s
  const pageOpacity = (startSec: number, endSec: number) => {
    const fadeIn = interpolate(frame, [fps * startSec, fps * (startSec + 0.4)], [0, 1], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    });
    const fadeOut = interpolate(frame, [fps * (endSec - 0.4), fps * endSec], [1, 0], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
    });
    return Math.min(fadeIn, fadeOut);
  };

  // Current page number for counter
  const pageNum =
    frame < fps * 3 ? 0 :
    frame < fps * 6 ? 1 :
    frame < fps * 9 ? 2 :
    frame < fps * 12 ? 3 :
    frame < fps * 15 ? 4 :
    frame < fps * 18 ? 5 :
    frame < fps * 21 ? 6 :
    frame < fps * 24 ? 7 :
    frame < fps * 27 ? 8 : 8;

  // Approval overlay
  const approvalOverlay = interpolate(frame, [fps * 28, fps * 29], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  const isClicked = frame > fps * 31;
  const confirmOpacity = interpolate(frame, [fps * 32, fps * 33], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
  });

  return (
    <SceneContainer className="relative overflow-hidden">
      {/* ===== PERSISTENT HEADER ===== */}
      <div
        className="absolute top-0 left-0 right-0 z-10 px-12 pt-6 pb-4"
        style={{ opacity: headerOpacity, backgroundColor: COLORS.bg }}
      >
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm uppercase tracking-widest font-semibold" style={{ color: COLORS.muted }}>
              Executive Decision Briefing
            </p>
            <h2 className="text-2xl font-bold mt-1 leading-tight" style={{ color: COLORS.text }}>
              Summit Lubricants — Base Oil & Additives Cost +26.9%
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <div
              className="px-3 py-1 rounded-full text-sm font-bold"
              style={{ backgroundColor: `${COLORS.red}20`, color: COLORS.red }}
            >
              CRITICAL
            </div>
            <div className="text-right">
              <p className="text-sm" style={{ color: COLORS.muted }}>Prepared by Agent9 Decision Studio</p>
              <p className="text-sm" style={{ color: COLORS.muted }}>March 17, 2026</p>
            </div>
          </div>
        </div>

        {/* 4 urgency metrics bar */}
        <div className="grid grid-cols-4 gap-6 mt-4 pt-3 border-t" style={{ borderColor: COLORS.border }}>
          {[
            { label: 'FINANCIAL IMPACT', value: '+26.9% vs baseline', color: COLORS.red },
            { label: 'TIME SENSITIVITY', value: 'Immediate (24-48 hrs)', color: COLORS.amber },
            { label: 'CONFIDENCE LEVEL', value: 'Very High', color: COLORS.emerald },
            { label: 'DECISION REQUIRED BY', value: 'End of Day', color: COLORS.text },
          ].map((m) => (
            <div key={m.label}>
              <p className="text-xs uppercase tracking-wider" style={{ color: COLORS.muted }}>{m.label}</p>
              <p className="text-base font-bold mt-0.5" style={{ color: m.color }}>{m.value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ===== PAGE COUNTER ===== */}
      {pageNum > 0 && frame < fps * 28 && (
        <div className="absolute bottom-8 left-12 z-10 flex items-center gap-2">
          <div className="flex gap-1">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full"
                style={{
                  backgroundColor: i < pageNum ? COLORS.accent : COLORS.border,
                  opacity: i === pageNum - 1 ? 1 : 0.5,
                }}
              />
            ))}
          </div>
          <span className="text-sm ml-2" style={{ color: COLORS.muted }}>
            Section {pageNum} of 8 · 19 pages
          </span>
        </div>
      )}

      {/* ===== CONTENT AREA (below header, same position for all pages) ===== */}
      <div className="absolute top-[180px] left-12 right-12 bottom-16">

        {/* PAGE 1: Executive Summary */}
        <div className="absolute inset-0" style={{ opacity: pageOpacity(3, 6) }}>
          <SectionHeader number="1" title="Executive Summary" />
          <div className="mt-4 border-l-2 pl-5 max-w-4xl" style={{ borderColor: COLORS.accent }}>
            <p className="text-base leading-relaxed" style={{ color: COLORS.textSecondary }}>
              Summit Lubricants & Specialty Products' Base Oil & Additives Cost has increased
              26.9% versus baseline, breaching the red threshold and directly threatening the
              strategic priority of improving gross margin from 38% to 42%.
            </p>
            <p className="text-sm leading-relaxed mt-3" style={{ color: COLORS.textSecondary }}>
              The overall cost increase is concentrated in two specific drivers:
              <strong style={{ color: COLORS.text }}> Synthetic Blend Engine Oil (+$1,882,789)</strong> and the
              <strong style={{ color: COLORS.text }}> Service Centers Division (+$2,004,041)</strong>,
              which together account for 93.9% of the total variance. Meanwhile,
              Commercial & Industrial Division (-$9.3M), Retail Products Division (-$4.8M),
              and National Auto Parts Chain A (-$12.1M) are outperforming.
            </p>
            <p className="text-base font-semibold mt-4" style={{ color: COLORS.text }}>
              Recommended Action: Emergency Spot-to-Contract Conversion — Renegotiate
              Synthetic Blend Engine Oil Base Oil Supply Terms Within 90 Days
            </p>
          </div>
        </div>

        {/* PAGE 2: Situation Analysis */}
        <div className="absolute inset-0" style={{ opacity: pageOpacity(6, 9) }}>
          <SectionHeader number="2" title="Situation Analysis" />
          <div className="mt-4 grid grid-cols-2 gap-5 max-w-4xl">
            <div className="rounded-xl border p-5" style={{ backgroundColor: COLORS.surface, borderColor: COLORS.border }}>
              <p className="text-sm font-semibold mb-2" style={{ color: COLORS.muted }}>Current State</p>
              <p className="text-base" style={{ color: COLORS.textSecondary }}>
                Base Oil & Additives Cost increased by 26.9% vs baseline
              </p>
            </div>
            <div className="rounded-xl border p-5" style={{ backgroundColor: COLORS.surface, borderColor: COLORS.border }}>
              <p className="text-sm font-semibold mb-2" style={{ color: COLORS.amber }}>The Problem</p>
              <p className="text-base" style={{ color: COLORS.textSecondary }}>
                Concentrated in Synthetic Blend Engine Oil (+$1.88M) and Service Centers Division (+$2.0M) — 93.9% of total variance
              </p>
            </div>
          </div>
          <div className="mt-5 max-w-4xl">
            <p className="text-sm font-semibold mb-3" style={{ color: COLORS.muted }}>Root Cause Analysis (Data-Driven)</p>
            {[
              { rank: '1', name: 'Service Centers Division', current: '+27.1M', prior: '+25.1M', delta: '+2.0M' },
              { rank: '2', name: 'Synthetic Blend Engine Oil', current: '+19.1M', prior: '+17.2M', delta: '+1.9M' },
              { rank: '3', name: 'Automatic Transmission Fluid', current: '+7.9M', prior: '+7.8M', delta: '+121.3K' },
            ].map((d) => (
              <div key={d.rank} className="flex items-center gap-4 mb-2 py-2 px-3 rounded-lg" style={{ backgroundColor: COLORS.surface }}>
                <span className="text-lg font-bold w-6" style={{ color: COLORS.accent }}>{d.rank}</span>
                <span className="text-base flex-1 font-medium" style={{ color: COLORS.text }}>{d.name}</span>
                <span className="text-sm" style={{ color: COLORS.muted }}>
                  Current: {d.current} | Prior: {d.prior}
                </span>
                <span className="text-base font-bold" style={{ color: COLORS.red }}>Δ {d.delta}</span>
              </div>
            ))}
          </div>
        </div>

        {/* PAGE 3: Key Question + Assumptions */}
        <div className="absolute inset-0" style={{ opacity: pageOpacity(9, 12) }}>
          <div className="max-w-4xl">
            <div className="border-l-2 pl-5 mb-6" style={{ borderColor: COLORS.accent }}>
              <p className="text-sm font-semibold uppercase tracking-wider" style={{ color: COLORS.accentLight }}>Key Question</p>
              <p className="text-xl italic mt-2 leading-relaxed" style={{ color: COLORS.textSecondary }}>
                What is the fastest, most capital-efficient operational intervention to reverse the $1.88M
                Synthetic Blend Engine Oil cost overrun in Service Centers Division — and how should Summit
                structure its procurement and pricing posture to prevent recurrence?
              </p>
            </div>
            <div className="rounded-xl border p-5" style={{ backgroundColor: COLORS.surface, borderColor: COLORS.border }}>
              <p className="text-sm font-semibold mb-3" style={{ color: COLORS.muted }}>Key Assumptions</p>
              {[
                'Sourcing flexibility exists for Synthetic Blend Engine Oil base oil inputs — no major supply constraints per principal input',
                'The $1.88M delta is primarily attributable to unhedged spot-market exposure, not volume growth alone',
                'Commercial & Industrial and Retail divisions\' outperformance reflects existing hedging or contract structures that can serve as internal benchmarks',
                'Full reversal to baseline (26.9% reduction) is the stated target, not partial mitigation',
                'ATF ($121K delta) is explicitly out of scope per principal direction',
              ].map((a, i) => (
                <p key={i} className="text-sm mb-1.5" style={{ color: COLORS.textSecondary }}>
                  • {a}
                </p>
              ))}
            </div>
          </div>
        </div>

        {/* PAGE 4: Market Intelligence */}
        <div className="absolute inset-0" style={{ opacity: pageOpacity(12, 15) }}>
          <SectionHeader number="" title="Market Intelligence" />
          <p className="text-sm mt-1 mb-4" style={{ color: COLORS.muted }}>
            External signals collected at the time of analysis that provide market and competitive context.
          </p>
          <div className="space-y-3 max-w-4xl">
            {[
              { title: 'Crude Oil Price Volatility Drives Base Oil Feedstock Costs Up 15-25%', relevance: '93%', detail: 'Brent crude $75-$95/barrel; API Group II base oils up 18-22% YoY in key trading hubs.' },
              { title: 'Specialty Additive Supply Constraints from Chemical Sector Tightness', relevance: '91%', detail: 'ZDDP, viscosity improvers, detergent packages up 10-15%; lead times extended to 8-12 weeks.' },
              { title: 'Asia-Pacific Base Oil Capacity Additions Reshaping Global Trade Flows', relevance: '82%', detail: 'New Group II/III capacity in Korea, Middle East, China creating 12% regional price divergences.' },
              { title: 'Regulatory-Driven Formulation Upgrades Increasing Additive Demand', relevance: '87%', detail: 'ILSAC GF-7 and API SN Plus requirements raising bill-of-materials costs 8-12%.' },
            ].map((m) => (
              <div key={m.title} className="rounded-xl border p-4 flex items-start justify-between gap-4" style={{ backgroundColor: COLORS.surface, borderColor: COLORS.border }}>
                <div className="flex-1">
                  <p className="text-base font-semibold" style={{ color: COLORS.text }}>{m.title}</p>
                  <p className="text-sm mt-1" style={{ color: COLORS.textSecondary }}>{m.detail}</p>
                </div>
                <span className="text-sm font-bold whitespace-nowrap" style={{ color: COLORS.amber }}>{m.relevance} relevant</span>
              </div>
            ))}
          </div>
        </div>

        {/* PAGE 5: Stage 1 — Independent Firm Proposals */}
        <div className="absolute inset-0" style={{ opacity: pageOpacity(15, 18) }}>
          <SectionHeader number="1" title="Stage 1: Independent Firm Proposals" />
          <p className="text-sm mt-1 mb-4" style={{ color: COLORS.muted }}>
            Each consulting firm independently analyzed the problem and proposed an intervention using their signature framework.
          </p>
          <div className="grid grid-cols-2 gap-4 max-w-5xl">
            {[
              { firm: 'Bain & Company', framework: 'Net Promoter System + Full Potential Transformation', subtitle: 'Hedging & SKU Mix Optimization' },
              { firm: 'Deloitte', framework: 'Digital Maturity Model + Procurement Operations Optimization', subtitle: 'Procurement visibility & controls' },
              { firm: 'Accenture', framework: 'Industry X.0 Supply Chain Exposure & Hedging Maturity', subtitle: 'Dynamic hedging triggers' },
              { firm: 'KPMG', framework: 'Connected Enterprise Risk & Controls Assessment', subtitle: 'Audit-ready governance' },
            ].map((f) => (
              <div key={f.firm} className="rounded-xl border p-4" style={{ backgroundColor: COLORS.surface, borderColor: COLORS.border }}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-base font-bold" style={{ color: COLORS.text }}>{f.firm}</span>
                  <span className="text-sm font-semibold" style={{ color: COLORS.emerald }}>High Conviction</span>
                </div>
                <p className="text-sm italic" style={{ color: COLORS.accentLight }}>{f.framework}</p>
                <p className="text-sm mt-1" style={{ color: COLORS.textSecondary }}>{f.subtitle}</p>
                <div className="flex items-center gap-1.5 mt-3 pt-2 border-t" style={{ borderColor: COLORS.border }}>
                  <div className="w-1 h-3 rounded-full" style={{ backgroundColor: COLORS.red }} />
                  <p className="text-sm font-medium" style={{ color: COLORS.muted }}>Primary Focus: Synthetic Blend Engine Oil</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* PAGE 6: Strategic Options Comparison Table */}
        <div className="absolute inset-0" style={{ opacity: pageOpacity(18, 21) }}>
          <SectionHeader number="3" title="Strategic Options" />
          <p className="text-sm mt-1 mb-4" style={{ color: COLORS.muted }}>
            Three pathways evaluated against financial impact, complexity, risk, and alignment with stated priorities.
          </p>
          <div className="rounded-xl border overflow-hidden max-w-5xl" style={{ borderColor: COLORS.border }}>
            <table className="w-full text-sm">
              <thead>
                <tr style={{ backgroundColor: COLORS.surface }}>
                  <th className="text-left p-3 font-semibold" style={{ color: COLORS.muted }}>Criteria</th>
                  <th className="text-left p-3 font-semibold" style={{ color: COLORS.emerald }}>
                    Option A (Recommended)
                  </th>
                  <th className="text-left p-3 font-semibold" style={{ color: COLORS.text }}>Option B</th>
                  <th className="text-left p-3 font-semibold" style={{ color: COLORS.text }}>Option C</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { criteria: 'Strategy', a: 'Emergency Spot-to-Contract Conversion', b: 'Structural Commodity Hedging Program', c: 'Strategic Product Mix Rebalancing' },
                  { criteria: 'Est. ROI', a: '+$940K to +$1.6M', b: '+$1.3M to +$1.9M', c: '+$500K to +$1.1M', roiRow: true },
                  { criteria: 'Investment', a: 'Low Effort', b: 'Moderate Effort', c: 'High Effort' },
                  { criteria: 'Timeline', a: '30-90 days', b: '3-6 months', c: '12-24 months' },
                  { criteria: 'Risk Level', a: 'Low', b: 'Medium', c: 'High', riskRow: true },
                  { criteria: 'Reversibility', a: 'High', b: 'Medium', c: 'Low' },
                ].map((row) => (
                  <tr key={row.criteria} style={{ borderTop: `1px solid ${COLORS.border}` }}>
                    <td className="p-3 font-semibold" style={{ color: COLORS.muted, backgroundColor: COLORS.card }}>{row.criteria}</td>
                    <td className="p-3" style={{
                      color: 'roiRow' in row ? COLORS.emerald : 'riskRow' in row ? COLORS.emerald : COLORS.textSecondary,
                      backgroundColor: COLORS.card,
                    }}>{row.a}</td>
                    <td className="p-3" style={{
                      color: 'roiRow' in row ? COLORS.emerald : 'riskRow' in row ? COLORS.amber : COLORS.textSecondary,
                      backgroundColor: COLORS.card,
                    }}>{row.b}</td>
                    <td className="p-3" style={{
                      color: 'roiRow' in row ? COLORS.emerald : 'riskRow' in row ? COLORS.red : COLORS.textSecondary,
                      backgroundColor: COLORS.card,
                    }}>{row.c}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* PAGE 7: Recommended Option Detail */}
        <div className="absolute inset-0" style={{ opacity: pageOpacity(21, 24) }}>
          <div
            className="rounded-xl border-2 p-6 max-w-4xl"
            style={{ borderColor: COLORS.emerald, backgroundColor: COLORS.card }}
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm uppercase font-semibold" style={{ color: COLORS.emerald }}>Recommended Option</p>
                <p className="text-xl font-bold mt-1" style={{ color: COLORS.text }}>
                  Option A: Emergency Spot-to-Contract Conversion
                </p>
                <p className="text-sm" style={{ color: COLORS.muted }}>
                  Renegotiate Synthetic Blend Engine Oil Base Oil Supply Terms Within 90 Days
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm" style={{ color: COLORS.muted }}>Est. ROI</p>
                <p className="text-3xl font-bold" style={{ color: COLORS.emerald }}>+$940K</p>
                <p className="text-lg font-bold" style={{ color: COLORS.emerald }}>to +$1.6M</p>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4 mb-5 pt-4 border-t" style={{ borderColor: COLORS.border }}>
              {[
                { label: 'INVESTMENT', value: 'Low Effort', color: COLORS.text },
                { label: 'TIMELINE', value: '30-90 days', color: COLORS.text },
                { label: 'RISK LEVEL', value: 'Low', color: COLORS.emerald },
                { label: 'REVERSIBILITY', value: 'High', color: COLORS.emerald },
              ].map((m) => (
                <div key={m.label} className="text-center">
                  <p className="text-sm uppercase tracking-wider" style={{ color: COLORS.muted }}>{m.label}</p>
                  <p className="text-base font-bold mt-1" style={{ color: m.color }}>{m.value}</p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className="text-sm font-semibold mb-2" style={{ color: COLORS.emerald }}>Arguments For</p>
                <p className="text-sm leading-relaxed" style={{ color: COLORS.textSecondary }}>
                  Directly targets the $1,882,789 cost driver — the single SKU responsible for 93.9%
                  of the overrun — with no capital expenditure required. Internal benchmark from C&I
                  Division's -$9.3M outperformance confirms contract-based procurement works.
                </p>
              </div>
              <div>
                <p className="text-sm font-semibold mb-2" style={{ color: COLORS.amber }}>Arguments Against</p>
                <p className="text-sm leading-relaxed" style={{ color: COLORS.textSecondary }}>
                  Fixed-price contracts during a potentially peaking commodity cycle could create
                  downside exposure if base oil prices decline below the contracted rate. Volume
                  commitments may constrain future mix-shift flexibility.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* PAGE 8: Implementation Roadmap + Risk */}
        <div className="absolute inset-0" style={{ opacity: pageOpacity(24, 27) }}>
          <div className="grid grid-cols-2 gap-6 max-w-5xl">
            {/* Left: Roadmap */}
            <div>
              <SectionHeader number="4" title="Implementation Roadmap" />
              <div className="mt-4 space-y-4">
                {[
                  { phase: 'Phase 1: Prerequisites', time: 'Week 1-2', items: ['SKU-level cost breakdown (Finance)', 'Spot vs contract audit (Procurement)', 'C&I contract terms as benchmark (Legal)'] },
                  { phase: 'Phase 2: Implementation', time: 'Week 3-8', items: ['Execute spot-to-contract conversion', 'Brief stakeholders & assign owners', 'Week 4 checkpoint: early actuals vs expected'] },
                  { phase: 'Phase 3: Monitor & Adjust', time: 'Ongoing', items: ['Weekly cost recovery tracking', 'Monthly executive review', '90-day: assess secondary option'] },
                ].map((p, i) => (
                  <div key={p.phase} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div
                        className="w-6 h-6 rounded-full border-2 flex items-center justify-center text-sm font-bold"
                        style={{ borderColor: COLORS.accent, color: COLORS.accent }}
                      >
                        {i + 1}
                      </div>
                      {i < 2 && <div className="w-px flex-1 mt-1" style={{ backgroundColor: COLORS.border }} />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-bold" style={{ color: COLORS.text }}>{p.phase}</p>
                        <span className="text-sm" style={{ color: COLORS.muted }}>{p.time}</span>
                      </div>
                      {p.items.map((item) => (
                        <p key={item} className="text-sm mt-0.5" style={{ color: COLORS.textSecondary }}>• {item}</p>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: Risk Analysis */}
            <div>
              <SectionHeader number="5" title="Risk Analysis" />
              <div className="mt-4 space-y-2">
                {[
                  { risk: 'Volume vs price decomposition unresolved', likelihood: 'High', impact: 'High' },
                  { risk: 'C&I contract terms unknown — negotiators lack benchmark', likelihood: 'High', impact: 'High' },
                  { risk: 'Competitor hedging posture unknown', likelihood: 'Medium', impact: 'Medium' },
                  { risk: 'Volume growth contribution unquantified', likelihood: 'Medium', impact: 'Medium' },
                ].map((r) => (
                  <div key={r.risk} className="rounded-lg border p-3" style={{ backgroundColor: COLORS.surface, borderColor: COLORS.border }}>
                    <p className="text-sm" style={{ color: COLORS.textSecondary }}>{r.risk}</p>
                    <div className="flex gap-4 mt-1">
                      <span className="text-sm" style={{ color: COLORS.muted }}>
                        Likelihood: <span style={{ color: r.likelihood === 'High' ? COLORS.red : COLORS.amber, fontWeight: 600 }}>{r.likelihood}</span>
                      </span>
                      <span className="text-sm" style={{ color: COLORS.muted }}>
                        Impact: <span style={{ color: r.impact === 'High' ? COLORS.red : COLORS.amber, fontWeight: 600 }}>{r.impact}</span>
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ===== APPROVAL OVERLAY ===== */}
      {frame > fps * 27 && (
        <div
          className="absolute inset-0 flex items-center justify-center z-20"
          style={{
            opacity: approvalOverlay,
            backgroundColor: `${COLORS.bg}ee`,
          }}
        >
          <div className="flex flex-col items-center gap-6">
            {!isClicked ? (
              <>
                <p className="text-3xl font-bold" style={{ color: COLORS.text }}>
                  Ready to proceed?
                </p>
                <p className="text-lg" style={{ color: COLORS.muted }}>
                  19-page briefing reviewed. Three options evaluated. One recommendation.
                </p>
                <div className="flex gap-4 mt-4">
                  <div
                    className="px-10 py-5 rounded-xl text-xl font-semibold text-white"
                    style={{ backgroundColor: COLORS.accent }}
                  >
                    Approve & Track
                  </div>
                  <div
                    className="px-10 py-5 rounded-xl text-xl font-semibold border"
                    style={{ borderColor: COLORS.border, color: COLORS.textSecondary, opacity: 0.5 }}
                  >
                    Request Changes
                  </div>
                </div>
              </>
            ) : (
              <div style={{ opacity: confirmOpacity }}>
                <div className="flex flex-col items-center gap-5">
                  <div
                    className="w-20 h-20 rounded-full flex items-center justify-center text-4xl"
                    style={{ backgroundColor: `${COLORS.emerald}20`, color: COLORS.emerald }}
                  >
                    ✓
                  </div>
                  <p className="text-3xl font-bold" style={{ color: COLORS.text }}>
                    Decision Registered
                  </p>
                  <p className="text-lg" style={{ color: COLORS.muted }}>
                    Value Assurance tracking begins. Actual vs. expected trajectory updated monthly.
                  </p>
                  <div className="flex gap-10 mt-4">
                    {[
                      { label: 'Solution', value: 'Option A: Spot-to-Contract', color: COLORS.text },
                      { label: 'Expected Recovery', value: '+$940K to +$1.6M', color: COLORS.emerald },
                      { label: 'Measurement Window', value: '90 days', color: COLORS.text },
                      { label: 'Decision Owner', value: 'Sarah Chen, CFO', color: COLORS.accentLight },
                    ].map((m) => (
                      <div key={m.label} className="text-center">
                        <p className="text-sm" style={{ color: COLORS.muted }}>{m.label}</p>
                        <p className="text-base font-bold mt-1" style={{ color: m.color }}>{m.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <LogoWatermark />
    </SceneContainer>
  );
};

/** Section header matching the briefing's numbered section style. */
const SectionHeader: React.FC<{ number: string; title: string }> = ({ number, title }) => (
  <div className="flex items-center gap-2">
    {number && <span className="text-2xl font-bold" style={{ color: COLORS.accent }}>{number}</span>}
    <h3 className="text-2xl font-bold" style={{ color: COLORS.text }}>{title}</h3>
  </div>
);
