# Agent9 Analytical Methodology: KT + MBB Architecture

**Last updated:** 2026-05-20
**Status:** Positioning & design rationale document

---

## 1. Executive Summary

Agent9 combines two complementary analytical traditions — **Kepner-Tregoe (KT) Problem Analysis** for automated root cause diagnosis and **MBB consulting frameworks** for strategic solution framing — connected through a **Value Assurance** measurement loop that uses KT's dimensional output as causal control groups.

This architecture is unique: no competing platform diagnoses with structured dimensional analysis, recommends with consulting-grade frameworks, AND proves results with causal attribution — all in a single automated pipeline.

```
KT (DA Agent)       →  MBB (SF Agent)      →  KT again (VA Agent)
Diagnose               Prescribe               Measure
IS / IS NOT            Persona frameworks       Control groups from IS NOT
Automated, data-driven Expert judgment, LLM     Causal attribution
```

**The next evolution — three Analytical Intelligence Layers** extend the architecture from reporting what the data says to reasoning about how much to trust it, how KPIs interact, and how to optimize across them simultaneously:

| Layer | Capability | Agent Owner | Phase |
|-------|-----------|-------------|-------|
| **Layer 1 — Statistical Rigor** | Confidence-scored IS/IS NOT; effect size; seasonal decomposition; outlier flagging | DA Agent | Phase 11H |
| **Layer 2 — Causal KPI Mapping** | KPI interdependency map; cross-KPI conflict detection before solution approval | DGA + DA | Phase 2 (2027) |
| **Layer 3 — Portfolio Optimization** | Optimal sequencing of concurrent interventions; cross-intervention conflict detection; strategic alignment scoring | Business Optimization Agent | Phase 3 (2028) |

See Section 8 for the full design rationale.

---

## 2. Why KT for Diagnosis (Deep Analysis Agent)

### The Framework

Kepner-Tregoe Problem Analysis asks four questions across two columns:

| Dimension | IS (affected) | IS NOT (not affected) |
|-----------|---------------|----------------------|
| **WHAT** | Which KPIs/products are affected? | Which similar ones are fine? |
| **WHERE** | Which regions/segments/channels? | Which ones are unaffected? |
| **WHEN** | When did it start? What changed? | When was it still normal? |
| **EXTENT** | How severe? How many? | What's the boundary of impact? |

### Why It's Ideal for Automation

1. **Maps directly to SQL queries.** "Is Gross Margin declining in Region East?" is a `GROUP BY region` query against the data product. MBB issue trees require senior partner judgment to scope — KT's dimensions are computable.

2. **Produces control groups for free.** The IS NOT column identifies unaffected dimensions (Region West, Product Line B) that become natural control groups for Value Assurance's counterfactual attribution. This dual-use was not designed intentionally — it's an emergent architectural advantage.

3. **Falsifiable.** KT forces you to explain WHY the distinction exists between IS and IS NOT. If you can't explain why Region East is affected but Region West isn't, you haven't found the root cause. This is scientific method applied to business diagnostics.

4. **Constrains LLM hallucination.** The DA Agent's LLM role is insight extraction from structured dimensional query results — not open-ended speculation. The data constrains the output.

5. **Deterministic and repeatable.** The same data produces the same IS/IS NOT analysis. MBB diagnosis quality varies with the consultant assigned. KT produces consistent results regardless of who (or what) runs it.

6. **Parallelizable.** Each dimension (WHAT, WHERE, WHEN, EXTENT) can be analyzed independently and concurrently. DA Agent already uses this for performance.

### Where KT Falls Short

| Gap | How Agent9 Compensates |
|-----|----------------------|
| KT doesn't ask "so what?" — it isolates the root cause but doesn't prescribe solutions | SF Agent (MBB personas) handles prescription |
| KT is bounded by available data dimensions — can't find causes not tracked in the data warehouse | MA Agent provides external market dimensions |
| KT struggles with multi-causal problems when multiple changes occur simultaneously | VA Agent reflects this as reduced confidence scoring |
| KT output is technical, not executive-friendly | LLM narrative generation translates to SCQA framing |
| KT doesn't assess strategic relevance | VA Strategy Alignment checks whether the problem still matters |
| **KT reports variance but doesn't say how much to trust it** — a segment delta could be statistical noise, a seasonal artefact, or a single outlier distorting the group mean | **Layer 1 (DA Statistical Enrichment)** — effect size relative to segment weight, seasonal decomposition, confidence scoring. KT's falsifiability principle is only meaningful if the IS/IS NOT distinction itself is statistically significant. |
| **KT analyses one KPI at a time** — it cannot detect when fixing KPI A degrades KPI B, or when two simultaneously recommended solutions conflict | **Layer 2 (KPI Causal Intelligence)** — interdependency map in DGA; conflict detection before solution approval; strategic alignment scoring across the full KPI portfolio |

