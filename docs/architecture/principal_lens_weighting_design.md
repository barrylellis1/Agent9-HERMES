# Principal Lens Weighting — Design Sketch

**Last updated:** 2026-07-02
**Status:** Design sketch (pre-implementation)
**Related:** [analytical_methodology_positioning.md](analytical_methodology_positioning.md) (KT + MBB engine), [principal_id_based_lookup_plan.md](principal_id_based_lookup_plan.md), [kpi_accountability_model.md](kpi_accountability_model.md)

---

## 1. Purpose

Agent9 runs one analytical engine (SA sensors → DA decomposition → SF framing → VA measurement). This sketch defines how that single engine produces **role-appropriate output per principal** — a CEO, CFO, and COO looking at the same client data should each see a different *ordering, threshold materiality, time horizon, and framing*, without forking the engine.

It corrects a tempting-but-wrong premise: **"McKinsey = CEO, BCG = CFO, Bain = Bain/COO" is not a real taxonomy.** All three MBB firms serve every C-suite seat. What actually varies is the **role's decision frame** — which *comparison lens* it weights, at what horizon, and what counts as material. Firm "house styles" only loosely echo those frames and belong (if anywhere) in a presentation skin, not the engine.

---

## 2. The Five Comparison Lenses (recap)

A thorough profitability-and-growth appraisal triangulates five lenses. Our current alert methodologies cover only the first two.

| # | Lens | Question | Engine coverage today |
|---|------|----------|-----------------------|
| L1 | **vs Plan** | Hitting commitments? | ✅ `plan_variance` |
| L2 | **vs Trend / momentum** | Improving or decaying, how fast? | ✅ `threshold_breach` (YoY) + `projected_breach` + `acceleration` |
| L3 | **vs Peer / market** | Gaining or losing share? | ❌ missing (hooks: `benchmark_range`/`benchmark_source`, MA agent) |
| L4 | **vs Full potential (value gap)** | Distance to best-in-class? | ⚠️ partial — DA replication targets (internal benchmark) |
| L5 | **Decomposition / bridge** | *Why* did it move (P×V×M×FX×one-off)? | ⚠️ DA dimensional, not a true P×V×M walk |

Opportunities in an MBB sense are **value gaps (L3/L4)**, not green-band beats. The strongest opportunity engine is therefore DA's L4 path, and the highest-value *new* lens is L3.

---

## 3. Role Decision Frames → Lens Weighting

The mapping the engine should encode (firm heritage shown only as intuition, not as config):

| Principal | Decision frame | Primary lenses | Horizon | Materiality bar | Echoes |
|-----------|----------------|----------------|---------|-----------------|--------|
| **CEO** | Value creation, portfolio, competitive position | L3 peer/market, L4 value gap, economic profit across BUs | Multi-year, three-horizons | Portfolio-moving | McKinsey |
| **CFO** | Capital efficiency, variance control, forecast reliability | L1 plan, L5 bridge, ROIC vs WACC | Quarter / year | Variance & cash | BCG |
| **COO** | Throughput, cost-to-serve, execution | L4 replication (best-unit), granular disaggregation, L5 of the operational miss | Weekly / monthly | Operational run-rate | Bain |

The **Hess CFO scan we validated already leans on L1 (`plan_variance`)** — evidence the CFO frame is the natural first cut and a good pilot.

---

## 4. Proposed Model: `PrincipalLensProfile`

A sibling of the KPI-level `monitoring_profile` — but scoped to the principal, controlling *how the engine prioritizes and frames*, not *what* it monitors.

```python
class PrincipalLensProfile(BaseModel):
    lens_weights: Dict[str, float]        # {"plan": 1.0, "trend": 0.6, "peer": 0.3, "value_gap": 0.8, "bridge": 0.9}
    materiality: Dict[str, float]         # per-lens threshold multiplier (CFO tighter on plan; CEO higher floor)
    horizon: str                          # "weekly" | "monthly" | "quarterly" | "annual" | "multi_year"
    forward_periods: int                  # forward-looking periods to project/show
    historical_periods: int               # trailing periods for trend/bridge
    emphasis: List[str]                   # framing hints for DA/PIB: ["variance","cash"] | ["share","portfolio"] | ["throughput"]
```

Attach as an optional field on `PrincipalProfile` (`None` → role-derived defaults keyed off `title`).

### ⚠️ Reuse, don't reinvent: `time_frame` is framed-but-NOT-wired

