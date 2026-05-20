# DA Mixed Analysis Mode — Design Document

**Created:** 2026-05-20
**Status:** Planned (Phase 11G)
**Supersedes:** Binary `analysis_mode` (problem | opportunity) set by SA/frontend

---

## Problem Statement

The current pipeline forces a binary framing: every KPI situation is either a *problem* (DA finds lagging segments, red IS/IS NOT) or an *opportunity* (DA finds leading segments, green IS/IS NOT). The framing is determined upstream by SA's threshold logic and propagated through to DA unchanged.

In practice, **mixed-signal KPIs are the dominant enterprise case.** An aggregate KPI that is slightly below target will almost always contain both outperforming segments (proof that the target is achievable) and underperforming segments (where the gap actually lives). The current binary model forces the analyst to either ignore the outperformers (problem mode) or ignore the laggards (opportunity mode).

**Example:** Gross Margin % is 2% below target. Service Centers Division (+20bps) and National Auto Parts Chain A (+90bps) are outperforming. Manual Gear Oil (-1.13bps) and two retail sub-segments are lagging. This is not a pure problem. It is not a pure opportunity. It is the normal state of a complex portfolio, and the most actionable insight is the *gap between the two* — the leading segments contain the proof of what works.

---

## Design Principle

> **SA is a sensor. DA is the analyst.**

SA emits `direction` (up / down) based on aggregate KPI threshold logic. That is all it should do. DA examines the segment variance structure and determines the appropriate analytical framing — including detecting the mixed case. The `analysis_mode` field passed from the frontend to DA is a *hint*, not a directive. DA overrides it when the segment data says otherwise.

---

## Detection Logic

After DA runs the IS/IS NOT dimensional query and computes segment deltas, it evaluates:

```
mixed_threshold = 0.10  # configurable per KPI monitoring profile

has_problem = any(segment.delta < -mixed_threshold for segment in is_segments)
has_opportunity = any(segment.delta > +mixed_threshold for segment in is_segments)

if has_problem and has_opportunity:
    effective_mode = 'mixed'
elif has_problem:
    effective_mode = 'problem'
elif has_opportunity:
    effective_mode = 'opportunity'
else:
    effective_mode = requested_mode  # fallback to hint when signal is weak
```

The `mixed_threshold` defaults to 10% of the KPI's baseline value and is configurable via the KPI monitoring profile (Phase 11D introduces adaptive calibration).

---

## Data Model Changes

### `DeepAnalysisResponse`

```python
class DeepAnalysisResponse(A9AgentBaseResponse):
    ...
    analysis_mode: Literal["problem", "opportunity", "mixed"] = "problem"
    mixed_framing: bool = False  # True when DA overrode the requested mode
    
    # Extended KTIsIsNot for mixed mode
    kt_is_is_not: Optional[KTIsIsNot] = None
```

### `KTIsIsNot`

```python
class KTIsIsNot(A9AgentBaseModel):
    # Existing fields retained (backward compatible)
    where_is: List[Dict[str, Any]] = Field(default_factory=list)
    where_is_not: List[Dict[str, Any]] = Field(default_factory=list)
    ...
    
    # Mixed mode: explicit segment classification
    problem_segments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Segments with significant negative delta — need fixing"
    )
    opportunity_segments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Segments with significant positive delta — proof of replicable success"
    )
```

**Backward compatibility:** In problem/opportunity mode, `problem_segments` and `opportunity_segments` are empty; `where_is` / `where_is_not` carry the data as today. In mixed mode, all four lists are populated.

---

## SCQA Narrative — Mixed Mode Prompt

The mixed-mode SCQA leads with the *gap story*, not a problem headline and not an opportunity headline:

