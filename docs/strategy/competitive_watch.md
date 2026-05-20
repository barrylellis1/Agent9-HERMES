# Decision Studio Competitive Watch
**Last Updated:** 2026-05-20
**Version:** 1.2 — BI/Dashboard and Decision Intelligence market categories added with ICP cost contrasts; causaLens/decisionOS, Sisu Data, Tellius, Palantir AIP mapped; architectural origin (deterministic-first vs LLM-native) documented

---

## 1. Methodology Comparison

| **Capability** | **Agent9** | **Consulting Firms** | **Cloud Providers** | **AI Finance Startups** |
|---|---|---|---|---|
| Problem Framing | OODA+Cynefin hybrid | SCQA/Hypothesis-driven | Anomaly detection | Domain templates |
| Decision Analysis | KT-inspired matrices | Human judgment | Basic metric explanation | Narrow financial models |
| Multi-Agent Debate | Protocol-governed, auditable | None | Basic multi-agent (no debate) | None |
| Registry Context | KPIs, principals, processes, data products | Manual/tribal knowledge | None | Limited (financial only) |
| Audit Trails | Full protocol traces | Slide decks | Limited query history | Transaction logs |
| Market Intelligence | Real-time (Perplexity + Claude) | Quarterly reports | Cloud marketplace signals | Limited/none |
| Post-Decision ROI Tracking | Three-trajectory chart (inaction/expected/actual) | None (engagement ends) | None | None |
| Opportunity Detection | Positive KPI + benchmark segments + replication targets | Ad hoc | Anomaly-based only | None |

---

## 2. Cloud Agent Platforms (Commoditization Risk — Orchestration)

Multi-agent orchestration is becoming infrastructure. These are NOT direct competitors but represent strategic risk for the orchestration layer.

- **AWS Bedrock Agents** — GA. Decision Studio adds domain intelligence Bedrock lacks.
- **Azure AI Agent Service** — GA. Same gap: no registry, no consulting methodology.
- **Google Vertex AI Agents** — GA. Lacks enterprise registry depth.
- **LangGraph / CrewAI / AutoGen** — Open-source, maturing fast. Potential building blocks, not competitors.

**Strategic implication:** Orchestration is commodity by Q4 2027. Decision Studio's moat is the SA→DA→SF→VA analytical pipeline + Registry + VA outcome corpus — not the orchestration layer.

---

## 2b. Vendor Semantic Layers (Commoditization Risk — Data Access)

*New in May 2026 — formalised as separate competitive category after Apr 2026 strategic refresh.*

These vendors are commoditizing NL-to-SQL, semantic models, and conversational analytics. They are NOT direct competitors to the pipeline but they ARE the substrate Decision Studio adapts to via the Tier 1/2/3 connectivity model.

- **Snowflake Cortex Analyst** — Production-ready. Native NL-to-SQL + semantic views over Snowflake data. Answers data questions; does not run a decision pipeline. Decision Studio routes ad-hoc follow-up questions to Cortex Analyst (Tier 3) for Snowflake-resident data.
- **Databricks Genie Spaces / AI/BI** — Production-ready. Conversational analytics over Unity Catalog. Same shape: strong on data access, no SA monitoring, DA root cause, SF debate, or VA tracking. Decision Studio routes via Tier 3 for Databricks-resident data.
- **SAP Datasphere + JouleAgent** — Planned for SAP-native customers. Direct semantic layer; eliminates extract step.
- **Microsoft Fabric + Copilot** — Production-ready. Same gap pattern; semantic models commoditized, decision pipeline absent.

**Strategic implication — the Apr 2026 moat refresh:**
- **Moat layer (never outsource):** SA→DA→MA→SF→VA pipeline, Registry domain model, VA outcome corpus, calibrated monitoring profiles
- **Commodity layer (vendors do it better):** Database connectivity, schema discovery, NL-to-SQL, semantic models, basic governance
- **Architectural consequence:** DPA and NLP agents become thin adapters over vendor semantic layers. DGA is the intelligent router across them. Decision Studio's data contracts remain the fallback for customers without vendor semantic layers.
- **What this means competitively:** Cortex Analyst and Genie do not threaten Decision Studio's product — they enable it. The vendor handles data access; Decision Studio runs the decision pipeline above it (starting with market context from MA). Don't build NL-to-SQL; vendors will commoditize it.

