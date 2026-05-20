# Decision Studio — Known Issues Log
**Version:** 1.0  
**Date:** May 2026  
**Audience:** Technical evaluators, pilot prospects, enterprise procurement  
**Purpose:** Transparent disclosure of known limitations and deferred hardening items

---

## Why This Document Exists

Enterprise software at pilot stage always has known issues. The question is whether the vendor knows what they are and has a plan. This document owns Decision Studio's current limitations directly — no euphemisms, no "planned enhancements" language that buries severity.

Issues are classified by severity and tagged with their target resolution phase.

---

## Severity Classifications

| Severity | Meaning |
|----------|---------|
| **Critical** | Blocks production deployment with real client data; must be resolved before first paid pilot |
| **High** | Workaround exists; known edge cases in specific scenarios |
| **Medium** | Deferred by design; will not affect pilot scope |
| **Low** | Tech debt; no user impact in current scope |

---

## Critical Issues (Pre-Pilot Blockers)

### KI-001: No Authentication or Authorization Layer

**Severity:** Critical  
**Status:** Scheduled — Infra B, Jul–Aug 2026  
**Affects:** All API endpoints

The Decision Studio backend has no authentication. Any caller with the Railway URL can read registry data, trigger workflows, and retrieve analysis results. This is acceptable for demo with synthetic data; it is not acceptable for production deployment with real client data.

**What is in place:** `client_id` filtering provides logical tenant isolation at the data layer. Demo environments use non-public URLs and synthetic data only.

**Resolution plan:** JWT-based authentication + Supabase Auth (or Auth0 SSO integration). Role-based authorization: principal profiles will scope which KPIs and analysis results each user can access. Explicitly scheduled as Infra B before first live pilot.

---

### KI-002: No Supabase Row-Level Security (RLS)

**Severity:** Critical  
**Status:** Blocked by KI-001 (no auth = no user identity to apply RLS against)  
**Affects:** All registry tables (KPIs, Principals, Data Products, Business Processes)

Tenant isolation is currently enforced at the application layer (strict `client_id` match filters in every query). Supabase's database-level RLS policies are not yet enabled. A bug in application-layer filter logic could leak records across tenants; RLS would prevent this at the database level.

**Resolution plan:** RLS policies on all registry tables, configured after KI-001 authentication ships and user identity is available.

---

## High Issues (Workarounds in Place)

### KI-003: Principal Lookup Uses Role Names, Not Principal IDs

**Severity:** High  
**Status:** Known limitation; migration plan documented  
**Affects:** `A9_Principal_Context_Agent`; principal profile retrieval

The Principal Context Agent looks up profiles by role name (e.g., `"CFO"`, `"COO"`) rather than by principal ID (e.g., `"cfo_001"`). This creates case sensitivity fragility, breaks when two principals hold the same role title, and doesn't support users with multiple roles.

**Current workaround:** Principal profiles are seeded with unique role-to-principal mappings. Duplicate roles within a single client are prevented by convention.

**Resolution plan:** Documented in `docs/architecture/principal_id_based_lookup_plan.md`. Migration to ID-based lookup is a post-pilot-hardening item.

---

### KI-004: Data Governance Agent Wired Post-Bootstrap

**Severity:** High  
**Status:** Known; explicit startup warnings document this  
**Affects:** `A9_Data_Product_Agent` view name resolution during startup window

The Data Governance Agent is wired to the Data Product Agent after all agents are created and connected, via `runtime._wire_governance_dependencies()`. During the initialization window before wiring completes, DPA view name resolution is unavailable.

**Current behavior:** Expected startup warnings are logged:
```
WARNING: Provider 'business_process' not found in registry factory
WARNING: Data Governance Agent not available for view name resolution
```
These resolve within seconds as bootstrap completes. They are not errors.

**Resolution plan:** Infra A4 — registry live-reload fix; explicitly in May–Jun 2026 active work.

---

### KI-005: Bicycle/FI Dataset Returns Sparse DA Results in 2026

**Severity:** High  
**Status:** Known; affects demo/test only — not lubricants (production dataset)  
**Affects:** Deep Analysis Agent when run against Bicycle/FI dataset

The Bicycle FI dataset has only 2 Actual transactions in 2026. The DA agent's dimensional analysis returns 0 rows for any Bicycle principal on a YTD timeframe. This causes empty DA output that appears to be a bug but is a data issue.

**Current workaround:** Lubricants + BigQuery is the primary demo dataset and is unaffected. Bicycle dataset is used for development only.

**Resolution:** Reseed bicycle dataset with representative 2026 Actual data before any demo using that tenant.

---

### KI-006: No Time-Based Expiry on Briefing Tokens

**Severity:** High  
**Status:** Low priority; single-use tokens mitigate most risk  
**Affects:** PIB email briefing deep links

Single-use briefing tokens (approve, delegate, request_info) expire on use but not on time. A long-lived unactivated token remains valid indefinitely.

**Resolution plan:** Add 48-hour expiry on briefing token creation — minor backend change.

---

## Medium Issues (Deferred by Design)

### KI-007: No Integration Test Suite Against Live Data

**Severity:** Medium  
**Status:** Accepted; 90 unit tests pass  
**Affects:** Test coverage confidence

Unit tests mock external dependencies (Supabase, BigQuery, LLM). There is no integration test suite that runs the full SA → DA → SF pipeline against real warehouse data and validates end-to-end outputs.