---

## 3. Why MBB for Solutions (Solution Finder Agent)

### The Framework

SF uses a 4-call parallel LLM architecture with consulting firm personas:

| Persona | Framework Lens | Solution Focus |
|---------|---------------|----------------|
| **McKinsey** | MECE issue trees, hypothesis-driven | Root cause fixes, structured options, risk assessment |
| **BCG** | Portfolio view, value chain analysis | Strategic pivots, growth plays, market positioning |
| **Bain** | Results delivery, full potential | Quick wins, operational fixes, clear owners/timelines |

### Why MBB for Prescription (Not KT)

1. **Strategic framing.** KT tells you "supplier costs spiked in Region East since Week 12." McKinsey asks "is this a procurement issue or a strategic sourcing decision?" BCG asks "does this product line still belong in our portfolio?" Bain asks "what's the fastest path to margin recovery?" These frames require different solution types.

2. **Completeness through diversity.** Three consulting traditions with different philosophies ensure solutions cover strategic, operational, and tactical dimensions. A single framework produces single-dimension solutions.

3. **Executive resonance.** CFOs and CEOs are trained to consume MBB-style deliverables. McKinsey's MECE structure, BCG's portfolio matrices, and Bain's results-first framing are the lingua franca of C-suite decision-making.

4. **Principal-adaptive.** SF maps the principal's `decision_style` to the most appropriate persona emphasis. An analytical CFO gets McKinsey-led framing. A pragmatic COO gets Bain-led framing. Same problem, different presentation.

### What MBB Can't Do That KT Can

MBB diagnosis is subjective, expensive, slow, and non-repeatable:

| Dimension | KT (automated) | MBB (manual) |
|-----------|----------------|--------------|
| **Speed** | Minutes (SQL queries + LLM) | 4-12 weeks |
| **Cost** | Near-zero marginal cost | $500K-$2M per engagement |
| **Consistency** | Same data → same analysis | Depends on team assigned |
| **Bias resistance** | Data-driven, systematic | Anchoring, confirmation bias in hypothesis selection |
| **Scalability** | Run across all KPIs simultaneously | One engagement = one problem |
| **Measurability** | IS NOT = built-in control group | No measurement framework produced |

---

## 4. The Architectural Innovation: IS NOT as Control Group

This is Agent9's most defensible technical advantage. The same KT analysis that diagnoses the problem also creates the measurement framework for proving the fix worked.

### During Diagnosis (DA Agent)

```
DA finds: Gross Margin declined
  IS:     Region East, Product Line A, Since Week 12
  IS NOT: Region West, Product Line B, Stable before Week 12

Root cause: Supplier cost spike affecting Region East raw materials
```

The IS NOT column narrows the root cause — Region West is fine, so it's not a company-wide issue; it's specific to Region East's supply chain.

### During Measurement (VA Agent)

The same IS NOT dimensions become the counterfactual control group:

```
6 weeks after solution implementation:
  Region East (treatment):  Gross Margin +3.9pp recovery
  Region West (control):    Gross Margin +1.2pp recovery (organic/market)

  Attributable impact:      3.9 - 1.2 = +2.7pp (solution-driven)
  Market-driven:            1.2pp (from MA: commodity prices fell industry-wide)
```

### Why This Matters

**No MBB firm does this.** McKinsey diagnoses, recommends, collects the fee, and leaves. There's no built-in mechanism to prove the recommendation worked — let alone separate the firm's contribution from market tailwinds.

**No BI platform does this.** Dashboards show before/after KPI movement but have no concept of control groups, dimensional isolation, or causal attribution.

**Agent9 does both** because the KT framework produces structured dimensional output that serves dual purposes — and it's all automated, stored, and queryable.

### Difference-in-Differences: The Statistical Foundation