`PrincipalProfile.time_frame` (`TimeFrame`: `default_period`, `historical_periods`, `forward_looking_periods`) and `communication.emphasis` **already exist on the model and in the legacy `DEFAULT_PRINCIPALS` seed — but have zero runtime consumers** (verified: the scan timeframe comes entirely from the API request; SA/DA/workflows never read `principal.time_frame`).

Implication for this design:
- **Do not add a parallel horizon field and leave both dangling.** Fold `time_frame`'s three fields into `PrincipalLensProfile` (or have the profile supersede them) and *wire the consumer*.
- The first concrete win is small and independent of lenses: **have the SA workflow default `request.timeframe` from the principal's preference when the caller omits it.** That closes an existing framed-not-wired gap immediately.

---

## 5. Runtime Integration

| Component | Change |
|-----------|--------|
| **Principal Context Agent** | Serve `PrincipalLensProfile` (explicit or role-derived) alongside the existing context. Single source of truth. |
| **SA Agent** | (a) Default scan `timeframe`/`horizon` from the profile when unset. (b) Apply per-lens `materiality` to threshold gating (CFO tighter plan bands; CEO higher floor). (c) Order/prioritize emitted situations by `lens_weights`. Detection methodologies stay universal — only prioritization & thresholds become principal-scoped. |
| **DA Agent** | Use `emphasis` + horizon to choose framing (e.g., CFO → P×V×M bridge; CEO → portfolio value gap; COO → best-unit replication). |
| **New lenses** | L3 peer/market (`benchmark_gap`) is the highest-value addition and is CEO-primary; build after the profile plumbing exists. |

Guardrail (per project rule): SA remains a sensor of facts; lens weighting affects **ordering, thresholds, and which sensors fire**, not the truth of a reading. DA owns interpretation/framing.

---

## 6. Agent Impact Analysis

The lens model is not just an SA change — it flows through the whole pipeline: **Principal Context** (serves the profile) → **SA** (senses, orders, thresholds) → **DA** (decomposes, frames) → **SF** (prescribes, frames) → **VA** (measures), with **MA** feeding the peer/market lens. Each agent's card must be updated as part of the build.

| Agent | Role in lens model | Change required | New capability gap |
|-------|--------------------|-----------------|--------------------|
| **Principal Context** | Source of truth for `PrincipalLensProfile` | Resolve explicit profile or derive role defaults from `title`; expose on principal context. Wire the framed-but-unwired `time_frame`. | Minor — additive field + resolver |
| **SA** (see §5) | Sensor; applies ordering + materiality + default timeframe | Read profile; prioritize/threshold by it; default timeframe when caller omits. Detection stays universal. | None — reuses threshold-presence gating |
| **DA** | Owns **L4 value gap** + **L5 bridge** | Framing responds to `emphasis`/horizon (CFO→bridge, CEO→portfolio gap, COO→replication). **Emit a structured driver-decomposition output** to feed the Value Driver Tree (node → driver → value-at-stake), not just narrative SCQA. Surface benchmark segments as first-class quantified opportunities. | **L5 true P×V×M bridge** — DA today does dimensional IS/IS-NOT, not a price/volume/mix walk. New methodology. Plus a structured tree-output contract. |
| **MA** | Enabler for **L3 peer/market** | Provide **quantified peer benchmarks / ranges** (not just narrative competitor context) that SA/DA can compute a gap against. Most relevant to the CEO frame. | **Structured benchmark output** — MA output is currently qualitative; L3 needs numeric comparators. Ties to `benchmark_range` / `benchmark_source` KPI fields. |
| **SF** | Prescribes; MBB persona framing | Bias persona emphasis + synthesis framing by lens profile (CFO→cost/variance/cash; CEO→portfolio/growth; COO→operational/execution). Tie quantified impact back to the driver-tree node it addresses. | Moderate — persona weighting becomes principal-scoped; value-at-stake linkage |
| **VA** (not named, noted) | Measures value-at-stake realized | Minimal now; later the driver-tree node's value-at-stake becomes the VA baseline / expected-impact anchor. | Deferred |

**Cross-agent insight:** the Value Driver Tree is only as good as **DA's L5 decomposition** and **MA's L3 benchmarks** — those two are the real capability gaps. The lens *plumbing* (Principal Context + SA) is cheap; the *analytical depth* (DA bridge, MA quantified benchmarks) is the hard part and should gate the roadmap. Cards to update when built: `a9_principal_context_agent`, `a9_situation_awareness_agent`, `A9_Deep_Analysis_Agent`, `a9_market_analysis_agent`, `a9_solution_finder_agent`.

---

