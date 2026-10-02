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
    severity     text NOT NULL,          -- 'info' | 'warning' | 'error' -- how urgent to a human reader
    outcome      text,                   -- 'pass' | 'fail' | 'abstain' -- what the check concluded
                                          -- (nullable: not every event_type is a check with a verdict;
                                          -- SF's narrative/debug events have no outcome, only severity)
    source_agent text NOT NULL,          -- 'A9_Solution_Finder_Agent'
    request_id   text,                   -- correlates to the workflow run
    payload      jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at   timestamptz NOT NULL DEFAULT now()
);
```

`severity` and `outcome` are independent axes, not synonyms -- a `fail` can be low-severity (DA's
`[ROLLUP-CHECK]` overshoot logs as `warning`, non-fatal by design: "a bad decomposition must not
take down a good analysis") and an `abstain` can be entirely routine (a slice-validity check with
no data yet to assess). Collapsing them into one column loses exactly the distinction the
`src/analysis` True/False/None convention exists to preserve. `outcome` is the column the
**stage-wise reliability panel** (`DEVELOPMENT_BACKLOG.md` -> *Audit event system*, 2026-10-02
extension) writes to for its five signals -- SA detection confidence, DA's `[ROLLUP-CHECK]`,
`check_tree_reconciles`, `check_slice_validity`, and KPI coverage. That panel's `event_type`
values live in their own namespace, separate from this section's pilot (SF) and from Infra C's
access/action trail (`auth.login`, `solution.approved`, ...) -- three families, one table, one write
path, distinguished by `event_type` prefix.

**Schema note, not yet reconciled:** Infra C's own draft (`DEVELOPMENT_BACKLOG.md` section C1) names
an `outcome text -- success/failure` column for the same table, written independently of this note.
The two drafts should converge before the migration is written -- this note's `pass`/`fail`/`abstain`
vocabulary is the one load-bearing for retention (below) and should be treated as the canonical one;
`success`/`failure` folds into it (`success` maps to `pass`, `failure` maps to `fail`, no `abstain`
case in the access/action family).

**RLS is mandatory** — this table carries `client_id`, so per root `CLAUDE.md` it sits outside the
tenant boundary unless the migration also includes the `GRANT` / `ENABLE ROW LEVEL SECURITY` /
`CREATE POLICY client_isolation` trio, and the table is added to `_RLS_TABLES` in
`scripts/verify_prod_registry.py`. Reference migration:
`supabase/migrations/20260713_rls_client_isolation.sql`.

### Retention — resolved, tiered by `outcome`

An events table with no expiry policy grows without bound, and the two families on it want
different answers. Raw retention is set **by `outcome`, not by `event_type` or family** — the
same rule applies everywhere the column is populated:

| `outcome` | Raw retention | Why |
|---|---|---|
| `pass` | 90 days, then rolled up | The overwhelming majority of rows. Long-term value is a rate, not the row — a daily/weekly aggregate (`pass_count`/`fail_count`/`abstain_count` per `event_type` per `client_id`, kept indefinitely) answers every "is this getting better" question the operator panel asks, at a fraction of the storage. |
| `abstain` | 90 days, then rolled up — **same as `pass`**, not `fail` | **Revised 2026-10-02**, after wiring the second signal. The original draft grouped `abstain` with `fail` on the assumption both are rare; SA's confidence-floor gate falsified that for this signal — a KPI sitting under `confidence_floor` (`MONITORING` status) can be the *common* case for a borderline KPI, not an anomaly. `abstain` means "inconclusive," which is routine noise for most signals, same as `pass`. A signal whose `abstain` case genuinely is a rare, valuable incident (none identified yet) can override this per-`event_type` in the rollup job's config — the default is not. |
| `fail` | 2 years minimum (matches Infra C1's SOC 2 horizon), no scheduled auto-delete | Rare by construction, and each one is an incident record — a caught ROLLUP-CHECK overshoot, a slice declared INVALID, a coverage gap, an SA detection error. Deleting evidence of a caught defect on a timer undercuts the reason this table exists: this design note's own §5 write-ups exist because similar evidence was dug up after the fact. These rows are also the candidate raw material for VA/theory-layer evidence (`theory_layer_design.md`'s causal-edge confirmation accretes "over real use, never by seeding") — don't foreclose that by expiring them against a clock unrelated to when a verdict might reference them. |
| `NULL` (no verdict — SF's narrative/debug events) | Unaffected by this table; follows `severity` only, per whatever the pilot scope (§4) already sets | Out of scope for this resolution — these aren't checks, they have no pass/fail/abstain to tier by. |

Mechanically: a Supabase scheduled job deletes `outcome IN ('pass', 'abstain')` rows older than 90
days after writing their counts into the aggregate table; it never touches `fail`/`NULL` rows.
Infra C's own 2-year SOC 2 retention (`DEVELOPMENT_BACKLOG.md` §C1) is untouched by this — it
governs the access/action family, which has no `pass`/`abstain` volume problem to begin with.

Volume at pilot scale (a handful of clients, tens to ~100 KPIs each, roughly one assessment run a
day) is hundreds to low thousands of rows/day — not a real storage cost yet. This split exists so
the aggregate path is already in place before volume becomes one, at the "commercial scale"
Infra C's own framing names as its trigger.

### Write path

Start by formalizing what SF already produces. Today's ad-hoc `Dict[str, Any]` appends become a
typed `AuditEvent` Pydantic model written at the point of generation, not only returned in the
response. The response field stays (it has in-process consumers) but stops being the only copy.

Pilot scope: `A9_Solution_Finder_Agent` (six event types already emitted, plus
`heuristic_stub_fallback`), then a generic uncaught-exception sink at the FastAPI layer.

### Read path — 🏁 BUILT (2026-10-02)

`GET /api/v1/admin/audit-events` (`src/api/routes/admin.py`), gated by the existing `X-Admin-Key`
dependency (`_require_admin_key`, `src/api/routes/admin.py:16-32`) — no second admin auth mechanism
invented. Filters on `client_id`, `event_type`, `severity`, `outcome`, `request_id`, and a `since`/
`until` time window, all optional and ANDed; `limit` clamped server-side to 500 regardless of what is
asked for. Spans every client by design — this is an admin diagnostics surface, not a tenant-facing
one, so there is deliberately no `tenant_scope()` on the read. The write path's own discipline
extends here: `AuditService.query()` never raises, returning an empty list on no pool or a query
failure rather than a 500 — a degraded diagnostics endpoint is not itself an incident worth paging
on, and an empty page with `status="ok"` says exactly that.

Tests: `tests/unit/test_audit_service.py` (filter/parameter wiring, limit clamping, one malformed row
not dropping the rest of the page), `tests/unit/test_admin_audit_events.py` (the auth gate, params
forwarded correctly, empty result is 200 not an error).

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

1. ~~**Retention policy.**~~ **Resolved 2026-10-02** — tiered by `outcome`, not by severity or
   family: see §4. `pass` rows live 90 days then roll into a permanent aggregate; `fail`/`abstain`
   rows get Infra C1's 2-year SOC 2 horizon with no scheduled deletion, since they are both rare and
   the candidate raw material for VA/theory-layer evidence.
2. ~~**Does this replace or feed Sentry?**~~ **Resolved 2026-10-02** — complementary, not
   overlapping. Sentry answers "what crashed" (infrastructure failure: an exception, a 500) on
   inputs that are otherwise structurally fine. This table answers "what did the agent conclude"
   (analytical-correctness failure: a slice declared INVALID, a rollup that overshoots) on inputs
   that never raise anything. Neither replaces the other; both stay.
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
