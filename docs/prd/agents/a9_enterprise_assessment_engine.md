# Phase 9 — Situation Monitor & Principal Intelligence Briefing (PIB)

<!-- arch-suppress-prd-phases: This document describes roadmap/future work. Phase 9A-9G references are historical; phases are not in DEVELOPMENT_PLAN.md. -->

> ⚠️ **CONCEPT DOCUMENT — NOT IN CURRENT DEVELOPMENT PLAN**
> 
> This document describes roadmap/future work for Phase 9B–9G. These phases are not in DEVELOPMENT_PLAN.md.
> The Phase 9 work (Situation Monitor, PIB composition, etc.) has been absorbed into later phases or deferred pending 
> enterprise assessment architecture redesign. This document is retained for historical reference and product direction clarity.

<!--
CANONICAL PRD DOCUMENT
Comprehensive PRD for Phase 9B (Situation Monitor) and Phase 9D-9E (PIB).
This document supersedes docs/prd/agents/a9_briefing_agent_concept.md
Last updated: 2026-04-01
Status: Phase 9B (Monitor) — In Development | Phase 9D-9E (PIB) — Planned
-->

---

## 1. Overview

**Purpose:** Transform Agent9 from a reactive, on-demand decision tool into a proactive intelligence delivery platform. Two tightly coupled components replace the broken `run_enterprise_assessment.py` and introduce executive briefing:

1. **Situation Monitor** — Scheduled, per-principal SA-only runs that detect KPI threshold breaches and persist findings to Supabase
2. **Principal Intelligence Briefing (PIB)** — Periodic email delivering new situations, in-progress solutions, and managed situations with one-click actions and deep-links to Decision Studio

**Core Design Principle:** SA is a **sensor** (facts only, no framing). DA determines framing (problem vs. opportunity). HITL approval is sacred — DA never runs automatically.

**Key Insight:** Executives don't log in daily to check dashboards. They want intelligence delivered. The PIB email is the primary interface; Decision Studio is the deep-dive tool launched from the email.

**Status:**
- ✅ Phase 9A (2026-04-01) — Supabase tables (`assessment_runs`, `kpi_assessments`), KPI monitoring profile fields, Pydantic models
- 🔄 Phase 9B (In Development) — Situation Monitor implementation and testing
- 📋 Phase 9C (Planned) — Situation state management (`situation_actions` table)
- 📋 Phase 9D-9E (Planned) — PIB composition engine and secure token system

---

## 2. Component 1: Situation Monitor

### 2.1 Purpose & Scope

The Situation Monitor replaces `run_enterprise_assessment.py` with a production-grade, offline batch process that runs SA-only (no DA) across registered KPIs for a specific principal and client, persists findings to Supabase, and enables delta detection (new vs. known situations).

**Core principles:**
- **SA-only:** No Deep Analysis, ever. DA is triggered only by HITL.
- **Per-principal, per-client:** Runs are scoped to one principal + one client (no enterprise-wide scans without principal context)
- **Orchestrated SA workflow:** Uses the same `orchestrator.orchestrate_situation_detection()` call chain as the Decision Studio UI's "Detect Situations" button
- **Real principal context:** Calls PC Agent with real `principal_id` → resolves `PrincipalContext` (role, business processes, client, filters)
- **Delta detection:** Compares current run against previous run to identify NEW situations

### 2.2 Entry Point & CLI

**File:** `run_situation_monitor.py` (project root)

**Invocation:**
```bash
python run_situation_monitor.py --principal <principal_id> --client <client_id> [--dry-run]
```

**Required arguments:**
- `--principal`: Principal ID (e.g., `cfo_001`). Used to resolve PrincipalContext
- `--client`: Client ID (e.g., `lubricants_inc`). Scope for this run

**Optional arguments:**
- `--dry-run`: Analyze but do not persist to Supabase

**Example:**
```bash
python run_situation_monitor.py --principal cfo_001 --client lubricants_inc
python run_situation_monitor.py --principal coo_001 --client lubricants_inc --dry-run
```

### 2.3 Workflow: Agent Initialization & Assessment Run

#### 2.3.1 Agent Initialization Sequence

Canonical sequence from Orchestrator PRD:

1. Initialize `RegistryFactory` and all providers
2. Create and connect `A9_Orchestrator_Agent`
3. Register `A9_Principal_Context_Agent`
4. Register `A9_Data_Product_Agent`
5. Register `A9_Situation_Awareness_Agent`

All agents instantiated via `AgentRegistry.get_agent()` or `AgentClass.create_from_registry()` — **never direct instantiation**.

#### 2.3.2 Assessment Run Lifecycle

**Step 1: Resolve Principal Context**

Call PC Agent with real `principal_id`:
```python
pc_agent = await AgentRegistry.get_agent("A9_Principal_Context_Agent")
principal_context = await pc_agent.get_principal_context(
    principal_id=principal_id,
    client_id=client_id
)
```

Extract:
- `role` (CFO, COO, CEO, etc.)
- `business_processes` (list of BP IDs mapped to this principal)
- `data_filters` (geography, product group, etc.)