---

## 3. AI Finance Startups (Direct Competitors)

These target a similar ICP (mid-market executives, PE ops) with well-funded teams.

| Startup | Funding | Focus | Threat | Agent9 Differentiation |
|---------|---------|-------|--------|----------------------|
| **Hebbia** | $130M | AI analyst for PE/finance | High | Document-centric vs Agent9 data-centric with live KPI monitoring + MA market intelligence + VA post-decision tracking |
| **Runway Financial** | $60M+ | AI-driven FP&A | Medium | Narrow FP&A scope vs strategic advisory + opportunity detection + ROI attribution |
| **Mosaic** | $48M | Strategic finance platform | Medium | Overlaps on CFO persona; Agent9 adds multi-perspective debate + market intelligence + trajectory tracking |
| **Numeric** | $28M | AI financial close | Low | Financial close != strategic decision intelligence; Agent9 tracks decision outcomes |
| **Clockwork** | $25M | AI financial modeling | Low | Modeling tool, not advisory platform; Agent9 provides end-to-end decision lifecycle |
| **Rogo** | $22M | AI research analyst | Medium | Research-focused; Agent9 goes from detection → analysis → solution → approval → ROI tracking |

**Strategic implication:** Executive decision intelligence space is crowded. Differentiate on multi-perspective analysis, registry context, and audit trails across any operational domain.

---

## 4. Consulting Firms (Indirect Competitors)

Building AI internally but NOT productizing for mid-market.

| Firm | AI Initiative | Threat | Notes |
|------|--------------|--------|-------|
| **McKinsey** | Lilli (30K+ internal users), QuantumBlack expanding | Medium | Won't serve $500M-$2B companies with AI tools; Agent9 now has market intelligence (MA) and post-decision tracking (VA) that MBB doesn't offer even to large clients |
| **BCG** | BCG X agentic AI capabilities | Medium | Building for own delivery, not a marketplace; Agent9's VA trajectory tracking is a capability BCG doesn't productize |
| **Deloitte** | AI-powered audit/advisory in production | Medium | Focuses on large enterprise; Agent9's three-trajectory ROI attribution is unique across all consulting firms |
| **Accenture** | $3B+ AI investment | Low | Serves F500 only |

**Strategic implication:** 18-24 month window before consulting firms expand AI downmarket. Agent9 must establish mid-market position before then.

---

## 5. BI / Dashboard Platforms (Adjacent — Wrong Layer)

BI tools answer *"what happened?"* Decision Studio answers *"what should we do, and did it work?"* These are different products with different buyers — but the ICP executive often has already spent on BI and will ask why they need both.

### 5a. Cost and Capability Comparison

| Platform | Typical Mid-Market Annual Cost | Buyer | Output | What's Missing |
|---|---|---|---|---|
| **Tableau + Einstein** | $80K–$250K/yr (5–10 Creators @ $115/user/mo + 50–100 Viewers @ $35/user/mo; add implementation $50K–$150K yr 1) | Analysts, BI team | Dashboards, basic AI anomaly narration | No root cause, no recommendations, no solution debate, no ROI tracking |
| **Power BI + Copilot** | $30K–$80K/yr (Premium Per User $20/user/mo; Copilot add-on $30/user/mo) | Finance analysts | Reports, Copilot natural language narration | Copilot explains charts — it does not generate recommendations, track decisions, or run a pipeline |
| **ThoughtSpot Sage** | $50K–$150K/yr (Team ~$1,250/user/yr; Enterprise custom $95K+ base) | Data analysts | Natural language queries over structured data | Search-oriented; no proactive monitoring, no decision advisory, no outcome tracking |
| **Qlik Sense + AutoML** | $50K–$120K/yr (enterprise; custom per node) | BI/Analytics teams | Interactive visualisations + basic ML predictions | Predictions without recommendations; no principal-driven framing; no audit trail |
| **Looker (Google)** | $50K–$200K/yr (Looker Core; bespoke enterprise) | Data teams | Semantic layer + dashboards | No anomaly detection, no decision pipeline, no solution tracking |

**Decision Studio pilot price: $18K (3 months) or $30K–$40K (6 months). Annual: $44K–$100K.**