**Impact:** Unit tests prove component logic; they do not prove that the full pipeline produces correct results on live data. This gap is mitigated by the demo environment running against real data (Lubricants + BigQuery) before any customer demo.

**Resolution plan:** Integration test suite — post-pilot, when test data sets are stable.

---

### KI-008: SQL Server Production Deployment Blocked on ODBC Driver

**Severity:** Medium  
**Status:** Operational in dev; production gated  
**Affects:** SQL Server connectivity for prospects using Microsoft data warehouses

SQL Server is wired and tested in local development. Production deployment on Railway is blocked by the ODBC driver dependency in the Dockerfile — the standard `msodbcsql18` installation process conflicts with Railway's build environment.

**Current state:** BigQuery, Snowflake, DuckDB, and Databricks are fully operational in production. SQL Server prospects can be onboarded via alternative connectivity (PostgreSQL extract, or a planned pilot-specific Railway environment with a custom base image).

**Resolution plan:** Custom Dockerfile base image with pre-installed ODBC drivers — Phase 10E or on-demand for first SQL Server prospect.

---

### KI-009: Value Assurance Supabase Persistence — Partial

**Severity:** Medium  
**Status:** Core tables live; trajectory store in-memory for complex state  
**Affects:** VA multi-trajectory tracking across server restarts

The VA Agent's `situations` and `value_assurance_solutions` tables persist to Supabase. The real-time trajectory computation state uses an in-memory store that does not survive server restarts. A Railway redeploy mid-trajectory would require the trajectory to be re-initialized on next API call.

**Impact:** Rare in practice (Railway deployments take 2-3 min, auto-triggered by push). The system re-derives trajectory state from Supabase-persisted solution records on startup.

**Resolution plan:** Full trajectory state persistence to Supabase — post-pilot when trajectory volumes justify it.

---

### KI-010: No Registry Admin Write UI

**Severity:** Medium  
**Status:** Deferred to Phase 2  
**Affects:** Customer self-service KPI management

The Registry Explorer in Decision Studio supports read-only viewing of KPIs, Principals, Data Products, Business Processes, and Glossary. Write-back (creating or editing registry records) requires running seed scripts via CLI.

**Impact:** During pilot, registry changes are handled by the Decision Studio team via seed scripts. Self-service KPI management is not customer-facing at pilot stage.

**Resolution plan:** Form-based registry editing in the Admin Console — Phase 2 feature.

---

## Low Issues (Tech Debt, No User Impact)

### KI-011: Principal Role System Uses Fixed Enum

**Severity:** Low  
**Status:** Workaround in place; low impact in current client set  
**Affects:** `PrincipalRole` enum in `situation_awareness_models.py`

The `PrincipalRole` enum supports a fixed set of roles. CEO and COO are mapped to Finance Manager as a workaround. Custom role titles are not supported.

**Resolution plan:** Replace with string-based role system backed by a Role Registry — post-pilot.

---

### KI-012: MCP Service Agent Deprecated, Not Yet Removed

**Severity:** Low  
**Status:** Marked deprecated; removal date set for Nov 2025 (overdue, scheduled for cleanup)  
**Affects:** `A9_Data_Product_MCP_Service_Agent`

The MCP Service Agent is marked deprecated with removal planned post-Nov 2025. It has not been removed due to competing priorities. It is not called by any active workflow; it is dead code.

**Resolution plan:** Remove in the next cleanup sprint; not load-bearing.

---

### KI-013: Some Absolute File Paths in Configuration

**Severity:** Low  
**Status:** Partially fixed; some remain  
**Affects:** Local development setup on non-standard paths

Some configuration references absolute paths that were written for the original development machine. These are replaced with `DATA_ROOT` environment variable references where identified.

**Resolution plan:** Audit and replace remaining absolute paths — ongoing cleanup.

---

## Issue Summary

| ID | Issue | Severity | Target |
|----|-------|----------|--------|
| KI-001 | No authentication | Critical | Infra B — Jul 2026 |
| KI-002 | No Supabase RLS | Critical | After KI-001 |
| KI-003 | Role-based principal lookup | High | Post-pilot hardening |
| KI-004 | DGA wired post-bootstrap | High | Infra A4 — Jun 2026 |
| KI-005 | Bicycle dataset sparse in 2026 | High | Reseed or label |
| KI-006 | No token time expiry | High | Minor — next sprint |
| KI-007 | No integration test suite | Medium | Post-pilot |
| KI-008 | SQL Server ODBC on Railway | Medium | Phase 10E / on-demand |
| KI-009 | VA trajectory in-memory | Medium | Post-pilot |
| KI-010 | No registry write UI | Medium | Phase 2 |
| KI-011 | PrincipalRole fixed enum | Low | Post-pilot |
| KI-012 | MCP agent not removed | Low | Next cleanup sprint |
| KI-013 | Absolute file paths | Low | Ongoing |

---

## What This Document Is Not

This is not a defect list implying the system is broken. The SA → DA → MA → SF → VA pipeline is operationally stable in production on Railway, running against real BigQuery data, delivering PIB briefings via email with working single-use tokens. These known issues represent the gap between "demo-ready production system" and "enterprise-hardened multi-tenant SaaS" — a gap that is well-understood, sequenced, and actively being closed.