**Step 2: Create Assessment Run Record**

Insert row into `assessment_runs` (Supabase):
```python
run = AssessmentRun(
    id=uuid4(),
    principal_id=principal_id,
    client_id=client_id,
    started_at=datetime.utcnow(),
    status="running",
    config=AssessmentConfig(principal_id=principal_id, severity_floor=0.3)
)
await assessment_runs_table.insert(run.model_dump())
```

**Step 3: Load KPI Registry**

Fetch all registered KPIs via:
```python
kpi_provider = registry_factory.get_provider("kpi")
all_kpis = await kpi_provider.get_all()

# Filter to KPIs mapped to principal's business processes
principal_kpis = [
    kpi for kpi in all_kpis
    if any(bp in principal_context.business_processes for bp in kpi.business_processes)
]
```

**Step 4: Per-KPI Loop (Sequential, Error-Isolated)**

For each KPI in `principal_kpis`:

##### a. SA Measurement

Call orchestrator's `orchestrate_situation_detection()` with real principal context:
```python
sa_response = await orchestrator.orchestrate_situation_detection(
    SituationDetectionRequest(
        principal_id=principal_id,
        client_id=client_id,
        kpi_id=kpi.id,
        use_monitoring_profile=True,  # Use KPI's per-profile settings
        context={
            "yaml_contract_text": kpi_contract_yaml,
            "principal_context": principal_context
        }
    )
)
```

SA uses the KPI's monitoring profile:
- `comparison_period` (MoM, QoQ, YoY) — determines comparison value fetch
- `volatility_band` (e.g., 0.05 = ±5%) — breach magnitude must exceed band
- `min_breach_duration` (periods) — KPI must be in breach for N consecutive periods
- `confidence_floor` (0–1) — gating for DA escalation
- `urgency_window_days` (SLA for principal action)

Result: `SituationDetectionResponse` containing detected situations and `escalate_to_da: bool` flag.

##### b. Persist SA Result

Insert/upsert row in `kpi_assessments`:
```python
kpi_assessment = KPIAssessment(
    id=uuid4(),
    run_id=run.id,
    kpi_id=kpi.id,
    kpi_value=sa_response.current_value,
    comparison_value=sa_response.comparison_value,
    severity=sa_response.severity,
    status=sa_response.status,  # "detected", "monitoring", "below_threshold"
    escalated_to_da=sa_response.escalate_to_da,
    monitoring_profile=kpi.monitoring_profile.model_dump(),
    created_at=datetime.utcnow()
)
await kpi_assessments_table.upsert(kpi_assessment.model_dump())
```

##### c. Confidence Gating

- If `confidence < kpi.monitoring_profile.confidence_floor`: mark `status="monitoring"`, skip DA, continue
- If `severity < run.config.severity_floor` (default 0.3): mark `status="below_threshold"`, skip DA, continue

##### d. DA Analysis (Only for Escalated KPIs)

If `escalate_to_da=True`:
```python
da_request = DeepAnalysisRequest(
    situation_id=situation.id,
    kpi_id=kpi.id,
    principal_id=principal_id,
    context={"yaml_contract_text": kpi_contract_yaml}
)
da_response = await orchestrator.orchestrate_deep_analysis(da_request)
```

Update `kpi_assessments` row with DA results:
```python
kpi_assessment.escalated_to_da = True
kpi_assessment.da_result = da_response.model_dump()
kpi_assessment.benchmark_segments = da_response.benchmark_segments
await kpi_assessments_table.update(kpi_assessment.model_dump())
```

##### e. Error Isolation & Progress Logging

Any exception for a single KPI is logged and marked `status="error"` in `kpi_assessments`. The loop continues.

**Progress log format:**
```
[Assessment a1b2c3d4] 12/35: gross_margin | severity=0.72 ✓ escalating to DA
[Assessment a1b2c3d4] 13/35: revenue_total | severity=0.18 | below threshold
[Assessment a1b2c3d4] 14/35: cogs_ratio | ERROR: BigQuery timeout — marked for retry
```

**Step 5: Delta Detection & Situation State**

After all KPIs processed, detect NEW situations vs. known ones:

```python
# Load previous run (most recent completed run for this principal+client)
previous_run = await assessment_runs_table.select()
    .eq("principal_id", principal_id)
    .eq("client_id", client_id)
    .eq("status", "complete")
    .order("completed_at", desc=True)
    .limit(1)
    .execute()

if previous_run:
    previous_assessments = await kpi_assessments_table.select()
        .eq("run_id", previous_run[0]["id"])
        .execute()
    
    # Composite key: (principal_id, kpi_id, period, geography, product_group)
    new_situation_ids = current_assessment_ids - previous_assessment_ids
else:
    new_situation_ids = current_assessment_ids  # All are new if no prior run
```

Mark situations as `state="new"` in the `situation_actions` table (Phase 9C — see below).

**Step 6: Complete Assessment Run**

