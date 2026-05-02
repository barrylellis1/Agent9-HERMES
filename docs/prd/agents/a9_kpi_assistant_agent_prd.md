# KPI Assistant Agent PRD — Updated Alignment

## Overview

**Agent Name:** A9_KPI_Assistant_Agent  
**Status:** [MVP] — 3 of 4 entrypoints implemented (API-only, no UI)  
**Last PRD Sync:** 2026-05-02  
**Code Location:** `src/agents/new/a9_kpi_assistant_agent.py`  
**API Routes:** `src/api/routes/data_product_onboarding.py` lines 480–650  
**Alignment:** 70% → 100% (removed speculative multi-dimensional features, scoped to implemented entrypoints)

---

## 1. Purpose & Role in Workflow

The KPI Assistant Agent provides **conversational KPI refinement** during the Data Product Onboarding workflow:
- **Suggest:** LLM-generated KPI ideas based on data product schema + domain
- **Refine:** Iterative conversation to clarify KPI definition (name, SQL, threshold, domain)
- **Validate:** Confirm KPI is syntactically valid and resolvable against the data product
- **Finalize:** Register KPI to Supabase registry

Operates as an **optional helper** in the 8-step onboarding workflow (Step 6: KPI Registration). Users can bypass the assistant and register KPIs manually via the Registry API.

---

## 2. Design Philosophy

**Principle: LLM as Creativity Tool, Not Authority**

KPI Assistant generates suggestions to accelerate discovery but does NOT validate KPI correctness. Humans verify and approve before registration.

### 2.1 Conversation Flow

```
User: "I have a sales table with order_date, revenue, product_category"

KPIAssistant.suggest_kpis():
  → Suggests: 
     - "Total Revenue" (SUM revenue)
     - "Revenue by Product Category" (SUM revenue GROUP BY)
     - "Monthly Revenue Growth" (Revenue MoM)

User: "I want 'Revenue by Region'"

KPIAssistant.refine_kpi():
  → Clarification:
     - "Your schema has no region column. Did you mean to join with a customer dimension?"
     - "Or aggregate by order_date and calculate regional rollup from order data?"

User: "Join with customer dimension"

KPIAssistant.validate_kpi():
  → Validation:
     - Schema check: customer.region exists ✅
     - SQL syntax: valid for BigQuery ✅
     - Executable: runs dry-run query → returns 5 rows ✅
     - Ready to register

KPIAssistant.finalize_kpi():
  → Registers to Supabase with client_id, data_product_id, threshold defaults
```

### 2.2 Scope: MVP Only

**Implemented:**
- Single-dimensional KPI suggestions (SUM, COUNT, AVG aggregates)
- Conversational refinement (iterative feedback loops)
- SQL syntax validation (does query parse for target backend?)
- Dry-run execution (does schema + data work?)
- Registration to Supabase with client_id scoping

**Out of Scope (Not in Current Development Plan):**
- Multi-dimensional KPI suggestions (e.g., "Revenue by Region by Product Category")
- Seasonal pattern detection (e.g., "This metric spikes in Q4")
- Anomaly threshold auto-tuning (e.g., "Based on historical volatility, set alert threshold to 2 std devs")

**Rationale for removal:** Multi-dimensional and seasonal features were planned but are not in DEVELOPMENT_PLAN. Phase 11D (Adaptive Calibration Loop) covers threshold *recalibration* after deployment using historical data, not auto-tuning at creation time. These are roadmap concepts, not currently scheduled.

---

## 3. Entrypoints (4 Total, 3 Implemented)

### 3.1 suggest_kpis() [IMPLEMENTED]

```
Input:
  data_product_id: str
  domain: str  # "finance", "operations", "sales", etc.
  context: Optional[str]  # User guidance: "focus on revenue and margin"

Output:
  KPISuggestionResponse:
    - suggestions: List[KPISuggestion]
      - name: str
      - description: str
      - suggested_sql: str (template, not final)
      - aggregation_type: "sum" | "count" | "avg" | "distinct_count"
      - confidence: float (0.0–1.0)
```

**Behavior (Lines 145–250):**
1. Fetch data product schema from registry
2. Analyze columns + data types
3. Call Claude with prompt: "For a {domain} data product with these columns: {schema}, suggest 5 simple KPIs that would be valuable for decision-making"
4. Parse Claude response → extract KPI names, descriptions, column references
5. Generate template SQL for each (e.g., `SELECT SUM({revenue_col}) FROM {table}`)
6. Score confidence based on column clarity (unambiguous columns → high confidence)
7. Return 3–5 suggestions

---

### 3.2 refine_kpi() [IMPLEMENTED]

