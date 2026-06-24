# Phase 12A End-to-End Test Runbook

**Last Updated:** 2026-06-04
**Owner:** Founder / QA
**Tested against:** Local Supabase + FastAPI + React stack started via `.\restart_decision_studio_ui.ps1`

> Repeatable manual test for the Phase 12A — Company Intelligence KPI Template Generator. Designed to be re-run safely: every session starts with a cleanup step and the test scenarios only touch `status='template'` rows, never active KPIs.

---

## What This Runbook Verifies

| Capability | Scenario |
|---|---|
| MA agent researches a company end-to-end | A |
| Source provenance badges render correctly (📄/🏭/🤖) | A |
| M4 degraded fallback works when Perplexity is unavailable | B |
| Commit writes correct rows with `status='template'` | C |
| Idempotency — re-committing produces no duplicates | D |
| SA agent guard — template KPIs are excluded from situation detection | E |
| Multi-tenant client_id isolation | F |

## What This Runbook Does NOT Cover

- Data Product onboarding for template KPIs (Phase 12B / future)
- Production Supabase (this is local-only; prod push is a separate decision)
- Load / concurrency testing
- Real LLM token cost accounting

---

## 1. Pre-Flight Checklist

Verify before starting each session.

| Check | How | Pass criteria |
|---|---|---|
| Stack running | `curl http://localhost:8000/healthz` + browse to http://localhost:5173 | API returns `{"status":"ok"}`, UI loads |
| Local Supabase up | `./supabase.exe status` | "supabase local development setup is running" |
| `PERPLEXITY_API_KEY` set (for Scenario A) | `echo $env:PERPLEXITY_API_KEY` in PowerShell | Non-empty value |
| `ANTHROPIC_API_KEY` set | Same | Non-empty — required for ALL scenarios |
| Active client_id selected | DevTools Console: `localStorage.getItem('a9_active_client_id')` | Returns `'lubricants'` or similar |
| Migration applied | Inspect `kpis` table | Has `status`, `benchmark_range`, `benchmark_source` columns |

If any check fails, fix the cause before continuing. Don't skip.

---

## 2. Cleanup — Run Before Each Session

**Recommended: use the cleanup script.**

```powershell
# Dry-run first to see what would be deleted
.venv/Scripts/python scripts/cleanup_phase_12a_test_data.py --dry-run

# Commit the cleanup
.venv/Scripts/python scripts/cleanup_phase_12a_test_data.py
```

Required env vars:
- `SUPABASE_URL` — typically `http://127.0.0.1:54321` for local
- `SUPABASE_SERVICE_ROLE_KEY` — from `./supabase.exe status -o env`