Update `assessment_runs`:
```python
run.status = "complete"
run.completed_at = datetime.utcnow()
run.kpi_count = len(principal_kpis)
run.kpis_escalated = len([a for a in assessments if a.escalated_to_da])
run.kpis_monitored = len([a for a in assessments if a.status == "monitoring"])
run.kpis_below_threshold = len([a for a in assessments if a.status == "below_threshold"])
run.kpis_errored = len([a for a in assessments if a.status == "error"])
await assessment_runs_table.update(run.model_dump())
```

### 2.4 Idempotency & Resilience

**Assessment Run Deduplication:**
- Primary key: `(run_id)` — unique UUID per run
- If `assessment_runs` row exists with `status="complete"`: skip rerun (no duplicate)
- If `status="running"` (crashed run): resume from last incomplete KPI via `kpi_assessments` log
- If `status="error"`: re-run all errored KPIs only

**KPI Assessment Deduplication:**
- Primary key: `(run_id, kpi_id)` — one entry per KPI per run
- Upsert on `(run_id, kpi_id)` to avoid duplicates within a run

**Situation Deduplication (Phase 9C):**
- Composite key: `(principal_id, kpi_id, period, geography, product_group)`
- Prevents duplicate situation cards across runs

### 2.5 Configuration & Parameters

**AssessmentConfig (Pydantic Model):**
```python
class AssessmentConfig(BaseModel):
    severity_floor: float = 0.3  # KPIs below 30% breach magnitude not escalated
    principal_id: str  # Required — no enterprise-wide scans
    client_id: str    # Required — scope to client
    dry_run: bool = False
```

**MonitoringProfile (on KPI Registry Entry):**
```python
class MonitoringProfile(BaseModel):
    comparison_period: Literal["MoM", "QoQ", "YoY"] = "YoY"
    volatility_band: float = 0.05  # ±5%
    min_breach_duration: int = 1   # periods
    confidence_floor: float = 0.5  # 0–1
    urgency_window_days: int = 7   # SLA for principal action
```

---

## 3. Component 2: Principal Intelligence Briefing (PIB)

### 3.1 Purpose & Scope

The Principal Intelligence Briefing is a periodic email summarizing new situations, in-progress solutions, and managed situations for each principal. It's the executive's primary interface — Decision Studio is the deep-dive tool launched from one-click email actions.

**Core design:**
- **Email-centric:** Principal receives intelligence proactively; no login required to receive
- **One-click actions:** Snooze, delegate, request info, approve solution — all from email token links
- **Deep links:** Single-use, 7-day token URL that auto-authenticates and routes directly to DA for a specific situation
- **Smart recommendations:** Delegate suggestions use RACI mapping (KPI → business process → principal assignments)
- **Secure tokens:** All actions secured via single-use, time-limited UUID tokens

### 3.2 Email Content & Sections

**Email Subject:**
```
[Decision Studio] 3 New Situations Detected — Gross Margin, Inventory Days (Week of Apr 1)
```

#### 3.2.1 Section 1: New Situations

Listed first; most actionable.

**Per-situation display:**
```
GROSS MARGIN ⚠️ BREACH
└─ Current: 32.1% | Expected: 35% | Gap: -2.9%
└─ Detected: Apr 1, 2026
└─ Profile: QoQ monitoring | 5% volatility band

[Launch Deep Analysis] [Snooze 7 days] [Delegate]
```

**Content:**
- KPI name + icon (red for breach, green for opportunity — DA framing TBD)
- Current value and expected/plan value (no monetary estimate — numbers speak)
- Deviation (color-coded: red = negative, green = positive)
- Detected timestamp
- Monitoring profile label (shows "QoQ", "±5%")
- Action buttons: Launch Deep Analysis, Snooze, Delegate

**Note:** Situations are listed in rank order: severity descending, then confidence descending. High-confidence, large-magnitude situations appear first.

#### 3.2.2 Section 2: Urgency Flags (Optional)

Situations open N weeks with no action:

```
OPEN LONGER THAN SLA (7 days)
- Churn Rate (open 14 days)
- Headcount Cost (open 10 days)
[Acknowledge & Confirm Status] [Request Analysis Refresh]
```

Shows only if situation has been in `status="acknowledged"` for longer than `urgency_window_days`.

#### 3.2.3 Section 3: Solutions in Progress

Brief summary from Value Assurance tracking:

```
IN PROGRESS (3 initiatives)
- Supplier Consolidation Program: Expected impact +$2.1M COGS, implemented 3 days ago
- Pricing Power Study: Pending analysis, approved for launch
- Freight Optimization: $340K/year expected, measurement window open
[View Detailed Portfolio Impact]
```

**Content per solution:**
- Initiative name
- Expected impact (as quantified by SF Agent)
- Status (implemented, pending, measurement window open)
- Link to portfolio dashboard (optional in PIB Phase 9E; can show in Decision Studio instead)

#### 3.2.4 Section 4: Managed Situations

Situations the principal has acted on:

```
MANAGED (Snoozed or Delegated)
- Inventory Days: Snoozed until Apr 8
- Working Capital Ratio: Delegated to Marcus Webb (Finance Manager), status pending
[Update Status]
```