```
MIXED MODE FRAMING RULES:
- The KPI has both outperforming AND underperforming segments simultaneously.
- The SITUATION is the aggregate KPI position (above/below target by X%).
- The COMPLICATION is the internal gap: leading segments are proving the playbook works
  while lagging segments have not yet adopted it.
- The QUESTION is how to systematically transfer the proven mechanics from leading segments
  to lagging segments — not "fix the problem" and not "chase the opportunity" in isolation.
- The ANSWER is a sequenced programme: codify the leading segment playbook, deploy into
  lagging segments, track aggregate KPI recovery.
- DO NOT frame this as purely a problem or purely an opportunity.
- Be specific: name the leading segments and their deltas. Name the lagging segments.
  Quantify the gap between them as the replication opportunity.
```

---

## IS/IS NOT Exhibit — Mixed Render

The `IsIsNotExhibit` component already renders both red (IS) and green (IS NOT) bars depending on `isOpportunity`. In mixed mode, both colors appear in the same exhibit without a mode switch:

- **Problem segments** → rendered red (same as problem mode IS bars)
- **Opportunity segments** → rendered green (same as opportunity mode IS bars)
- **Header badge:** "Mixed Signal" in amber instead of the current red/green badge
- **Legend:** "Lagging — needs fixing" (red) + "Leading — replication proof" (green)
- **Net variance display:** split into `netProblemVariance` (red) and `netOpportunityVariance` (green)

No new component required — `IsIsNotExhibit` accepts `isOpportunity='mixed'` and branches rendering.

---

## Downstream Agent Impact

### Market Analysis Agent

MA receives `mixed_framing=True` in context. Prompt adjustment:

> "The internal analysis shows both outperforming segments (+Xbps) and underperforming segments (-Ybps) within the same KPI. Search for market signals that help explain: (a) why leading segments are succeeding — is there a market tailwind specific to their category? (b) why lagging segments are underperforming — is there a market headwind specific to their category? Surface signals that differentiate the two."

### Solution Finder Agent

In mixed mode, SF receives the full segment breakdown. The Council Debate personas are prompted to generate options spanning the fix-and-replicate trade-off space:

- **Option 1 (replication-first):** Codify leading segment playbook and deploy into lagging segments. Fixes laggards as an indirect consequence.
- **Option 2 (fix-first):** Directly address lagging segment root causes, then accelerate leading segment growth.
- **Option 3 (parallel tracks):** Run both workstreams simultaneously. Higher resource requirement, faster aggregate recovery.

The cross-review debate naturally surfaces the sequencing tension — this is a richer debate than either pure-problem or pure-opportunity mode.

### Value Assurance Agent

VA tracks the composite KPI recovery as the primary signal. In mixed mode, VA's trajectory chart optionally breaks out:
- Leading segment delta (should be maintained or improved)
- Lagging segment delta (should move toward leading segment benchmark)
- Aggregate KPI delta (the primary tracked metric)

This is a display enhancement only — the underlying DiD attribution model operates at the KPI level unchanged.

---

## ICP Stakeholder Value

The mixed framing is the most executive-natural view of a complex KPI:

> "We're 2% below target overall, but Service Centers is up 20bps and National Auto Parts Chain A is up 90bps. The problem and the solution are sitting next to each other in the same data — it's a deployment gap, not a market problem."

This is exactly how a McKinsey or BCG partner would frame a KPI miss in a board presentation. Decision Studio should speak that language natively.

---

## Implementation Sequence

1. **Pydantic model changes** — `DeepAnalysisResponse.mixed_framing`, `KTIsIsNot.problem_segments` / `opportunity_segments`
2. **DA detection logic** — post-query mixed_threshold evaluation in `execute_deep_analysis`
3. **DA SCQA prompt** — mixed mode prompt variant in `_generate_scqa_summary`
4. **Frontend IS/IS NOT exhibit** — `isOpportunity='mixed'` branch in `IsIsNotExhibit`
5. **MA prompt enrichment** — differentiated market signal search for mixed context
6. **SF Council Debate** — mixed-mode option framing guidance in synthesis prompt
7. **VA trajectory display** — optional segment breakdown in portfolio chart

---

*See DEVELOPMENT_PLAN.md Phase 11G for delivery scope and sequencing.*