**Alternative (direct SQL via Supabase Studio at http://127.0.0.1:54323):**

```sql
-- See what's there
SELECT id, name, client_id, status, benchmark_source, metadata->>'created_by' AS created_by
FROM kpis
WHERE status = 'template';

-- Cleanup for one client (status filter is the safety gate)
DELETE FROM kpis
WHERE client_id = 'lubricants' AND status = 'template';
```

**Safety contract:** Both methods filter on `status='template'`. Active KPIs are NEVER touched.

---

## 3. Test Scenarios

### Scenario A — Happy Path (Perplexity Available)

**Goal:** Verify the full 4-search + Sonnet synthesis pipeline produces a complete profile.

**Steps:**
1. Browse to http://localhost:5173/settings/kpi-intelligence
2. Fill in:
   - Company name: `Valvoline Inc.`
   - Industry hint: `Specialty Chemicals`
   - Sub-sector: `Industrial Lubricants`
   - Business description: `B2B distributor of industrial lubricants to manufacturing accounts.`
   - Target KPI count: `15`
3. Click **Research company**

**Expected:**
- Loading screen for ~30–60 seconds (4 parallel Perplexity calls + Sonnet synthesis)
- Review table appears with 10–15 KPIs
- Industry inferred: matches your input
- **Mix** of badges — at least one 📄 Filing, one 🏭 Peer, one 🤖 Inferred
- "Degraded research mode" amber banner is NOT visible

**Pass criteria:**
- [ ] At least one 'filing' badge present
- [ ] Industry inferred is non-empty and reasonable
- [ ] No console errors in DevTools
- [ ] Network tab shows POST `/api/v1/templates/research-company` returning `status: "success"`

**On failure:** Check backend log for `MA research_company_kpi_profile failed`. If timeout, check Perplexity API key validity and rate limit.

---

### Scenario B — Degraded Path (Perplexity Unavailable)

**Goal:** Verify M4 fallback — when Perplexity is missing, system still produces a profile but marks it degraded.

**Setup:** Temporarily unset `PERPLEXITY_API_KEY` and restart the stack:
```powershell
# In your .env or terminal session, before restart:
$env:PERPLEXITY_API_KEY=""
.\restart_decision_studio_ui.ps1
```

**Steps:**
1. Same input as Scenario A
2. Click **Research company**

**Expected:**
- Faster response (~10–20 seconds — only one LLM call, no web search)
- Amber **"Degraded research mode"** banner at top of the review table
- **Every** KPI shows 🤖 Inferred badge
- `research_sources` lists `"LLM training knowledge"` only

**Pass criteria:**
- [ ] Degraded banner visible
- [ ] Zero 📄 or 🏭 badges
- [ ] Profile still has KPIs (graceful degradation, not empty)

**Restore `PERPLEXITY_API_KEY` and restart before continuing.**

---

### Scenario C — Commit and Verify in Registry

**Goal:** Verify accepted KPIs are written with `status='template'` and benchmark fields populated.

**Steps:**
1. From Scenario A's review table, uncheck 5 KPIs (leaving ~10 checked)
2. Edit one KPI's name and benchmark range inline
3. Click **Commit N KPIs to registry**

**Expected:**
- Success screen shows: `Written: 10`, `Skipped: 0`, `Failed: 0`
- "Connect data sources →" CTA visible

**Verify in DB** (Supabase Studio SQL editor or psql):
```sql
SELECT id, name, status, benchmark_range, benchmark_source, data_product_id,
       metadata->>'created_by' AS created_by, metadata->>'confidence' AS confidence
FROM kpis
WHERE client_id = 'lubricants' AND status = 'template'
ORDER BY name;
```

**Pass criteria:**
- [ ] Row count equals the number you accepted
- [ ] All rows have `status='template'`
- [ ] All rows have `data_product_id='pending'`
- [ ] `benchmark_range` is populated where you saw a range in the UI
- [ ] `metadata->>'created_by'` is `'kpi_intelligence_ui'`
- [ ] The edited row has your edited values, not the original

---

### Scenario D — Idempotency

**Goal:** Verify re-committing the same KPIs is safe — no duplicates.

**Steps:**
1. Click **Research another company** (NOT cleanup — keep the templates from C)
2. Run Scenario A again with the **same** inputs
3. Accept the same 10 KPIs
4. Click **Commit**

**Expected:**
- Success screen shows: `Written: 0`, `Skipped: 10`, `Failed: 0`
- Each row in the result list shows `skipped_duplicate`

**Verify in DB:** The row count from Scenario C is unchanged; `updated_at` timestamps are unchanged.

**Pass criteria:**
- [ ] `rows_written = 0` on the second commit
- [ ] `rows_skipped = 10`
- [ ] DB row count matches Scenario C's count exactly

---

### Scenario E — SA Guard (Template KPIs Excluded)

**Goal:** Verify template KPIs do NOT appear in situation detection.

**Steps:**
1. Navigate to http://localhost:5173/dashboard
2. Confirm the active principal is one belonging to the test client (e.g. a Lubricants CFO)
3. Click **Detect Situations**

**Expected:**
- Situation cards appear for ACTIVE KPIs only
- None of the template KPI names from Scenario C appear in the results

**Verify in backend log** (FastAPI stdout):
- Search for `skipped N template KPIs` from the SA loader
- N should equal the number of template KPIs in DB for this client

**Pass criteria:**
- [ ] Template KPI names absent from dashboard results
- [ ] Backend log shows the expected skip count

---

### Scenario F — Multi-Tenant Isolation

**Goal:** Verify a different client cannot see another tenant's template KPIs.

**Steps:**
1. Switch active client to `bicycle`:
   - Log out, log back in as a Bicycle principal, OR
   - DevTools Console: `localStorage.setItem('a9_active_client_id', 'bicycle')` then reload
2. Browse to http://localhost:5173/settings/kpi-intelligence
3. Note the client badge shows `bicycle`
4. (Optional) Research a different company specific to bicycle context

**Verify in DB:**
```sql
SELECT client_id, COUNT(*) AS template_count
FROM kpis
WHERE status = 'template'
GROUP BY client_id;
```

**Pass criteria:**
- [ ] `lubricants` templates from Scenario C still exist with their original count
- [ ] `bicycle` shows 0 templates (unless you ran a research under that client)
- [ ] The KPI Intelligence page never returned lubricants templates while client = bicycle

**Restore active client to `lubricants` before cleanup.**

---

## 4. Sign-Off Checklist

Run through all six and check off as you go. A clean run = all boxes ticked.

- [ ] Scenario A: Happy path produced mixed-source KPIs
- [ ] Scenario B: Degraded fallback marked all sources as inferred
- [ ] Scenario C: DB rows match commit count with correct fields
- [ ] Scenario D: Re-commit produced zero duplicates
- [ ] Scenario E: SA detection excluded all template KPIs
- [ ] Scenario F: Bicycle client did not see lubricants templates
- [ ] Cleanup: Final `cleanup_phase_12a_test_data.py` run reports the expected row count

If all seven check, Phase 12A is **production-pushable for the local stack**. The remaining gate is the production Supabase migration (`supabase db push --linked`) — handled outside this runbook.

---

## 5. Failure Triage Quick Reference

| Symptom | First place to look |
|---|---|
| Page shows "Select a workspace client" | `localStorage.getItem('a9_active_client_id')` is empty |
| 503 from `/api/v1/templates/*` | Backend stdout — Supabase pool not initialized; restart |
| Empty `template_kpis` array | Backend log — search for `JSON parse failed` (LLM returned malformed JSON) or `MA research_company_kpi_profile failed` |
| Perplexity timeout / 4 empty results → degraded auto | Expected behaviour — confirm by looking for `falling back to LLM-only` in backend log |
| Commit returns 400 "At least one KPI must be accepted" | Check at least one row checkbox is selected in the review table |
| Template appears in SA detection results | Bug — check that the migration applied (`SELECT status FROM kpis LIMIT 1`) and that the SA loader skip log fires |
| Bicycle client sees lubricants templates | Critical — check `client_id` filter in `_get_relevant_kpis` and the page's `localStorage` read |

---

## 6. Useful Queries

```sql
-- All template KPIs across clients (audit view)
SELECT client_id, COUNT(*) AS templates
FROM kpis
WHERE status = 'template'
GROUP BY client_id;

-- Detail view for one client
SELECT id, name, domain, benchmark_range, benchmark_source,
       metadata->>'created_by' AS created_by,
       metadata->>'confidence' AS confidence,
       created_at
FROM kpis
WHERE status = 'template' AND client_id = 'lubricants'
ORDER BY domain, name;

-- Confirm active KPIs were never touched
SELECT COUNT(*) AS active_count
FROM kpis
WHERE status = 'active' AND client_id = 'lubricants';
-- Compare to the value before testing started
```

---

## 7. Notes for Future Iterations

- When **Phase 12B** ships, accountability assignment will happen during template review (process-template suggestion). Update this runbook with that scenario.
- When **Data Product Onboarding** is wired to promote `status='template'` → `status='active'` after data connection, add a Scenario G covering that transition.
- The Settings page tab bar density (10+ tabs) is logged as deferred tech debt; if a left-hand nav refactor lands, the navigation paths in this runbook may shift.