The CFO spends $80K–$250K on Tableau and still needs a consultant when a KPI breaks. Decision Studio is not a replacement for BI — it is the advisory layer above it. Coexistence framing: *"Your Tableau shows you the number. Decision Studio tells you what to do about it."*

### 5b. ICP Objection: "We Already Have Tableau"

This is the most common early objection. The response framework:

| Their assumption | The reality |
|---|---|
| "Tableau with AI does analysis" | Tableau AI explains what the chart shows. It does not detect anomalies, run root-cause queries, debate options across three consulting personas, or track whether the approved solution worked. |
| "Our analysts do the rest" | Analysts are a bottleneck. Decision Studio runs analysis in 4–24 hours and delivers a role-personalised executive artefact — not a slide deck the analyst has to write. |
| "We can't afford another platform" | Decision Studio replaces the ad-hoc consulting spend, not Tableau. The comparison is the $50K retainer for a one-off analysis, not the BI licence. |
| "It duplicates what we have" | BI covers reporting (Tier 1). Decision Studio covers advisory (Tier 2) and outcome validation (Tier 3). No BI tool delivers Tier 2 or Tier 3. |

---

## 5c. Decision Intelligence Platforms (Emerging Direct Category)

This is a new and partially formed software category. Tools here attempt to automate parts of the analytical workflow — primarily for data teams, not executives. Decision Studio is the only platform in this space targeting VP-level functional buyers directly with an end-to-end decision lifecycle.

### Architectural distinction that matters

**Deterministic-first + LLM bolted on** (Sisu, causaLens, Tellius): Built on statistical algorithms or causal inference engines. LLMs added post-2023 as a natural language interface over outputs the algorithm already produced. The AI explains what the model computed — it did not generate the reasoning. Executive communication is an afterthought.

**LLM-native** (Decision Studio): The LLM *is* the reasoning engine. SCQA framing, IS/IS NOT interpretation, Council Debate, role-personalised output — generated by the model, not explained after the fact. Statistical rigour (Layer 1) is being added *on top* of LLM reasoning to provide confidence signals, not to replace the reasoning.

The two architectures are converging from opposite ends. The question for the executive buyer is which foundation matters more: technical rigour that no executive can consume, or executive communication grounded in statistical evidence.

### Platform Comparison

| Platform | Origin | Primary Buyer | Price Signal | What It Does | Decision Studio Gap |
|---|---|---|---|---|---|
| **Sisu Data** (Databricks-acquired) | 2018 — statistical driver analysis; decision-tree exhaustive variance decomposition | Data teams, analytics engineers | Was $100K–$300K/yr standalone; now bundled with Databricks; requires Databricks infrastructure | Automated root-cause analysis: which dimension explains the KPI move? Strong on statistical rigour. | No SA monitoring, no solution debate, no executive output, no VA tracking. Data team tool that produces findings an analyst still has to interpret for the CFO. |
| **Tellius** | 2016 — NLP + ML on top of BI data | Analytics teams, BI managers | $50K–$200K/yr enterprise; custom | NL queries + automated insight detection on connected BI data | No decision pipeline, no principal context, no recommendations, no outcome tracking. Answer layer only. |
| **Outlier** (ThoughtSpot) | Anomaly detection SaaS, acquired by ThoughtSpot | Analytics/data teams | Bundled in ThoughtSpot Enterprise | Automated anomaly alerts + contributing factor explanation | Alert + explanation; does not frame the situation for an executive, generate options, or track outcomes. |
| **causaLens / decisionOS** | 2018 — causal inference, DAG-based structural causal models; LLM added post-2023 | Data scientists, quant teams in finance/pharma | $150K–$500K/yr; enterprise custom | Causal inference: isolates true cause-and-effect vs correlation in KPI behaviour | Technically rigorous but requires causal modelling expertise to configure. No executive artefact. No SA→DA→SF→VA pipeline. No mid-market pricing. |
| **Palantir AIP** | 2023 LLM wrapper over Palantir Foundry data fabric | Enterprise, defence, government ($1B+ revenue orgs) | $1M–$100M+ enterprise contracts | Decision intelligence at enterprise scale; workflow automation, AI-assisted operations | Wrong market. No mid-market reach. No standard pilot model. AIP validates the space; it does not compete in it. |