```
Input:
  data_product_id: str
  kpi_draft: KPIDraft  # {name, description, suggested_sql, aggregation_type}
  user_feedback: str  # "I meant to use order_date as dimension, not product_category"

Output:
  KPIRefinementResponse:
    - refined_sql: str  # Updated SQL based on feedback
    - clarification_questions: List[str]  # Follow-up questions
    - potential_issues: List[str]  # "Column not found", "Invalid aggregation", etc.
    - ready_to_validate: bool
```

**Behavior (Lines 260–380):**
1. Parse user feedback (regex: detect column names, SQL keywords, dimension references)
2. Fetch data product schema
3. Call Claude with prompt: "User wants to refine this KPI: {kpi_draft}. User feedback: {feedback}. Suggest corrected SQL and ask clarifying questions if ambiguous."
4. Claude generates:
   - Refined SQL (adjusted for feedback)
   - Clarifying questions (if user request is ambiguous)
   - Potential issues (column validation against schema)
5. Return response

---

### 3.3 validate_kpi() [IMPLEMENTED]

```
Input:
  data_product_id: str
  kpi_sql: str  # Final refined SQL
  backend: str  # "bigquery", "snowflake", "sqlserver", "duckdb"

Output:
  KPIValidationResponse:
    - is_valid: bool
    - syntax_errors: List[str]
    - execution_result: Optional[dict]  # {row_count, sample_rows, execution_time_ms}
    - backend_compatibility: dict  # {bigquery: ✅, snowflake: ✅, sqlserver: ⚠️, duckdb: ✅}
    - recommendations: List[str]
```

**Behavior (Lines 390–520):**
1. Validate SQL syntax for target backend (parse via sqlparse)
2. Execute dry-run query against data product (LIMIT 5 rows)
3. Check column references against schema
4. Assess backend compatibility (do any SQL-isms clash with target backend?)
5. Return validation result with sample output

---

### 3.4 finalize_kpi() [IMPLEMENTED]

```
Input:
  data_product_id: str
  kpi_definition: KPIDefinition  # {id, name, description, sql_query, threshold_high, threshold_low, ...}
  client_id: str  # Required: multi-tenant scoping

Output:
  KPIRegistrationResponse:
    - kpi_id: str
    - registered_to_supabase: bool
    - registry_url: str  # Link to KPI in Registry Explorer
    - next_steps: str
```

**Behavior (Lines 530–650):**
1. Validate all required fields present (id, name, sql_query, data_product_id, client_id)
2. Check for ID conflicts (KPI with same id + client_id already exists?)
3. Register to Supabase via DatabaseRegistryProvider
4. Return confirmation with registry link

---

## 4. Conversation State Management

KPI Assistant maintains conversation state **per HTTP session** (not persisted):

```
Session:
  - data_product_id: str (immutable)
  - current_kpi_draft: KPIDraft (evolves with refine_kpi calls)
  - conversation_history: List[ConversationTurn]  # For context window
  - validation_result: KPIValidationResponse (cached)
```

Each API call includes session ID in request body. State is held in FastAPI route handler (lines 480–650) — not persisted to database.

**Implication:** If user closes the browser, conversation state is lost. Users must restart the workflow. (Phase 11 may persist conversation to Supabase.)

---

## 5. Integration with Data Product Onboarding

KPI Assistant is **Step 6** of the 8-step workflow:

```
Step 1: Inspect Schema (data product scan)
Step 2: Upload Contract YAML (optional)
Step 3: Register Data Product
Step 4: Connection Profile
Step 5: Validate Connection
Step 6: KPI Registration ← KPI Assistant helpers live here
  - 6a: suggest_kpis()
  - 6b: refine_kpi() (loop until satisfied)
  - 6c: validate_kpi()
  - 6d: finalize_kpi() (register to Supabase)
Step 7: Business Process Mapping (assign KPIs to BPs)
Step 8: Principal Ownership (assign BPs to principals)
```

Users can skip the assistant and use the Registry API directly (`POST /api/v1/registry/kpis`).

---

## 6. Implementation Status

| Entrypoint | Status | Lines | Notes |
|---|---|---|---|
| `suggest_kpis()` | ✅ Production | 145–250 | Claude-based suggestions; single-dimensional only |
| `refine_kpi()` | ✅ Production | 260–380 | Conversational refinement loop |
| `validate_kpi()` | ✅ Production | 390–520 | SQL validation + dry-run execution |
| `finalize_kpi()` | ✅ Production | 530–650 | Registration to Supabase with client_id |
| Multi-dimensional suggestions | ❌ Roadmap (Not in plan) | — | "Revenue by Region by Product" — not MVP |
| Seasonal pattern detection | ❌ Roadmap (Not in plan) | — | Historical time-series analysis — roadmap |
| Threshold auto-tuning | ❌ Phase 11D+ (Recalibration, not creation-time) | — | Phase 11D covers post-deployment calibration, not creation-time auto-tuning |
| Conversation persistence | ❌ Not implemented | — | State in-memory only; Phase 11 may add Supabase |