The VA attribution method is a simplified difference-in-differences (DiD) approach — the same technique economists use for policy evaluation:

```
                        Pre-intervention    Post-intervention    Change
Treatment (IS):         28.3%              32.2%                +3.9pp
Control (IS NOT):       31.5%              32.7%                +1.2pp
                                                                ------
Attributable impact:                                            +2.7pp
```

**Adjustments layered on top:**
- **Market factor** (MA): If the entire industry recovered, subtract the industry-wide portion
- **Seasonal factor** (SA): If the measurement period includes known seasonal patterns, subtract
- **Confidence scoring**: Based on control group quality, data volume, confounder count

---

## 5. The Full Pipeline: Diagnosis → Prescription → Measurement

```
┌──────────────────────────────────────────────────────────────────┐
│                    AGENT9 ANALYTICAL PIPELINE                     │
│                                                                   │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐       │
│  │   SA    │───→│   DA    │───→│   MA    │───→│   SF    │       │
│  │ Detect  │    │ Diagnose│    │ Context │    │Prescribe│       │
│  └─────────┘    └────┬────┘    └────┬────┘    └────┬────┘       │
│                      │              │              │              │
│                      │ IS/IS NOT    │ Market       │ HITL         │
│                      │ Change-point │ signals      │ Approval     │
│                      │              │              │              │
│                      └──────────────┼──────────────┘              │
│                                     │                             │
│                              ┌──────▼──────┐                     │
│                              │     VA      │                     │
│                              │   Measure   │                     │
│                              │  Attribute  │                     │
│                              │   Report    │                     │
│                              └──────┬──────┘                     │
│                                     │                             │
│                                     ▼                             │
│                          ┌──────────────────┐                    │
│                          │ Portfolio View   │                    │
│                          │ Honest ROI       │                    │
│                          │ Strategy Check   │                    │
│                          └──────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

### What Each Stage Contributes to VA

| Stage | What VA Receives | How VA Uses It |
|-------|-----------------|----------------|
| **SA** | KPI breach data, historical baselines, seasonal patterns | Baseline value, seasonal adjustment, ongoing re-monitoring |
| **DA** | IS/IS NOT dimensions, change-point detection, pre-intervention trend | Control group (IS NOT), trend projection, timing anchor |
| **MA** | Market signals at breach time + measurement time | Market factor adjustment — isolate industry-wide recovery |
| **SF** | impact_estimate (recovery_range), time_to_value, key_assumptions | Expected outcome, measurement window, strategy snapshot |
| **HITL** | Approval timestamp, selected option, principal context | Registration trigger, accountability, strategy baseline |

---

## 6. Competitive Positioning

### The "Never-Engaged MBB Partner"

Agent9 delivers what MBB charges $500K+ per quarter to provide — but continuously, automatically, and with measurement:

| Capability | MBB Engagement | Agent9 |
|-----------|----------------|--------|
| Problem detection | Client tells the firm what's wrong | SA detects automatically |
| Root cause analysis | 2-4 weeks, team of 3-5 consultants | DA: minutes, automated KT |
| Market context | Separate research workstream | MA: real-time market signals |
| Solution options | 4-8 weeks, structured workshops | SF: 4 parallel LLM calls, minutes |
| Executive presentation | PowerPoint decks | LLM-generated SCQA narratives |
| Outcome measurement | Rarely done; no built-in methodology | VA: automated, causal, strategy-aware |
| Cost per problem | $200K-$500K | Near-zero marginal cost |
| Throughput | 1-2 problems per engagement | All KPIs, simultaneously, continuously |

### What Agent9 Does NOT Replace

Honesty matters. Agent9 doesn't replace:

- **Board-level strategic planning** — Agent9 measures strategy alignment but doesn't set strategy
- **Human judgment on novel situations** — KT requires historical data; truly unprecedented events need human creativity
- **Relationship-driven insights** — "The VP of Sales is about to quit" is information no data pipeline captures
- **Deep industry expertise** — MBB partners bring 20 years of pattern recognition; Agent9's LLM personas are approximations
- **Organizational change management** — Agent9 recommends; humans implement

Agent9 is the **always-on analytical infrastructure** that makes MBB-quality diagnosis accessible between (or instead of) $500K engagements. When an MBB partner IS engaged, Agent9's data pipeline accelerates their work.

---

## 7. The Honesty Advantage

Most AI platforms overclaim results. Agent9's Value Assurance is explicitly designed for honest accounting:

1. **Attribution breakdown** — never claim 100% credit; always show what portion was market, seasonal, organic
2. **Confidence scoring** — every evaluation declares its confidence level and explains why
3. **Strategy alignment** — don't count wins on goals the business has abandoned
4. **Control group quality** — when the IS NOT data is thin, confidence drops and the narrative says so
5. **Methodology transparency** — every evaluation states the method used (DiD, trend projection, simple before/after)

**Paradoxically, this honesty builds more executive trust than overclaiming.** A CFO who sees "Solution delivered +2.2pp of the 3.9pp total recovery; 1.2pp was market-driven; confidence: MODERATE" trusts the system more than one that claims "+3.9pp — our AI saved the day."

This positions Agent9 as the **credible analytical partner** — not a black box that inflates its own importance.

---

## 8. Analytical Intelligence Layers: The Next Evolution

The KT + MBB + VA architecture established in Sections 2–7 is structurally correct but analytically shallow in two ways that matter for enterprise adoption:

1. **KT IS/IS NOT analysis reports what the numbers say — it doesn't say how much to trust them.** A CDO or FP&A team will immediately ask: is National Auto Parts Chain A's +90bps a statistically robust finding, or is it one large transaction distorting the group mean? Is Service Centers Division's outperformance a structural 12-month trend, or a seasonal artefact? The current architecture has no answer.

2. **Each KPI is analysed in isolation.** Real enterprise KPIs are coupled — Revenue Growth and Gross Margin % are in structural tension; Customer Satisfaction and Cost of Service move together. When SA flags both simultaneously and SF recommends independent solutions, those solutions may partially cancel each other. The current architecture has no mechanism to detect this.

The three Analytical Intelligence Layers address these gaps progressively.

---

### Layer 1 — Statistical Rigor (DA Agent, Phase 11H)

**What it adds to KT:** Statistical evidence behind every IS/IS NOT finding. KT's falsifiability principle — "explain why Region East is affected but Region West isn't" — is only meaningful if the IS vs IS NOT distinction is itself statistically significant.

| Capability | What it produces |
|-----------|-----------------|
| **Effect size scoring** | Each segment delta expressed as % of total KPI variance — surfaces which segments actually drive the headline number, not just which have the largest absolute delta |
| **Seasonal decomposition** | Separates trend + seasonal + residual for segments with ≥12 periods of history. A delta that is structural (trend component) has high replication confidence; one that is seasonal has low confidence |
| **Confidence-scored IS/IS NOT** | Replaces heuristic `replication_potential` (0–1) with evidence-based score: `effect_size × trend_stability × data_completeness` |
| **Outlier flagging** | Segments with delta >2σ from peer distribution are flagged — "statistical outlier; interpret with caution" |

**ICP resonance:** CDO and Head of Analytics are the gatekeepers who will challenge any recommendation built on weak statistical ground. Layer 1 converts them from blockers to champions — Decision Studio is now analytically rigorous by their standard.

---

### Layer 2 — Causal KPI Mapping (DGA + DA, Phase 2 — 2027)

**What it adds beyond KT:** Cross-KPI reasoning. Enterprises are complex systems where KPIs interact. The same IS NOT segment that is a healthy control group for Gross Margin % may be an IS segment for a Revenue Growth analysis running simultaneously. Layer 2 maps these relationships.

| Capability | What it produces |
|-----------|-----------------|
| **KPI interdependency registry** | Governed in DGA — which KPIs are causally linked, in which direction, with what estimated lag. Populated from business process hierarchy and empirical correlation analysis |
| **Cross-KPI conflict detection** | Before the CFO approves solutions on two simultaneously flagged KPIs, the system flags: "These two solutions are causally coupled and will partially offset each other — expected net impact is X, not X + Y" |
| **Strategic alignment scoring** | Maps the portfolio of pending solutions against the client's declared corporate priorities (growth / margin / efficiency weighting). A solution that improves Gross Margin % but degrades Revenue Growth scores low when the declared strategy is "profitable growth" |

**ICP resonance:** CFO and CSO are the primary buyers. The CFO lives in the world of competing KPI trade-offs daily — surfacing these conflicts before approval is a direct pain point solution. The CSO's entire job is managing strategic trade-offs; the interdependency map is their domain.

The most immediately valuable output of Layer 2 is not the full optimization result — it is **conflict detection before approval**. The CFO can see "you are about to approve actions on two causally coupled KPIs that will partially cancel each other out" before committing. No current tool does this.

---

### Layer 3 — Portfolio Optimization (Business Optimization Agent, Phase 3 — 2028)

**What it adds beyond Layer 2:** Full constrained optimization across the enterprise KPI portfolio. Corporate strategy is an optimization problem — given the causal structure of the KPI system and the declared strategic priorities, what is the optimal allocation of management attention and capital across all active situations?

| Capability | What it produces |
|-----------|-----------------|
| **Portfolio-level KPI forecasting** | Projected aggregate KPI movement under proposed solution sequence, with uncertainty bands |
| **Execution sequencing DAG** | Optimal order to execute approved solutions, respecting causal dependencies and interaction effects |
| **Cross-intervention conflict detection** | Extends Layer 2's pre-approval detection to the full active solution portfolio |
| **Dimensional targeting** | Solutions targeted at the specific segment coordinates where variance lives — not at the KPI headline |

**The key insight behind Layer 3:** The unit of decision is not the KPI — it is the segment. "Revenue is down 3%" is not actionable. "National Auto Parts Chain A is up 90bps while Manual Gear Oil is down 1.13bps" are two actionable coordinates in the same KPI. Portfolio optimization operates at the segment level and aggregates back to KPI recovery.

**ICP resonance:** CEO and PE-backed CFOs. Their investment thesis is a bet on specific KPI movements within a defined timeframe. Portfolio optimization directly maps to the value creation plan their sponsors are tracking. Enterprise PMO and transformation offices managing 20–40 concurrent initiatives are the user-level stakeholder.

---

### Mixed Analysis Mode: The Natural Completion of KT

A direct consequence of the three-layer model is that the binary problem/opportunity framing is insufficient for real enterprise KPIs.

**KT's IS/IS NOT structure already contains both problem and opportunity information simultaneously.** In a mixed-signal KPI, some segments are lagging (IS — problem coordinates) and some are outperforming (IS NOT — opportunity / replication proof). The current architecture forces a choice between analysing the laggards or the leaders. The correct analysis presents both.

**Mixed mode framing (Phase 11G):**

> "Despite Gross Margin % being 2% below target, Service Centers (+20bps) and National Auto Parts Chain A (+90bps) are outperforming — indicating a deployment gap rather than a market constraint. The question is how to systematically transfer proven mechanics from leading segments to lagging segments."

This is the most executive-natural frame. It is also the most actionable: the leading segments are not a distraction from the problem — they are the answer to it. Decision Studio is the only platform that presents both dimensions in a single coherent narrative because it is the only platform where the analytical framework (KT IS/IS NOT) naturally produces both simultaneously.

---

## 9. Implications for the Video / Customer Outreach

### The Story Arc

1. **"Your margin is dropping and you don't know why"** (SA — detect)
2. **"Here's exactly where, when, and what changed"** (DA — KT Is/Is Not)
3. **"Here's what the market is doing about it"** (MA — external context)
4. **"Here are three options from McKinsey, BCG, and Bain perspectives"** (SF — MBB personas)
5. **"Here's what happens if you do nothing"** (VA — cost of inaction)
6. **You decide** (HITL — executive picks an option)
7. **"Your fix is working — and here's proof"** (VA — causal attribution)
8. **"Here's what Agent9 has delivered this quarter"** (VA — portfolio ROI)

### Key Differentiating Claims

- "Agent9 doesn't just find problems — it proves solutions work"
- "Honest ROI: we separate our contribution from market tailwinds"
- "The same analysis that finds the root cause creates the measurement framework"
- "MBB-quality insight at near-zero marginal cost, continuously, not quarterly"
- "Strategy-aware: as your priorities shift, our measurement adapts"

### What NOT to Claim

- Don't claim Agent9 replaces MBB — claim it delivers MBB-quality analysis between engagements
- Don't claim perfect causal attribution — claim honest, transparent, confidence-scored attribution
- Don't claim AI autonomy — emphasize human-in-the-loop and principal control
- Don't claim universality — KT requires structured dimensional data; not all problems fit
