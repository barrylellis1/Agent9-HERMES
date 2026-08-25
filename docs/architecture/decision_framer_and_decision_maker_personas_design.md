# Decision Framer and Decision Maker — two principal workflow roles

**Created:** 2026-08-22
**Status:** Design note. **Not built.** Three open questions require sign-off (§7).

---

## 1. Why this exists

Stated directly, 2026-08-22:

> "early in the workflow design, I thought the executives themselves would run SA, DA, MA, SF, VA
> but now with the depth of problem framing and perhaps reframing multiple times, they aren't going
> to have the patience for that. Seems like we need 'Decision Framing' principals and 'Decision
> Maker' principals. the PIB agent is trying to help here."

This is not a new idea in the codebase — it was independently derived from a different direction in
`raci_accountability_model.md` ("It was designed for the wrong persona"), which describes the
realistic ICP workflow as: an FP&A analyst stewards situations, a VP tests solution constraints, and
the executive mostly consumes a distilled PIB briefing and gives final sign-off. That observation
was made about *visibility filtering*; it was never turned into a first-class distinction in the
principal model or the UI.

**Observed live, same session:** running as David Torres (CEO), the framing gate rendered
*"Owned by Finance Manager. You may still submit — your role will be recorded with the decision."*
The system correctly knew the KPI belonged to someone else, and still asked the CEO to do the
framing interview. That is the gap in one screen.

---

## 2. What exists today

| Question | Answer today |
|---|---|
| Does `PrincipalProfile` distinguish a steward from an executive? | **No.** `principal_type` is `INDIVIDUAL \| TEAM \| COMMITTEE` (`src/registry/models/principal.py:14-17`) — about *what kind of entity*, not *what they do in the workflow*. |
| Does the frontend branch on principal role? | **No.** `DecisionStudio.tsx:63-136` branches only on whether a situation is selected. Zero role-based view branching anywhere in the router. |
| Does anything adapt per principal? | `communication.detail_level` (high/medium/low) exists on the model and is the documented adaptation axis. |
| Is there any second-principal machinery? | **Yes, in PIB only** — delegation (`_load_delegated_to_principal`, `a9_pib_agent.py:448`), the `situation_actions` table, token-based approve/delegate/request-info actions (`TokenType`, `:485`), and the `/delegate` + `/action` unauthenticated token pages. |
| Does onboarding ask? | **No.** `PrincipalEditor.tsx` captures ID, name, title, decision style, email, description, BPs, KPIs, responsibilities, plus an unrelated `settings_admin` boolean. |

### The precedent to avoid repeating

`decision_style` looks like a first-class field from the frontend (`PrincipalEditor.tsx` writes it,
`RegistryExplorer.tsx` displays it) but is **not a field on `PrincipalProfile` at all**. The backend
reads it out of `metadata` (`a9_principal_context_agent.py:47-70`, `_extract_decision_style`) and
falls back to `"Analytical"` for effectively every principal in production —
`ProblemRefinementChat.tsx:79-82` carries a comment saying exactly that. Pydantic silently drops
unknown keys, so the round-trip fails quietly.

**The new field must be first-class on `PrincipalProfile` from day one.** Not a `metadata` string.

---

## 3. The invariant this must not break

Role adaptation controls **entry point and depth only, never the facts or the recommendation**.
Stated independently in three places:

- `src/registry/models/principal.py:79-84` — option-ranking weights "are a property of the
  enterprise's strategy, not of the individual reading the screen"
- `DecisionAskBlock.tsx:19-20` — "M1 — this block is IDENTICAL for every principal"
- `DEVELOPMENT_PLAN.md` Phase 13 M1 — "CFO and COO reading the same briefing independently must
  reach the same recommendation"

So the split must be designed as a **workflow-stage axis** (who drives the SA→DA→SF investigation
loop vs. who reviews a distilled brief and signs off), explicitly **not** a "different principals
see different recommendations" axis. Conflating the two would violate M1.