---

### 3.3 One-Click Actions from Email

All actions are **token-based** with no login required. Single-use, 7-day expiry.

#### 3.3.1 Action: Launch Deep Analysis

**URL format:**
```
https://app.trydecisionstudio.com/auth/briefing-token/<token>
```

**Flow:**
1. Token validated against `briefing_tokens` table
2. Token type = `deep_link`
3. Token contains: `principal_id`, `situation_id`, `briefing_run_id`
4. Check expiry (`expires_at`) and used status (`used_at`)
5. If valid: auto-authenticate principal, redirect to Decision Studio
6. Deep link routes to DeepFocusView pre-loaded with that situation + auto-trigger DA
7. Mark token as `used_at=now()`

**Token reuse prevention:** Token becomes invalid after first click (single-use).

#### 3.3.2 Action: Snooze

**URL format:**
```
https://app.trydecisionstudio.com/pib/snooze/<token>
```

**Form (minimal, email-optimized):**
```
Snooze "Gross Margin" for:
○ 3 days  ○ 7 days (default)  ○ 14 days  ○ Custom...
[Snooze] [Cancel]
```

**Flow:**
1. Token validated (type = `snooze`)
2. Principal selects duration
3. Insert row into `situation_actions`:
   ```python
   SituationAction(
       id=uuid4(),
       situation_id=situation.id,
       principal_id=principal.id,
       action_type="snooze",
       snooze_expires_at=now() + duration,
       created_at=now()
   )
   ```
4. Situation does NOT appear in next briefing run until `snooze_expires_at` is past
5. Mark token as `used_at=now()`

#### 3.3.3 Action: Delegate

**URL format:**
```
https://app.trydecisionstudio.com/pib/delegate/<token>
```

**Form (pre-populated with RACI recommendation):**
```
Delegate "Gross Margin" analysis to:

Recommended (Based on KPI business process assignments):
◐ Marcus Webb (Finance Manager)  ← default selected

Other principals:
○ Rachel Kim (COO)
○ Sarah Chen (CFO, you)
○ David Torres (CEO)

Note: [text field, optional]
[Delegate] [Cancel]
```

**RACI Resolution:**
- Look up KPI's `business_processes`
- For each BP, query principal assignments (from Principal registry)
- Recommend principal with `role="manager"` in that BP (or fallback to domain expert role)

**Flow:**
1. Principal selects target principal (or accepts recommendation)
2. Insert row into `situation_actions`:
   ```python
   SituationAction(
       id=uuid4(),
       situation_id=situation.id,
       principal_id=principal.id,  # delegating principal
       action_type="delegate",
       target_principal_id=selected_principal.id,
       note=optional_note,
       created_at=now()
   )
   ```
3. Situation marked as `delegated=True` in next PIB for delegating principal
4. Situation appears as `assigned_by` in next PIB for target principal
5. Mark token as `used_at=now()`

#### 3.3.4 Action: Request More Information

**URL format:**
```
https://app.trydecisionstudio.com/pib/request-info/<token>
```

**Form (minimal):**
```
Request information about "Gross Margin":

What would help you decide?
[text field, required]

Examples: "What's the geographic breakdown?", "How does this compare to last year?"

[Submit] [Cancel]
```

**Flow:**
1. Principal enters question
2. Insert row into `situation_actions`:
   ```python
   SituationAction(
       id=uuid4(),
       situation_id=situation.id,
       principal_id=principal.id,
       action_type="request_info",
       note=question_text,
       created_at=now()
   )
   ```
3. Question flagged for analyst (TODO Phase 9E: email analyst or add to analyst queue)
4. Mark token as `used_at=now()`

#### 3.3.5 Action: Approve Solution (When Available)

**Shown only if:**
- A solution exists pending HITL approval for this situation
- Solution is from SF Agent's most recent call on this situation

**URL format:**
```
https://app.trydecisionstudio.com/pib/approve/<token>
```

**Form:**
```
Approve solution for "Gross Margin":

Recommendation: Supplier Consolidation Program
Expected impact: +$2.1M annual COGS reduction | Confidence: 85%

[Approve & Track] [Review in Decision Studio] [Cancel]
```

**Flow:**
1. Token validated (type = `approve`)
2. Principal confirms
3. Trigger SF Agent's HITL approval workflow (same as Decision Studio approval)
4. VA Agent registers solution for tracking
5. Mark token as `used_at=now()`

---

### 3.4 Data Models & Supabase Tables

#### 3.4.1 Table: `situation_actions` (New — Phase 9C)

Tracks principal actions on situations (snooze, delegate, request_info, acknowledge).

**Schema:**
```sql
CREATE TABLE situation_actions (
    id UUID PRIMARY KEY,
    situation_id UUID NOT NULL REFERENCES situations(id),
    principal_id UUID NOT NULL REFERENCES principal_profiles(id),
    action_type TEXT NOT NULL, -- 'snooze', 'delegate', 'request_info', 'acknowledge'
    target_principal_id UUID, -- for 'delegate' action
    snooze_expires_at TIMESTAMP, -- for 'snooze' action
    note TEXT, -- for 'delegate' (reason) or 'request_info' (question)
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT check_action_type CHECK (action_type IN ('snooze', 'delegate', 'request_info', 'acknowledge'))
);
```

