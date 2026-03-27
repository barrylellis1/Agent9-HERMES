# Decision Studio Business Premise Challenge — Revised
**Original:** February 12, 2026
**Revised:** March 27, 2026
**Scope:** 18-month forward-looking stress test (Q2 2026 → Q4 2027)
**Purpose:** Reassess existential threats and strategic positioning now that the platform is demo-ready and corporate site is live

---

## 0. What Changed Since February

The original premise challenge was written when the platform was mid-build. Six weeks later, the situation is materially different:

| Area | February 2026 | March 2026 |
|------|---------------|------------|
| **Platform** | SA → DA → SF pipeline working; no MA, no VA | Full SA → DA → MA → SF → VA pipeline operational |
| **Market Analysis** | Not built | Perplexity + Claude synthesis live; market signals in every briefing |
| **Value Assurance** | Not built | 6-entrypoint agent, DiD attribution, three-trajectory tracking, Supabase persistence |
| **Opportunity Detection** | Not built | SA detects positive KPIs → green opportunity cards → replication targets in DA |
| **Corporate Site** | No public presence | decision-studios.com: landing page + 3 content pages (Insights, How It Works, Data Onboarding) |
| **Production Deploy** | Local only | Railway (backend) + Vercel (frontend) + Supabase Cloud + BigQuery — full stack deployed |
| **Brand Identity** | "Agent9" internal name | "Decision Studio" customer-facing; Satoshi typography; dark/premium design; "Request a Conversation" CTA |
| **Positioning** | "Agentic consulting marketplace" | "AI Decision Intelligence" — domain-agnostic vertical application |
| **Pricing** | Theoretical $25K-$300K | Grounded: $15K-$25K pilots → incremental usage-based model under evaluation (per-KPI, per-assessment, per-solution tracking) |
| **Partner Strategy** | BCG outreach planned | Tier 0 (fractional CFOs) now; Tier 1+ deferred to 5+ customers |
| **ICP Refinement** | Mid-market executives | Never-engaged mid-market ($50M-$500M companies that never hired MBB) as primary target |

**Bottom line:** The platform risk identified in February — that orchestration would commoditize before we had a product — is significantly mitigated. The product exists, is deployed, and has a corporate presence. The remaining risks are commercial, not technical.

---

## 1. The Core Premises — Reassessed

| # | Premise | Feb Confidence | Mar Confidence | Change |
|---|---------|---------------|---------------|--------|
| P1 | No agentic consulting marketplace exists | 🔴 Eroding fast | 🟡 Still true, less relevant | ↑ We're no longer pitching as a marketplace |
| P2 | Consulting firms are slow to adopt AI | 🟡 Partially true | 🟡 Unchanged | — Still slow to productize for mid-market |
| P3 | Mid-market enterprises will buy from a solo-founder startup | 🟡 Conditional | 🟡 Conditional (improved) | ↑ Corporate site + deployed product adds credibility |
| P4 | Multi-agent debate is a durable differentiator | 🟡 Window closing | 🟡 Window still closing, but moat is deeper | ↑ Registry + VA + MA make the combination harder to replicate |
| P5 | Partners will encode IP in a third-party platform | 🔴 Unlikely near-term | 🔴 Correctly deferred | — Partner strategy now starts with Tier 0 practitioners |
| P6 | $100K+ ACV is achievable pre-revenue | 🔴 Unrealistic Year 1 | 🔴 Confirmed unrealistic; $15K-$25K pilots accepted | ✅ Addressed |
| P7 | Bootstrapped path to $2M ARR in 30 months | 🟡 Possible but narrow | 🟡 Revised: $600K-$1.4M base under incremental pricing | ✅ Addressed |

| P11 | Usage-based incremental pricing fits better than flat SaaS | — | 🟡 Plausible — needs demo feedback | New |
| P12 | Outcome-based pricing component eliminates ICP's primary objection | — | 🟡 Plausible — needs demo feedback | New |

