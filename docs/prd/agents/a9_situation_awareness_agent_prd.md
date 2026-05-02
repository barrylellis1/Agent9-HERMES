# Situation Awareness Agent PRD — Updated Alignment

## Overview

**Agent Name:** A9_Situation_Awareness_Agent  
**Status:** [MVP + Phase 8 Extension] — All core features implemented  
**Last PRD Sync:** 2026-05-02  
**Code Location:** `src/agents/new/a9_situation_awareness_agent.py`  
**Alignment:** 85% → 100% (corrected phase references, documented Phase 8 opportunity→situation)

---

## 1. Purpose & Role in Workflow

The Situation Awareness Agent is the **sensor layer** of the decision pipeline — it detects **facts, not prescriptions**:
- **Situations** — KPI threshold breaches or anomalies requiring investigation (card_type="situation")
- **Opportunities** — Positive outliers or high-confidence upside signals (card_type="opportunity")
- **Queries** — Natural language follow-up questions from principals

Operates as the **entry sensor** to trigger Deep Analysis and Solution Finding. Produces situation/opportunity cards that drive downstream investigative workflows.

---

## 2. Design Philosophy

**Principle: Sensor Only, Not Decision-Maker**

SA agent detects and reports KPI state. It does NOT prescribe solutions or filter by feasibility. Downstream agents (DA for analysis, SF for recommendations) add context and judgment.

### 2.1 Three-Tier KPI Evaluation Model

1. **Tier 1: Threshold Breach** — KPI value crosses alert threshold (absolute or relative to baseline)
2. **Tier 2: Anomaly Detection** — Unexplained spike/drop exceeding confidence band
3. **Tier 3: Opportunity Signal** — Positive outlier matching strategic domain (new in Phase 8)

Each KPI can generate multiple situation/opportunity cards in a single assessment (e.g., "Revenue threshold breach" + "YoY growth anomaly" + "Regional expansion opportunity").

### 2.2 Multi-Tenant Client Isolation (Critical)

Every assessment is scoped to a single `client_id`:

```
Assessment input:
  - principal_id: "cfo_001" (implies client_id="lubricants")
  - kpi_id: optional (single-KPI mode)
  - date_range: optional

KPI filtering inside SA:
  1. Fetch principal context → extract client_id="lubricants"
  2. Load all KPIs from registry
  3. Filter: [kpi for kpi in kpis if kpi.client_id == "lubricants"]
  4. Apply principal.kpi_portfolio filter
  5. Evaluate only lubricants KPIs
```

**Critical enforcement:** The `_get_relevant_kpis()` method (line 1785) uses strict match filter:
```python
if client_id:
    if kpi.client_id != client_id:  # STRICT MATCH — no is-not-None fallback
        continue
```

KPIs with `client_id=None` are excluded when evaluating a tenant-scoped principal. This prevents Shared KPIs (bicycle contract-loaded KPIs) from leaking into lubricants assessment results.

### 2.3 KPI Portfolio Principal Scoping

Principal portfolio is **immutable context** set by PCA:

```
Principal "Sarah Chen" (lubricants):
  - client_id: "lubricants"
  - business_process_ids: ["finance_revenue_growth", "cost_management"]
  - kpi_portfolio: [
      "gross_revenue", "net_revenue", "cogs",
      "operating_expenses", "profit_margin", ...
    ]

SA assessment:
  1. Load all lubricants KPIs
  2. Filter by principal.kpi_portfolio
  3. Evaluate only KPIs in her assigned portfolio
```

**Effect:** Sarah sees only KPIs linked to her business processes. Cannot assess KPIs outside her domain.

### 2.4 Backend Routing by Source System (Phase 10 Foundation)

KPI evaluation routes to the correct SQL backend based on `DataProduct.source_system`:

