# DA + SF Prompt Redesign — Context Contract & Structured Outputs

**Status:** Proposal (Jul 2026) — umbrella design for DEVELOPMENT_PLAN Phase 13 Categories 2 & 4
**Evidence base:** Phase 11O A/B rounds 1–3 (synthesis quality), HITL replay A/B (refinement chat + briefing Q&A), Cascade-guardrails leak incident (2026-07-13)

---

## 1. What the evidence showed

Three controlled A/B rounds and a HITL conversational A/B (Sonnet 4.6 / Sonnet 5 / Fable 5) exposed structural prompt problems that are model-independent:

1. **Format policing dominates the prompts.** The SF synthesis prompt spends ~12 mandatory rule blocks enforcing JSON shape ("EXACTLY 3 options", "NEVER 0.0", enum lists, persona-key echoes). These rules exist because the current contract is a hand-built JSON template parsed by regex — every historical LLM format failure got patched with another MUST-rule (Phases 11–12 changelog in the SF card is a record of this).
2. **Truncation corrupts silently.** Round 2: Sonnet 5 hit the 16384 `max_tokens` cap mid-JSON; the regex salvage produced a 2-option briefing with no next steps and no impact estimate — *presented as a success*. Sonnet 5 synthesis runs 11–16K output tokens; headroom is thin even in production shape.
3. **Context is thin where it matters most.** Stage 1 personas receive zero principal context; synthesis receives a 4-field `decision_maker` that no instruction references. Business context falls back to hardcoded generic terms when the registry record is missing (cross-tenant contamination class). `principal.time_frame` is not wired anywhere.
4. **Stronger models obey everything — including what shouldn't be there.** Fable followed the dev-era Cascade guardrails literally and leaked `PLAN:/VERIFIED_ACTION:` into a customer-facing answer. Over-prescriptive prompts measurably reduce output quality on Sonnet 5 / Fable (per Anthropic migration guidance and our round-1 vs round-3 outputs).
5. **The refinement interviewer re-asks known facts.** In the HITL replay, the incumbent re-probed the Chain A contract lock the principal had already stated. No instruction tells the interviewer to build on captured refinements rather than re-validate them.

## 2. Design principles

1. **Schema in the API, analysis in the prompt.** Move output-shape enforcement to structured outputs (`output_config.format` with a JSON schema derived from the Pydantic response models). The API then *guarantees* shape; every format MUST-rule comes out of the prompt; regex salvage paths become dead code kept only as a fallback. (Known schema limits: no numeric min/max — recovery-range non-zero anchoring stays in the prompt, simplified.)
2. **Context contract, explicitly consumed.** Every context block injected must be paired with an instruction that says what to *do* with it. Data without direction is tokens wasted.
3. **Strict tenancy, no generic fallbacks.** A missing business-context record produces an explicit "no business context available" line — never invented defaults. (Same principle as the `_lookup_kpi_scoped` fix.)
4. **De-prescribe for current-generation models.** State the goal, the accuracy constraints, and the audience; stop enumerating steps. A/B every deletion — the CONSISTENCY CHECK and grounding rules are analytical (keep); the format rules are scaffolding (remove once schemas land).
5. **Principal lens at every LLM touchpoint** — not just persona selection. This is the product's stated differentiator (principal-lens weighting design) and is currently unwired at the reasoning layer.

## 3. Solution Finder changes

