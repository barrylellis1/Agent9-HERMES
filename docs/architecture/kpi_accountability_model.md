# KPI Accountability Model

## Overview

This document defines a dimensional accountability model for KPI-to-principal assignments in Agent9-HERMES. The model solves the core signal-to-noise problem: principals receive situations for KPIs they cannot directly control, leading to alert fatigue and platform abandonment.

The core principle: **A principal is accountable for a KPI at the dimensional scope they control.** Same KPI, different scope = different responsible principals. This eliminates the need for per-principal preference layers (snooze, hide, filter) by routing the right signal to the right decision-maker by construction.

---

## The Problem

### Current State
- KPI assignments are enterprise-wide with no dimensional scoping
- CFO owns Net Revenue across the entire enterprise
- Regional VP also owns Net Revenue but has no way to specify "only EMEA"
- Situation detection fires for all Net Revenue events, then downstream agents or UI filters suppress unwanted situations
- Principals are buried in noise and disengage from the platform

### Why Preferences Don't Work
Snooze/hide/filter layers are downstream band-aids:
- They don't prevent noise generation (system still runs analysis on irrelevant data)
- They're fragile (user preferences get lost, require frequent re-configuration)
- They create maintenance burden (who owns the snooze rules?)
- They scale poorly (10 KPIs × 5 principals = 50 potential snoozed situations)

### Why Dimensional Scoping Works
The variance itself is dimensional. When DA (Deep Analysis) agent runs IS/IS NOT analysis, it identifies which dimension is driving the breach:
- "Net Revenue down 12%" — caused by "Industrial LOB down 18%, others flat"
- This dimension match should determine routing, not a filter applied after the fact

---

## Target Data Model

### Registry Structure

A new `kpi_accountability` registry (or extension to `principal_profiles` registry) with the following schema:

```yaml
accountabilities:
  - id: acc_001
    kpi_id: net_revenue
    principal_id: cfo_001
    scope_dimension: null           # null = enterprise-wide (responsible)
    scope_value: null               # null = all values in this dimension
    role: accountable               # accountable | responsible
    created_at: 2026-04-06T12:00:00Z
    created_by: admin
    notes: "CFO accountable for group revenue"

  - id: acc_002
    kpi_id: net_revenue
    principal_id: emea_vp_001
    scope_dimension: geography      # optional — null = enterprise-wide
    scope_value: EMEA               # optional — corresponds to data dimension value
    role: responsible               # accountable | responsible
    created_at: 2026-04-06T12:00:00Z
    created_by: admin
    notes: "EMEA VP responsible for regional revenue"

  - id: acc_003
    kpi_id: gross_margin_pct
    principal_id: industrial_director_001
    scope_dimension: line_of_business
    scope_value: Industrial
    role: accountable               # accountable = decision-maker, sets targets
    created_at: 2026-04-06T12:00:00Z
    created_by: admin
    notes: "LOB Director accountable for margin in Industrial segment"
```

### Key Fields

| Field | Type | Purpose |
|---|---|---|
| `id` | string | Unique accountability assignment ID |
| `kpi_id` | string | References KPI in kpi registry |
| `principal_id` | string | References principal in principal_profiles registry |
| `scope_dimension` | string | Data dimension name (geography, line_of_business, cost_center, etc.) — null for enterprise-wide |
| `scope_value` | string | Value in that dimension (EMEA, Industrial, CC-1234) — null for all values |
| `role` | enum | `accountable` (decision-maker, sets targets) or `responsible` (contributor, execution) |
| `created_at` | timestamp | Audit trail |
| `created_by` | string | Audit trail — which admin created this |
| `notes` | string | Human-readable context for the assignment |

### Pydantic Model (Python)

```python
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AccountabilityRole(str, Enum):
    """Role level for KPI accountability."""
    ACCOUNTABLE = "accountable"  # Decision-maker, sets targets
    RESPONSIBLE = "responsible"  # Contributor, execution

class KPIAccountability(BaseModel):
    """KPI accountability assignment with dimensional scope."""
    id: str
    kpi_id: str
    principal_id: str
    scope_dimension: Optional[str] = None  # null = enterprise-wide
    scope_value: Optional[str] = None      # null = all values in dimension
    role: AccountabilityRole
    created_at: datetime
    created_by: str
    notes: Optional[str] = None
    
    class Config:
        use_enum_values = False
```

---

## Governance Rules

These rules ensure accountability clarity and prevent chaos:

### Mandatory
1. **Singleton Accountable Owner per Scope**
   - For each (kpi_id, scope_dimension, scope_value) tuple, there is at most 1 principal with role=`accountable`
   - Exception: enterprise-wide scope (scope_dimension=null, scope_value=null) can have multiple accountables if split by function (e.g., CFO + COO co-own revenue)

