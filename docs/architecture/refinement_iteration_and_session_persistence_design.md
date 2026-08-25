# Refinement iteration and session persistence — rounds, not silent overwrites

**Created:** 2026-08-22
**Status:** Design note. **Not built.** Two cheap guard-fixes are separable and filed as tech debt.

---

## 1. Why this exists

Raised directly: during DA problem refinement or when reviewing solutions, a question can come up
that takes a while to answer — so being able to save progress and resume would be valuable. Refined
in discussion to a sharper need:

> "problem refinements might need adjusting after user sees solution set. almost a 2nd refinement
> session"

Three distinct needs sit at the same seam (the refinement interview → SF hand-off):

1. **Pause / resume** — the interview is interrupted; come back later and continue.
2. **Re-refine** — same objective, revised answers, informed by having seen Round 1's solutions.
3. *(Adjacent, already designed elsewhere)* **Reframe** — a *different* objective. Owned by
   `reframe_relaunch_and_lineage_design.md`.

---

## 2. What actually happens today

### 2.1 The interview is stateless by explicit design

`/workflows/deep-analysis/refine`'s own docstring (`src/api/routes/workflows.py:376-380`):

> "This is a synchronous endpoint... The conversation is stateless on the server — the client
> maintains conversation_history and passes it back each turn."

`ProblemRefinementChat.tsx` holds the entire transcript in component-local `useState`
(`:99-113`) with nothing written to any storage. A refresh or closed tab loses it completely; on
remount `startConversation()` fires from turn 0. Nothing about mid-interview turns survives
independently — the only durable trace is the *final* `framing_decision`, captured onto the VA
solution at approval time (`_resolve_va_kpi_id_and_framing`, `workflows.py:92-134`).

### 2.2 Re-opening refinement silently destroys a completed SF run

**This is a live bug, not a hypothesis.** `DeepFocusView` has no awareness that Solution Finder
already completed for a situation — `DeepFocusViewProps` (`:122-172`) carries no
`solutions`/`hasSolutions`/`debateComplete` prop, and the "Start Refinement Session" /
"Generate Solutions →" panel renders unconditionally (`:961`, `:1083-1108`).

Re-running the interview and dispatching again causes `CouncilDebatePage.runDebate()` to:

1. Delete every `solutions_*`, `briefing_*` and `solution_request_*` key from `localStorage`
   (`CouncilDebatePage.tsx:232-237`), then
2. Re-run **both** Stage 1 (3 parallel LLM calls) and synthesis from scratch (`:300-324`).

There is no partial-retry path (reuse Stage 1, redo only synthesis) and no "you already have
solutions — regenerate anyway?" confirmation. The cached-restore branch is unreachable on this path
by explicit design comment (`:199-202`): *"On fresh navigation from DeepFocusView,
routerState.situation is always set — in that case always run a new debate."*

Measured cost: a full synthesis run took **~5.5 minutes** end-to-end on 2026-08-22 (stage 1 at
~130s, phase 4 at ~310s), all of it real LLM spend.

### 2.3 There is no persisted "run" concept at all

`_workflow_store` (`workflows.py:86-87`) is a plain in-process dict, wiped on every restart or
redeploy. `WorkflowRecord.state` only ever takes `pending` → `completed` / `failed` — there is no
`awaiting_input` or `paused` state anywhere. The frontend's only durable handle into it is a
`solution_request_${situationId}` key in browser `localStorage`
(`CouncilDebatePage.tsx:343`), which `DecisionChat` then depends on
(`ExecutiveBriefing.tsx:110-111`, throws `'No request ID found'` if absent).

### 2.4 Deep Analysis re-runs on every reselect

`handleDeepAnalysis` (`useDecisionStudio.ts:313-342`) has **no cache check**. Reselecting the same
situation — same session, zero elapsed time — dispatches a fresh `POST /workflows/deep-analysis/run`
and overwrites `analysisResults[sitId]`. Unrelated to resume; just waste.

---

## 3. The reusable precedent, and why it doesn't transfer cleanly