### 3.1 Structured outputs (enables everything else)
- Define `output_config.format` JSON schemas generated from `SolutionFinderResponse` sub-models (Stage 1: persona hypothesis schema; synthesis: full briefing schema including Phase 13's planned `DecisionAsk` and `List[ImmediateAction]`).
- `cross_review` keys are dynamic (persona IDs) — build the schema per request; the 24h schema cache keys on content, and the persona sets are few (MBB default + presets).
- Delete from the prompt once schemas land: "EXACTLY 3", enum echoes, JSON skeleton (~140 lines), perspectives format examples, persona-key compliance line. Keep (simplified): recovery-range anchors, grounding rules.
- Raise synthesis `max_tokens` 16384 → 20000 (defensive; Sonnet 5 tokenizer). Track `stop_reason` — a `max_tokens` stop must surface as a warning on the response, never a silent salvage.

### 3.2 Context contract
**Principal block — injected at BOTH stages** (Stage 1 task + synthesis INPUT DATA), sourced from the full principal profile:

```json
"decision_maker": {
  "role", "decision_style", "priorities",
  "time_frame",            // planning horizon — currently unwired
  "accountability_scope",  // owned KPIs / business processes
  "decision_authority"     // what they can approve vs must escalate
}
```

Paired instructions:
- Stage 1: "You are advising the {role} directly. Weight your hypothesis and option toward their stated priorities ({priorities}) and planning horizon ({time_frame}). Conviction should reflect what evidence would move *this* decision maker."
- Synthesis: "Rank options and frame `time_to_value` against the decision maker's horizon. Lead `recommendation_rationale` with their top priority. Flag any option exceeding their decision authority as requiring escalation in `prerequisites`."

**Business context** — strictly tenant-scoped; delete the hardcoded fallback dict. Extend the BC registry record (Phase 12A company-intelligence generator already researches this) with: competitive posture, margin-structure norms, strategic objectives. Instruction: "Calibrate recovery estimates and option feasibility against this business's structure — do not import generic industry assumptions that contradict it."

**Label fix:** `dataset_recap`'s `PRINCIPAL CONTEXT:` line → `PRINCIPAL-PROVIDED CONTEXT (from refinement):` — it is the principal's *statements*, not their profile.

### 3.3 Prompt slimming (post-schema)
Target: synthesis instruction prefix shrinks from ~12 rule blocks to 4: (1) role + council framing, (2) accuracy contract (grounding, CONSISTENCY CHECK, cross-basis scoping, no-more-analysis), (3) context-consumption instructions (§3.2), (4) mode/alert framing. Everything else moves to schema or dies. A/B each removal batch on the frozen Lubricants scenario using the existing harness.

## 4. Deep Analysis changes

### 4.1 Refinement interviewer (`_generate_refinement_question`)
- **Value-of-information rule:** "Ask the question whose answer would most change either the diagnosis or the viable solution space. Prefer questions that could *eliminate* a whole class of options (contractual locks, capacity constraints, board commitments)."
- **No re-asking:** "Never re-ask something already in REFINEMENTS CAPTURED — reference it and probe the adjacent unknown instead." (Directly fixes the observed Chain A re-ask.)
- **Elicitation targets over topic scripts:** keep the topic sequence as coverage scaffolding, but give the model the *unknowns checklist* per topic (unexercised levers, off-limits actions, structural barriers to replication, hidden one-time events) rather than a single canned objective.
- **Principal lens:** pass `time_frame` and `priorities` so questions calibrate ("given your Q4 target…").
- Structured output `{question, suggested_responses}` via schema (removes the multi-question post-processing hack).

### 4.2 SCQA narrative
Largely sound (mode- and alert-aware since 11I). Two refinements: (a) structured output with `{situation, complication, question, answer}` fields instead of labelled-sentence parsing; (b) inject `decision_maker.time_frame` so "Question" frames the decision window ("before Q1 renewal") rather than generic urgency.

### 4.3 Briefing Q&A endpoint
- Structured output `{answer, sources[], followups[]}` — deletes the `SOURCES:`/`FOLLOWUPS:` sentinel parsing.
- `max_tokens` 800 → 1200 (Fable answer truncated mid-sentinel in testing).

## 5. Runtime default system prompt
Done 2026-07-13: the product runtime is **decoupled** from `docs/cascade_guardrails.yaml`. That file was development coaching for the coding assistant that built the codebase (Windsurf/Cascade era) and is preserved untouched as a dev artifact — the product never reads it. The runtime default now lives in code: `A9_DEFAULT_SYSTEM_PROMPT` in `src/llm_services/claude_service.py` (grounding, format-follows-request, business audience, no-guessing); the LLM Service agent's unused loader delegates to the same constant. Longer term: per-call-site system prompts everywhere (audit: SF QA, DA insight extraction, SA observations currently rely on the default).

## 6. Test & migration plan
1. Reuse the frozen-input A/B harness (scratchpad `ab_synthesis_test.py` / `hitl_ab_test.py` patterns — recreate from DEVELOPMENT_PLAN 11O notes if scratchpad is gone).
2. Acceptance per change batch: (a) schema-valid output on 20+ synthetic runs (Phase 13's own bar for `ImmediateAction`), (b) no regression on the Lubricants scenario vs the current-prompt baseline output (side-by-side review), (c) unit suite green.
3. Sequence: 3.1 schemas → 4.3 QA schema (smallest) → 3.2 context contract → 3.3 slimming (batched deletions, A/B each) → 4.1 interviewer → 4.2 SCQA.
4. Each batch is independently shippable and env-rollback-safe (prompts are code; rollback = revert commit).

## 7. Effort

| Batch | Scope |
|---|---|
| 3.1 + 4.3 structured outputs + token caps | M |
| 3.2 context contract (incl. BC registry fields + no-fallback) | M |
| 3.3 prompt slimming + A/B validation | S–M |
| 4.1 refinement interviewer | S |
| 4.2 SCQA structured output | S |
