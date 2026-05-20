# Decision Studio — Architecture Decision Record
**Version:** 1.0  
**Date:** May 2026  
**Audience:** Technical evaluators, AI architects, enterprise procurement

---

## Purpose

This document records the key architectural decisions made during the design of Decision Studio (codebase: Agent9-HERMES). For each decision, it states the context, the options considered, the choice made, and the rationale. The goal is to give a technical evaluator a defensible account of why the system is built the way it is — not just what it does.

---

## ADR-001: Centralized LLM Routing

**Status:** In force since Phase 3 (Sep 2025)

### Context

A multi-agent system that calls LLMs from multiple agents creates several operational problems at scale:
- Token usage is invisible and uncontrollable
- Model selection is inconsistent (one agent uses GPT-4, another Haiku)
- Provider migration requires touching every agent file
- Prompt guardrails cannot be applied uniformly
- Cost and latency attribution is impossible

### Options Considered

| Option | Description | Rejected Because |
|--------|-------------|-----------------|
| Direct LLM calls per agent | Each agent imports and calls `anthropic`/`openai` directly | No central visibility, no guardrails, fragile to provider changes |
| Shared utility module | Common helper functions in a shared module | Functions, not an agent — no lifecycle, no registry, no token tracking |
| Dedicated LLM Service Agent | All LLM calls route through a single registered agent with full lifecycle management | — selected — |

### Decision

All LLM calls in the system route through `A9_LLM_Service_Agent`. No agent file may directly import `anthropic` or `openai` (enforced by pre-commit hook). The LLM Service Agent is responsible for:
- Provider selection (Anthropic Claude / OpenAI, set by `LLM_PROVIDER` env var)
- Task-based model routing (Haiku for fast/cheap tasks, Sonnet for synthesis)
- Token tracking and usage logging
- Prompt guardrails and output validation
- Model override propagation through `A9_LLM_AnalysisRequest.model`

### Consequences

- Positive: Provider swap is a single-file change; no scattered API keys; uniform token tracking; guardrails apply everywhere
- Positive: Task-based routing (Stage 1 persona calls → Haiku, synthesis → Sonnet) is configured centrally, not in each agent
- Negative: All LLM failures surface through a single chokepoint — this is mitigated by async/await architecture and per-call error handling
- Accepted debt: The LLM Service Agent itself is not yet behind a queue or rate limiter — deferred to pilot hardening

---

## ADR-002: Human-in-the-Loop at Two Specific Gates

**Status:** In force since Phase 5 (Nov 2025); Gate 2 interactive workspace shipped Phase 8

### Context

Decision Studio operates in a domain with real financial consequences. An architecture that autonomously applies recommendations — even well-reasoned ones — creates three problems:

1. **Trust failure:** Executives will not trust a system that acts without their approval, regardless of quality
2. **Accountability gap:** If the AI recommendation leads to a bad outcome and no human reviewed it, the question becomes "why did you let an AI decide this?"
3. **Data blindness:** The system cannot know what executives know — undocumented decisions, stakeholder dynamics, pending strategic pivots that haven't hit the data yet

### Options Considered

| Option | Description | Rejected Because |
|--------|-------------|-----------------|
| Fully automated pipeline | SA → DA → SF → action, no human gates | Unacceptable in enterprise finance context; no accountability |
| Notification only | System runs full pipeline and notifies human of outcome | Human approval is post-hoc, not decision-shaping |
| HITL at final approval only | Human approves the recommendation but has no structured engagement with the analysis | Rubber-stamping AI output; misses the value of executive context |
| **HITL at two meaningful gates** | Gate 1: validate the problem; Gate 2: interrogate the solutions | — selected — |

### Decision

Two gates are enforced in the pipeline:

**Gate 1 — Problem Refinement (post-DA, pre-SF)**  
Before the Solution Finder council convenes, the principal validates the root cause diagnosis. They review the IS/IS NOT table, ask data questions (routed to Data Product Agent via NLP Interface), and confirm or refine the problem statement. This is not optional — the SF agent is not invoked until refinement is complete.