**Pydantic Model:**
```python
class SituationAction(BaseModel):
    id: UUID
    situation_id: UUID
    principal_id: UUID
    action_type: Literal["snooze", "delegate", "request_info", "acknowledge"]
    target_principal_id: Optional[UUID] = None
    snooze_expires_at: Optional[datetime] = None
    note: Optional[str] = None
    created_at: datetime
```

#### 3.4.2 Table: `briefing_tokens` (New — Phase 9E)

Secure, single-use tokens for PIB email actions and deep links.

**Schema:**
```sql
CREATE TABLE briefing_tokens (
    token UUID PRIMARY KEY,
    type TEXT NOT NULL, -- 'deep_link', 'snooze', 'delegate', 'request_info', 'approve'
    principal_id UUID NOT NULL REFERENCES principal_profiles(id),
    situation_id UUID NOT NULL REFERENCES situations(id),
    briefing_run_id UUID NOT NULL REFERENCES briefing_runs(id),
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP, -- NULL if unused
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT check_type CHECK (type IN ('deep_link', 'snooze', 'delegate', 'request_info', 'approve')),
    CONSTRAINT check_expiry CHECK (expires_at > created_at)
);

CREATE INDEX idx_briefing_tokens_principal_id ON briefing_tokens(principal_id);
CREATE INDEX idx_briefing_tokens_situation_id ON briefing_tokens(situation_id);
CREATE INDEX idx_briefing_tokens_expires_at ON briefing_tokens(expires_at);
```

**Pydantic Model:**
```python
class BriefingToken(BaseModel):
    token: UUID
    type: Literal["deep_link", "snooze", "delegate", "request_info", "approve"]
    principal_id: UUID
    situation_id: UUID
    briefing_run_id: UUID
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: datetime
```

#### 3.4.3 Table: `briefing_runs` (New — Phase 9D)

Records of PIB generation and delivery.

**Schema:**
```sql
CREATE TABLE briefing_runs (
    id UUID PRIMARY KEY,
    principal_id UUID NOT NULL REFERENCES principal_profiles(id),
    client_id TEXT NOT NULL,
    assessment_run_id UUID REFERENCES assessment_runs(id),
    sent_at TIMESTAMP,
    new_situation_count INT,
    format TEXT, -- 'detailed', 'digest'
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Pydantic Model:**
```python
class BriefingRun(BaseModel):
    id: UUID
    principal_id: UUID
    client_id: str
    assessment_run_id: Optional[UUID] = None
    sent_at: Optional[datetime] = None
    new_situation_count: int = 0
    format: Literal["detailed", "digest"] = "detailed"
    created_at: datetime
```

#### 3.4.4 Principal Profile Extension (Phase 9F)

Add fields to `principal_profiles` table for PIB preferences:

```sql
ALTER TABLE principal_profiles
ADD COLUMN briefing_frequency TEXT DEFAULT 'weekly', -- 'daily', 'weekly', 'off'
ADD COLUMN briefing_format TEXT DEFAULT 'detailed'; -- 'detailed', 'digest'
```

**Pydantic extension:**
```python
class PrincipalProfile(BaseModel):
    # ... existing fields ...
    briefing_frequency: Literal["daily", "weekly", "off"] = "weekly"
    briefing_format: Literal["detailed", "digest"] = "detailed"
```

---

### 3.5 API Surface

**Base path:** `/api/v1/pib/`

#### 3.5.1 POST /run

Trigger a PIB generation and delivery run for a principal+client.

**Request:**
```json
{
    "principal_id": "cfo_001",
    "client_id": "lubricants_inc",
    "format": "detailed",
    "dry_run": false
}
```

**Response:**
```json
{
    "briefing_run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "new_situation_count": 3,
    "solutions_in_progress": 2,
    "managed_situations": 1,
    "email_sent": "2026-04-01T14:30:00Z"
}
```

**Behavior:**
1. Load most recent completed assessment run for principal+client
2. Compare to previous PIB run
3. Identify NEW situations (not seen in prior PIB)
4. Compose email (see Section 3.2)
5. Generate secure tokens for all actions
6. Insert `briefing_run` record
7. Send email via SMTP
8. Return summary

#### 3.5.2 GET /runs

List briefing runs for a principal.

**Query parameters:**
- `principal_id` (required)
- `client_id` (optional)
- `limit` (default 10)

**Response:**
```json
{
    "runs": [
        {
            "briefing_run_id": "a1b2c3d4-...",
            "sent_at": "2026-04-01T14:30:00Z",
            "new_situation_count": 3,
            "format": "detailed"
        }
    ]
}
```

#### 3.5.3 GET /token/{token}

Validate and execute a one-click action from email.

**Request:**
```
GET /api/v1/pib/token/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response (on valid token):**
```json
{
    "valid": true,
    "type": "deep_link",
    "principal_id": "cfo_001",
    "situation_id": "sit_abc123",
    "redirect_url": "https://app.trydecisionstudio.com/decision/sit_abc123?auto_da=true"
}
```

