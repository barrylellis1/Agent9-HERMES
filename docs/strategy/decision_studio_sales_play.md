# Decision Studio — Sales Play

**Last Updated:** 2026-05-31
**Status:** Field-ready
**Owner:** Founder (until first sales hire)

> A field-ready playbook for selling Decision Studio. Contains the value proposition, the moats, the 10 core + 3 advanced objections with responses, the things we explicitly do NOT promise, and quick-reference talking points. Every claim in this document is verifiable in the codebase — cite agent cards in `src/agents/new/cards/` if a prospect asks for proof.

**Related collateral:**
- [agent9_executive_summary.md](agent9_executive_summary.md) — short executive brief
- [business_premise_challenge.md](business_premise_challenge.md) — internal premise reassessment
- [customer_roi_calculator.md](customer_roi_calculator.md) — quantified ROI model
- [enterprise_security_faq.md](enterprise_security_faq.md) — answers to security/compliance questions
- [competitive_watch.md](competitive_watch.md) — competitor positioning

---

## 1. The One-Line Value Proposition

**Decision Studio is the only system that closes the complete loop from KPI breach to verified outcome — automatically detecting problems, structuring the diagnosis, generating ranked solutions with market context, capturing approval, and then *proving whether the fix worked* using counterfactual attribution.**

Everything else on the market does one or two of these steps. Decision Studio does all five. The integration is the product.

---

## 2. Who We Sell To (ICP)

**Mid-market companies, $50M–$500M revenue, who have *never* had Big-3 consulting on retainer.**

- Sweet spot: regional/specialty industrials, finance ops at PE-owned portfolio companies, ops/finance leadership at family-owned businesses moving from spreadsheets to enterprise systems.
- Decision-maker: CFO or COO. Champion: Finance Manager, FP&A lead, or Director of Ops who has been asked to "modernize" reporting.
- Disqualifier: McKinsey/BCG/Bain on a multi-year retainer (we are not displacing them in this account — yet).

---

## 3. What the Customer Actually Gets (Six Concrete Outcomes)