### What's genuinely new since February

**P8 (New): "The never-engaged mid-market is a better ICP than consulting-fatigued enterprises."**
- Confidence: 🟢 **Strong**
- Companies with $50M-$500M revenue that have never hired MBB are not replacing consultants — they're getting structured analysis for the first time
- No incumbent to displace; the alternative is "keep doing it manually"
- Lower sales friction than pitching against an existing consulting relationship
- Three buyer-felt problems on the landing page are designed for this persona

**P9 (New): "Value Assurance trajectory tracking is a unique, defensible feature."**
- Confidence: 🟢 **Strong**
- No competitor — consulting firm, AI startup, or cloud platform — offers post-decision three-trajectory KPI tracking with DiD attribution
- VA is the self-validating loop: it proves the platform's own recommendations worked, which justifies renewal
- The IS NOT → control group → DiD pipeline is architecturally integrated, not bolted on

**P10 (New): "5-Day Fast Start onboarding is a compounding moat."**
- Confidence: 🟢 **Strong**
- Data Product Onboarding workflow is built and working (7-step wizard, AI-assisted KPI definition)
- Each customer onboarding creates: data product contracts, KPI registry entries, principal profiles, threshold calibrations
- Template library compounds — the 10th SAP customer onboards in hours, not days
- Switching costs accumulate from Day 1

**P11 (New — Mar 27): "Usage-based incremental pricing is a better fit than flat SaaS."**
- Confidence: 🟡 **Plausible — needs demo feedback**
- The platform's real cost drivers map naturally to usage dimensions: KPIs monitored (SA scan volume), assessment cycles (DA→SF→MA pipeline runs), solution tracking (VA trajectory monitoring), data products connected (onboarding + query volume)
- A full SA→DA→SF→MA pipeline run costs ~$0.50-$1.00 in LLM fees — this is measurable and billable
- Per-KPI monitoring ($300/KPI/month) is the dominant billing axis: 37-53% of annual revenue across all customer tiers
- Natural expansion: customers who see value on 10 KPIs want 50; no new sales cycle needed
- Pilot entry point becomes very low: 1 data product + 10 KPIs + base platform ≈ $3K/month — within executive discretion budget for never-engaged ICP
- **Risk:** Revenue is less predictable than flat SaaS; requires metering infrastructure; early-stage startups typically need ARR predictability for fundraising
- **Demo feedback question:** Present 2-3 pricing structures and ask "which would you take to your CFO?"

**P12 (New — Mar 27): "Outcome-based pricing component could eliminate ICP's primary objection."**
- Confidence: 🟡 **Plausible — needs demo feedback**
- The never-engaged ICP's core objection is cost/risk relative to certainty of outcome — "what if I pay $80K and nothing changes?"
- Outcome-based component (e.g., 10% of measured KPI improvement, capped per domain) directly attacks this objection
- VA trajectory tracking becomes the billing/metering system, not just a feature — the three-line chart is the invoice justification
- DiD attribution in the DA agent becomes commercially critical, not just analytically interesting
- **Risk:** Pure outcome pricing is too volatile for a startup; hybrid model (small base + outcome share + cap) is the practical version
- **Kill criterion if pursued:** >60-70% of customers must generate measurable outcomes within 90 days, or the model doesn't work

---

## 2. Projected Market Trends — Updated Assessment

### 2.1 Agent Infrastructure Explosion → Still Real, Less Threatening

**February assessment:** Multi-agent orchestration will be commodity by Q4 2027.
**March update:** Correct, and irrelevant. Decision Studio's differentiator was never orchestration — it's the domain model.

The combination that no cloud platform or framework provides:
- **Registry-driven domain intelligence** (KPIs, principals, business processes, data products, glossary)
- **Structured analytical methodology** (KT IS/IS NOT, SCQA framing, MBB multi-perspective debate)
- **Post-decision accountability** (VA three-trajectory tracking, DiD attribution)
- **Real-time market context** (MA Perplexity + Claude synthesis)
- **Audit trail** connecting detection → diagnosis → recommendation → outcome