**Response (on expired token):**
```json
{
    "valid": false,
    "reason": "Token expired"
}
```

**Response (on already-used token):**
```json
{
    "valid": false,
    "reason": "Token already used"
}
```

**Behavior:**
1. Look up token in `briefing_tokens`
2. Check `expires_at` > now
3. Check `used_at` IS NULL
4. Mark token as `used_at=now()`
5. Return appropriate response
6. Frontend uses `redirect_url` to navigate

#### 3.5.4 POST /delegate/{token}

Render and process delegate confirmation page.

**Request (GET):**
```
GET /api/v1/pib/delegate/a1b2c3d4-...?principal_override=coo_001
```

**Response (GET — HTML form or JSON):**
```json
{
    "situation_id": "sit_abc123",
    "situation_name": "Gross Margin",
    "recommended_principal": {
        "id": "finance_mgr_001",
        "name": "Marcus Webb",
        "role": "Finance Manager"
    },
    "other_principals": [
        { "id": "coo_001", "name": "Rachel Kim", "role": "COO" },
        { "id": "ceo_001", "name": "David Torres", "role": "CEO" }
    ]
}
```

**Request (POST):**
```json
{
    "token": "a1b2c3d4-...",
    "target_principal_id": "finance_mgr_001",
    "note": "Can you analyze this in context of the supplier consolidation?"
}
```

**Response (POST):**
```json
{
    "success": true,
    "message": "Delegated to Marcus Webb. They'll see this in their next briefing."
}
```

---

### 3.6 Email Delivery

#### 3.6.1 SMTP Configuration

Provider-agnostic SMTP via environment variables. Recommended: Resend (free tier, good deliverability).

**Environment variables:**
```bash
SMTP_HOST=smtp.resend.com
SMTP_PORT=465
SMTP_USER=default
SMTP_PASSWORD=<resend_api_key>
SMTP_FROM=insights@trydecisionstudio.com
SMTP_TLS=true
```

#### 3.6.2 Email Library

Use `aiosmtplib` (async SMTP) + Jinja2 for templates.

**Python package:**
```bash
pip install aiosmtplib jinja2
```

#### 3.6.3 Email Template Structure

**Template file:** `src/templates/pib_email.html.j2`

**Template variables:**
```jinja2
principal_name: "Sarah"
client_name: "Lubricants Inc"
new_situations: [
    {
        "kpi_name": "Gross Margin",
        "current_value": "32.1%",
        "expected_value": "35%",
        "severity": "high",
        "deep_link_url": "...",
        "snooze_url": "...",
        "delegate_url": "..."
    }
]
solutions_in_progress: [...]
managed_situations: [...]
```

**Rendering:**
```python
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('src/templates'))
template = env.get_template('pib_email.html.j2')

html = template.render(
    principal_name=principal.name,
    new_situations=new_situations,
    ...
)
```

---

### 3.7 Token Generation & Security

**Single-use, time-limited tokens for all email actions:**

```python
import secrets
from datetime import datetime, timedelta
from uuid import uuid4

def generate_briefing_token(
    type: str,  # 'deep_link', 'snooze', 'delegate', 'request_info', 'approve'
    principal_id: UUID,
    situation_id: UUID,
    briefing_run_id: UUID,
    ttl_days: int = 7
) -> BriefingToken:
    token = BriefingToken(
        token=uuid4(),
        type=type,
        principal_id=principal_id,
        situation_id=situation_id,
        briefing_run_id=briefing_run_id,
        expires_at=datetime.utcnow() + timedelta(days=ttl_days),
        created_at=datetime.utcnow()
    )
    return token
```

**Token validation (on every action):**
1. Check token exists in `briefing_tokens`
2. Check `expires_at > now()`
3. Check `used_at IS NULL`
4. Mark token as `used_at=now()` (idempotency: return cached result if token already used within 60s)

**Token cleanup (cron job, daily):**
```sql
DELETE FROM briefing_tokens WHERE expires_at < NOW() - INTERVAL '30 days';
```

---

## 4. Implementation Phases

### Phase 9A — Data Model & Registry (✅ COMPLETE — 2026-04-01)

| Item | Status |
|------|--------|
| `assessment_runs` Supabase table | ✅ Done |
| `kpi_assessments` Supabase table | ✅ Done |
| `MonitoringProfile` Pydantic model | ✅ Done |
| `AssessmentRun`, `KPIAssessment` models | ✅ Done |
| KPI registry fields (`comparison_period`, `volatility_band`, etc.) | ✅ Done |

### Phase 9B — Situation Monitor (🔄 IN DEVELOPMENT)