2. **Every KPI Must Have an Accountable Principal at Some Scope**
   - Cannot have a KPI with only `responsible` role assignments
   - Every KPI needs someone who owns the variance and decides on response

3. **Valid Dimension Reference**
   - `scope_dimension` must exist in the target data product's schema (validated against data governance registry)
   - `scope_value` must be a valid value in that dimension (can be validated against cardinality from schema inspection)

### Recommended
4. **Principal Capacity Limit** (8 KPI assignments max per principal)
   - Prevents principal overload
   - Enforces clear lines of accountability
   - Ease of navigation in executive dashboard
   - Warning at 6+ assignments, error at >8

5. **Dimensional Spread Limit**
   - Flag if same KPI assigned to >3 principals without dimensional scoping
   - Indicates unclear accountability structure (should restructure org or scopes)
   - Example: Net Revenue assigned to 5 principals all with scope=enterprise is a red flag

6. **Scope Consistency**
   - If assigning a KPI at dimension D, all higher-level dimensions should also have an accountable principal
   - Example: If LOB Director owns Gross Margin by line_of_business, then a Regional VP cannot own the same KPI by geography alone (no roll-up path)

---

## How Situations Are Routed

### Situation Generation with Dimensional Context

SA (Situation Awareness) agent detects a KPI threshold breach and generates a SituationCard with dimensional context:

```python
class SituationCard(BaseModel):
    kpi_id: str
    metric_value: float
    threshold: float
    breach_type: str  # "threshold_breach" | "trend_reversal" | "anomaly"
    
    # NEW: Dimensional context from variance analysis
    variance_dimension: Optional[str] = None     # e.g., "line_of_business"
    variance_segment: Optional[str] = None       # e.g., "Industrial"
    variance_contribution: Optional[float] = None # e.g., 0.68 (68% of breach)
```

### Accountability-Based Routing

After detecting a situation, SA agent queries the kpi_accountability registry:

```python
# Find all principals accountable for (kpi_id, variance_dimension, variance_segment)
accountabilities = await governance_agent.query_accountabilities(
    kpi_id="gross_margin_pct",
    scope_dimension="line_of_business",
    scope_value="Industrial"
)

# accountabilities = [
#   {principal_id: "industrial_director_001", role: "accountable"},
#   {principal_id: "cfo_001", role: "responsible"}  # rolled up from enterprise accountability
# ]

# Only these principals receive this situation
for acc in accountabilities:
    principal = await pc_agent.get_principal_context(principal_id=acc.principal_id)
    await situation_store.save_situation(
        situation=situation_card,
        principal_id=acc.principal_id,
        visibility=principal.briefing_channel  # email, dashboard, etc.
    )
```

### Roll-Up Logic
If a situation is dimensional (e.g., "Industrial LOB variance"), routing also includes:
- Principals accountable at the parent/aggregate level (CFO who owns enterprise revenue)
- Marked with `visibility: "secondary"` or `priority: "low"` (FYI, not action-required)

---

## LLM-Assisted Onboarding

### The Cold-Start Problem
Manual KPI accountability registry entry is a barrier:
- Requires domain expertise to map org structure to data dimensions
- Slow, error-prone, blocks launch
- Same problem that prevents BI platform adoption

### The Existing Solution (KPI Assistant Pattern)
`A9_KPI_Assistant_Agent` already solves this for schema inspection:
1. User provides database schema (raw SQL or DuckDB introspection)
2. LLM extracts candidate KPIs from column names and descriptions
3. User confirms, refines, or rejects in UI
4. Approved KPIs written to registry

### Same Pattern for Accountability

**A9_Accountability_Import_Agent** (new agent, Phase 12):

1. **Input: HCM Documents**
   - Job descriptions (unstructured text or PDF)
   - Org chart (CSV, JSON, or API integration)
   - Performance review framework / OKR documents
   - RACI matrix (if available)

2. **LLM Extraction Pass**
   - Parse job description for accountability statements: *"accountable for revenue performance across the Industrial segment"*
   - Extract role, KPI mention, and dimensional scope
   - Map org chart to principal IDs
   - Align performance framework KPI names to registry KPI IDs

3. **Candidate Suggestion**
   ```python
   class AccountabilitySuggestion(BaseModel):
       kpi_id: str
       principal_id: str
       scope_dimension: Optional[str]
       scope_value: Optional[str]
       role: AccountabilityRole
       confidence: float  # 0.0-1.0
       extraction_source: str  # e.g., "job_description_line_23"
       reasoning: str  # Why the LLM thinks this is correct
   ```

4. **UI Confirmation**
   - Present suggested accountabilities in tabular form
   - Allow admin to accept, reject, or adjust scope/dimension
   - Show extraction reasoning for transparency
   - Validate against governance rules before save