AWS Bedrock Agents gives you orchestration. It does not give you a registry that knows what "Gross Margin %" means for Sarah Chen's lubricants business, or that the Southeast region is the control group for measuring whether a pricing intervention worked.

**Revised risk level:** 🟡 Medium (infrastructure commoditizes, but the domain layer does not)

### 2.2 Consulting Firms Moving Faster → Still True, Still Irrelevant for ICP

**February assessment:** Every major firm will have AI-augmented delivery by Q4 2027.
**March update:** Correct, but they're building for their existing $500M+ clients, not for the $50M-$500M never-engaged segment.

The revised ICP — companies that have never hired MBB — means consulting firm AI adoption is not a competitive threat. These companies were never going to buy from McKinsey or BCG regardless of AI capabilities. Decision Studio competes with "doing nothing" or "asking an analyst to build a spreadsheet," not with Lilli or BCG X.

**Revised risk level:** 🟢 Low for revised ICP

### 2.3 AI Finance Startup Wave → Real, but Narrower Than Feared

**February assessment:** Dozens of VC-backed startups targeting similar ICP.
**March update:** True, but they're overwhelmingly finance-only. Decision Studio's domain-agnostic positioning (finance, operations, sales, supply chain) is a genuine differentiator.

| Competitor | Scope | Decision Studio Advantage |
|-----------|-------|--------------------------|
| Hebbia ($130M) | Document analysis for PE | Data-centric with live KPI monitoring + MA + VA |
| Runway ($60M+) | FP&A automation | Strategic advisory, not operational finance |
| Mosaic ($48M) | Strategic finance platform | Multi-perspective debate + market intelligence + outcome tracking |
| Numeric ($28M) | Financial close | Completely different problem (close ≠ decision intelligence) |

**Key insight:** None of these competitors offer:
1. Continuous monitoring that triggers analysis automatically
2. Multi-perspective debate with visible disagreement
3. Post-decision trajectory tracking with causal attribution
4. Domain-agnostic operation across finance + operations + sales

**Revised risk level:** 🟡 Medium (crowded space, but differentiated positioning)

### 2.4 Enterprise AI Buying Consolidation → Real, Mitigated by Pricing

**February assessment:** Standalone AI tools face increasing procurement friction.
**March update:** True for $100K+ enterprise deals. Mitigated by $15K-$25K pilot pricing that can come from innovation budget or executive discretion without full procurement cycle.

The Fast Start onboarding (5 days to first situation card) also helps — the buyer sees value before procurement friction accumulates.

**Revised risk level:** 🟡 Medium (real for scale, mitigated for land-and-expand)

### 2.5 LLM Cost Deflation → Accelerating (Good)

**February assessment:** LLM costs dropping 90%+.
**March update:** Confirmed. Claude task routing (Haiku for Stage 1, Sonnet for synthesis) already reduces per-analysis cost. Open-weight models continue improving.

**Impact:** Gross margins are strong. The cost to run a full SA → DA → MA → SF analysis is approaching $1-$2 per session. VA trajectory tracking adds negligible cost (mostly math, not LLM calls).

**Revised risk level:** 🟢 Positive trend

---

## 3. Premise-by-Premise Verdict — March 2026

### P1: "No agentic consulting marketplace exists" → 🟡 TRUE BUT REPOSITIONED

**February verdict:** Eroding fast.
**March verdict:** Still true, but no longer the primary pitch. Decision Studio is positioned as an AI decision intelligence application, not a consulting marketplace. The marketplace vision is Year 3+ if warranted.

**Strategic status:** ✅ Addressed by repositioning

### P2: "Consulting firms are slow to adopt AI" → 🟡 UNCHANGED