### ICP Cost Reality for Decision Intelligence Category

An analytics-focused mid-market company ($100M–$300M revenue) choosing between these options faces:

| Option | Year 1 All-In Cost | Who Consumes the Output | Time to First Insight |
|---|---|---|---|
| Sisu (via Databricks) | $200K–$500K+ (Databricks platform + Sisu licences + data engineering) | Analytics team → analyst translates → CFO gets slide deck | 4–12 weeks onboarding |
| causaLens | $200K–$600K (licence + causal model build + data science resource) | Data scientists → months of model calibration → findings report | 8–20 weeks |
| Tellius | $80K–$200K | BI analysts | 2–4 weeks |
| **Decision Studio** | **$30K–$40K pilot, $44K–$100K/yr** | **CFO / VP Finance directly** | **5 days** |

The cost case is not "Decision Studio is cheaper." The cost case is: *Decision Studio is the only option in this category that delivers an executive-ready artefact without a data engineering prerequisite.* The others require a data team to operate and an analyst to translate. Decision Studio delivers the translated output directly.

---

## 6. Bridge Component Roadmap (Deferred)

*Original Q2-Q4 2026 timeline deferred. Bridge components are Year 2+ priorities after first paying customers.*

| Priority | Component | Purpose | Timeline | Status (May 2026) |
|----------|-----------|---------|----------|-------------------|
| 1 | LLM Provider Abstraction | Support Claude / Azure OpenAI for regulated industries | Build when prospect blocked by data residency | Infra B2 — single-customer trigger; Anthropic Claude is sole provider today |
| 2 | Vendor MCP Connectivity (Tier 2) | Connect via Snowflake Cortex MCP, Databricks MCP, Postgres MCP | Phase 10D, gated on vendor MCP maturity | Vendor MCPs released; Decision Studio MCP client + decorator pattern pending |
| 3 | Vendor AI Agent Routing (Tier 3) | DGA routes complex NL follow-up to Cortex Analyst / Genie | Phase 11F | Tier 1 native SDK shipped May 2026 (Phase 10C); Tier 2/3 follow |
| 4 | BI Embed Adapter | Insight cards in Tableau/Power BI | H1 2028 | Not started |
| 5 | Cloud Agent Bridge | Map Decision Studio protocols to Bedrock/Azure | H2 2028 | Not started |

---

## 7. Tracking Table

| Competitor | Last Updated | Key Moves | Decision Studio Countermeasures |
|---|---|---|---|
| McKinsey | 2026-Q1 | Lilli scaling to 30K+ users; QuantumBlack expanding AI delivery | Focus on mid-market they ignore; defer partnership outreach to Year 4+ |
| BCG | 2026-Q1 | BCG X building agentic AI; published AI adoption frameworks | Monitor but do not engage until 10+ customers |
| AWS | 2026-Q1 | Bedrock multi-agent orchestration GA; QuickSight AI integration | Shift differentiation to pipeline + outcome corpus; build alongside, not against |
| **Snowflake** | 2026-Q2 | Cortex Analyst production-ready; Cortex MCP server available | Adopt as Tier 2/3 (vendor MCP + AI agent); Decision Studio pipeline sits above |
| **Databricks / Sisu** | 2026-Q2 | Genie Spaces production-ready; Sisu acquired and bundled | Sisu is data-team tool requiring Databricks infra; Decision Studio delivers executive output without data engineering prerequisite |
| **causaLens / decisionOS** | 2026-Q1 | Pivoted to "decision intelligence" branding; enterprise causal AI | Architecture is deterministic-first + LLM bolted on; wrong buyer (data scientist); no mid-market pricing; use as category validation, not competitive threat |
| **Tableau / Salesforce** | 2026-Q2 | Einstein Copilot expanding; Tableau Pulse AI-narrated dashboards | Coexistence strategy: Decision Studio is advisory layer above BI. "Tableau shows the number; Decision Studio decides what to do about it." |
| **Power BI / Microsoft** | 2026-Q2 | Copilot for Power BI GA; Fabric unified platform | Same coexistence frame; Copilot narrates charts, does not run a decision pipeline |
| Hebbia | 2026-Q1 | $130M raised; expanding PE/finance AI analyst | Differentiate on live data (vs documents), multi-agent debate, VA outcome tracking |
| Runway | 2026-Q1 | FP&A automation expanding to mid-market | Differentiate on strategic advisory vs operational finance |
| OpenAI | 2026-Q1 | GPT-5 expected mid-2026; agent capabilities expanding | Anthropic Claude is sole provider (Mar 2026); add Azure OpenAI on customer trigger |