5. **Registry Persistence**
   - Approved suggestions written to kpi_accountability registry
   - Audit trail captures which suggestions were auto-extracted vs. manually created

### Why This Works
- Reduces onboarding from weeks to days
- Leverages existing, valuable company documents
- LLM errors are caught in human review (no auto-approval)
- Follows proven pattern from KPI Assistant (no novel architecture)

---

## Integration with Existing Agents

### A9_Situation_Awareness_Agent
- **Current**: Generates situation cards for all KPIs a client tracks
- **New**: When detecting a situation, attach `variance_dimension` and `variance_segment`
- **New**: Query kpi_accountability registry to filter situations by principal
- **New**: Add `visibility` field to SituationCard (primary, secondary, hidden)

### A9_Deep_Analysis_Agent
- **Current**: Runs IS/IS NOT analysis to isolate variance drivers
- **No change needed**: Already identifies which dimension drives variance
- **New**: Return dimensional context in AnalysisResponse for routing

### A9_Principal_Context_Agent
- **Current**: Maps principal_id to profile (name, role, briefing channel)
- **New**: Add `get_principal_kpis()` method that returns KPIs by accountability
- **New**: Support filtering KPIs by role (accountable vs. responsible)

### A9_Data_Governance_Agent
- **Current**: Validates registry entries and business term mappings
- **New**: Validate kpi_accountability entries against governance rules
- **New**: Flag violations (no accountable owner, dimension mismatch, etc.)

### Assessment Runs
- **Current**: Assessment tagged with `principal_id` at execution time
- **New**: Assessment tagged with `client_id` (organization scope)
- **New**: SA agent uses kpi_accountability to filter KPIs per principal (not hardcoded principal_id)
- **Result**: One enterprise assessment run, multiple principal-specific views

---

## Phase Plan

### Phase 11: Registry and Routing Foundation
- Add `kpi_accountability` registry (YAML + Supabase dual persistence)
- Add Pydantic models: `KPIAccountability`, `AccountabilitySuggestion`
- Implement governance rule validation in Data Governance Agent
- Update SA agent to query accountability registry when filtering situations
- Add `variance_dimension` and `variance_segment` to SituationCard model
- Update Principal Context Agent: `get_principal_kpis()` method

**Deliverable**: One enterprise assessment run can generate principal-specific situation cards based on accountability scope.

### Phase 12: LLM-Assisted Onboarding
- Build `A9_Accountability_Import_Agent` (LLM extraction from HCM docs)
- Add Admin Console UI for accountability review and confirmation
- Implement `A9_KPI_Assistant_Agent` pattern for accountability suggestions
- Add batch import capability (upload CSV of org chart + job descriptions)
- Build audit trail UI (show extraction source, reasoning, approval history)

**Deliverable**: New customer onboarding: upload org structure documents → LLM suggests accountabilities → admin confirms → registry populated.

### Phase 13: Dashboard and Alerts (Optional)
- Principal dashboard shows only KPIs in scope
- Alert noise reduced by 70%+ (no off-scope situations)
- PIB emails contain only dimensional insights relevant to principal's scope

---

## Success Criteria

1. **Routing by Construction**: Situations are scoped to dimensions at generation time; no post-hoc filtering needed
2. **One Assessment, Many Views**: Single enterprise assessment run generates principal-specific situation feeds based on accountability registry
3. **Governance Enforced**: System prevents invalid accountability assignments (no unaccountable KPIs, no duplicate accountables at same scope)
4. **LLM-Assisted Onboarding**: New client onboarding can import accountability from job descriptions with >80% accuracy (as validated by admin review)
5. **Audit Trail Complete**: Every accountability assignment has created_by, created_at, and extraction source (if LLM-generated)
6. **Alert Fatigue Reduced**: Pilot customer reports >60% reduction in irrelevant situation notifications

---

## What This Replaces

### Snooze/Hide/Filter Preference Layer
- No longer needed; accountability scope replaces post-hoc filtering
- Simplifies UI (no preference panel for hiding situations)

### Manual KPI-to-Principal Mapping in Registry Explorer
- Registry Explorer still shows accountabilities, but entry is now via LLM-assisted import + confirmation UI
- Reduces data entry burden

### Principal-Scoped Assessment Runs
- Current: Run assessment once per principal (N assessment runs for N principals)
- New: One enterprise assessment run, multiple principal-specific views generated at routing time
- Reduces compute cost and data duplication

---

## Related Documents

- `principal_id_based_lookup_plan.md` — Refactoring to ID-based principal lookups (prerequisite)
- `a9_situation_awareness_agent_prd.md` — SA agent capabilities and extensions
- `a9_principal_context_agent_prd.md` — Principal context lookup and scope filtering
- `DEVELOPMENT_PLAN.md` — Active development timeline (Phase 11+)