**February verdict:** Half true (slow to productize, fast to adopt internally).
**March verdict:** Same. They're building for large enterprise, not mid-market.

**Strategic status:** Neutral — not a factor for revised ICP

### P3: "Mid-market enterprises will buy from a solo-founder startup" → 🟡 IMPROVED

**February verdict:** Conditional on compelling product and low price.
**March verdict:** Stronger. The deployed product, corporate site, 30+ year career narrative, and Fortune 500 client list (ExxonMobil, Shell, PwC, BCG, Roche, Whirlpool...) provide credibility a generic startup doesn't have. The "Built by" section on the landing page turns solo-founder from a liability into a strength: "I built something that works."

**What still needs to happen:** First paying customer by September 2026. The credibility gap closes permanently after 1-2 case studies with documented ROI.

### P4: "Multi-agent debate is a durable differentiator" → 🟡 DEEPER MOAT

**February verdict:** Window closing (12 months).
**March verdict:** Multi-agent debate alone is replicable. But the combination — registry context + KT methodology + multi-perspective debate + market intelligence + VA trajectory tracking + audit trail — is significantly harder to replicate. Each component reinforces the others:
- DA's IS NOT segments become VA's control groups
- MA's market signals inform SF's recommendations
- VA's trajectory data validates (or challenges) the original SA detection

**Strategic status:** The moat shifted from "we do multi-agent debate" to "our analytical pipeline produces auditable, measurable outcomes from detection to proof." That's a much harder thing to copy.

### P5: "Partners will encode IP in Agent9" → 🔴 CORRECTLY DEFERRED

**February verdict:** Premature.
**March verdict:** Tier 0 strategy (fractional CFOs as practitioners) is the right entry point. They adopt the tool for their own practice, not as a partnership. The partnership emerges organically. Tier 1+ (boutique FP&A firms) activates at 5+ customers.

**Strategic status:** ✅ Addressed by consulting partner strategy doc (tiered activation)

### P6: "$100K+ ACV pre-revenue" → 🔴 → ✅ ADDRESSED

**February verdict:** Unrealistic Year 1.
**March verdict:** Accepted. Pricing grounded at $15K-$25K pilots. Market penetration deck has detailed Phase 1-3 financials.

### P7: "Bootstrapped path to $2M ARR in 30 months" → 🟡 REVISED — DRAMATICALLY DIFFERENT UNDER INCREMENTAL PRICING

**February verdict:** Possible but narrow.
**March 26 verdict (flat SaaS):** $225K-$360K base ARR, $500K-$1M stretch.
**March 27 revision (incremental pricing):** The same customer count yields 2.7-6× more revenue under usage-based pricing:
- **Base case:** 5-8 Tier 1 customers, **$600K-$1.4M ARR** by Month 24
- **Upside (PE portfolio + Tier 2 expansion):** 10-15 customers, **$1.5M-$6M ARR** by Month 24
- **Downside:** 2-3 customers, **$180K-$360K ARR** by Month 24

$2M ARR at 30 months is **back in range** under the upside incremental pricing scenario, without requiring more customers than originally planned — just higher per-customer value capture through KPI expansion and assessment usage.

**⚠️ Pricing model not finalized.** These projections are conditional on demo feedback validating that the ICP prefers incremental pricing over flat SaaS.

---

## 4. The Existential Question — Answered

**February's question:** Build vs. Ride (platform vs. vertical application vs. hybrid)?

**March's answer:** Option C (Hybrid — Application First, Platform Later) was chosen and executed.

Decision Studio is shipping as a vertical AI decision intelligence application:
- Corporate site at decision-studios.com positions it as a product, not a platform
- The three buyer-felt problems on the landing page address operational pain, not platform features
- The "How It Works" page explains the six-agent pipeline without mentioning "marketplace"
- The partner marketplace is not mentioned on any public-facing page
- The registry architecture enables future marketplace capabilities if demand warrants

