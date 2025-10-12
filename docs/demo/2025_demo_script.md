# 2025 Decision Studio Demo Script — KPI Narrative Arc (10–12 min)

Status: Draft presenter runbook

## Setup: 2025 overview (1 min)
- View: Monthly trend of Actual vs Budget (2024 → 2025)
- Talk track:
  - “We entered 2025 with plan pressure, bottoming in spring, then recovering by fall.”

## KPI Story 1: QA bottleneck (2 min)
- Dimension: PROFITCENTERID = US10_PCC3S
- Window: Jan–Apr 2025 (partial relief May–Jun)
- Views:
  - Filter Profit Center = US10_PCC3S
  - Show monthly Actual vs Budget and share of month
- Talk track:
  - “A new torque-testing procedure throttled small-batch assembly throughput in Q1–Q2. The center’s share dips visibly, widening the variance.”
- Evidence:
  - Lower Actual vs Budget and lower share Jan–Apr; stabilization starts post-May

## KPI Story 2: Downstream surge (1–2 min)
- Dimension: PROFITCENTERID IN (US10_PCY1L, US10_PCY1S)
- Window: Aug–Oct 2025 (strongest in Oct)
- Views:
  - Filter each center; compare Aug/Sep vs Oct
- Talk track:
  - “After upstream fixes, downstream centers absorb demand—pop-up activation and routing boost Oct volumes.”
- Evidence:
  - Visible share lift and stronger Actuals in Oct

## KPI Story 3: SKU mix misalignment (2 min)
- Dimension: PRODUCTCATEGORYID = YH (under-index H1), PRODUCTCATEGORYID = FG (late ramp)
- Window: YH depressed Jan–Jun; FG boosted Aug–Sep
- Views:
  - Compare YH vs FG monthly Actual vs Budget and monthly share
- Talk track:
  - “Planning over-indexed on YH in H1; a demand-sensing pivot lifts FG in late summer.”

## KPI Story 4: Customer experience regression/recovery (2 min)
- Dimension: CUSTOMERTYPEID = Z1 (early dip), CUSTOMERTYPEID = Z2 (mild late boost)
- Window: Z1 down Jan–Jun (heavier Q1–Q2); Z2 boosted Sep–Oct
- Views:
  - Compare Z1 vs Z2 Actual vs Budget and share for 2025
- Talk track:
  - “A loyalty/CRM hiccup suppressed Z1 in early 2025; the playbook restored confidence by fall. Z2 picks up slightly Sep–Oct.”

## Wrap: narrative arc recap (1 min)
- H1: QA bottleneck + SKU misalignment + CRM friction
- H2: Ops stabilization, demand mix correction, downstream surge
- Close:
  - “The system’s deep analysis detects these patterns without hardcoded text—purely from data.”

## What to Click (quick guide)
- Time frame: 2025-Jan through 2025-Oct
- Compare: Show Actual vs Budget as separate series or variance
- Filters by dimension:
  - Profit centers: US10_PCC3S, US10_PCY1L, US10_PCY1S
  - Product categories: YH, FG
  - Customer types: Z1, Z2
- Views:
  - Monthly trend (line)
  - Share-of-month (stacked or table with % of total Actual)
  - If needed: top-N by profit center to highlight shifts

## Evidence Checklist (for each story)
- QA bottleneck: US10_PCC3S
  - Lower Actual vs Budget Jan–Apr
  - Share-of-month visibly down; stabilization after May
- Downstream surge: US10_PCY1L/S
  - Lift in Aug/Sep; strong pop in Oct
- SKU mix: YH vs FG
  - YH under-index Jan–Jun; FG > Budget in Aug–Sep
  - Share moves from YH toward FG late summer
- Customer types: Z1 vs Z2
  - Z1 share depressed Q1–Q2; improvement through summer
  - Z2 small boost in Sep–Oct

## Q&A Prompts
- How does the system infer the story?
  - From data patterns: anomalies, variance trends, and dimensional shifts—no hardcoded narrative in the codebase.
- What changed in data?
  - 2025 Actuals shaped to demonstrate internal issues; Budget recast for realistic baselines; intra‑month rebalancing preserves monthly totals while shifting dimensional weights.
- Can we swap the storyline?
  - Yes. Replace the CSV with another shaped variant; restart. The agents will generate new insights aligned to the data.

## Troubleshooting (fast recovery)
- Signals look flat
  - Ensure you filtered to the correct codes: US10_PCC3S, US10_PCY1L/S, YH, FG, Z1, Z2
  - Restart servers to clear caches
  - If a month is zero, verify Actual rows exist for that month
- Budget too far from Actuals
  - Recast Budget (2025 Jan–Oct) to ~4–20% above Actuals; restart
- Dimension codes differ
  - Run a quick “top codes” scan to discover real values and adjust filters accordingly

## Presenter Talk Track (condensed)
- “We’re a boutique e‑bike brand. 2025 began with process strain—QA bottlenecks, misaligned SKU mix, and CRM friction.”
- “Profit center US10_PCC3S shows a clear H1 dip; as we fix upstream, downstream centers surge in Oct.”
- “SKU mix pivots away from YH, and FG benefits in late summer.”
- “Z1 customers struggled early; improvements lift satisfaction and revenue by fall.”
- “All of this is inferred from the data—no scripted narrative in the code.”

## Post‑Demo
- Restore the previous CSV if needed
- Note follow-ups: which signals resonated, where to strengthen/weaken effects (tune factors and re-run)

## Notes
- These codes correspond to stable ID-style filters (e.g., PROFITCENTERID, PRODUCTCATEGORYID, CUSTOMERTYPEID). If the UI exposes readable labels, maintain a mapping to IDs for test repeatability.
- For test-only shaping guidance, see `docs/testing/kpi_fi_transaction_test_cases.md`.
