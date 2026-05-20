# Decision Studio — Threat Model
**Version:** 1.0  
**Date:** May 2026  
**Audience:** Technical evaluators, AI architects, enterprise security teams  
**Scope:** Pilot-stage deployment (single-tenant demo, pre-SOC 2)

---

## Purpose

This document identifies the failure modes and security risks present in Decision Studio at its current stage of development, states which are mitigated, and explicitly names what is deferred to pilot hardening. The intent is transparent disclosure, not marketing.

---

## Risk Register

### 1. LLM Hallucination — Plausible but Wrong Analysis

**What goes wrong:** The LLM produces a confident, well-structured analysis that is factually incorrect — wrong root cause, wrong market context, or fabricated statistics.

**Likelihood:** Medium. KT Is/Is Not constrains the DA Agent's LLM to interpreting structured query results — the hallucination surface is narrower than open-ended prompting. SF and MA agents use web search (Perplexity) and synthesized context; hallucination risk is higher there.

**Mitigated by:**
- DA Agent: LLM receives dimensional SQL results as ground truth; it interprets, not speculates
- VA Agent: Attribution is computed from warehouse data (DiD), not from LLM claims
- All agents: Pydantic v2 models validate structured output fields — free-text narrative is labeled as such
- Two HITL gates: an executive reviews and challenges analysis before any action is taken
- Confidence scoring: VA explicitly scores and narrates confidence level (HIGH / MODERATE / LOW) based on control group quality and data volume

**Not mitigated:** MA Agent market signals rely on Perplexity web search synthesis — factual errors in web sources propagate. SF persona recommendations include qualitative judgment that cannot be data-validated. Both are labeled as "judgment" in the briefing, not as verified facts.

**Deferred:** Automated factual grounding checks (e.g., citation verification) — out of scope for pilot stage.

---

### 2. Data Pipeline Failure — Bad Data In, Bad Analysis Out

**What goes wrong:** The data warehouse returns incorrect values (ETL failure, schema change, NULL propagation, timezone mismatch), and the system produces a confident but wrong situation card.

**Likelihood:** Medium. DuckDB and BigQuery connectors are operationally stable. SQL Server is operational in dev but not yet production-tested. ETL issues in the source warehouse are outside the system's control.

**Mitigated by:**
- KPI definitions include threshold bounds and expected ranges — SA Agent's anomaly detection will fire on outlier values, which may surface ETL corruption
- HITL Gate 1 (Problem Refinement): a principal who knows the business can spot implausible analysis and question it
- Situation cards display the raw KPI value and the comparison period — the executive sees the numbers, not just the narrative

**Not mitigated:** No automated data quality checks on ingested values. No schema-change detection. If the warehouse silently returns wrong data, the system will analyze it confidently.

**Deferred:** Integration with data quality frameworks (Great Expectations, dbt tests) — roadmap item, not pilot-stage requirement.

---

### 3. Multi-Tenant Data Leakage

**What goes wrong:** A request authenticated for Client A returns registry records (KPIs, principals, data products) belonging to Client B.

**Likelihood:** Low, by design. The risk is in application-layer bugs, not in the data model.

**Mitigated by:**
- `client_id` is a composite primary key component on every Supabase registry table — isolation enforced at the database level
- All API list endpoints accept and apply `client_id` as a strict match filter — no `is not None` guards that allow unscoped records to leak
- SA Agent's `_get_relevant_kpis()` filters by client_id — this filter cannot be weakened for test convenience (enforced by team rule)
- Record IDs are semantic (`"net_revenue"`, not `"lubricants_net_revenue"`) — tenant identity lives in `client_id`, not encoded in IDs

**Not mitigated:** No row-level security (RLS) policies enabled in Supabase at pilot stage — tenant isolation is application-enforced, not database-enforced. A bug in the filter logic could leak records across tenants.

**Deferred:** Supabase RLS policies on all registry tables — required before multi-tenant production deployment. Currently blocked by: no authentication layer (see below).

---

### 4. No Authentication or Authorization Layer

**What goes wrong:** The Decision Studio API is unauthenticated. Any party with network access to the Railway backend URL can read KPIs, principals, and analysis results, or trigger workflows.

**Likelihood:** High impact if exploited; low likelihood in practice because the Railway URL is not publicly advertised and the demo uses non-sensitive synthetic/sanitized data.