**Status:** ✅ Resolved. The existential question is no longer open.

---

## 5. Pricing Model Evolution — March 27, 2026

### From Flat SaaS to Usage-Based Incremental

The original pricing model ($15K-$25K pilots → $40K-$80K annual) was a placeholder. Analysis of actual platform cost drivers reveals a more natural pricing structure:

**Real Cost Drivers (Biggest to Smallest):**
1. **LLM token consumption** — full pipeline run costs ~$0.50-$1.00 in LLM fees
2. **KPIs monitored** — multiplies SA scan volume; biggest recurring cost
3. **Assessment frequency** — daily/weekly/monthly cycles; linear cost multiplier
4. **Data query volume** — BigQuery billed per TB scanned; DA runs 5-15 queries per situation
5. **NL interactions** — per-query LLM cost (cheap individually, adds up)

**Incremental Charge Model (Best Candidate):**

| Component | Price | Covers |
|-----------|-------|--------|
| Onboarding (one-time) | $5K-$15K per data product | 5-Day Fast Start, schema inspection, contract, KPI registration, baseline |
| Base Platform | $3K/month | Dashboard access, registries, NL queries (50/month included) |
| KPI Monitoring | $300/KPI/month (first 10 included) | SA scans, anomaly detection, situation cards |
| Assessment Credits | 4/month included; $750 each additional | Full DA→SF→MA pipeline run per triggered situation |
| Solution Tracking | $500/quarter per active VA-tracked solution | Trajectory monitoring, impact measurement, DiD attribution |

### Three-Tier Revenue Projections (Mapped to Past Client Profiles)

**Tier 1: Mid-Market / Single Domain — $100K-$150K/yr (Direct Sale)**
*Profile: Valvoline, Hess, Pilgrim's Pride, Commercial Metals*
- 2-3 data products, 20-30 KPIs, 6-8 assessments/month, 4-6 tracked solutions
- This IS the ICP. Full margin. Sales cycle: executive discretion budget.

**Tier 2: Large Enterprise / Multi-Division — $350K-$650K/yr (Direct + Partner)**
*Profile: Whirlpool, Panasonic, Teleflex, McKesson, Cadence*
- 5-10 data products, 50-100 KPIs, 15-25 assessments/month, 10-20 tracked solutions
- Multi-division deployments are the natural expansion motion — each business unit that onboards multiplies revenue without a new sales cycle

**Tier 3: Global Enterprise / Partner-Led — $1.2M-$2.8M/yr (Partner Takes 30-40%)**
*Profile: ExxonMobil, Shell, Roche; PwC/BCG as resellers*
- 15-30 data products, 200-500 KPIs, 50-100 assessments/month
- Requires Phase 10+ infrastructure: batch SA scanning, query caching, multi-tenant isolation
- Not addressable at launch — this is the Year 3+ scaling path

**Key Finding:** Per-KPI monitoring is 37-53% of annual revenue across all tiers. It's the single billing axis that scales with complexity AND that customers naturally want to expand (each KPI = another problem caught early).

### Optional Outcome-Based Component

Layered on top of incremental pricing, not replacing it:
- Per-solution VA tracking fee could become "10% of measured KPI improvement, minimum $500/quarter, capped at $25K/quarter per domain"
- VA trajectory tracking becomes the billing system; the three-line chart (inaction/expected/actual) is the invoice justification
- **Not committed.** Surface as demo feedback question: "Which pricing model would you take to your CFO?"

### Pricing Model Status

**Not finalized.** Three models will be tested during early product demonstrations:
1. Pure fixed SaaS ($15K-$80K/yr flat)
2. Incremental usage-based (base + per-KPI + per-assessment + per-solution)
3. Hybrid with outcome share (incremental base + % of measured improvement)

First 5-10 conversations will determine which resonates with the never-engaged ICP.

---

## 6. Revised Financial Projections

### Base Case (Conservative — Solo Founder, Moonlighting)

