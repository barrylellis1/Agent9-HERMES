# KPI Test Cases for FI Transactions (2025 Narrative Arc)

Status: Draft for test environments only

## Purpose
Define deterministic test cases to validate KPI behavior and dimensional analysis on `FI_Star_View` using Decision Studio and agent workflows. This manifests a 2025 storyline across months, combining external shocks and internal process issues that appear via dimensional analysis.

- KPIs: Gross Revenue, Cost of Goods Sold (COGS), Gross Margin
- Comparators: Budget vs Actual (primary), Month-over-Month (for WHEN deltas)
- Dimensions to analyze:
  - Profit center: `Parent Profit Center/Group Description` → `Profit Center Name`
  - Product category: `Parent Product/Group Description` → `Product Name`
  - Customer type: `Customer Type Name` → `Customer Name`
- Time bucket: `Fiscal Year-Month` (join via `time_dim`)

Notes:
- Use readable labels for categories/groups as configured in `src/contracts/fi_star_schema.yaml` `llm_profile.dimension_hierarchies`.
- For filters requiring stable keys, prefer `... ID` columns in fixtures (e.g., `Profit Center ID`, `Product Category ID`) and map them to display labels where needed.

## Preconditions
- Contract: `FI_Star_View` configured; dimension hierarchies present (customer/product/profit center).
- DPA SQL generator joins `time_dim` and supports `Budget vs Actual` and grouped breakdowns.
- Budget data present for each tested month.

## 2025 Monthly Narrative Targets
| Month | Proposed Actual (USD) | Key Internal Issue | Dimension Signal (target) |
|------|------------------------:|--------------------|----------------------------|
| Jan 2025 | 21,400,000 | QA backlog after torque-test rollout stalls US10_PCC3S line | Profit center → `US10_PCC3S` at ~55% of Budget |
| Feb 2025 | 47,000,000 | CRM migration fails to route Retail_Boutique orders | Customer type → `Retail_Boutique` ~60% (down 40%), `B2B_Fleet` ~100% |
| Mar 2025 | 70,000,000 | SKU planning over-indexed on Performance_Road inventory | Product category → `Performance_Road` ~65%, `Urban_Commuter` ~100% |
| Apr 2025 | 68,000,000 | Warranty repair surge consumes US10_PCC3S capacity | Profit center → US10_PCC3S further below plan (e.g., ~60–70%) |
| May 2025 | 62,000,000 | Marketing ops pause delays Retail_Boutique campaigns | Customer type → `Retail_Boutique` ~75% (recovering), `B2B_Fleet` ~100% |
| Jun 2025 | 64,800,000 | Vendor finance hold forces manual approvals for Performance_Road SKUs | Product category → `Performance_Road` ~85% (still 15% below plan) |
| Jul 2025 | 80,100,000 | Ops improvement team clears QA backlog | Profit center → `US10_PCC3S` ~90% |
| Aug 2025 | 87,500,000 | New demand-sensing cell shifts mix toward Urban_Commuter | Product category → `Urban_Commuter` ~105%, `Performance_Road` ~92% |
| Sep 2025 | 89,000,000 | Loyalty portal fixes restore Retail_Boutique confidence | Customer type → `Retail_Boutique` ~98%, `B2B_Fleet` ~102% |
| Oct 2025 | 92,500,000 | Regional pop-up shops feed US10_PCY1L surge | Profit center → `US10_PCY1L/S` ~110% |

Ratios are Actual/Budget guidance; adjust exact fixture amounts to meet the percentage targets and monthly totals.

## Test Design per Month (template)
For each month M in Jan–Oct 2025:

- Timeframe: `current_month = M`, Comparison: `Budget vs Actual`
- KPI: Primary COGS for margin stress, plus Gross Revenue / Gross Margin for corroboration
- Breakdown: one of the three dimension families according to the table above
- Expected Where/When:
  - WHERE: groups with largest negative deltas appear in `Where is` for underperformance months (or `Where is not` for overperformance peers)
  - WHEN: Top/Bottom deltas in `Fiscal Year-Month` emphasize the current month spike vs previous month

### Example: Feb 2025 (Customer Type)
- Filters: timeframe `Feb 2025`, comparator `Budget vs Actual`
- Breakdown: `Customer Type Name`
- Expectation:
  - `Retail_Boutique` ~60% of Budget (large negative delta)
  - `B2B_Fleet` ~100% (near plan)
  - WHERE: `Retail_Boutique` in `kt.where_is`, peers in `kt.where_is_not`
  - WHEN: current month shows negative delta vs previous month for the chosen KPI

### Example: Aug 2025 (Product Category)
- Breakdown: `Parent Product/Group Description`
- Expectations: `Urban_Commuter` ~105%, `Performance_Road` ~92%
- WHERE: overperformer/underperformer appear accordingly

## Minimal Fixture Guidance (tests only)
Create fixture rows (tests directory or isolated test DB) with columns representative of `FI_Star_View`:

- Dimensions: `Profit Center ID/Name`, `Parent Profit Center/Group Description`, `Product Category ID` or `Parent Product/Group Description`, `Customer Type Name`
- Measures: `Transaction Value Amount`
- Version: `Actual` and `Budget`
- Time: `Transaction Date` mapped via `time_dim` to `Fiscal Year-Month`

Strategy:
- For each month, allocate totals to hit the Proposed Actual and the targeted group ratios.
- Ensure at least two groups exist per dimension to surface relative differences (e.g., `Retail_Boutique` vs `B2B_Fleet`).

## Validation in Decision Studio
1. Select Time Frame → the month (e.g., `Feb 2025`).
2. Select Comparison → `Budget vs Actual`.
3. Use Deep Analysis:
   - Check `KT Is/Is Not` WHERE for the targeted dimension family.
   - Check WHEN Top/Bottom for the time bucket change vs prior month.
4. Optionally adjust to `Month over Month` to visualize delta with the previous month.

## Narrative Cues for Demo Notes
- Jan–Apr: Highlight internal process constraints (QA backlog, warranty surge) visible in profit center contributions.
- Feb/May/Sep: Customer flow issues (CRM routing, marketing pause, loyalty portal fixes) reflected in customer type.
- Mar/Jun/Aug: Inventory and finance gating drive product category mix and performance.
- Oct: Agile response via pop-up shops shows profit center surge.

## References
- Contract: `src/contracts/fi_star_schema.yaml`
- KPIs: `src/registry/kpi/kpi_registry.yaml`
- DPA behavior: `src/agents/new/a9_data_product_agent.py`
- Deep Analysis agent: `src/agents/new/a9_deep_analysis_agent.py`
