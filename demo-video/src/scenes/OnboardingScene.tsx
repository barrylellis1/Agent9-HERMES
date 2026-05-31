import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';
import { SceneContainer, SectionTitle, LogoWatermark } from '../shared/components';
import { COLORS } from '../shared/constants';

/**
 * Scene 9: KPI Accountability Onboarding
 *
 * Replaces the generic "Live in 5 Days" timeline with a live demo of the
 * Phase 11B accountability interview — an admin-led AI session that maps
 * every KPI to an accountable owner before the first assessment runs.
 *
 * Visual sequence:
 * 0-2s:   Title: "Map Every KPI to an Owner"
 * 2-3s:   Left panel fades in — Admin Console interview header
 * 3-4.5s: AI opening message about David Torres (CEO) + domain chips appear
 * 5-5.5s: "Strategy" and "Operations" chips highlight (selected)
 * 6-7s:   Admin bubble: "Strategy and Operations" + AI proposes 5 KPIs
 * 7-10s:  Right panel: CEO rows fill in one by one, coverage 0% → 33%
 * 10-13s: Time compression — 3 more principals, rows race in, bar fills to 100%
 * 13-14s: "Confirm Assignments" button appears
 * 14.5s:  Confirmed → success state
 * 15-17s: "Value Assurance tracking enabled for all KPIs"
 * 17-18s: Closing line
 */