`OnboardingResume.tsx` already solves "come back later" for a different workflow — but **not** by
storing workflow state. `GET /api/v1/onboarding/progress` (`src/api/routes/onboarding.py:156-196`)
*re-derives* completion by querying the real registry rows each step produces (a principal row, a
KPI row, a data product row) and computing `first_incomplete_step` fresh.

That works because every onboarding step writes a durable, independently meaningful record.
**DA/SF's intermediate steps produce no equivalent** — refinement answers, the framing decision and
Stage 1 hypotheses exist only inside transient request/response payloads. Reusing the *pattern*
requires first deciding which of those become first-class persisted artifacts.

Worth noting: `onboarding.py:136-137` carries its own comment that `_assessment_runs` is
"in-memory only and resets on every backend redeploy" — the same class of gap, already acknowledged
in a neighbouring module.

---

## 4. Target model

### 4.1 Refinement rounds as first-class objects

Stop treating "run the interview again" as a silent destructive overwrite. A second pass creates a
**Round 2**, with Round 1's solutions retained and viewable.

```python
class RefinementRound(BaseModel):
    id: str
    client_id: str
    situation_id: str
    round_number: int
    iterated_from_id: Optional[str]   # prior round, same objective
    status: Literal["in_progress", "ready_for_solutions", "superseded", "abandoned"]
    turns: List[RefinementTurn]       # the durable transcript (§4.2)
    framing_decision: Optional[FramingDecision]
    solution_request_id: Optional[str]
    created_at: str
    updated_at: str
```

`iterated_from_id` deliberately mirrors the shape of `reframed_from_id` in
`reframe_relaunch_and_lineage_design.md`. **Same lineage mechanism, different axis** — that document
links successive *objectives*; this one links successive *passes at the same objective*. They must
compose, not compete: a real chain can contain both.

### 4.2 Durable turns

The refinement endpoint stays stateless in shape (the client still passes history), but each turn is
additionally persisted server-side against the round. That is what makes genuine pause/resume
possible — §2.1's design is fine for a single sitting and fatal across an interruption.

### 4.3 The UI must distinguish two different intents

- **"Resume"** — an `in_progress` round exists; continue where it stopped. Same round.
- **"Start a new round"** — a `ready_for_solutions` round with solutions already exists; the user
  wants to revise inputs having seen the output. New round, prior one marked `superseded`, prior
  solutions retained.

`DeepFocusView` needs to know a debate already completed in order to offer the second at all —
which it cannot do today (§2.2).

---

## 5. Two cheap guard-fixes, separable from all of the above

Not gated on the rounds model. Filed independently in `DEVELOPMENT_PLAN.md` tech debt.

1. **DA reselect guard** — skip re-running Deep Analysis when `analysisResults[sitId]` already exists
   and nothing changed (`useDecisionStudio.ts:313-342`).
2. **Stop silently discarding solutions** — `CouncilDebatePage.runDebate()`'s unconditional
   `localStorage.removeItem` sweep (`:232-237`). At minimum, do not delete what cannot yet be
   restored; ideally confirm first.

---

## 6. Open questions

1. **How many rounds are retained, and is a round-comparison UI in scope?** Comparing Round 1 and
   Round 2 solution sets is genuinely useful ("did narrowing the constraint change the answer?") and
   is also a whole surface of its own.
2. **How do rounds interact with VA registration?** `AcceptedSolution` already carries a
   `FramingSnapshot` (shipped 2026-08-22). Does it need a round pointer so VA can tell which pass
   produced the approved solution?
3. **Does the durable-turn store reuse `audit_events`** (`audit_event_system_design.md`) or get its
   own table? Different lifetimes and access patterns suggest its own table, but they are adjacent.
4. **Should a superseded round's solutions stay visible indefinitely,** or expire? Retaining them is
   the point; retaining them forever has a storage and confusion cost.

---

## 7. Related documents

- `reframe_relaunch_and_lineage_design.md` — the *reframe* axis; shares the lineage mechanism, must
  not duplicate it
- `problem_framing_design.md` — the framing gate that opens every interview
- `audit_event_system_design.md` — adjacent persistence question
- `hitl_decision_philosophy.md` — Gate 1 is the interview this document makes resumable
