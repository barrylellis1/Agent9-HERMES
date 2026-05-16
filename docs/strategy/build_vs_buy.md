# Decision Studio — Build vs. Buy Analysis

**Audience:** CFO, CTO, VP Engineering, procurement committees
**Last Updated:** May 2026 | Version 1.1
**Status:** Phase 10A-10D capabilities now shipped; pricing model finalized (Business Plan v1.6)

---

## The Honest Starting Point

A skilled engineer can build a proof of concept in a week. They connect to your data warehouse, send a KPI value and some dimensional breakdown to an LLM, and get a structured recommendation back. It looks impressive in a demo. The CFO approves a budget to build it properly.

This document is about what "building it properly" actually costs — and what you give up while you're building.

---

## What the Proof of Concept Misses

The POC demonstrates that an LLM can generate recommendations from business data. That part is not the hard problem. The hard problems are:

**Knowing when to ask.** Which KPIs should trigger analysis today? Is a 3.2% decline in Gross Margin significant for this business, at this time of year, compared to this reference period? Is the same movement a problem for the CFO but within expected range for the COO given their scope? Getting this wrong means either alert fatigue (fires on everything) or missed signals (fires on nothing). Reliable KPI monitoring takes 2–3 months of calibration to get right for a single client.

**Isolating the real driver.** Sending "Gross Margin is down 3.2%, what's wrong?" to an LLM produces generic output. Decision Studio implements a formal control group methodology — IS segments (what deteriorated) vs. IS NOT segments (what held flat) — that disproves alternative explanations before the LLM frames the problem. This is how MBB consultants structure root cause analysis. Without it, the recommendation addresses symptoms, not causes.

**Producing actionable recommendations rather than generic advice.** A single LLM prompt asking for recommendations reliably produces output like "improve operational efficiency" and "review supplier contracts." Decision Studio runs three simultaneous analytical perspectives — CFO (financial impact and optionality), COO (operational feasibility and sequencing), Strategy (market positioning and risk) — with a synthesis call that resolves tensions between them. The difference in output quality is significant and took months of prompt iteration to achieve.

**Proving it worked.** The internal build has no mechanism to answer "did the action we took actually improve the KPI?" Decision Studio uses difference-in-differences attribution — measuring the counterfactual of what would have happened without the intervention — to separate the decision's effect from market movements and seasonal factors. Without this, the CFO cannot distinguish "our decision worked" from "the market recovered."

**Staying contextually intelligent as the business changes.** Decision Studio maintains a governed registry layer: KPI definitions, principal ownership, data product contracts, business glossary, accountability model. When an org structure changes, a registry entry updates. An internal build hardcodes all of this. It breaks every time a KPI is renamed, a division is restructured, or a new principal joins the leadership team.

---

## Realistic Build Timeline

The table below compares what a "build it internally" project actually delivers at each milestone against what Decision Studio ships at onboarding.

| Capability | Week 1 POC | Month 3 | Month 6 | Month 12–18 | Decision Studio Day 1 |
|---|---|---|---|---|---|
| LLM recommendation from KPI data | Yes | Yes | Yes | Yes | Yes |
| Calibrated KPI monitoring (signal vs. noise) | No | Partial | Partial | Yes | Yes |
| IS/IS NOT dimensional root cause | No | No | Partial | Yes | Yes |
| Multi-persona debate + synthesis | No | No | No | Yes | Yes |
| HITL approval workflow + audit trail | No | No | Partial | Yes | Yes |
| Value Assurance + outcome attribution | No | No | No | No | Yes |
| Registry-based governance layer | No | No | No | Partial | Yes |
| Multi-tenant isolation | No | No | No | Partial | Yes |
| Usage metering + quota management | No | No | No | No | Yes |
| **Production-ready, calibrated system** | **No** | **No** | **No** | **Approaching** | **Yes** |

---

## True Cost of Internal Build

### Direct Cost