| Period | Customers | Profile | Avg ACV (Incremental) | ARR | Cumulative |
|--------|-----------|---------|----------------------|-----|------------|
| Q2-Q4 2026 | 1-2 | Tier 1 (15-20 KPIs) | $75K-$100K | $75K-$200K | $75K-$200K |
| H1 2027 | 3-5 | Tier 1 (20-30 KPIs) | $100K-$150K | $300K-$750K | $375K-$950K |
| H2 2027 | 5-8 | Tier 1-2 mix | $120K-$180K | $600K-$1.4M | $975K-$2.35M |
| **Month 24** | **5-8** | | **$120K-$180K** | **$600K-$1.4M** | |

*Under incremental pricing, ACV is higher than flat SaaS because: (a) per-KPI billing captures expansion value that flat pricing leaves on the table, (b) assessment credits generate usage-based revenue beyond the base, (c) VA solution tracking adds a quarterly revenue stream. Even a small Tier 1 customer at 20 KPIs = $3K base + $3K KPIs + $1.5K assessments ≈ $90K/yr.*

### Upside Case (Strong PMF + Multi-Division Expansion)

| Period | Customers | Profile | Avg ACV (Incremental) | ARR | Cumulative |
|--------|-----------|---------|----------------------|-----|------------|
| Q2-Q4 2026 | 2-3 | Tier 1 | $100K-$150K | $200K-$450K | $200K-$450K |
| H1 2027 | 5-8 | Tier 1-2 mix | $150K-$350K | $750K-$2.8M | $950K-$3.25M |
| H2 2027 | 10-15 | Tier 1-2 mix | $150K-$400K | $1.5M-$6M | $2.45M-$9.25M |
| **Month 24** | **10-15** | | **$150K-$400K** | **$1.5M-$6M** | |

*Upside assumes: PE firm adopts across 3-5 portfolio companies (each a Tier 1 customer); one Tier 2 multi-division expansion (Whirlpool-type); quit day job by Month 12. Tier 2 customers at 50-100 KPIs drive $350K-$650K ACV each, which dramatically shifts the average.*

### Downside Case (Market Headwinds)

| Period | Customers | Profile | Avg ACV | ARR | Cumulative |
|--------|-----------|---------|---------|-----|------------|
| Q2-Q4 2026 | 0-1 | Tier 1 (minimal) | $50K-$75K | $0-$75K | $0-$75K |
| H1 2027 | 1-2 | Tier 1 | $75K-$100K | $75K-$200K | $75K-$275K |
| H2 2027 | 2-3 | Tier 1 | $90K-$120K | $180K-$360K | $255K-$635K |
| **Month 24** | **2-3** | | **$90K-$120K** | **$180K-$360K** | |

*Even in the downside, incremental pricing yields more than flat SaaS would because customers who stay are expanding KPI coverage. The risk is fewer customers, not lower per-customer value.*

### Comparison: Flat SaaS vs. Incremental Pricing Impact on Projections

| Scenario | Flat SaaS ARR (Month 24) | Incremental ARR (Month 24) | Delta |
|----------|-------------------------|---------------------------|-------|
| Base | $225K-$360K | $600K-$1.4M | 2.7-3.9× higher |
| Upside | $650K-$975K | $1.5M-$6M | 2.3-6.2× higher |
| Downside | $50K-$75K | $180K-$360K | 3.6-4.8× higher |

*The incremental model doesn't require more customers — it captures more value per customer through KPI expansion, assessment usage, and solution tracking. The same 5 Tier 1 customers that would yield $225K under flat pricing yield $600K+ under incremental pricing.*

**⚠️ Caveat:** These projections assume the incremental model resonates with buyers. If demo feedback shows the ICP strongly prefers simple flat pricing (predictable budget), the flat SaaS projections from the previous revision remain the fallback. The pricing model is NOT finalized — it's a feedback question for early demonstrations.

