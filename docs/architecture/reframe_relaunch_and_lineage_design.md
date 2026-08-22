# Reframe Re-Launch: New-Window DA + Framing Lineage

**Created:** 2026-08-22
**Status:** Design note, not built
**Triggered by:** live-testing the Gross Margin % → COGS reframe this session and asking a direct
question — does reframing actually re-run analysis on the new KPI?

---

## 1. The finding: reframe today re-narrates, it doesn't re-analyze

Confirmed by reading `generate_scqa_for_frame` (`a9_deep_analysis_agent.py:4094`): it reconstructs
`kt`, `change_points`, and `plan` from the **existing** `da_output` dict — the same Is/Is-Not
dimensional breakdown and change points already computed for the *original* breached KPI. It never
calls `execute_deep_analysis` again. The `frame` parameter only changes the SCQA's narrative text, not
the evidence underneath it.

Concretely, in today's own live test: the CFO reframed Gross Margin % onto COGS, and the resulting SF
solutions ("Base Oil Procurement Renegotiation," etc.) were grounded in Gross Margin %'s *own*
dimensional breakdown (Synthetic Blend Engine Oil, Compressor Oil segments — margin's drivers), dressed
in COGS-sounding language. They read as COGS-grounded. They weren't.

**This was named, not missed — but the mitigation never shipped.** The Phase 19 implementation plan
has a section on exactly this ("New Situation Card on reframe," explicitly out of scope) and specifies
an honest disclosure: *"Recorded. Solutions will be generated against this objective. A separate
analysis of {kpi} has not been run."* Checked: that string exists nowhere in
`decision-studio-ui/src/`. The plan disclosed the limitation; the disclosure itself was never built.
Today the product is worse than "known gap, stated plainly" — it's "known gap, silently unstated."

---

## 2. Why the deferred fix (SA situation-card provenance) isn't actually required

The Phase 19 plan deferred the real fix because SA has no provenance path for a situation card born
from a reframe rather than a threshold breach — a large blast radius (card creation, the situations
store, the dashboard grid).

**Checked directly: that blast radius belongs to the UI path, not to DA itself.**
`DeepAnalysisRequest` requires only `kpi_name` (+ `client_id`, optional threshold/timeframe) —
`execute_deep_analysis` runs against any KPI id directly, breach or no breach. COGS is already a fully
registered KPI with its own thresholds seeded. The situation-card dependency is specific to
`DeepFocusView` being driven by in-memory React state set by clicking a card — not a constraint DA
itself has.

**Proposed mechanism: a new browser window/tab, not a new situation card.** `/dashboard` currently
takes no URL params — everything is in-memory state from a card click, so a fresh tab has nothing to
hydrate. The actual missing piece is small and specific: a URL-param-driven entry
(`/dashboard?kpi=cogs&principal=cfo_001&reframed_from=<assumption_id>`) that `useDecisionStudio.ts`
reads on mount and uses to trigger a DA run directly, bypassing the situation-card click entirely. This
avoids the situations store, the dashboard grid, and SA's card-provenance model completely — the three
things the original plan named as the reason to defer.

---

## 3. The framing gate runs fresh at each hop — confirmed, not a judgment call

Direct question raised in conversation: does the new window's DA run skip its own framing gate (since
the objective was "already decided" by the reframe), or run it again?

**The answer is yes, run it again — the two are different questions, not the same one asked twice.**
Once COGS has its own fresh DA run, it has its own causal neighbourhood — `base_oil_cost`,
`distribution_cost` sit one hop from COGS, not from Gross Margin %. Whether COGS itself is the right
place to stop, or whether the real lever is one hop further out, is a genuinely new question at a
genuinely new node. Skipping the gate would answer a question that was never asked. This can chain
multiple times (margin → COGS → base_oil_cost → ...) and there is no reason to cap it artificially —
the causal graph itself is finite (`max_hops=2` per hop) and bounds how far any single step can reach.