| Resource | Assumption | 12-month cost |
|---|---|---|
| Senior engineer (lead) | 1.0 FTE at $200K fully loaded | $200K |
| Mid-level engineer (support) | 0.5 FTE at $150K fully loaded | $75K |
| Data engineer (integration) | 0.5 FTE at $160K fully loaded | $80K |
| LLM API costs (development + production) | $2K–$5K/month | $24K–$60K |
| Cloud infrastructure | $1K–$3K/month | $12K–$36K |
| **Total direct cost — Year 1** | | **$391K–$451K** |

This buys you an approaching-production system at month 12–18. It does not include ongoing maintenance, prompt engineering iteration, calibration, or the cost of the engineers' opportunity cost — what else they could have shipped.

### Opportunity Cost

Every sprint the engineering team spends on analytical infrastructure is a sprint not spent on your core product. For most organisations, building decision intelligence tooling is not a strategic differentiator. It is infrastructure. The question is whether you want to own and maintain that infrastructure indefinitely, or whether you want to use it.

### Calibration Cost

The internal build starts at zero calibration on day one. No history of which KPI thresholds generate real decisions vs. noise. No record of which recommendation categories have worked in your business context. No baseline for attributing outcomes.

Decision Studio accumulates calibration across every assessment cycle. After 12 months, a client that switches to an internal build loses all of that history and restarts the calibration clock.

---

## What You Get on Day 5 with Decision Studio

The 5-Day Fast Start delivers a production-ready system against your existing governed KPI views:

- Day 1–2: Data product connection and contract validation
- Day 3: KPI registry, principal mapping, monitoring profile setup
- Day 4: First enterprise assessment run — live situation cards for your principals
- Day 5: Deep Analysis and Solution Finding on your real KPI data, with HITL approval workflow active

No internal engineering required beyond making your governed KPI views accessible. No infrastructure to maintain. No prompt engineering to iterate. The analytical methodology is already calibrated.

---

## The Compounding Moat

Decision Studio improves with every cycle:

- Monitoring profiles calibrate to your specific KPI volatility patterns
- Breach rate history separates structural anomalies from seasonal noise
- Value Assurance outcomes tell the system which recommendation categories work in your business context
- Per-principal accountability registry reflects your org structure accurately over time

An internal build does not compound. It stabilises at whatever the engineering team shipped and degrades as the business changes. Decision Studio's value increases as it learns your business.

---

## When Internal Build Makes Sense

To be direct: internal build is the right answer if:

1. **You have a large, dedicated AI engineering team** (5+ engineers) with capacity to own analytical infrastructure as a long-term product — not a project
2. **Your KPI structure changes frequently** in ways that would require ongoing custom development regardless of vendor
3. **Your regulatory environment** prohibits all third-party data processing, including Azure-hosted services (in which case on-premise LLM is the only option, and the quality trade-off is significant)
4. **You intend to resell the capability** to your own customers — in which case licensing or white-labelling Decision Studio may be more efficient than building

For most mid-market organisations, none of these apply. The engineering team has a product to build. Analytical infrastructure is not that product.

---

## The Question to Ask Internally

*"Is building and maintaining decision intelligence infrastructure a better use of our senior engineers' time than [your core product roadmap]? And can we afford 12–18 months of delay before that infrastructure is production-ready?"*

If the answer is no — Decision Studio is ready on day 5.

---

## Appendix: What the Proof of Concept Won't Tell You

The week-one POC is convincing because it demonstrates the easiest 5% of the problem. The engineer shows:
- LLM receives KPI data and returns a structured recommendation ✓
- Output looks analytical and coherent ✓
- Cost per call is low ✓

The POC does not demonstrate:
- Whether the monitoring system can distinguish signal from noise at scale
- Whether the root cause analysis correctly isolates the driver vs. a correlated variable
- Whether the recommendations are specific to your business or generic to any business
- Whether the system produces auditable, attributable outcomes that a CFO can present to a board
- Whether the system still works correctly after an org restructure, a KPI rename, or a new data product is added

Those are the questions that take 12–18 months to answer with an internal build. Decision Studio has already answered them.
