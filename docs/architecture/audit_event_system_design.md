# Audit event system — persisted diagnostics for monitoring and error review

**Created:** 2026-08-22
**Status:** Design note. **Not built.** Supersedes the error-log / audit-log portions of two
existing one-line stubs (§2).

---

## 1. Why this exists

Requested directly: "need a diagnostic support for monitoring and review of error logs."

Nothing today aggregates or persists backend errors, warnings, or agent-level audit signals.
Verified end-to-end:

- **No table.** No `audit_log` / `event_log` / `error_log` / `execution_trace` in any of the 34
  files under `supabase/migrations/`. The word "audit" appears only as a `created_at`/`updated_at`
  naming convention.
- **No endpoint.** No `/logs`, `/audit` or `/error-log` route in any backend router.
- **No UI.** The nearest analog, `ConnectionHealthPanel.tsx`, covers *data-source connectivity only*
  (per-data-product ok/error/latency from a `SELECT 1`-style probe, cached in memory on the backend
  via `probe_connection_health`, `src/api/runtime.py:266-319`). It is not application diagnostics.
- **Logs go to stdout only.** Plain stdlib `logging.getLogger(__name__)`, no `basicConfig`, no
  handler, no sink. `A9_SharedLogger` is named as the target in both `CLAUDE.md` files and **does
  not exist** anywhere in `src/`. Runtime logs are viewable only in the Railway dashboard, outside
  the product.

### The one signal that already exists, and why it isn't usable

`A9_Solution_Finder_Agent` builds an `audit_log` during synthesis — a **local variable**,
`a9_solution_finder_agent.py:1028`, appended to at ~9 sites, attached to the response at `:3257-3261`
and typed only as `Optional[List[Dict[str, Any]]]` on `solution_finder_models.py:300`.

It is request-scoped, in-memory, never written to Supabase, and unqueryable after the response is
returned. Even its in-process consumer treats it as unreliable: `src/analysis/decision_quality.py:209-211`
reads it to flag `is_stub_run`, and `src/analysis/mechanism.py:140-145` keeps a title-matching
fallback (`STUB_TITLES`) as a "safety net" for when the audit log is not attached.

**Confirmed live 2026-08-22:** a real SF run emitted
`["ranked_options","causal_context","llm_debate_analysis_req","llm_debate_completed","decision_briefing_generated","token_usage"]`.
Genuinely useful operational signal — six events describing a real pipeline execution — discarded
the moment the HTTP response completed.

---

## 2. Not a green field — two existing stubs this supersedes

| Stub | Location | Status |
|---|---|---|
| "Admin Console — Workflow history, **error log**, token cost, registry editor, LLM config" | `DEVELOPMENT_PLAN.md:102` (Infra A5) | Unbuilt, never designed |
| "SOC 2 Controls Foundation — **audit event log**, sign-in audit, principal archive lifecycle, briefing provenance footer, Sentry availability monitoring" | `DEVELOPMENT_PLAN.md:108` (Infra C, Q4 2026) | Unbuilt, never designed |

This document is the detailed design those one-liners never received — the same relationship
`raci_accountability_model.md` has to `kpi_accountability_model.md`'s original stub. Both lines
should be annotated to point here so they are not independently redesigned later.

---

## 3. Scope decision: start narrow, generalize after

Infra C bundles audit events with sign-in audit, principal archive lifecycle, briefing provenance
and Sentry. **Recommendation: do not absorb those here.** Ship one real pilot — SF's existing
events plus a generic error sink — and generalize once the write path has proven itself. That is
the pattern `kpi_accountability_model.md → raci_accountability_model.md` used successfully.

Sign-in audit and archive lifecycle are compliance artifacts with different retention and access
requirements; they deserve their own design once this exists to build on.

---

## 4. Target model

### Table