**The corollary matters as much as the mechanism: confirming at any hop is a legitimate outcome, not a
failure.** This is the same finding the original Phase 19 adjudication already established for the
first hop — *"the objective was very likely right, but was never once examined."* A chain that
terminates in a confirm, after genuinely walking outward and checking, is the gate working as designed.
Worth stating plainly in whatever documentation covers this, since a terminating confirm is easy to
misread as a dead end rather than a legitimate answer arrived at honestly.

**Checked, not assumed: does this risk looping back to the KPI just left?** No — the existing
`causal_direction` path-validity filter (built earlier this session) already prevents it as a side
effect, not something new. Gross Margin % is a confirmed downstream effect of COGS, so the hop-1
exclusion rule already keeps it off COGS's own alternative list. The chain can walk outward; it cannot
accidentally walk back to where it came from.

---

## 4. The real gap: nothing links successive framing decisions into one chain

`AssumptionProvider.get_active_framing(client_id, scope=kpi_id)` is scoped per-KPI. Gross Margin %'s
framing record and COGS's are two independent rows with no structural link between them. Reframe
margin → COGS → base_oil_cost, and nothing today reconstructs that as one lineage rather than three
disconnected decisions.

**Proposed: `reframed_from_id: Optional[str]` on `Assumption`** (meaningful only for
`record_type="framing"` rows) — a back-reference to the prior framing record's own `id` in the chain.
Walking it backward reconstructs the full lineage: which KPI was the origin, every intermediate hop,
and the falsification criterion recorded at each step. Small, additive, no migration surprises — same
shape as `causal_direction`'s own default-preserving addition.

**Why this matters beyond UI display (though it matters there too — the user should be able to see the
whole path they walked, not just the last hop):** it's what the VA-capture gap found two turns ago
actually needs to be useful. `kpi_relationship_basis_design.md`'s sibling finding — `AcceptedSolution`
captures no framing decision and no reference to which `KPIRelationship` edge a solution's mechanism
relied on — only gets fully answered by capturing the *chain*, not the last hop alone. VA's eventual
"confirm or modify theory layer components" job needs to know every edge the final decision rests on to
grade the right ones, not just the one edge nearest the final KPI.

---

## 5. What's built vs. not

**✅ Built (2026-08-22):** the disclosure banner. Rendered in `DeepFocusView.tsx` immediately below the
SCQA block, conditioned on `(refinementResult?.framing_decision ?? framingDecision)` having
`choice !== 'confirm_stated'` — the exact same decision-resolution pattern already used (and live-
verified this session) for SF's dispatch payload at the same file's line 359, so the data path is known
correct. States the chosen objective plus *"A separate analysis has not been run for this objective —
the evidence above still reflects the original KPI's own analysis, re-framed to this decision."*
`tsc --noEmit` and `npm run build` both clean. Not re-verified against a fresh live run (the underlying
`framing_decision` resolution was already live-verified for the SF-dispatch consumer of the same field
in this session's `live-framing-gate.spec.ts` run) — a live screenshot check would still be worth doing
before this is considered fully confirmed in the running app, not just compiled correctly.

**Not built, the rest:**
- The new-window URL-param entry route and `useDecisionStudio.ts` wiring to trigger DA directly from it.
- `reframed_from_id` on `Assumption`, and the UI work to display a reconstructed chain.
- Threading the full chain (not just the last hop) into `AcceptedSolution`'s framing snapshot — extends
  the still-unwritten VA-capture design from `kpi_relationship_basis_design.md`'s pending follow-up.
- Any cap or safeguard on chain depth — not needed today (the causal graph is finite), flagged as a
  tripwire if this pattern ever needs revisiting.

**Sequencing:** the disclosure text is independent and cheap — ship it any time. Everything else in
this note (new-window entry, fresh framing gate per hop, lineage field, whole-chain VA capture) is one
coherent piece of work; building the new-window mechanism without the lineage field would recreate the
same "which edges does this decision actually rest on" gap one level up.