| Item | Status | Notes |
|------|--------|-------|
| `run_situation_monitor.py` entry point | 🔄 In Development | Sequential SA-per-KPI loop, error isolation, progress logging |
| Agent initialization sequence | 🔄 In Development | PC Agent context resolution, orchestrated SA calls |
| Assessment run lifecycle (Steps 1–6) | 🔄 In Development | SA measurement, persistence, DA gating, completion |
| Delta detection & situation states | ⏳ Planned | Maps to Phase 9C |
| Idempotency & error resilience | ⏳ Planned | Resume on crash, dedup logic |
| Unit tests (run_situation_monitor_unit.py) | ⏳ Planned | Test orchestration, error cases, idempotency |
| Integration test (full workflow) | ⏳ Planned | End-to-end SA→DA with Supabase |

**Dependencies:** Phase 9A (Supabase tables, models), SA Agent (operational), PC Agent (operational), Orchestrator (operational)

### Phase 9C — Situation State Management (📋 PLANNED)

| Item | Status |
|------|--------|
| `situation_actions` Supabase table | 📋 Planned |
| Situation state enum: `new`, `snoozed`, `delegated`, `request_info`, `acknowledged` | 📋 Planned |
| Delta detection logic in Situation Monitor | 📋 Planned |
| Decision Studio UI: show situation state badges | 📋 Planned |

**Dependencies:** Phase 9B complete

### Phase 9D — PIB Composition Engine (📋 PLANNED)

| Item | Status |
|------|--------|
| `briefing_runs` Supabase table | 📋 Planned |
| PIB email composition (content sections, templates) | 📋 Planned |
| Email delivery via SMTP (`aiosmtplib` + Jinja2) | 📋 Planned |
| RACI-based delegate recommendation | 📋 Planned |
| `POST /api/v1/pib/run` endpoint | 📋 Planned |
| Unit tests (pib_composition_unit.py) | 📋 Planned |

**Dependencies:** Phase 9B complete, Phase 9C (situation states)

### Phase 9E — Secure Token System & One-Click Actions (📋 PLANNED)

| Item | Status |
|------|--------|
| `briefing_tokens` Supabase table | 📋 Planned |
| Token generation & validation | 📋 Planned |
| `GET /token/{token}` validation endpoint | 📋 Planned |
| `POST /delegate/{token}` confirmation page | 📋 Planned |
| Deep link auto-authentication (Decision Studio route) | 📋 Planned |
| Action endpoints: snooze, delegate, request_info, approve | 📋 Planned |
| Integration test (full email → action flow) | 📋 Planned |

**Dependencies:** Phase 9D complete, briefing email sent to test principal

### Phase 9F — Briefing Preferences on Principal Profile (📋 PLANNED)

| Item | Status |
|------|--------|
| `briefing_frequency` field (daily, weekly, off) | 📋 Planned |
| `briefing_format` field (detailed, digest) | 📋 Planned |
| Scheduled PIB runs (cron or timer) | 📋 Planned |
| Registry UI: edit principal briefing prefs | 📋 Planned |

**Dependencies:** Phase 9E complete

### Phase 9G — Decision Studio UI Integration (📋 PLANNED)

| Item | Status |
|------|--------|
| Load situations from `assessment_runs` instead of running SA live | 📋 Planned |
| Display situation state badges (new, snoozed, delegated, etc.) | 📋 Planned |
| Update `kpi_evaluated_count` from assessment data | 📋 Planned |
| Test: verify no duplicate situations from pre-computed assessment | 📋 Planned |

**Dependencies:** Phase 9B–9C complete

---

## 5. Dependencies & Prerequisites

### Existing (Already Built)

- ✅ `assessment_runs`, `kpi_assessments` Supabase tables — Phase 9A
- ✅ `MonitoringProfile`, `AssessmentRun`, `KPIAssessment` Pydantic models — Phase 9A
- ✅ A9_Situation_Awareness_Agent with monitoring profile support — operational
- ✅ A9_Principal_Context_Agent — operational
- ✅ A9_Deep_Analysis_Agent — operational
- ✅ A9_Orchestrator_Agent — operational
- ✅ A9_Value_Assurance_Agent — operational
- ✅ `situations` Supabase table (from Phase 8)
- ✅ `value_assurance_solutions`, `value_assurance_evaluations` tables (from Phase 7)

### To Be Built

- 🔨 Phase 9B: `run_situation_monitor.py` entry point + orchestration
- 🔨 Phase 9C: `situation_actions` table + delta detection
- 🔨 Phase 9D: PIB composition + SMTP delivery
- 🔨 Phase 9E: `briefing_tokens` table + one-click action endpoints
- 🔨 Phase 9F: Principal profile extensions (briefing preferences)
- 🔨 Phase 9G: Decision Studio UI integration

---

## 6. Technical Considerations

### 6.1 Protocol Compliance

All Phase 9 work follows Agent9 A2A protocol requirements:

1. **Agent Instantiation** — Always via `AgentRegistry.get_agent()` or `AgentClass.create_from_registry()`
2. **Pydantic Models Only** — No raw dicts in agent-to-agent communication
3. **LLM Routing** — All LLM calls via A9_LLM_Service_Agent
4. **Orchestrator-Driven** — No direct agent method calls outside orchestrator
5. **Logging** — Via `logging.getLogger(__name__)` (interim; target: `A9_SharedLogger`)

