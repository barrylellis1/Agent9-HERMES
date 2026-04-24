# Decision Studio — Enterprise Security FAQ

**Audience:** IT Security, CISO, General Counsel, procurement teams
**Last updated:** April 2026

---

## The Short Answer

Decision Studio's AI analysis works on **aggregated business intelligence, not raw transaction data.** Your underlying records never leave your warehouse. What the AI does receive is a structured analytical context — KPI movements, dimensional segment breakdowns, problem framing, and business context — assembled from your governed KPI views. This is detailed business intelligence, and we treat it that way.

We provide four deployment options, from standard cloud API to fully air-gapped on-premise, depending on your data residency and regulatory requirements.

---

## Five Questions We Always Get

### 1. "Does Anthropic (or any AI provider) train on our data?"

**No.**

The Anthropic API operates under a zero-data-retention policy by default. Your prompts and responses are not used to train models, are not retained after the response is returned, and are not accessible to Anthropic staff for model improvement purposes.

This is in Anthropic's API Terms of Service and available as a written Data Processing Addendum (DPA) for enterprise contracts. For regulated industries, Anthropic offers a BAA (Business Associate Agreement) covering HIPAA obligations.

**If you need everything contractually bound within your own environment:** We support Azure OpenAI, which processes all requests within your own Azure subscription — the prompt never leaves your cloud tenant.

---

### 2. "What data actually gets sent to the LLM?"

**Aggregated analytical intelligence — not raw records, but more than a summary.**

We want to be precise here, because this matters to a security review.

**What does NOT go to the LLM:**
- Individual transaction records, GL line items, or journal entries
- Customer, counterparty, or employee identities
- Raw SQL query results
- Any data below the KPI aggregation level defined by your own database views

**What DOES go to the LLM in a Solution Finding session:**

```
Business context:   Industry, division, reporting period, principal roles
KPI analysis:       KPI name, current value, percent change vs. comparison period
IS/IS NOT table:    Segment names, values, change direction, rankings
                    (e.g. "Base Oil & Additives, North America: -19.5% YoY — primary driver")
SCQA narrative:     Structured problem statement assembled from the dimensional analysis
Market context:     External market signals from public web sources (Perplexity search)
Persona analyses:   Three analytical assessments (CFO lens, COO lens, Strategy lens)
Synthesis prompt:   "Given the above, generate recommended courses of action"
```

This is detailed, identifiable business intelligence. It is equivalent to what a senior analyst would present in a board pack — segment-level performance data, directional trends, and a structured problem statement. It does not contain individual records, but it does contain enough context to understand the business situation.

A security review should evaluate this on that basis: **structured business intelligence under aggregation, processed by a third-party AI API under contractual zero-retention terms.**

---

### 3. "Could this data be captured in transit?"

**Network interception: No.**

All communication between Decision Studio's backend and the LLM API uses HTTPS with TLS 1.3. Data in flight is encrypted end-to-end. A third party monitoring network traffic cannot read the payload — this is the same protection used by online banking, Salesforce, and Workday.

**At the API endpoint: This is the substantive question.**

The LLM provider's infrastructure receives and processes the full prompt. Under Anthropic's API terms, the prompt is not retained after the response is returned. But during processing, it passes through Anthropic's systems. You are trusting Anthropic's security posture and contractual commitments — the same trust model as any enterprise cloud SaaS.

**API key compromise:**

If a Decision Studio API key were exposed, an attacker could send or intercept LLM calls. This is mitigated by key rotation, environment-scoped credentials, and the LLM prompt audit log (see Audit section). Decision Studio never exposes API keys to the browser — all LLM calls originate server-side.

**Honest risk summary:**

| Threat | Real risk | Mitigation |
|--------|-----------|------------|
| Network interception | Negligible | TLS 1.3 in transit |
| Anthropic retaining data | Low | Zero-retention API terms + DPA |
| Anthropic infrastructure breach | Low — same risk as any cloud SaaS | Azure OpenAI option eliminates this |
| API key compromise | Medium | Server-side only, key rotation, audit log |
| Regulatory non-compliance (FINRA, HIPAA, FCA) | High without controls | Azure OpenAI or on-premise LLM |

---

### 4. "What if the AI recommends something wrong?"

**Every recommendation requires a named human to approve it before anything happens.**

Decision Studio is not an autonomous agent. The Solution Finder generates options and structured reasoning. A named principal — your CFO, COO, or relevant executive — reviews the full recommendation, including the AI's reasoning chain, supporting data, trade-off analysis, and risk flags — and explicitly approves or rejects it before it enters the action tracking pipeline.