**Gate 2 — Solution Decision (post-SF, pre-approval)**  
The Executive Briefing is an interactive workspace, not a static document. The principal interrogates the recommendations via Solution Q&A dialogue before approving. The system assembles a full context stack (DA + SF Stage 1/2/3 + MA signals + Principal Context) to answer questions with transparency tier labeling. The approval button is below the briefing and Q&A, not above it.

**Design principle:** When the principal disagrees with the system's recommendation, that is the system working correctly. The principal's judgment is the final authority. The system presents; it does not argue.

### Consequences

- Positive: Executives feel they did due diligence, not rubber-stamping — critical for adoption
- Positive: Gate 1 captures organizational context (political, strategic) that the data pipeline cannot
- Positive: Gate 2 Q&A turns a static briefing into an interactive decision workspace — differentiator vs. BI dashboards
- Negative: Pipeline is not fully automated; a principal must actively engage to complete a workflow
- Accepted by design: Automation of the approval gate is a future enterprise feature (email → delegate → approve in one click), not appropriate at pilot stage

---

## ADR-003: Registry-Backed Configuration (Supabase) Over Config Files

**Status:** In force since Phase 4 (Oct 2025); YAML fallbacks explicitly removed Mar 2026

### Context

Early versions of the system stored KPI definitions, principal profiles, business processes, and data product contracts in YAML files checked into the repository. This created several problems at scale:

1. **Config drift:** YAML files diverge across environments (dev/staging/production) silently
2. **Multi-tenant impossibility:** YAML files cannot enforce `client_id` isolation; all tenants see all records
3. **No audit trail:** Changes to KPI thresholds or principal mappings leave no trace in the registry
4. **Deployment coupling:** Changing a KPI threshold requires a code deploy, not a data operation
5. **Runtime inconsistency:** File-backed providers can return different results depending on when the file was last written

### Options Considered

| Option | Description | Rejected Because |
|--------|-------------|-----------------|
| YAML files in repo | KPI/principal/process definitions in checked-in YAML | Multi-tenant unsafe; no audit; config drift; requires code deploy for data changes |
| Environment variables | Configuration injected at startup | Doesn't scale to 35+ KPIs, 14+ principals, multiple data products |
| Supabase (PostgreSQL) with YAML fallback | Database-backed with file fallback when database is unavailable | Fallback creates split-brain; masks connectivity errors; defeated the purpose |
| **Supabase only — no fallback** | Single source of truth; if Supabase returns empty, log error and return empty | — selected — |

### Decision

Supabase (PostgreSQL, hosted cloud) is the sole registry backend. No YAML file reads for registry data are permitted anywhere in the agent codebase. This is enforced by:

- A `RegistryFactory` that does not auto-create YAML-backed providers
- A documented rule: if a provider returns no data, log an error and return empty — never load from files
- The `src/registry/` YAML files have been deleted; `src/registry_references/` contains schema definitions only (not runtime data)

**Multi-tenant design:** `client_id` is a composite primary key component on every registry table. Tenant isolation is enforced at the database level (composite PK) and at the application level (strict match filters — no `is not None` guards that allow unscoped records to leak). Every API list endpoint accepts `client_id` as a required query parameter.

**Data change protocol:** Registry data changes (new KPI, updated threshold, new principal) go through seed scripts in `scripts/clients/<client_id>.py` and are applied via `scripts/onboard_client.py`. Code and data travel separately — code via git → Railway auto-deploy; data via explicit seed-script run against production Supabase.

### Consequences

- Positive: Adding a new client requires a seed script, not a code deploy
- Positive: Multi-tenant isolation is enforced at the data model level, not at the application layer
- Positive: KPI threshold changes take effect without restarting the backend
- Positive: Full audit trail of data changes via Supabase's built-in logging
- Negative: Requires Supabase to be running; local development uses Supabase CLI with Docker
- Accepted debt: No registry admin UI yet (read-only Registry Explorer exists; write-back via seed scripts only) — deferred to Phase 2