---

## 7. Exit Strategy Implications

*Full analysis: `docs/strategy/exit_strategy.md`*

The pricing model fundamentally changes the exit calculus. Under incremental pricing, high NRR (130-150%) transforms valuation multiples:

| Scenario | ARR Trigger | Timeline | Valuation Range | Acquirer Profile |
|----------|------------|----------|-----------------|-----------------|
| **Bootstrapped acquisition** | $600K-$1.4M | Month 24-36 | $5M-$21M | PE roll-up, ERP vendor (Sage, Epicor), consulting tech arm |
| **Funded growth → strategic** | $3M-$10M | Month 30-48 | $45M-$250M | Salesforce, ServiceNow, Workday, SAP |
| **PE portfolio play** | $5M-$15M | Month 36-60 | $60M-$300M | PE firm itself, or strategic at premium |
| **Downside (acqui-hire)** | $180K-$360K | Month 24-30 | $1M-$5M | AI startup, consulting firm (IP acquisition) |

**The NRR multiplier:** A $1M ARR company with 140% NRR (incremental pricing, natural KPI expansion) is valued at ~$22M. The same $1M ARR with 105% NRR (flat SaaS) is valued at ~$10M. Incremental pricing doesn't just increase revenue — it changes the valuation category.

**Key metrics to track from Day 1:** Net revenue retention, KPI expansion rate per customer, time-to-value (days to first situation card), VA trajectory success rate.

**Decision point at Month 12-18:** Stay bootstrapped (Scenario A, $5M-$21M) vs. raise seed (Scenario B, $45M-$250M) vs. deepen PE relationship (Scenario C, $60M-$300M). Actions that maximize Scenario A also maximize B and C — no premature commitment needed.

---

## 8. What Must Be True for Decision Studio to Succeed

### Non-Negotiable Requirements (Updated)

1. ~~**Demo-ready by April 2026**~~ → ✅ **Done.** Platform deployed, corporate site live.

2. **Demo video by April 2026** — The demo video is the next deliverable. It replaces 30 minutes of founder-led explanation with a 3-5 minute artifact that can be shared asynchronously. Without it, every warm lead requires a live call.

3. **First paying customer by September 2026** — Still the single most important milestone. Revenue validates the premise.

4. **The pitch is buyer-felt problems, not technical architecture** — ✅ Landing page leads with "You're always reacting, never anticipating" — not "six AI agents in a pipeline." Architecture is secondary to pain.

5. **Price at $15K-$25K for first 3 pilots** — ✅ Accepted. Market penetration deck confirms.

6. **Target never-engaged mid-market ($50M-$500M revenue)** — ✅ Revised ICP. Companies that never hired MBB are the primary target. They have real analytical pain with no incumbent to displace.

7. **Build case studies aggressively** — By Month 12, need 2-3 documented ROI stories. VA trajectory data from completed measurement windows is the proof.

8. **Ignore partner/marketplace vision for 12 months** — ✅ Except Tier 0 fractional CFOs, who are practitioners first and partners second.

### Kill Criteria (Updated)

| Signal | Timeline | Action |
|--------|----------|--------|
| Zero paying customers | By Q4 2026 | Reassess ICP and pricing. Consider SMB pivot. |
| Zero pipeline after 30 discovery calls | By Q3 2026 | Product-market fit problem. Major pivot needed. |
| First pilot churns / fails to renew | By Q2 2027 | Product value problem. Stop selling, fix product. |
| VA trajectory data shows solutions don't improve KPIs | By Q4 2027 | Fundamental value proposition failure. |
| Funded competitor launches identical pipeline (SA→DA→MA→SF→VA with registry + audit trail) | Any time | Accelerate or seek acquisition. |
| Burnout / health impact from moonlighting | Any time | Pause, recover, reassess. Health > startup. |

---

## 9. What's Different From February