export const OnboardingScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Interpolation helper: seconds → output value
  const fi = (start: number, end: number, from: number, to: number) =>
    interpolate(frame, [fps * start, fps * end], [from, to], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });

  // Coverage animation: fills in two stages
  //   CEO (5 KPIs): 7s → 10s → 0% → 33%
  //   Remaining 10 KPIs: 10s → 12.5s → 33% → 100%
  const coveragePct = frame < fps * 10
    ? fi(7, 10, 0, 33)
    : fi(10, 12.5, 33, 100);

  // Per-row opacity — each row slides in sequentially
  const rowOpacity = (index: number): number => {
    if (index < 5)  return fi(7 + index * 0.5,        7.3 + index * 0.5,        0, 1);
    if (index < 10) return fi(10 + (index - 5) * 0.4, 10.3 + (index - 5) * 0.4, 0, 1);
    if (index < 13) return fi(11 + (index - 10) * 0.4, 11.3 + (index - 10) * 0.4, 0, 1);
    return              fi(11.5 + (index - 13) * 0.5, 11.8 + (index - 13) * 0.5, 0, 1);
  };

  // Derived: how many rows are visible right now
  const TOTAL_KPIS = 15;
  const assignedCount = Array.from({ length: TOTAL_KPIS }, (_, i) => i)
    .filter(i => rowOpacity(i) > 0.05).length;

  // Chip selection timing
  const strategySelected   = frame > fps * 5;
  const operationsSelected = frame > fps * 5.4;

  // Confirm / success
  const confirmVisible = fi(13, 13.5, 0, 1);
  const isConfirmed    = frame > fps * 14.5;
  const successOpacity = fi(14.5, 15.1, 0, 1);
  const closingOpacity = fi(17, 17.5, 0, 1);
  const timeCompressOpacity = fi(9.5, 10, 0, 1);

  // Assignment data — 15 lubricants KPIs, 4 principals
  const assignments = [
    { kpi: 'Net Revenue Growth',        principal: 'D. Torres', role: 'CEO',        color: COLORS.accent  },
    { kpi: 'Market Share %',            principal: 'D. Torres', role: 'CEO',        color: COLORS.accent  },
    { kpi: 'Customer Retention Rate',   principal: 'D. Torres', role: 'CEO',        color: COLORS.accent  },
    { kpi: 'On-Time Delivery Rate',     principal: 'D. Torres', role: 'CEO',        color: COLORS.accent  },
    { kpi: 'Strategic Initiative ROI',  principal: 'D. Torres', role: 'CEO',        color: COLORS.accent  },
    { kpi: 'Gross Margin %',            principal: 'S. Chen',   role: 'CFO',        color: COLORS.emerald },
    { kpi: 'EBITDA Margin',             principal: 'S. Chen',   role: 'CFO',        color: COLORS.emerald },
    { kpi: 'Base Oil & Additives Cost', principal: 'S. Chen',   role: 'CFO',        color: COLORS.emerald },
    { kpi: 'Days Sales Outstanding',    principal: 'S. Chen',   role: 'CFO',        color: COLORS.emerald },
    { kpi: 'Budget Variance',           principal: 'S. Chen',   role: 'CFO',        color: COLORS.emerald },
    { kpi: 'Order Fill Rate',           principal: 'R. Kim',    role: 'COO',        color: COLORS.blue    },
    { kpi: 'Manufacturing Yield',       principal: 'R. Kim',    role: 'COO',        color: COLORS.blue    },
    { kpi: 'Cost Per Unit Produced',    principal: 'R. Kim',    role: 'COO',        color: COLORS.blue    },
    { kpi: 'Accounts Receivable Aging', principal: 'M. Webb',   role: 'Finance Mgr', color: COLORS.amber  },
    { kpi: 'Cash Conversion Cycle',     principal: 'M. Webb',   role: 'Finance Mgr', color: COLORS.amber  },
  ];

  const domains = ['Finance', 'Strategy', 'Operations', 'Pricing', 'Sales', 'Product'];

  // ── Panel shared styles ───────────────────────────────────────────────────
  const panelStyle: React.CSSProperties = {
    borderRadius: '14px',
    border: `1px solid ${COLORS.border}`,
    backgroundColor: COLORS.surface,
  };

  const chipStyle = (isSelected: boolean): React.CSSProperties => ({
    borderRadius: '999px',
    border: `1px solid ${isSelected ? COLORS.accent : COLORS.border}`,
    backgroundColor: isSelected ? `${COLORS.accent}28` : COLORS.surface,
    color: isSelected ? COLORS.accentLight : COLORS.textSecondary,
    padding: '5px 14px',
    fontSize: '13px',
    fontWeight: isSelected ? 600 : 400,
  });

  const agentBubbleStyle: React.CSSProperties = {
    borderRadius: '12px',
    borderTopLeftRadius: '3px',
    border: `1px solid ${COLORS.border}`,
    backgroundColor: COLORS.card,
    padding: '13px 16px',
    maxWidth: '92%',
  };

  return (
    <SceneContainer className="p-16 relative">
      <SectionTitle subtitle="Step 4 of 5 — an AI-guided admin interview maps every KPI to an accountable owner before the first assessment runs.">
        Map Every KPI to an Owner
      </SectionTitle>

      {/* ── Main content: two panels ── */}
      <div
        style={{
          display: 'flex',
          gap: '28px',
          marginTop: '28px',
          height: '600px',
        }}
      >

        {/* ── LEFT: Interview chat ── */}
        <div
          style={{
            width: '46%',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            opacity: fi(1.5, 2, 0, 1),
            transform: `translateY(${fi(1.5, 2, 14, 0)}px)`,
          }}
        >
          <div
            style={{
              ...panelStyle,
              flex: 1,
              padding: '18px 20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
              overflow: 'hidden',
            }}
          >
            {/* Panel header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                paddingBottom: '12px',
                borderBottom: `1px solid ${COLORS.border}`,
              }}
            >
              <div
                style={{
                  width: '26px',
                  height: '26px',
                  borderRadius: '7px',
                  backgroundColor: COLORS.accent,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '12px',
                  fontWeight: 700,
                  color: '#fff',
                  flexShrink: 0,
                }}
              >
                DS
              </div>
              <span style={{ fontSize: '14px', fontWeight: 600, color: COLORS.text }}>
                KPI Accountability Setup
              </span>
              <span
                style={{
                  marginLeft: 'auto',
                  fontSize: '12px',
                  color: COLORS.muted,
                  padding: '2px 10px',
                  borderRadius: '999px',
                  border: `1px solid ${COLORS.border}`,
                }}
              >
                Admin session
              </span>
            </div>

            {/* AI message: domain question */}
            <div
              style={{
                ...agentBubbleStyle,
                opacity: fi(2.5, 3, 0, 1),
                transform: `translateY(${fi(2.5, 3, 10, 0)}px)`,
              }}
            >
              <div style={{ fontSize: '11px', fontWeight: 600, color: COLORS.accentLight, marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Decision Studio
              </div>
              <div style={{ fontSize: '15px', lineHeight: 1.65, color: COLORS.textSecondary }}>
                <strong style={{ color: COLORS.text }}>David Torres</strong> is your CEO.
                Which business domains is he responsible for?
              </div>
            </div>

            {/* Domain chips */}
            <div
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '8px',
                opacity: fi(3.2, 3.7, 0, 1),
              }}
            >
              {domains.map((domain, i) => {
                const isSelected = (domain === 'Strategy' && strategySelected) ||
                                   (domain === 'Operations' && operationsSelected);
                return (
                  <div
                    key={domain}
                    style={{
                      ...chipStyle(isSelected),
                      opacity: fi(3.2 + i * 0.1, 3.5 + i * 0.1, 0, 1),
                    }}
                  >
                    {isSelected ? '✓ ' : ''}{domain}
                  </div>
                );
              })}
            </div>

            {/* Admin response bubble */}
            <div
              style={{
                opacity: fi(6, 6.4, 0, 1),
                transform: `translateY(${fi(6, 6.4, 8, 0)}px)`,
                display: 'flex',
                justifyContent: 'flex-end',
              }}
            >
              <div
                style={{
                  backgroundColor: COLORS.accent,
                  borderRadius: '14px',
                  borderBottomRightRadius: '3px',
                  padding: '10px 16px',
                  maxWidth: '65%',
                }}
              >
                <span style={{ fontSize: '15px', fontWeight: 500, color: '#fff' }}>
                  Strategy and Operations
                </span>
              </div>
            </div>

            {/* AI response: KPI proposal */}
            <div
              style={{
                ...agentBubbleStyle,
                opacity: fi(6.6, 7.1, 0, 1),
                transform: `translateY(${fi(6.6, 7.1, 8, 0)}px)`,
              }}
            >
              <div style={{ fontSize: '11px', fontWeight: 600, color: COLORS.accentLight, marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Decision Studio
              </div>
              <div style={{ fontSize: '15px', lineHeight: 1.65, color: COLORS.textSecondary }}>
                Proposing <strong style={{ color: COLORS.text }}>5 KPIs</strong> for David Torres
                across Strategy and Operations. Three more principals to go.
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginTop: '8px' }}>
                <div style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: COLORS.emerald }} />
                <span style={{ fontSize: '12px', color: COLORS.muted }}>
                  Proposals appear in the coverage panel →
                </span>
              </div>
            </div>
          </div>

          {/* Time compression label */}
          <div style={{ opacity: timeCompressOpacity, textAlign: 'center', padding: '4px 0' }}>
            <span style={{ fontSize: '13px', color: COLORS.muted, fontStyle: 'italic' }}>
              Interview continues for Sarah Chen (CFO) · Rachel Kim (COO) · Marcus Webb (Finance Manager)
            </span>
          </div>
        </div>

        {/* ── RIGHT: Coverage + assignments ── */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            opacity: fi(6.5, 7, 0, 1),
          }}
        >
          {/* Coverage meter */}
          <div style={{ ...panelStyle, padding: '18px 20px', flexShrink: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: COLORS.text }}>KPI Coverage</span>
              <span
                style={{
                  fontSize: '26px',
                  fontWeight: 700,
                  color: coveragePct >= 100 ? COLORS.emerald : COLORS.accentLight,
                }}
              >
                {Math.round(coveragePct)}%
              </span>
            </div>
            <div style={{ width: '100%', height: '7px', borderRadius: '999px', backgroundColor: COLORS.border }}>
              <div
                style={{
                  height: '7px',
                  borderRadius: '999px',
                  width: `${Math.min(coveragePct, 100)}%`,
                  backgroundColor: coveragePct >= 100 ? COLORS.emerald : COLORS.accent,
                }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px' }}>
              <span style={{ fontSize: '12px', color: COLORS.muted }}>
                {assignedCount}/{TOTAL_KPIS} KPIs assigned
              </span>
              <span style={{ fontSize: '12px', color: COLORS.muted }}>
                {assignedCount >= 13 ? '4' : assignedCount >= 10 ? '3' : assignedCount >= 5 ? '1' : '0'}/4 principals
              </span>
            </div>
          </div>

          {/* Assignments table */}
          <div
            style={{
              ...panelStyle,
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
            }}
          >
            {/* Table header */}
            <div
              style={{
                padding: '9px 16px',
                borderBottom: `1px solid ${COLORS.border}`,
                backgroundColor: COLORS.card,
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                flexShrink: 0,
              }}
            >
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  textTransform: 'uppercase' as const,
                  letterSpacing: '0.08em',
                  color: COLORS.muted,
                }}
              >
                Proposed Assignments
              </span>
              <span
                style={{
                  marginLeft: 'auto',
                  fontSize: '12px',
                  fontWeight: 600,
                  backgroundColor: `${COLORS.accent}20`,
                  color: COLORS.accentLight,
                  borderRadius: '999px',
                  padding: '2px 10px',
                }}
              >
                {assignedCount} of {TOTAL_KPIS}
              </span>
            </div>

            {/* Rows */}
            <div style={{ flex: 1, overflow: 'hidden' }}>
              {assignments.map((a, i) => (
                <div
                  key={i}
                  style={{
                    opacity: rowOpacity(i),
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '8px 16px',
                    borderBottom: `1px solid ${COLORS.border}`,
                  }}
                >
                  <div
                    style={{
                      width: '7px',
                      height: '7px',
                      borderRadius: '50%',
                      backgroundColor: a.color,
                      flexShrink: 0,
                    }}
                  />
                  <span style={{ fontSize: '13px', flex: 1, color: COLORS.text }}>{a.kpi}</span>
                  <span
                    style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '999px',
                      backgroundColor: `${a.color}20`,
                      color: a.color,
                      flexShrink: 0,
                    }}
                  >
                    {a.role}
                  </span>
                  <span style={{ fontSize: '12px', color: COLORS.muted, flexShrink: 0, width: '84px', textAlign: 'right' }}>
                    {a.principal}
                  </span>
                  <span style={{ fontSize: '13px', color: COLORS.emerald, flexShrink: 0, width: '16px' }}>
                    {rowOpacity(i) > 0.5 ? '·' : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Confirm / success button */}
          <div style={{ opacity: confirmVisible, flexShrink: 0 }}>
            {!isConfirmed ? (
              <div
                style={{
                  borderRadius: '12px',
                  backgroundColor: COLORS.accent,
                  padding: '15px',
                  textAlign: 'center',
                  cursor: 'default',
                }}
              >
                <span style={{ fontSize: '15px', fontWeight: 600, color: '#fff' }}>
                  Confirm Assignments →
                </span>
              </div>
            ) : (
              <div
                style={{
                  opacity: successOpacity,
                  borderRadius: '12px',
                  border: `1px solid ${COLORS.emerald}`,
                  backgroundColor: `${COLORS.emerald}15`,
                  padding: '15px',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: '16px', fontWeight: 700, color: COLORS.emerald }}>
                  ✓ 15 assignments confirmed
                </div>
                <div style={{ fontSize: '13px', color: COLORS.muted, marginTop: '4px' }}>
                  Value Assurance tracking enabled for all KPIs
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Closing line */}
      <div
        style={{
          opacity: closingOpacity,
          textAlign: 'center',
          marginTop: '20px',
        }}
      >
        <p style={{ fontSize: '30px', fontWeight: 700, color: COLORS.text }}>
          Every KPI has an owner. Zero spreadsheets.
        </p>
      </div>

      <LogoWatermark />
    </SceneContainer>
  );
};