**Mitigated by:**
- Pilot deployments will use client-specific Railway environments with Railway-level network controls
- Demo data (Lubricants dataset) contains no real client financial data — it is synthetic
- The `client_id` filter means an unauthenticated caller must know a valid client_id to retrieve relevant records

**Not mitigated:** No JWT, OAuth, or SSO. No per-user access control. No rate limiting on API endpoints. No audit log of who called what.

**Deferred:** Authentication (JWT + Supabase Auth or Auth0) and authorization (role-based, principal-scoped) are **Infra B** — explicitly scheduled for Jul–Aug 2026, before the first pilot goes live with real client data. This is the single largest pre-pilot hardening item.

---

### 5. LLM Provider Dependency (Single Point of Failure)

**What goes wrong:** Anthropic API is unavailable (outage, rate limit, account issue). All LLM-dependent agents fail — DA, SF, MA, VA narrative generation.

**Likelihood:** Low for extended outages. Anthropic's Claude API has strong uptime historically. Rate limits are a higher practical risk under load.

**Mitigated by:**
- `A9_LLM_Service_Agent` is the single routing point — failover logic is in one place, not distributed across agents
- Task-based model routing means Haiku failures fall back to Sonnet configuration (configurable)
- SA Agent's anomaly detection (threshold checks, change-point detection) is non-LLM — situations are still detected even if LLM narrative fails

**Not mitigated:** No retry queue or circuit breaker on LLM calls. No OpenAI fallback in production (wired in code, not tested in production). No graceful degradation path for SF agent (no LLM = no solution options).

**Deferred:** Queue-based LLM call management with retry and fallback — post-pilot infrastructure item.

---

### 6. Prompt Injection via Data Warehouse Content

**What goes wrong:** Malicious content in the data warehouse (e.g., a product name containing an LLM instruction) is incorporated into a prompt and alters agent behavior.

**Likelihood:** Low in the current customer profile (mid-market FP&A, structured warehouse data). Higher risk if the platform expands to ingest unstructured content (documents, emails, CRM notes).

**Mitigated by:**
- Structured Pydantic models are used to pass data between agents — raw string interpolation of warehouse values into prompts is avoided by design
- DA Agent prompts include dimensional query results as structured JSON, not as free-text string interpolation
- HITL Gate 1 (Problem Refinement): an executive reviews the DA output before solutions are generated

**Not mitigated:** No systematic prompt injection scanning. No content sanitization layer on warehouse values before LLM inclusion.

**Deferred:** Systematic prompt injection defenses — lower priority for structured financial data use case; will re-evaluate if unstructured data ingestion is added.

---

### 7. Briefing Token Security (Single-Use Deep Links)

**What goes wrong:** A PIB briefing email contains a single-use token for deep-link access, delegation, or approval. If the token is intercepted or the email is forwarded, an unintended party could approve a recommendation.

**Likelihood:** Low — tokens are single-use, expire after use, and are stored in Supabase with audit trail.

**Mitigated by:**
- Briefing tokens are single-use — once consumed, re-use returns an error
- Token table stores: token, action type, situation ID, principal ID, created timestamp, used timestamp
- Delegation flow creates a new token for the delegate — original token is not transferred

**Not mitigated:** Tokens do not expire by time (only by use). A long-lived unactivated token is valid indefinitely.

**Deferred:** Time-based token expiry (e.g., 48-hour window) — minor hardening item.

---

## Maturity Summary

| Risk | Severity | Mitigated? | Deferred To |
|------|----------|-----------|-------------|
| LLM hallucination | High | Partially — HITL + data-constrained prompts | Ongoing design discipline |
| Bad data in | High | Partially — HITL visibility | Integration with data quality tooling |
| Multi-tenant leakage | Critical | Partially — app-enforced filters | Supabase RLS + auth (Infra B) |
| No authentication | Critical | None — demo data only | Infra B (Jul–Aug 2026) |
| LLM provider outage | Medium | Partially — single routing point | Queue + circuit breaker post-pilot |
| Prompt injection | Low | Partially — structured data pipeline | Re-evaluate at unstructured data milestone |
| Token security | Low | Mostly — single-use | Time-based expiry (minor item) |

**Bottom line:** The system is appropriately hardened for demo and pilot with synthetic/sanitized data. It is not yet appropriate for production deployment with real client financial data until Infra B (authentication + Supabase RLS) ships. That work is on the roadmap and explicitly scheduled before the first production pilot.