```python
_gen_dp_id = getattr(kpi_definition, 'data_product_id', None)
_source_system = self._resolve_source_system(_gen_dp_id)  # Lookup from registry

if _source_system == 'bigquery':
    # BigQuery path: backtick-quoted identifiers, CURRENT_DATE(), DATEADD()
    base_sql = self._bq_apply_period(...)
elif _source_system == 'snowflake':
    # Snowflake path: bare identifiers, CURRENT_DATE(), DATEADD()
    base_sql = self._bq_apply_period(...)  # Reuse logic; syntax differences handled in method
elif _source_system == 'sqlserver':
    # SQL Server path: bracket-quoted identifiers, GETDATE(), DATEDIFF()
    base_sql = self._ss_apply_period(...)
else:  # duckdb or fallback
    # DuckDB path: embedded in Python
    base_sql = self._bq_apply_period(...)
```

**Tier 1 routing:** Lookup `data_product_id` → get `source_system` from registry  
**Tier 2 fallback:** Regex detection (backticks → BigQuery, brackets → SQL Server) if data_product_id missing  

---

## 3. Entrypoints (All Implemented)

### 3.1 detect_situations()

```
Input:
  principal_id: str
  date_range: Optional[DateRange] = None
  kpi_id: Optional[str] = None  # Single-KPI mode
  include_opportunities: bool = True

Output:
  SituationDetectionResponse:
    - situations: List[SituationCard]
    - opportunities: List[OpportunityCard]
    - kpi_definitions: List[KPIDefinition]
    - assessment_timestamp: datetime
    - execution_summary: dict  # Diagnostics: KPI count, timeouts, errors
```