### 6.2 Performance Considerations

**Assessment Run Duration:**
- Per-KPI SA: ~500ms (metric fetch + anomaly detection)
- Per-KPI DA (if escalated): ~2–3 seconds (Is/Is Not analysis, LLM synthesis)
- For 35 KPIs, expect ~20–40 min runtime (sequential; ~3 DA escalations)

**Optimization strategies (future):**
- Parallel DA calls via asyncio tasks (HITL approval constraint still applies)
- Caching of metric data for 1-hour window
- Delta-only re-analysis (skip unchanged KPIs)

### 6.3 Error Handling & Resilience

**Per-KPI error isolation:**
- Single KPI failure does not abort run
- Mark `kpi_assessments.status = "error"`, log exception
- Resume with next KPI

**Run resumption (on crash):**
- Check `assessment_runs.status = "running"` on startup
- Query `kpi_assessments` for last completed KPI
- Resume from next KPI in sequence

**Token expiry management:**
- Daily cron job deletes expired tokens (30-day grace period)
- Invalid token request returns 410 (Gone), not 404

### 6.4 Notification Delivery

**Email delivery guarantees:**
- Resend API (recommended): ~99.9% uptime, ~60s delivery
- Fallback to console logging if SMTP fails (for dev/test)
- Retry logic: 3 attempts with exponential backoff (1s, 5s, 30s)

**Bounce/complaint handling (future):**
- Track bounces in `principal_profiles.email_valid = false`
- Pause briefings for invalid addresses

---

## 7. Migration Path from `run_cfo_assessment.py`

The existing `run_enterprise_assessment.py` will be replaced, not evolved:

**Old (broken):**
```bash
python run_enterprise_assessment.py [--principal <id>] [--kpi <id>]
```

**New (Phase 9B):**
```bash
python run_situation_monitor.py --principal <principal_id> --client <client_id> [--dry-run]
```

**Key changes:**
1. **Real PC Agent integration** — Resolves principal context, not guesses it
2. **Orchestrated calls** — Uses same SA call chain as Decision Studio UI
3. **Per-KPI monitoring profiles** — No hardcoded timeframes
4. **Delta detection** — Identifies new vs. known situations
5. **Scheduled execution** — Not ad-hoc scripting

---

## 8. Success Criteria

### Phase 9B (Situation Monitor)

- ✅ Situation Monitor runs for a principal+client without errors
- ✅ Assessment run persists to Supabase with accurate KPI counts
- ✅ SA and DA results stored in `kpi_assessments` with correct status
- ✅ Error handling isolates single-KPI failures without aborting run
- ✅ Idempotency: re-running same principal+client does not duplicate situations
- ✅ Unit tests cover happy path, error cases, idempotency
- ✅ Integration test covers full SA→DA pipeline with Supabase

### Phase 9D–9E (PIB Email + One-Click Actions)

- ✅ PIB email generates with all sections (new situations, solutions, managed)
- ✅ All email links are token-secured and single-use
- ✅ Snooze, delegate, request_info actions persist to `situation_actions`
- ✅ Deep-link token auto-authenticates principal and pre-loads Decision Studio
- ✅ RACI delegate recommendation works correctly
- ✅ Email delivered successfully (dry-run and live modes)
- ✅ End-to-end integration test: run assessment → send PIB → execute email action

---

## 9. References & Related Documents

- [A9_Situation_Awareness_Agent_PRD](a9_situation_awareness_agent_prd.md) — SA agent behavior, monitoring profiles
- [A9_Value_Assurance_Agent_PRD](a9_value_assurance_agent_prd.md) — VA solution tracking
- [A9_Orchestrator_Agent_PRD](a9_orchestrator_agent_prd.md) — Orchestration patterns, agent initialization
- [Assessment Models](../../src/agents/models/assessment_models.py) — Pydantic data models
- [DEVELOPMENT_PLAN.md](../../../DEVELOPMENT_PLAN.md) — Phase roadmap, tech debt, known issues
- [Reference: Production Deployment](../../../reference_production_deployment.md) — Env vars, SMTP config

---

## 10. Change Log

| Date | Phase | Change |
|------|-------|--------|
| 2026-04-01 | 9A | Initial Phase 9A complete: Supabase tables, models, monitoring profile fields |
| 2026-04-01 | 9B | PRD published; Phase 9B implementation in progress |
| TBD | 9C | Situation state management, delta detection |
| TBD | 9D–9E | PIB composition, email delivery, one-click actions |
| TBD | 9F | Scheduled briefing runs, principal preferences |
| TBD | 9G | Decision Studio UI integration, unified situation stream |

---

**Document Metadata:**
- **Type:** Product Requirements Document (PRD)
- **Status:** Active (Phase 9B in development, 9D–9G planned)
- **Last Updated:** 2026-04-01
- **Owner:** Agent9-HERMES Project
- **Replaces:** `docs/prd/agents/a9_briefing_agent_concept.md`