Also carry over Phase 12E's adopted decision (`DEVELOPMENT_PLAN.md:1487-1488`): do not *infer*
principal traits via LLM. Propose a default (title keywords are already used this way by
`useDecisionStudio.ts`'s `inferDecisionStyle`), then require explicit admin confirmation.

---

## 4. Target model

Add a first-class enum to `PrincipalProfile`:

```python
class WorkflowRole(str, Enum):
    FRAMER = "framer"                  # stewards SA→DA→SF; runs refinement + reframing
    DECISION_MAKER = "decision_maker"  # consumes the distilled brief; approves
```

`workflow_role: WorkflowRole = WorkflowRole.FRAMER` — defaulting to `framer` keeps every existing
principal's behaviour unchanged (today everyone gets the full pipeline), so the migration is
additive and non-breaking.

### What it changes downstream

| Surface | Framer | Decision maker |
|---|---|---|
| Default landing view | Situation console (today's dashboard) | Briefing-centric: what's awaiting my decision |
| Refinement / framing gate | Primary workflow | Reachable, not the default path |
| Executive Briefing disclosure | Analysis layer open | Analysis layer collapsed |
| PIB briefing | Optional | Primary delivery channel |

**A full-view escape hatch is always available**, matching the pattern Phase 13 M1 already
established ("A full-view toggle is always available regardless of principal type"). A Decision
Maker who wants the whole pipeline can always get it; the role sets the default, not a permission.

The briefing-surface consequence of this is designed separately in
`executive_briefing_redesign.md` — one document, two default disclosure states.

---

## 5. Reconciliation required: `hitl_decision_philosophy.md` §6

That document currently states, flatly:

> "Not a board collaboration tool. Single principal as decision maker."

This is already de facto contradicted by PIB's shipped delegation mechanics — a delegate *is* a
second principal, and `hitl_decision_philosophy.md` does not discuss delegation at all. The line
should be updated to distinguish "one accountable decision maker per decision" (still true, and
worth keeping) from "one principal performs every step" (not true today, and less true under this
design).

---

## 6. Onboarding

Add the question to Day 2 (`PrincipalEditor.tsx`, also embedded in the wizard step per
`onboardingSteps.ts:42-54`). Keep it orthogonal to the existing `settings_admin` checkbox — that
flag governs registry maintenance access, an unrelated axis.

Suggested default from title keywords (CEO/CFO/COO/Chief → `decision_maker`; Manager/Analyst/
Director → `framer`), presented for confirmation, never silently applied.

---

## 7. Open questions requiring sign-off

1. **Can one principal be both, over time?** A Finance Manager frames most weeks and decides on
   small items. Is `workflow_role` a fixed profile attribute, or a per-situation stance derived from
   RACI (`accountable` → decides, `responsible` → frames)? The RACI-derived version is more correct
   and more work; the profile attribute ships sooner. **Recommendation: profile attribute now, with
   the RACI derivation as the eventual replacement** — noted so the field is not designed in a way
   that blocks it.
2. **Does the Decision Maker default view need building, or is PIB already it?** PIB delivers
   email-only today with no in-app briefing inbox. A "what's awaiting my decision" landing view is a
   real new surface; leaning on PIB instead is cheaper but leaves the in-app experience unchanged.
3. **Does `workflow_role` drive briefing disclosure, or does `communication.detail_level`?**
   The former is semantically right; the latter already exists and needs no migration. See
   `executive_briefing_redesign.md` §6.3.

---

## 8. Related documents

- `executive_briefing_redesign.md` — the briefing-surface half of this split
- `raci_accountability_model.md` — independently derived the same persona observation; also owns
  regional/dimensional KPI scoping (`scope_dimension`/`scope_value`), which is a *different* axis
  from this one and must not be conflated
- `hitl_decision_philosophy.md` §6 — requires the reconciliation in §5
- `DEVELOPMENT_PLAN.md` Phase 12E — the "do not infer principal traits" precedent
- `docs/prd/agents/a9_pib_agent_prd.md` — PIB is the existing delivery channel for the Decision
  Maker persona; note the PRD and the implementation already disagree on entrypoint shape