1. **Continuous KPI monitoring across any backend** — BigQuery, Snowflake, SQL Server, DuckDB, Databricks. Routing by data-product registry, not by SQL syntax detection.
2. **Structured root-cause diagnosis** — Kepner-Tregoe IS/IS NOT with SCQA framing, dimensional change-points, bridge analysis for ratio KPIs, mixed-mode self-determination (problem / opportunity / both).
3. **Three independent strategic perspectives + synthesis** — Parallel persona analyses (McKinsey/BCG/Bain-style framing tuned to principal's decision style) → synthesized recommendation → trade-off matrix → single HITL approval event with full audit trail.
4. **Real-time market context with semantic conflict detection** — Perplexity web search + Claude synthesis. When external market signals contradict the internal recommendation, the system flags it before approval.
5. **Proof of outcome via causal attribution** — Difference-in-Differences using Deep Analysis's IS NOT segments as natural control groups. Isolates the solution's causal contribution from market recovery, seasonality, and organic trend. 9-cell composite verdict matrix: "Full success", "Misdirected win", "Strategic waste", etc.
6. **KPI ownership before the first scan runs** — Conversational AI interview walks an admin through assigning every KPI to an owner across the leadership team.

---

## 4. The Pipeline (This Is the Moat)

```
KPI Accountability Interview
   ↓ (owners assigned)
Situation Awareness          ← multi-backend, per-KPI monitoring profiles, opportunity detection
   ↓ (situation cards)
Deep Analysis                ← KT IS/IS NOT, SCQA, mixed-mode self-determination
   ↓ (root cause + benchmarks)
Market Analysis              ← signals + semantic conflict detection
   ↓ (external context attached)
Solution Finder              ← 3-persona parallel debate → synthesis → HITL gate
   ↓ (approved solution)
Value Assurance              ← DiD attribution + strategy drift + composite verdict
   ↓ (proof of impact)
Principal Intelligence Briefing  ← email + 1-click delegation tokens
```

Every stage hands a typed payload to the next. Every stage is client-isolated. Every LLM call routes through one gateway. Every state change is auditable.

---

## 5. The Six Moats (Each Verifiable in Code)

### 5.1 The Integrated Loop (Detection → Proof)
No competitor integrates **causal outcome attribution** back to the original situation card. "AI insights" tools claim impact; they don't measure it. The IS NOT segments from DA become the control groups for VA. That handoff only works because we own the full pipeline.

### 5.2 Strategy Drift Detection
At approval time, a `StrategySnapshot` captures principal priorities, KPI thresholds, business process, and assumptions. At evaluation time, the agent diffs the snapshot against the live registry and produces verdicts: `ALIGNED`, `DRIFTED`, `SUPERSEDED`. No one else compares the world-at-approval to the world-at-measurement.

### 5.3 Mixed-Mode Self-Determination + HITL Resolution
DA inspects its own output and decides: problem-dominated, opportunity-dominated, or genuinely mixed. When mixed, the UI forces a HITL resolution before Solution Finder runs. Most "agentic" systems propagate a fixed framing top-to-bottom. This one knows what it's looking at.

### 5.4 Semantic Market Conflict Detection
Market Analysis passes signals AND the DA conclusion to an LLM call that semantically decides whether external reality contradicts internal recommendation. Conflict is then piped into Solution Finder's persona prompts so each persona's hypothesis must account for the contradiction. Competitors paste market headlines into a sidebar. This one weaponizes them.

### 5.5 Principal-Adaptive Throughout
Every surface adapts to the principal's `decision_style`:
- **Deep Analysis** changes KT framing language (MECE / strategic / pragmatic).
- **Solution Finder** changes which consulting personas debate.
- **Situation Awareness** reorders KPI tiles by `kpi_line_preference` / `kpi_altitude_preference`.
- **PIB** customizes briefing format per principal.

Guardrail: agents adapt presentation FOR the principal, never speak FOR them. No fabricated quotes.

### 5.6 Multi-Tenant Isolation Baked Into the Schema
`client_id` is first-class on every row. Composite primary key is `(client_id, id)`. KPI IDs are semantic (`net_revenue`), not tenant-encoded. Every endpoint accepts and enforces `client_id`. Cross-tenant leakage is structurally impossible — not policy-enforced.

### Supporting Moats

**Cost-Efficient Model Routing.** All LLM calls flow through one gateway. Haiku for fast tasks (Stage 1 personas, narratives, observations), Sonnet for synthesis and conflict. Centralized routing means policy tunes in one place. ~$1–$2 per full pipeline run.

**Configuration-as-Lock-In.** The wired registry (KPIs → data products → business processes → principal accountability → monitoring profiles) becomes the customer's institutional memory. Switching means re-onboarding every KPI, re-mapping every owner, re-defining every threshold.

---

## 6. What We Replace

| Today's "solution" | What it misses |
|---|---|
| BI dashboard (Tableau, Power BI, Looker) | No diagnosis, no recommendation, no outcome tracking, no ownership enforcement |
| Consulting engagement (MBB / Big 4) | $500K–$5M, 8–12 weeks, single-shot, no replay, knowledge leaves with the firm |
| Anomaly-detection AI tool | Detects the breach, then hands off to humans — no diagnosis, no proof |
| AI finance copilot (Concourse, Aleph, etc.) | Domain-locked, no causal attribution, no strategy drift |
| Spreadsheet + email | Every step manual, every handoff lossy, zero institutional memory |

---

## 7. Objections + Responses

### Core Objections (7.1–7.10) — Asked by Most Buyers


### 7.1 "We already have a BI stack. We don't need another tool."

**Real fear:** Adding another vendor on top of Tableau/Power BI/Looker that the team won't adopt.

**Response:** BI tools answer "what is happening." Decision Studio answers four questions BI cannot: **why** it's happening (Deep Analysis), **what to do** (Solution Finder), **whether anyone owns it** (Accountability Interview), and **whether the fix actually worked** (Value Assurance). Your BI stack stays where it is — we read from the same warehouse it does. We don't replace dashboards; we replace the human work that happens after someone reads the dashboard.

**Pivot:** "Walk me through your last KPI miss. Who decided what to do, how long did it take, and how do you know the action actually moved the number?"

---

### 7.2 "We can't trust AI to recommend business decisions."

**Real fear:** "I'll lose my job if I act on an LLM hallucination."

**Response:** Decision Studio is explicitly HITL — human-in-the-loop. The principal sees three independent persona analyses (not one black-box answer), the trade-off matrix, the synthesis, the market signals, and the conflict assessment. They approve. They reject. They modify. The AI does the *analysis*; humans make the *decision*. There is exactly one approval event per cycle, and every approval is auditable.

**Pivot:** "We don't ask your CFO to trust the AI. We ask them to trust three structured perspectives — the same way they'd trust three pages of a McKinsey deck — and then decide."

---

### 7.3 "Our data isn't ready / our KPIs aren't well-defined."

**Real fear:** "This will turn into a 6-month data engineering project before we see value."

**Response:** We don't need clean data; we need *defined* KPIs. The KPI Assistant generates KPI definitions from your schema in minutes. The Accountability Interview assigns ownership before the first scan. The Data Product Agent profiles any backend (BigQuery, Snowflake, SQL Server, DuckDB, Databricks) and produces a contract YAML automatically. If you have a warehouse, you're ready.

**Pivot:** "What's your warehouse? Let's pick three KPIs that matter to your CFO and have the first situation card running this week."

---

### 7.4 "You have no customers. Too risky to be your first."

**Real fear:** "I'll be on the hook if this vendor goes away."

**Response:** Three honest answers. (a) The product is built and deployed — not vaporware. You can use it today. (b) The founder has 30+ years across Fortune 500 finance and consulting; this isn't a 22-year-old's first project. (c) The pilot is structured to de-risk you: $15K–$25K, three months, defined success criteria, no multi-year contract. If it doesn't work, you walk. If it does, you have a first-mover case study and likely a price lock-in.

**Pivot:** "Would you rather be customer #1 with a founder who picks up the phone, or customer #500 of an enterprise vendor who routes you through five layers of support?"

---

### 7.5 "$15K–$25K for a pilot then six figures a year — show me the ROI."

**Real fear:** "I can't get this past procurement without a hard number."

**Response:** The Value Assurance agent is literally built to produce that hard number. After approval, the system measures DiD impact against IS NOT control segments, attributes the dollar value to your action (separating it from market recovery and seasonality), and produces a verdict your CFO can defend. By the end of the pilot, *we generate the ROI document* — you don't have to build it. Most BI tools cost more annually than our pilot and produce zero verified-outcome data.

**Pivot:** "Pick one $1M+ decision you made in the last 12 months. How would you prove today that it worked? That's the report VA generates by default."

---

### 7.6 "How is this different from hiring McKinsey, Bain, or BCG?"

**Real fear:** Either "we already have a consulting firm" or "we trust consultants more than software."

**Response:** Big consulting firms cost $500K–$5M per engagement, take 8–12 weeks, deliver one-shot deliverables, and leave when they're done. Decision Studio runs the *same structured analysis methods* — KT IS/IS NOT, MECE decomposition, SCQA framing, multi-perspective debate — continuously, on every KPI, for ~$100K/year. The analytic rigor is comparable; the cycle time is 10× faster and the cost is 10× lower. And critically: we capture institutional memory. When Bain leaves, the knowledge leaves. With us, every situation, diagnosis, approval, and outcome is permanently recorded and searchable.

**Pivot:** "Our target customer is companies who have *never* hired Big-3 consulting because the deal size doesn't justify it. Are you one of them, or do you have a firm on retainer already?"

---

### 7.7 "What if the LLM hallucinates and we act on bad recommendations?"

**Real fear:** Liability — "I'll be the one explaining to the board why we did the wrong thing."

**Response:** Three structural defenses. (a) The LLM never sees raw recommendations alone — it sees the **structural** facts: dimension breakdowns, segment values, change-point deltas, benchmark data computed deterministically by SQL. The LLM frames; SQL produces the numbers. (b) Solution Finder produces **three independent persona analyses** before synthesis. If they disagree materially, the synthesis must call out the unresolved tension explicitly. (c) Market Analysis produces a semantic **conflict assessment** — if external signals contradict the recommendation, the system flags it before approval. You can't hallucinate past three personas, a market reality check, and a HITL gate.

**Pivot:** "Show me the last consulting deck you got. Was every number traceable to a source? Ours are — every recommendation cites the dimension, the delta, and the segment it came from."

---

### 7.8 "Our CFO/COO won't actually adopt this."

**Real fear:** "I'll champion this, fail to drive adoption, and own the failure."

**Response:** Three answers on how we attack adoption: (a) **Principal-adaptive output** — the system reads each principal's decision style and adapts presentation. Analytical CFOs get MECE; pragmatic COOs get quick wins; visionary CEOs get strategic implications. (b) **Email briefings with 1-click delegation** — the principal does not have to log into the app. The briefing arrives in their inbox with deep-link tokens. (c) **Honest scope** — we're not selling "AI replaces your finance team." We're selling "your finance team writes 50% less PowerPoint."

**Pivot:** "Who's the principal in your org who *would* use this if it actually saved them time? Let's pilot with that one person first."

---

### 7.9 "How do we handle security, data privacy, and compliance?"

**Real fear:** Either security review will kill the deal, or KPI data will leak to an LLM provider.

**Response:** **What's solid today:** all LLM calls route through one gateway with full audit logging, secret redaction, and token-cost tracking. Credentials sit in vault folders, never in git. Client isolation is enforced at the database level — composite primary keys make cross-tenant leakage structurally impossible. Multi-backend SQL routing keeps your data in your warehouse — we send queries, not data dumps. **What's pilot-honest:** SOC 2 Type II is a 2027 commitment, not a 2026 reality. For the pilot, we can run in your VPC if required; the certification path is mapped.

**Pivot:** "We're enterprise-architecture-ready, not enterprise-certificate-ready. If certifications block, let's structure the pilot under your existing vendor-risk tolerance for early-stage tools."

See [enterprise_security_faq.md](enterprise_security_faq.md) for the long-form security answers.

---

### 7.10 "GenAI is changing every week. Why commit to a vendor now?"

**Real fear:** "I'll lock in to a tool that's obsolete in 18 months."

**Response:** This is the strongest objection — and the answer reveals the moat. The model layer (Claude vs GPT vs the next thing) **is** commoditizing — and we're built for that. Every LLM call routes through the LLM Service Agent. Swapping providers is a config change. **What is not commoditizing** is the integrated pipeline: SA→DA→MA→SF→VA with DiD attribution, strategy drift, mixed-mode resolution, and the KPI ownership graph. Anyone can chain LLM calls. Nobody else closes the detection-to-proof loop with counterfactual attribution. If a competitor wants to copy us, they need 18 months and a re-architecture. If you wait 18 months to buy, you've left $500K–$2M of unverified decisions on the table.

**Pivot:** "The model layer is becoming a commodity. The orchestration layer is becoming the moat. We're betting on the orchestration layer. What are you betting on?"

---

### Advanced Buyer Objections (7.11–7.13) — Asked by Sophisticated Buyers

These come from CTOs, technical CFOs, or operationally experienced buyers who have seen recommendation engines fail before. Handle them with depth, not deflection.

---

### 7.11 "I'll just build it myself with Claude / Claude Code / a custom LLM workflow."

**Real fear:** "If I'm tech-savvy enough to evaluate you, I'm tech-savvy enough to build it myself for less."

**Response:** For a one-shot analysis on a single KPI, you can — and you should. We do not pretend otherwise. Where DIY breaks down is operationalization. Seven things in our pipeline are not prompts:

1. **DiD attribution** requires state captured at decision time and replayed at evaluation time — Claude has no memory between sessions.
2. **The strategy snapshot** is a data model that diffs registry-then vs registry-now to detect drift.
3. **Multi-backend SQL routing** needs a dialect layer that survives BigQuery / Snowflake / SQL Server / DuckDB / Databricks syntax differences.
4. **The integrated state graph** (situations → KPIs → data products → processes → principals → solutions → evaluations) is what makes history searchable across quarters.
5. **Mixed-mode self-determination** tags items at collection time *before* the LLM frames them.
6. **Operational concerns** — cron, retry, email delivery, token TTLs, audit logs, per-request registry refresh — eat 80% of the build.
7. **Methodology choices** (DiD, bridge analysis, inverse-logic sign-flips, semantic conflict detection) were discovered over 10 months of iteration. DIY builders discover them the same way — by getting them wrong first.

Realistic cost of DIY: $200K–$400K of engineer time, 6–12 months, $50K–$100K/year ongoing. Realistic cost of our pilot: $15K–$25K, 5 days, vendor owns the maintenance burden — and the methodology liability.

**Pivot:** "Walk me through your build plan. Who maintains it when the warehouse schema changes? What happens when the engineer who built it leaves? How does the board verify the methodology is sound?"

---

### 7.12 "I'll just upload my report or dashboard to Claude — same input, right?"

**Real fear:** "My BI tool already shows me what's wrong. Why go back to raw data?"

**Response:** Reports and dashboards are **deliverables, not data** — they are pre-aggregated outputs of choices an analyst already made about which dimensions to show, what to filter, and how to roll up. The IS/IS NOT method requires the high-dimensional reality the dashboard hides. Five specific failures:

1. **Dashboards pre-aggregate.** IS/IS NOT needs raw segment-level granularity across N dimensions — products × customers × channels × reps × fiscal months — not just the rollup the dashboard chose to show.
2. **IS NOT requires knowing what did NOT move.** The dashboard shows the slice; you need the full dimensional space to identify the natural control groups VA will use 90 days later.
3. **Bridge analysis for ratio KPIs** needs numerator-per-segment AND denominator-per-segment separately — never on a report. A "Gross Margin dropped 2.1pp" line cannot distinguish revenue collapse from cost surge from mix shift. Each implies a different fix.
4. **Time-comparison structure** requires the same dimensional rollup for current and prior periods — rarely preserved in dashboards beyond a top-line "vs last year" arrow.
5. **Hallucination amplifies on summaries.** Claude infers what underlying data must have looked like, then pattern-matches plausible recommendations from training data on similar reports. You get smooth narrative; you don't get evidence.

The reframe to use with the prospect: **"A dashboard is testimony. The source data is evidence. We can prove things with evidence; we can only argue from testimony."**

**Pivot:** "Let's run an experiment. Send me your last quarterly financial summary as a PDF. I'll feed it to Claude. Then we'll point Decision Studio at the underlying warehouse and run the same KPI through dimensional analysis. Compare the outputs side by side. If the dashboard-fed analysis is as actionable as the structured analysis, we're not the right tool for you."

This is a winnable demo. We have run it. The dashboard-fed output is smooth and shallow. The dimensional output is specific and often surprising. The CFO sees the difference instantly.

---

### 7.13 "Even if you produce great recommendations, my org won't execute them."

**Real fear:** "I'll buy this, get sound recommendations, fail to drive execution, and the whole investment looks worthless to the board."

**Response:** This is the most honest objection in the cycle and the biggest churn risk in our category. Every recommendation engine in history hits this wall — consulting decks, BI insights, auditor findings. We cannot manufacture political will, capital allocation discipline, or middle-management buy-in. But we have built six structural features that meaningfully shift the dynamic:

1. **HITL approval is a recorded commitment, not a suggestion** — captured, dated, attributed, audit-logged. Harder to quietly abandon a decision you personally made on the record than a recommendation someone else made to you.
2. **Strategy drift detection prevents silent abandonment** — at evaluation time, verdict = KPI verdict × strategy alignment. Forgotten recommendations whose underlying priorities shifted produce "SUPERSEDED" verdicts — an explicit deprioritization, not silent decay.
3. **The 5-phase lifecycle makes stalls visible** — APPROVED → IMPLEMENTING → LIVE → MEASURING → COMPLETE. Items sitting in APPROVED for >60 days surface on the portfolio dashboard as managerial artifacts, not invisible failures.
4. **Cost of Inaction quantifies doing nothing** — "Not executing this is costing $180K/quarter at current trajectory." Converts an abstract "we should do this" into a quantified pressure that competes more effectively for executive attention.
5. **Right-sized recommendations** — many actions are operational, not strategic. "Shift product mix at distributor X" does not compete with "should we enter Asia?" The 5–7 day analysis cadence pulls execution out of the annual planning cycle.
6. **The accountability graph names the owner** — every KPI has an assigned owner before the first scan. No "well, nobody is really responsible for that."

**The reframe to use:**

> *"Decision Studio does not execute. It makes execution legible."*

That visibility is what forces the leadership conversation. Without it: 50 unverified recommendations in PowerPoint slides, no owner, no deadline, no cost-of-delay attached. With it: 50 explicit decisions with named owners, expected impact, CoI, lifecycle phase, and a 90-day verdict. Execution still has to come from leadership — but now leadership has the artifact to manage against.

**Honest expectation setting (say this at the contract stage):**

> "If your org currently executes 30% of consulting recommendations, expect 30–50% on ours. Visibility gives you a 1.3–1.7× lift, not 3×. Anyone who promises more is lying."

This sets expectations low enough that we usually exceed them. Customers who hit 50% adoption become reference accounts; customers who hit 30% renew because they trust us not to overpromise.

**Pivot:** "Tell me about the last 5 recommendations your CFO got from consultants. How many were implemented? What killed the rest? When a recommendation isn't executed today, how long does it take you to know?"

- If they say "implementation always works in our org" — they're misremembering or unusual. Close the deal.
- If they say "implementation is the wall" — common ground. Pivot: "Then our value is not the recommendation. It's the *visibility into which recommendations are landing and which aren't.* Let's structure the pilot around that outcome."

---

## 8. Quick-Reference Card

Print this. Keep it in your laptop bag.

| Objection | One-line response |
|---|---|
| Already have BI | "BI tells you what happened. We tell you why, what to do, and whether it worked." |
| Don't trust AI | "The AI analyzes. Humans decide. Every approval is auditable." |
| Data not ready | "We don't need clean data. We need defined KPIs — we generate those in minutes." |
| No customers yet | "Be customer #1 with a founder who picks up. Or customer #500 of a vendor who doesn't." |
| ROI unclear | "VA proves causal impact with DiD. We generate the ROI document by default." |
| Why not consultants | "Same methods, 10× faster, 10× cheaper, permanent institutional memory." |
| LLM hallucination | "Three personas. Market conflict check. HITL gate. SQL produces the numbers — LLM only frames." |
| Adoption | "Principal-adaptive output. Email-based interaction. Pick one champion, prove value in 90 days." |
| Security | "Client isolation at DB level. Query-only, no data dumps. VPC-deployable for pilots." |
| GenAI moving fast | "Models commoditize. Orchestration doesn't. We're the orchestration layer." |
| DIY with Claude | "One-shot questions: yes. Continuous operation with proof of outcome: $200K–$400K and 6–12 months to replicate. Pilot is $15K–$25K, 5 days." |
| Upload dashboard to Claude | "Dashboards are testimony. Source data is evidence. Want a side-by-side demo against your own warehouse?" |
| Won't execute | "We don't make orgs execute — we make execution legible. Visibility lifts adoption 1.3–1.7×, not 3×. Anyone promising more is lying." |

---

## 9. The Two Objections We Cannot Yet Defeat (Honest)

Sales discipline requires admitting these. Do not lie. Pivot.

1. **"Where are your case studies and reference customers?"**
   We have none. Pivot to: "You'd be the case study. Want first-mover pricing in exchange?"

2. **"What about [specific enterprise system you haven't connected to]?"**
   If they name SAP, Workday, NetSuite, ServiceNow, etc. and we don't have a connector, do not fake it. Pivot to: "We've shipped BigQuery, Snowflake, SQL Server, DuckDB, and Databricks. We can build a [system] connector in 4 weeks if it's a deal-blocker. Is it a deal-blocker?"

Honest objection handling = faster trust. Better to lose a deal on day 1 than discover the deal-blocker on day 90.

---

## 10. Discovery Questions (Use Early in the Conversation)

Lead with these to qualify and surface real pain:

1. "Walk me through your last KPI miss — how was the breach detected, and what happened after?"
2. "How long does it take from spotting a problem to a board-ready recommendation? Who does that work today?"
3. "When your CFO approves an investment, how do you prove 6 months later that it worked?"
4. "If a market shift contradicted your internal analysis, would you know about it before acting?"
5. "Who owns each of your top 20 KPIs? Could you name them right now?"
6. "Of the last 5 strategic recommendations your CFO received — from consultants, BI tools, or analysts — how many were implemented? What killed the rest?"
7. "When a recommendation isn't executed, how do you currently know — and how long does it take you to know?"

If they can't answer #3 or #5 cleanly — you have a deal.
If they admit they don't track #6 or #7 — they have the execution-visibility problem we solve.

---

## 11. Recommended Marketing Headlines (For Site + Decks)

**Hero:**
> "From detection to proof. Automatically."
> *The only platform that closes the loop from KPI breach to verified outcome.*

**Moat section:**
> "Five integrated stages. One audit trail. Zero handoffs."
> *Detection, diagnosis, recommendation, decision, proof — every stage hands typed data to the next.*

**Differentiator:**
> "We don't just tell you the fix worked. We prove it with counterfactual attribution."
> *Difference-in-Differences using IS NOT segments as control groups isolates your solution's causal contribution from market tailwinds and seasonal effects.*

**Why-now:**
> "Strategy drift is silent. We make it visible."
> *Every approved solution carries a snapshot of the strategic context at decision time. We compare it to the live world at measurement time and tell you when the original objective is no longer valid.*

---

## 12. Pricing Reference (Internal — Confirm Before Quoting)

| Component | Price | Notes |
|---|---|---|
| Onboarding | $5K–$15K | Per data product, one-time |
| Base Platform | $3K/month | Dashboard, registries, 50 NL queries |
| KPI Monitoring | $300/KPI/month | First 10 included in base |
| Assessment Credits | $750 each | 4/month included; on-demand thereafter |
| Solution Tracking | $500/quarter | Per VA-tracked solution |

**Pilot package (3 months):** $15K–$25K
**Tier 1 (mid-market, single domain):** $100K–$150K/year — 20–30 KPIs, 6–8 assessments/month
**Tier 2 (large enterprise, multi-division):** $350K–$650K/year — 50–100 KPIs
**Tier 3 (global / partner-led):** $1.2M–$2.8M/year — 200–500 KPIs (Year 3+)

See [customer_roi_calculator.md](customer_roi_calculator.md) for the customer-facing ROI model.

---

## 13. Honest Current State (May 2026)

| Capability | Status |
|---|---|
| 14 agents operational | ✓ |
| 2 client datasets in production (bicycle + lubricants) | ✓ |
| 5 SQL backends wired (BigQuery, Snowflake, SQL Server, DuckDB, Databricks) | ✓ |
| Demo video shipped | ✓ |
| Email briefings + 1-click delegation | ✓ |
| SOC 2 Type II | Roadmap (2027) |
| Reference customers | None yet — first paying pilot is the next milestone |
| SAP / Oracle / Workday connectors | Not yet — built on demand |
| Realistic execution-rate lift | 1.3–1.7× over status quo. Visibility, not magic. |

Do not oversell. The product is real. The customer count is zero. Both facts close deals when stated honestly.

---

## 14. What We Don't Promise (Honest Differentiation)

Honesty closes more deals than enthusiasm. These are things Decision Studio explicitly does **not** do. Use them in sales conversations to differentiate from competitors who overpromise — and to set expectations that lead to renewals, not churn.

1. **We do not manufacture execution.** We surface decisions, name owners, quantify cost-of-delay, and make stalls visible. We do not make organizations execute things they don't have the will to execute. Expect a 1.3–1.7× lift in adoption versus your current baseline — not a 3× lift.

2. **We do not replace consultants for strategic transformation.** If your question is "should we enter Asia?" — that's still a McKinsey engagement. We handle the operational tier (5–7 day analysis cycles, $K to low-$M decisions), not the transformational tier ($M to $B decisions).

3. **We do not eliminate the need for finance / FP&A / data teams.** Their work shifts from manual analysis and slide-building to validation, refinement, and execution oversight. Same headcount, higher leverage.

4. **We do not fix poor data quality.** If your warehouse is incomplete or wrong, our analysis will inherit those flaws. We require defined KPIs and source-of-truth data products to function. The KPI Assistant and Data Product Agent accelerate definition — they do not invent ground truth.

5. **We do not eliminate cognitive bias.** Principals can still approve bad recommendations or reject good ones. Our role is to make the choice structured, auditable, and reviewable — not to override human judgment.

6. **We do not promise specific ROI multiples in advance.** We promise honest causal measurement via DiD attribution. If your decisions are bad, the report will show that. We are a thermometer, not a thermostat.

**The selling principle:**

> Customers who pilot us with these expectations renew at high rates. Customers who pilot us expecting magic churn within two quarters. Sell to the first kind. Walk away from the second.