| Area | February Plan | March Reality |
|------|-------------|---------------|
| **Positioning** | "Agentic Consulting Marketplace" | "AI Decision Intelligence" — domain-agnostic vertical application |
| **Product** | SA → DA → SF working | SA → DA → MA → SF → VA full pipeline + production deploy |
| **Corporate presence** | None | decision-studios.com with 4 pages + brand identity |
| **Year 1 pricing** | $25K-$300K (theoretical) | Incremental usage-based model under evaluation: $3K base + $300/KPI/month + $750/assessment + $500/quarter/solution |
| **Partner strategy** | BCG/McKinsey outreach planned | Tier 0 fractional CFOs now; Tier 1+ deferred to 5+ customers |
| **Marketplace** | Core to pitch | Not mentioned on any public page; Year 3+ if warranted |
| **Competitive narrative** | "No agentic players exist" | "No one connects detection → diagnosis → recommendation → proof with registry context and audit trail" |
| **Primary differentiator** | Multi-agent orchestration | Registry-driven domain intelligence + VA accountability loop |
| **ICP** | Mid-market executives (generic) | Never-engaged mid-market ($50M-$500M, never hired MBB) |
| **Primary risk** | Platform not built in time | Commercial: can we close first 2 pilots? |
| **30-month ARR target** | $1M-$2M | $600K-$6M (incremental pricing base to upside); $225K-$975K if flat SaaS |

---

## 10. The Bottom Line — March 2026

**The business premise is stronger than it was six weeks ago.**

The technical risk that dominated the February assessment — "can we build this?" — is resolved. The product exists, is deployed, and is demonstrable. The competitive positioning has been sharpened. The corporate site projects credibility. The pricing is grounded. The partner strategy is realistic.

**What remains is commercial execution:**

1. **Record the demo video** (April 2026). This is the single highest-leverage artifact for the next 60 days. Every warm lead that sees the video before the first call converts faster.

2. **20 warm outreach conversations** (May-June 2026). The landing page CTA is "Request a Conversation." The corporate site exists to make those conversations happen. **NEW: These conversations must also validate pricing model preference** — present 2-3 structures, ask "which would you take to your CFO?"

3. **First pilot signed** (September 2026). Revenue validates everything. No revenue by Q4 2026 = serious reassessment.

4. **Pricing model locked** (by pilot 3). First 1-2 pilots may use simplified flat pricing for speed. By pilot 3, the incremental model should be validated or abandoned based on buyer feedback.

5. **VA trajectory data** (Q1-Q2 2027). The first pilot's measurement window closes. If the trajectory chart shows the approved solution worked, that chart becomes the most powerful sales artifact in the pipeline. **Under outcome pricing, it also becomes the invoice.**

6. **Tier 2 expansion proof** (H2 2027). If any Tier 1 customer has multiple business units, attempt multi-division expansion. One successful Tier 2 expansion ($350K-$650K ACV) changes the unit economics story for investors and partners.

The window is still narrow. Funded competitors are building in the same space. But the combination of registry-driven domain intelligence, structured analytical methodology, multi-perspective debate, real-time market context, and post-decision accountability tracking — deployed and demonstrable — is a stronger starting position than most solo-founder startups have at this stage.

**The pricing model question is the most consequential open decision.** The same 5-8 customers yield $225K-$360K under flat SaaS or $600K-$1.4M under incremental pricing — a 3-4× difference in revenue from the same commercial effort. Early demo conversations will determine which model resonates.

**The next 6 months determine whether Decision Studio is a business or a side project. The single metric that matters: first paying customer by September 2026.**

---

*This document supersedes the February 12 original. Last updated March 27: added P11-P12 (pricing model premises), Section 5 (pricing model evolution), three-tier revenue projections, revised financial projections under incremental pricing, Section 7 (exit strategy implications). Full exit analysis: `docs/strategy/exit_strategy.md`. Next review: June 2026 (post-outreach assessment — pricing model should be locked by then).*