**Behavior (Lines 240–400):**
1. Load principal context (including client_id, kpi_portfolio)
2. Load all KPIs for principal's client + portfolio
3. For each KPI:
   - Fetch base value (current period, native SQL for KPI's backend)
   - Fetch comparison value (prior period: YoY, QoQ, WoW depending on KPI config)
   - Evaluate thresholds (absolute, relative, anomaly detection)
   - Generate situation cards (threshold breach, anomaly)
   - If base value is positive outlier → generate opportunity card
4. Sort cards by severity + confidence
5. Return response with all cards

### 3.2 process_nl_query()

```
Input:
  principal_id: str
  query: str  # "Why is revenue down?" or "What changed in Q2?"
  situation_card_id: Optional[str] = None  # Context from situation card

Output:
  NLQueryResponse:
    - answer: str
    - supporting_data: List[dict]
    - confidence: Literal["high", "medium", "low"]
    - recommended_next_step: str
```

**Behavior (Lines 420–550):**
1. Parse NL query with A9_NLP_Interface_Agent (extracts KPI, timeframe, grouping)
2. Execute query SQL against principal's data (routed to correct backend)
3. Summarize results with Claude
4. Return structured answer with supporting data

### 3.3 process_hitl_feedback()

```
Input:
  situation_card_id: str
  feedback: HitlFeedback  # {action: "snooze"|"dismiss"|"investigate", duration?: str, notes?: str}

Output:
  FeedbackResponse:
    - acknowledged: bool
    - next_steps: str
    - stored_feedback_id: str
```

**Behavior (Lines 560–620):**
1. Update situation in situations_store (in-memory; Supabase persistence Phase 11)
2. Log feedback for audit trail
3. If action="investigate" → return pointer to Deep Analysis workflow
4. If action="snooze" → return re-evaluation schedule
5. If action="dismiss" → mark card as acknowledged, stop alerting

### 3.4 get_recommended_questions()

```
Input:
  situation_card_id: str

Output:
  RecommendedQuestionsResponse:
    - questions: List[str]  # 3–5 clarifying questions
    - question_types: List[str]  # ["root_cause", "trend", "segment", ...]
```

**Behavior (Lines 630–680):**
1. Load situation card
2. Analyze KPI metadata (domain, business process, sensitivity)
3. Generate 3–5 diagnostic questions relevant to the KPI domain
4. Return questions for principal to explore further

### 3.5 get_kpi_definitions()

```
Input:
  principal_id: str
  client_id: Optional[str] = None

Output:
  List[KPIDefinition]  # All KPIs in principal's portfolio
```

**Behavior (Lines 690–710):**
1. Load principal context
2. Return `_get_relevant_kpis(principal_id, client_id)`
3. Used by Registry Explorer UI to populate KPI list

---

## 4. Phase 8: Opportunity→Situation Conversion (Implemented)

**New in February 2026:** SA detects positive outliers as **opportunities** and converts high-confidence signals to **opportunity cards**.

### 4.1 Opportunity Detection Logic

After evaluating KPI against thresholds, SA checks for high-confidence upside:

```python
def _evaluate_kpi(self, kpi_def, base_value, comparison_value):
    """Returns List[SituationCard | OpportunityCard]"""
    cards = []
    
    # Situation: threshold breach
    if base_value < kpi_def.threshold_low:
        cards.append(SituationCard(
            kpi_id=kpi_def.id,
            card_type="situation",
            title=f"{kpi_def.name} below threshold",
            severity="high",
            ...
        ))
    
    # Opportunity: positive outlier (Phase 8)
    if base_value > comparison_value * 1.15:  # 15% above prior period
        confidence = self._confidence_score(base_value, comparison_value, volatility)
        if confidence >= 0.75:  # High confidence
            cards.append(SituationCard(  # card_type="opportunity"
                kpi_id=kpi_def.id,
                card_type="opportunity",
                title=f"{kpi_def.name} above baseline",
                severity="info",  # Green KPI tile
                confidence=confidence,
                ...
            ))
    
    return cards
```

### 4.2 DA Agent Integration

Deep Analysis Agent processes opportunity cards similarly to situation cards:

```python
# DA entrypoint: analyze_situation()
if situation.card_type == "opportunity":
    # Run Is/Is Not analysis on WHY the upside occurred
    # Generate "Replication Targets" section (regions/segments to expand into)
else:  # situation
    # Run Is/Is Not analysis on WHY the problem occurred
    # Generate root-cause findings
```

---

## 5. Implementation Status

| Feature | Status | Lines | Notes |
|---|---|---|---|
| Threshold detection | ✅ Production | 1400–1500 | Absolute + relative thresholds |
| Anomaly detection | ✅ Production | 1520–1600 | Z-score + change-point detection |
| Opportunity detection | ✅ Production (Phase 8) | 1650–1750 | Positive outlier + confidence scoring |
| Multi-tenant filtering | ✅ Production | 1785–1800 | Strict client_id match |
| Portfolio scoping | ✅ Production | 1805–1830 | Principal → KPI portfolio filter |
| NL query parsing | ✅ Production | 420–450 | Via NLP Interface Agent |
| Backend routing | ✅ Production | 2000–2100 | BigQuery, Snowflake, SQL Server, DuckDB |
| HITL feedback store | ✅ MVP | 560–620 | In-memory; Supabase Phase 11 |

---

## 6. Deferred Features

### 6.1 Per-KPI Monitoring Profiles (Phase 11D — Adaptive Calibration Loop)

**Original plan (Phase 9A):** Registry would store per-KPI monitoring configs.

**Status:** Postponed. Registry model fields added but SA runtime does NOT use them yet. Phase 11D (Adaptive Calibration Loop, DEVELOPMENT_PLAN line 381) will wire up registry configs for threshold recalibration based on historical volatility.

**Rationale for deferral:** Registry improvements and MVP shipping prioritized over per-KPI customization. Recalibration (Phase 11D) happens post-deployment with historical data, not at startup.

### 6.2 Monthly Aggregation & Rollup (Not in Current Development Plan)

**Original plan (Phase 9B):** Rolled-up monthly cards showing month-over-month trends (not daily updates).

**Status:** Not implemented and not in DEVELOPMENT_PLAN. SA agent currently produces daily assessments with YoY/QoQ/WoW comparisons. Phase 11C (Unified Situation Stream) covers merging problem/opportunity streams but not monthly aggregation.

**Rationale for deferral:** Daily alerts are more actionable. Monthly rollup deferred pending customer feedback and explicit demand.

### 6.3 Scheduled Offline Assessment (Implemented Separately; Not Integrated to UI)

**Original plan (Phase 9C):** Nightly SA run without principal interaction (enterprise assessment mode).

**Status:** Implemented in `run_enterprise_assessment.py` (Phase 9C shipped, Feb 2026), but NOT integrated into Decision Studio UI. Users currently run assessments on-demand via the UI.

**Rationale for deferral:** On-demand assessment is MVP sufficient. Scheduled execution deferred to Phase 11+ once scheduler infrastructure is added. `run_enterprise_assessment.py` is a CLI tool, not yet UI-integrated.

---

## 7. Known Operational Constraints

### 7.1 Bicycle Client: Empty DA Results on YTD Timeframe

**Issue:** The bicycle/FI dataset has only 2 Actual transactions in 2026. When evaluating YTD (Year-to-Date), DA dimensional analysis returns 0 rows.

**Workaround:** Test with lubricants principal (BigQuery has full 2026 data) or use MTD/QTD timeframe for bicycle.

**Fix (pending Phase 10):** Reseed bicycle FI with 2026 Actual data from SAP DataSphere export, OR add UI client/dataset indicator so testers understand which dataset is active.

### 7.2 Snowflake Comparison SQL Partial

**Issue:** SA agent's Snowflake routing (lines 2103–2118) uses `_bq_apply_period()` method which was designed for BigQuery. Snowflake DATEADD/GETDATE syntax differs.

**Status:** Base SQL (lines 2042–2050) routes to DuckDB/default handler. Comparison SQL uses fallback logic. Demo-only client; fix deferred.

### 7.3 No Visible Client Indicator in UI

**Issue:** Decision Studio header/sidebar has no badge showing which client's data is active (bicycle vs lubricants).

**Fix pending:** Phase 10C will add client badge in DecisionStudio header.

---

## 8. Dependencies

- **A9_Principal_Context_Agent** — loads principal context (immutable throughout assessment)
- **A9_NLP_Interface_Agent** — parses natural language queries
- **A9_Deep_Analysis_Agent** — receives situation/opportunity cards for dimensional analysis
- **A9_Solution_Finder_Agent** — receives DA results to generate recommendations
- **A9_Data_Product_Agent** — executes SQL queries (routed by SA based on source_system)
- **RegistryFactory** — KPI provider, data product provider (for source_system lookup)
- **Situations Store** — in-memory HITL feedback (Phase 11 migration to Supabase pending)

---

## 9. Testing

**Unit tests:** `tests/unit/test_a9_situation_awareness_agent.py`
- ✅ Threshold detection (absolute, relative)
- ✅ Anomaly detection (Z-score, change-point)
- ✅ Opportunity detection (positive outlier scoring)
- ✅ Multi-tenant filtering (client_id strict match)
- ✅ Portfolio scoping (principal.kpi_portfolio)
- ✅ NL query parsing
- ✅ Backend routing (BigQuery, SQL Server, DuckDB paths)
- ⚠️ Snowflake routing (partial; uses DuckDB fallback)

**Integration tests:** Run against live Supabase + BigQuery
- Detect situations for lubricants principal
- Verify no bicycle KPIs appear in lubricants assessment
- Verify opportunity cards generated for high-confidence upside

---

## 10. Changelog

**v1.0 (2025-10-15)** — Initial MVP with threshold + anomaly detection

**v2.0 (2026-02-28)** — Phase 8 extension: opportunity detection + opportunity cards

**v3.0 (2026-05-02)** — Aligned with DEVELOPMENT_PLAN:
- Documented opportunity→situation conversion (Phase 8, shipped)
- Clarified multi-tenant client_id strict matching (critical for SaaS isolation)
- Corrected phase references: Per-KPI monitoring profiles now Phase 11D; monthly aggregation not in current plan; enterprise assessment implemented separately
- Updated backend routing logic with Tier 1/2 fallback pattern
- Documented known operational constraints (bicycle data, Snowflake SQL, missing client UI badge)
- Simplified "Deferred Features" section to show actual plan status per DEVELOPMENT_PLAN.md

---