---

## 8. Key Competitive Insights (Updated May 2026)

1. **Both orchestration AND data connectivity are now commoditized.** Multi-agent orchestration via Bedrock/Azure/LangGraph; data access via Cortex Analyst, Genie, Fabric Copilot. The moat is NOT in either layer.
2. **The durable moat is the SA→DA→MA→SF→VA pipeline + Registry + VA outcome corpus.** No vendor is building this. Cortex Analyst answers data questions; Decision Studio runs the decision pipeline above (SA detects, DA analyzes, MA frames, SF recommends, VA tracks). Different products entirely.
3. **Don't build NL-to-SQL.** Vendors will commoditize it. The NLP Interface Agent stays deterministic regex; complex follow-up routes to Tier 3 vendor AI (Cortex Analyst / Genie) via the DGA router.
4. **Vendor semantic layers are partners, not competitors.** A customer with Snowflake gets a better Decision Studio experience because Cortex Analyst handles ad-hoc questions. Adopt the substrate; the pipeline is the product.
5. **"AI Decision Intelligence for mid-market executives" is the right positioning.** Domain-agnostic vertical application, not a platform. The "agentic consulting marketplace" framing is deferred to Year 3+.
6. **Mid-tier consulting firms (FTI, A&M, Huron) are more realistic partners than BCG/McKinsey.** They lack internal AI capabilities and are more likely to engage with a startup. MBB engagement deferred to Year 4+ post-Series A.
7. **First paying customer by September 2026 is the single most important competitive move.** Everything else is secondary.
8. **Value Assurance trajectory tracking + 5-phase lifecycle is a unique competitive feature.** No competitor — consulting firm, AI startup, or cloud platform — offers post-decision three-trajectory KPI tracking with DiD attribution and phase-aware rendering. This is the self-validating loop that justifies renewal.
9. **Market Analysis Agent runs BETWEEN DA and SF to align recommendations with market signals.** Real-time competitor and market context from Perplexity + Claude synthesis — after DA's root-cause analysis, MA enriches the options debate with market alignment signals. Explicit framing of internal-vs-market signal conflicts (outperforming headwinds / missing tailwinds / confirming pressure). Vendor AI doesn't do this.
10. **Calibrated monitoring profiles compound.** After 12 months of customer use, switching means losing calibrated noise/signal thresholds for 50+ KPIs. Phase 11D adaptive calibration loop deepens this further.
11. **The BI comparison is an objection to handle, not a competitive threat.** The ICP executive has already spent $80K–$250K on Tableau or Power BI and will ask "why do I need this too?" The answer is: BI is the reporting layer; Decision Studio is the advisory layer above it. The comparison in the CFO's mind should be "what did I spend on that one-off analysis?" not "what do my BI licences cost?"
12. **The Decision Intelligence category (Sisu, causaLens, Tellius) validates the problem space without competing for the ICP buyer.** These tools were built for data scientists and analytics engineers. They require significant data infrastructure to operate and still require an analyst to translate findings into executive language. Decision Studio's architectural origin (LLM-native, principal-driven) is a durable differentiation from their deterministic-first heritage. The existence of this category is a market development asset, not a threat.
13. **No competitor offers the full executive decision lifecycle.** The accurate competitive claim: *"No other platform integrates continuous KPI monitoring, root-cause analysis, market context, multi-perspective solution debate, HITL approval, and three-trajectory ROI validation in a single executive-facing workflow."* Individual capabilities exist in isolation; the integrated lifecycle does not exist elsewhere.
14. **Palantir AIP validates the category at the enterprise tier.** Palantir's multi-billion dollar enterprise decision intelligence business demonstrates the strategic endpoint. Mid-market is structurally underserved by Palantir (minimum engagement size incompatible with $50M–$500M revenue companies). Decision Studio enters from the segment Palantir ignores — the exit path to a strategic acquirer (or an upmarket growth path) is visible from day one.