```sql
CREATE TABLE audit_events (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id    text NOT NULL,
    event_type   text NOT NULL,          -- 'heuristic_stub_fallback', 'llm_debate_completed', ...
    severity     text NOT NULL,          -- 'info' | 'warning' | 'error'
    source_agent text NOT NULL,          -- 'A9_Solution_Finder_Agent'
    request_id   text,                   -- correlates to the workflow run
    payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at   timestamptz NOT NULL DEFAULT now()
);
```

**RLS is mandatory** — this table carries `client_id`, so per root `CLAUDE.md` it sits outside the
tenant boundary unless the migration also includes the `GRANT` / `ENABLE ROW LEVEL SECURITY` /
`CREATE POLICY client_isolation` trio, and the table is added to `_RLS_TABLES` in
`scripts/verify_prod_registry.py`. Reference migration:
`supabase/migrations/20260713_rls_client_isolation.sql`.

**Retention** is an open question (§6) — an events table with no expiry policy grows without bound.

### Write path

Start by formalizing what SF already produces. Today's ad-hoc `Dict[str, Any]` appends become a
typed `AuditEvent` Pydantic model written at the point of generation, not only returned in the
response. The response field stays (it has in-process consumers) but stops being the only copy.

Pilot scope: `A9_Solution_Finder_Agent` (six event types already emitted, plus
`heuristic_stub_fallback`), then a generic uncaught-exception sink at the FastAPI layer.

### Read path

`GET /api/v1/admin/audit-events` with filters on `client_id`, `event_type`, `severity`, `request_id`
and a time window. Reuse `admin.py`'s existing `X-Admin-Key` gate (`src/api/routes/admin.py:16-32`)
rather than inventing a second admin auth mechanism.

### UI

A diagnostics page reachable from the new left nav (`collapsible_left_nav_design.md`) or as a fourth
card in `AdminConsole.tsx`'s existing launcher pattern (`src/pages/AdminConsole.tsx:20-56`). Table
view: time, severity, agent, event type, request id, expandable payload. Filter by severity and
agent. `ConnectionHealthPanel` remains separate — connectivity and application diagnostics are
different questions and merging them would make both harder to scan.

---

## 5. What this makes possible that isn't possible today

- **`heuristic_stub_fallback` becomes queryable.** `project_sf_synthesis_output_ceiling` describes SF
  truncating into a stub while reporting success. Today that is detectable only by inspecting a
  single live response. Persisted, "how often did this fire this month, for which client" becomes a
  question with an answer.
- **Token cost per run becomes historical.** `token_usage` is already emitted and already discarded.
- **DQ scoring gets a real corpus.** `src/analysis/decision_quality.py` currently reads audit events
  in-process; `dq_l1_framing_signal_design.md` is explicitly blocked on "real accumulated usage over
  time." A persisted event store is the substrate that unblocks it.

---

## 6. Open questions

1. **Retention policy.** 90 days? Per-severity (errors longer than info)? Needed before the
   migration, since it affects partitioning.
2. **Does this replace or feed Sentry?** Infra C names Sentry for availability monitoring. Two
   overlapping systems is a real cost; this table is application-semantic (what the agents decided),
   Sentry is operational (what crashed). Probably complementary, but state it deliberately.
3. **Should `A9_SharedLogger` be built as part of this?** Both `CLAUDE.md` files name it as the
   logging target and it does not exist. A write path to `audit_events` is a natural place to
   finally introduce it — or a deliberate reason to keep them separate (structured business events
   vs. line-oriented debug logging).
4. **Does the SF response keep its `audit_log` field** once events are persisted, or read back from
   the store? Keeping both risks drift; removing it breaks in-process DQ scoring.

---

## 7. Related documents

- `DEVELOPMENT_PLAN.md:102` (Infra A5), `:108` (Infra C) — the stubs this supersedes
- `dq_l1_framing_signal_design.md` — blocked on accumulated usage this would capture
- `theory_layer_design.md` — the provenance ladder is a related "record why we believed this" concern
- root `CLAUDE.md` — the mandatory RLS trio for any new `client_id` table