---

## ADR-004: Typed Pydantic Contracts at Every Agent Boundary

**Status:** In force from system inception

### Context

Multi-agent systems fail in two ways: agents produce outputs that downstream agents cannot consume (type mismatch, missing fields), or they fail silently (a missing field becomes `None`, the downstream agent produces wrong output, no error is raised). In a financial decision context, silent failures are worse than loud ones.

### Decision

Every agent-to-agent communication uses Pydantic v2 models — no raw dicts, no `Any` types at agent boundaries. Each agent has explicit input and output model definitions in `src/agents/models/`. Pydantic validates on instantiation; a malformed payload raises `ValidationError` immediately, preventing silent propagation of bad data.

**Additional constraint:** Agent instantiation uses the registry (`await AgentRegistry.get_agent("name")`) — never direct class construction (`AgentClass(config)`). This ensures lifecycle methods (`create`, `connect`, `disconnect`) have been invoked before the agent handles requests.

### Consequences

- Positive: Type errors surface at the producing agent, not three pipeline stages later
- Positive: Agent contracts are self-documenting — the Pydantic model is the API spec
- Negative: Adding a new field to an agent's output requires updating the model and all consumers
- Accepted: This is intentional. Loose coupling across agent boundaries creates the silent failure modes we're specifically avoiding

---

## ADR-005: KT Is/Is Not as the Diagnostic Framework (Not Open-Ended LLM Analysis)

**Status:** In force since Phase 2 (Aug 2025)

### Context

The Deep Analysis Agent's original design used open-ended LLM prompts to "analyze why a KPI declined." This produced plausible-sounding explanations that were frequently unverifiable and occasionally hallucinatory. The LLM was operating outside of data — reasoning from patterns in training data, not from the actual dimensional structure of the client's warehouse.

### Decision

The DA Agent's diagnostic structure is Kepner-Tregoe Problem Analysis: a systematic two-column framework (IS / IS NOT) that computes dimensional breakdowns from SQL queries before invoking the LLM.

The LLM's role in the DA Agent is **insight extraction from structured query results**, not open-ended diagnosis. The SQL runs first; the LLM interprets the pattern the data reveals.

**Secondary benefit — emergent:** The IS NOT column (unaffected dimensions) becomes the control group for the Value Assurance Agent's Difference-in-Differences attribution. The same analysis that diagnoses the problem creates the measurement framework for proving the fix worked. This dual-use was not designed intentionally; it is a structural advantage of choosing a dimensional framework over unstructured LLM analysis.

### Consequences

- Positive: Diagnostic output is constrained by actual data — hallucination surface is minimized
- Positive: IS NOT dimensions double as attribution control groups for VA — no separate measurement framework required
- Positive: Same input data → same IS/IS NOT output (deterministic); LLM variation is in narrative only
- Negative: Requires structured dimensional data in the warehouse; not all KPI problems decompose along clean GROUP BY dimensions
- Accepted limitation: KT requires historical baselines. Truly novel events (no prior data) produce low-confidence analysis — surfaced transparently in the confidence scores

---

## Summary Table

| Decision | Chosen Approach | Primary Rationale |
|---------|----------------|------------------|
| LLM routing | Centralized through LLM Service Agent | Visibility, guardrails, provider portability |
| Human gates | Two HITL gates (post-DA, post-SF) | Accountability, executive trust, organizational context capture |
| Registry backend | Supabase only, no YAML fallback | Multi-tenant isolation, audit trail, no-deploy config changes |
| Agent contracts | Pydantic v2 models at every boundary | Fail-fast on type errors, self-documenting APIs |
| Diagnostic framework | KT Is/Is Not (data-first, LLM interprets) | Constrain hallucination; emergent control groups for VA |