## 7. Value Driver Tree — Visualization Requirement

Five lenses at granular resolution produce a lot of signal. A principal needs a **single "bigger picture" digest**: a **Value Driver Tree** that roots on the principal's apex metric and decomposes into the drivers each situation attaches to.

**Requirement (V1):**
- **Root** = principal's apex value metric (CEO → Economic Profit / ROIC-vs-WACC; CFO → Net Income / margin; COO → cost-to-serve / throughput).
- **Branches** = the driver decomposition: Revenue → Volume × Price × Mix; Margin → operating leverage, cost-to-serve, inflation; Capital → working capital, asset intensity. Driven by DA's decomposition (L5), not hand-drawn.
- **Node state** = worst attached situation's severity/polarity (red problem / green opportunity), with **value-at-stake** ($ impact) as the node weight — so the eye goes to the biggest lever, not the loudest alert.
- **Interaction** = click a node → the underlying situation cards / DA analysis (reuses existing DeepFocusView drill-down).
- **Per-principal shaping** = the tree's root and the branch emphasis come from the `PrincipalLensProfile` — the CFO tree foregrounds the margin/variance branch; the CEO tree foregrounds portfolio/market.

**Why it matters:** it turns N independent alert cards into one causally-organized, value-weighted picture — the deliverable an MBB team would put on the first page. It also gives L4/L5 (value gap + bridge) a natural home in the UI, which today they lack.

**Status:** requirement only. Needs its own UI spec (data shape from DA, layout, sizing by value-at-stake). Candidate sibling to the KPI-tile and DA-visualization specs already in memory.

---

## 8. Phasing

Sequencing is gated by agent capability, not UI: the cheap plumbing (Principal Context + SA) comes first, but the high-value lenses depend on the two hard agent gaps from §6 — **MA structured benchmarks** (blocks P2) and **DA L5 bridge output** (blocks P3).

1. **P0 — Plumbing.** Add `PrincipalLensProfile` (role-derived defaults); Principal Context Agent serves it; wire SA to default `timeframe` from it (closes the framed-not-wired gap). No new lenses yet. *Agents: PC, SA.*
2. **P1 — CFO pilot.** Apply materiality + ordering for the CFO frame on Hess (L1 + L5 emphasis). Validate against the scan we already trust. *Agents: SA, DA (framing).*
3. **P2 — L3 peer/market (`benchmark_gap`).** Highest-value new lens; CEO-primary. **Blocked on MA emitting quantified benchmarks** into `benchmark_range` / `benchmark_source`. *Agents: MA, SA.*
4. **P3 — Value Driver Tree V1.** **Blocked on DA emitting a structured L5 driver-decomposition contract** (node → driver → value-at-stake). *Agents: DA, UI.*
5. **P4 — Cheap symmetry.** Acceleration-improvement + tag outperformance (the deferred Option A) once the frame is in place. *Agents: SA.*
6. **P5 — SF framing + VA linkage.** Principal-scoped SF persona/synthesis framing; driver-tree value-at-stake feeds VA expected impact. *Agents: SF, VA.*

---

## 9. Open Questions

### Model & framing
- Should `lens_weights` be continuous (0–1) or ordinal (primary/secondary/off)? Ordinal is simpler to seed and reason about.
- Where does economic-profit framing (ROIC vs WACC) live — a derived KPI, a DA framing layer, or a new responsibility? Affects the CEO tree root.
- Does the Value Driver Tree root differ per *principal* or per *client apex metric*? Likely principal, with a client default.
- Committee/team principals (`PrincipalType.COMMITTEE`) — blended lens profile, or the chair's?

### Agent-impact questions (from §6)
- **DA output contract:** does DA emit a *structured* driver-decomposition (tree nodes + value-at-stake) as a new output model, or as an extension of the existing SCQA output? The Value Driver Tree depends on it.
- **L5 bridge data:** does a true P×V×M bridge require new columns (volume, unit price) in the data-product contract, or can it be derived from existing amount/quantity fields? Determines whether L5 is a modeling change or just a DA method.
- **MA benchmark reliability:** can MA produce quantified peer benchmarks reliably via Perplexity + Claude, or do we need a curated per-industry benchmark source? What confidence do we attach, and how is a low-confidence benchmark surfaced vs suppressed?
- **SF persona scoping:** should SF *persona weighting* become principal-scoped, or stay universal with only the synthesis framing shifting by lens profile?
- **VA linkage:** when the driver-tree node carries a value-at-stake, does that become the VA expected-impact baseline automatically, or stay a separate SF-supplied number?