No recommendation is acted upon without human sign-off. The HITL (Human-in-the-Loop) gate is not optional and cannot be bypassed in the workflow.

The full AI reasoning chain is visible in the Council Debate view — every prompt sent to the LLM and every response received is logged and displayed. There is no black box. The audit log is exportable for compliance review.

---

### 5. "We can't send business intelligence to a third-party AI API."

**We have a path for every level of requirement.**

**Option A — Anthropic API (standard)**
Default deployment. Zero-retention policy. DPA and BAA available. Suitable for most enterprise customers including those with general data protection requirements.

**Option B — Azure OpenAI (customer's Azure tenant)**
For organisations where no business data can leave their cloud boundary — regulated financial services, pharmaceutical companies, PE-backed firms with covenant restrictions. Decision Studio routes all LLM calls to the customer's own Azure OpenAI deployment. The analytical intelligence never leaves their Azure subscription. Covered under their existing Microsoft enterprise agreement.

Configuration change at deployment — not a separate product or professional services engagement.

**Option C — On-premise LLM (Ollama)**
For no-cloud mandates — defence contractors, certain banks, air-gapped environments. Decision Studio runs a local LLM within the customer's network. No data leaves the building. Trade-off: analytical quality is meaningfully lower than GPT-4o or Claude. Evaluated case-by-case.

**Option D — Prompt anonymization (future capability)**
For customers who want cloud LLM quality but need to minimise identifiability: company name and KPI display names are replaced with internal codes before the prompt is assembled (`CLIENT_A`, `KPI_003`). The LLM performs the same analytical reasoning without knowing whose data it is. Modest quality trade-off due to loss of domain context. Available as a configurable option in a future release.

---

## Data Flow Diagram

```
Your Data Warehouse (Snowflake / BigQuery / Postgres / SQL Server)
    │
    │  SQL query (via MCP or direct SDK — credentials never leave backend)
    ▼
Decision Studio Backend (Railway / your cloud)
    │
    │  Aggregate SQL results → IS/IS NOT table
    │  Compute percent changes, segment rankings
    │  Assemble SCQA narrative + business context
    │
    │  ← RAW RECORDS STOP HERE — nothing below this line
    ▼
Structured analytical intelligence
(segment-level KPI data, problem framing, business context)
    │
    │  HTTPS / TLS 1.3
    ▼
    ├── Option A: Anthropic API (zero-retention, DPA)
    ├── Option B: Azure OpenAI (your Azure tenant — data stays in your cloud)
    └── Option C: On-premise LLM (your network — no external call)
    │
    │  Structured recommendation + reasoning
    ▼
Decision Studio UI
    │
    │  Principal reviews full reasoning chain
    │  HITL approval required before any action
    ▼
Value Assurance pipeline (outcome tracking — all within your systems)
```

---

## Compliance Posture

| Requirement | Decision Studio position |
|-------------|-------------------------|
| GDPR | No PII in LLM prompts. Analytics at KPI/segment level. DPA available for Anthropic. |
| SOC 2 Type II | Backend on Railway (SOC 2 certified). Supabase (SOC 2 certified). Certificates available on request. |
| HIPAA | Anthropic BAA available. Azure OpenAI option fully HIPAA-eligible within customer's tenant. |
| FCA / SEC / MiFID II | Azure OpenAI keeps all data within regulated environment. On-premise option for stricter mandates. |
| Data residency | Anthropic: US-based by default, EU available. Azure OpenAI: customer selects region. On-premise: customer's own infrastructure. |
| FINRA record retention | LLM prompt audit log is exportable and timestamped. HITL approval trail is immutable. |

---

## Audit and Transparency

- **Full prompt log:** Every message sent to and received from the LLM is logged server-side and visible in the Council Debate UI. Exportable as JSON for security or compliance review.
- **HITL audit trail:** Every principal approval and rejection is recorded with timestamp, principal ID, and decision rationale. Immutable — cannot be edited after the fact.
- **Usage log:** Every assessment run, solution session, and NL query is recorded in the usage events table with timestamps and client ID. Available to platform admins on request.
- **No browser-side LLM calls:** All AI calls originate from the backend server. API keys are never exposed to the client.

---

## Questions Not Covered Here

Contact us for:
- Penetration test results / vulnerability disclosure policy
- Vendor security questionnaire completion (SIG Lite, CAIQ, VSA, etc.)
- Custom DPA or BAA negotiations
- Azure OpenAI deployment scoping
- On-premise LLM evaluation