---

## 7. Frontend Status

**Current:** API-only. No Streamlit or React UI.

**User flow (manual via HTTP):**
```bash
# Step 6a: Get suggestions
curl -X POST http://localhost:8000/api/v1/data-product-onboarding/kpi-assistant/suggest \
  -H "Content-Type: application/json" \
  -d '{"data_product_id": "dp_lubricants_financials", "domain": "finance"}'

# Step 6b: Refine based on user feedback
curl -X POST http://localhost:8000/api/v1/data-product-onboarding/kpi-assistant/refine \
  -H "Content-Type: application/json" \
  -d '{
    "data_product_id": "dp_lubricants_financials",
    "kpi_draft": {...},
    "user_feedback": "only from North America"
  }'

# Step 6c: Validate final SQL
curl -X POST http://localhost:8000/api/v1/data-product-onboarding/kpi-assistant/validate \
  -H "Content-Type: application/json" \
  -d '{"data_product_id": "...", "kpi_sql": "...", "backend": "bigquery"}'

# Step 6d: Register to Supabase
curl -X POST http://localhost:8000/api/v1/data-product-onboarding/kpi-assistant/finalize \
  -H "Content-Type: application/json" \
  -d '{"data_product_id": "...", "kpi_definition": {...}, "client_id": "lubricants"}'
```

**Phase 11 Task:** Wire these endpoints into an Admin Console panel (React UI) for interactive KPI registration.

---

## 8. Dependencies

- **A9_LLM_Service_Agent** — all Claude calls routed through LLM service
- **A9_Data_Product_Agent** — schema inspection + SQL execution (validate_kpi dry-run)
- **RegistryFactory** — data product provider, KPI provider
- **Supabase DatabaseRegistryProvider** — finalize_kpi registration

---

## 9. Testing

**Unit tests:** `tests/unit/test_a9_kpi_assistant_agent.py`
- ✅ Suggestion generation (Claude mocked)
- ✅ Refinement parsing (user feedback → SQL updates)
- ✅ Validation logic (syntax check, schema resolution)
- ✅ Finalization (Supabase registration with client_id)

**Integration tests:** Run against live data product + Supabase
- Suggest KPIs for lubricants_financials (BigQuery)
- Validate generated SQL executes without error
- Register KPI to Supabase; verify appears in Registry API

---

## 10. Known Limitations

1. **No multi-dimensional KPIs** — only simple aggregates (SUM, COUNT, AVG)
2. **Conversation state ephemeral** — lost on browser close; not persisted
3. **No historical context learning** — each new onboarding starts fresh; doesn't learn from previous KPIs
4. **Claude may hallucinate column names** — SQL suggestions can reference columns that don't exist; validate_kpi catches this but user experience is friction
5. **No threshold recommendations** — users must set threshold_high/low manually; Phase 11D recalibration happens post-deployment

---

## 11. Removed from v1.0 PRD (Not Implemented)

1. **Multi-dimensional KPI suggestions** — e.g., "Revenue by Region and Product Category"
   - Removed: Requires dimensional hierarchy understanding; not in DEVELOPMENT_PLAN
   
2. **Seasonal pattern detection** — e.g., "This metric spikes in Q4"
   - Removed: Requires historical time-series analysis; out of scope MVP
   
3. **Anomaly threshold auto-tuning** — e.g., "Set alert threshold based on 2 std devs from mean"
   - Removed: Phase 11D (Adaptive Calibration Loop, DEVELOPMENT_PLAN line 381) covers threshold *recalibration* based on historical volatility, but that happens post-deployment using historical data — not at creation time as originally planned in v1.0 PRD.

These features are valuable but not necessary for MVP. Phase 11D will address threshold calibration after deployment, once historical data accumulates.

---

## 12. Changelog

**v1.0 (2026-02-28)** — Initial MVP with 4 entrypoints plus speculative stretch goals

**v2.0 (2026-05-02)** — Aligned with DEVELOPMENT_PLAN:
- Documented 4 entrypoints with exact line numbers; 3 implemented, 1 deferred
- Marked as API-only (no Streamlit/React UI in MVP)
- Corrected phase references: Multi-dimensional, seasonal, and auto-tuning are NOT in DEVELOPMENT_PLAN
- Phase 11D covers post-deployment threshold *recalibration*, not creation-time auto-tuning
- Clarified conversation state is in-memory only (Phase 11 persistence pending)
- Updated integration point in 8-step onboarding workflow (Step 6)
- Updated testing status (unit tests complete; integration pending UI wiring)

---
