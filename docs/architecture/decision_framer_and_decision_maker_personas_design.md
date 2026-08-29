# Decision Framer and Decision Maker — two principal workflow roles

**Created:** 2026-08-22
**Status:** Built. Stages 1-9 (Aug 2026) shipped `workflow_role`, the routing branch, the Decision
Maker landing view, and the briefing disclosure-state split. All three §7 questions resolved by what
was actually built — see there. **Updated:** 2026-08-28.

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

## 6. Onboarding — captured in the admin editor, NOT in the wizard, no title inference

**Corrected 2026-08-28 against what actually shipped, which differs from this section's original plan
in two ways:**

**Title-keyword suggested default — explicitly rejected, not just unbuilt.** `useDecisionStudio.ts`
carries a dated comment: *"workflow_role is STRICTLY an attribute of the principal registry
(2026-08-25, explicit user direction) — no title-keyword inference here, unlike
`inferDecisionStyle`."* `decision_style` already does exactly the keyword-inference this section
proposed, and was named in §2 as *the precedent to avoid repeating* for a different reason (it lived
in `metadata`, not as a first-class field). The keyword-inference *mechanism itself* was
independently rejected for this field one workflow_role file iteration later — a plain manual
`<select>` in `PrincipalEditor.tsx`, defaulting to `framer`, with no suggestion logic. Do not add
inference here; it was considered and turned down.

**Wizard step — not built, a real gap, orthogonal to the field's own design.** The field is
selectable in `PrincipalEditor.tsx` (used for editing any principal, new or existing, via Settings →
Principal Management) but `OnboardingSteps`/`OnboardingDayView.tsx`'s Day 2 flow never surfaces it —
grep for `workflow_role` in either file returns nothing. A brand-new client's principals therefore all
start as the `framer` default with nothing in the onboarding wizard prompting an admin to mark any of
them `decision_maker`; the field only gets set if someone separately visits Principal Management
afterward. Not blocking — the field is reachable, just not discoverable at the moment it would matter
most. Left as a follow-up, not built as part of this correction pass; it is a new wizard step, not a
documentation fix.

---

## 7. Open questions — resolved by what shipped (2026-08-28)

1. **Can one principal be both, over time?** **Shipped as recommended: profile attribute.**
   `workflow_role` is a first-class field on the principal record (`PrincipalEditor.tsx`), editable
   any time — not derived from RACI. The RACI-derived version remains the correct eventual
   replacement; nothing here blocks it (the field is just an enum, not baked into routing logic that
   would need to change shape).
2. **Does the Decision Maker default view need building, or is PIB already it?** **Built —
   `DecisionMakerLanding.tsx`, not a lean on PIB.** A real "Awaiting Your Decision" inbox, backed by
   `GET /workflows/solutions/pending`, opening the completed recommendation's *snapshot* (never
   re-running DA/SF live — a live-caught bug in the first version did exactly that and was fixed the
   same day). Routed in `DecisionStudio.tsx`: `workflow_role === 'decision_maker' && !selectedSituation
   && !showFullView`. The full-view escape hatch is real and was verified live — clicking "View full
   dashboard" routes to the same situation console a Framer sees by default, kicking off the same live
   scan.
3. **Does `workflow_role` drive briefing disclosure, or `communication.detail_level`?**
   **`workflow_role`**, as recommended. `ExecutiveBriefing.tsx`'s `roleDefaultApplied` effect looks up
   the principal's `workflow_role` and defaults `ANALYSIS_SECTION_IDS` open for a framer, closed for a
   decision maker.

**What this means for the M1 invariant (§3):** the Executive Briefing itself is content-identical for
both roles by design — only default disclosure state differs. A design critique this session
(2026-08-27) initially read that as the split being merely cosmetic ("what would you delete entirely
from a Decision Maker's briefing?"). That question assumed the wrong axis: this document already
settled, in three independent places (§3), that role adaptation must never touch facts or the
recommendation. The real differentiation is the ENTRY POINT — an entirely different landing surface,
not a trimmed version of the same one — and that part is substantial and correctly built. The
critique's error, not a build gap; corrected here so it isn't re-litigated.

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
