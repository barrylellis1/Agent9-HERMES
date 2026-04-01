# Decision Studio Demo Script — Lubricants Business

**Duration:** 15–18 minutes
**Audience:** Early prospects, trusted colleagues, domain advisors
**Session type:** Feedback / discovery (not a sales pitch)
**Environment:** Production (trydecisionstudio.com)
**Principal:** Sarah Chen, CFO (analytical style)
**Backup pivot:** Rachel Kim, COO (pragmatic style) — if audience is ops-focused

---

## Pre-Demo Checklist

- [ ] Production backend running (Railway) — verify at api endpoint /docs
- [ ] Supabase Cloud has lubricants KPIs seeded (15 KPIs)
- [ ] BigQuery data accessible (lubricants star schema)
- [ ] Browser: dark mode, zoom 90% for full-screen effect
- [ ] **Pre-run the full pipeline** before the demo (see "Pre-Demo: Pipeline Setup" below)
- [ ] Tab 1: Login page (clean starting point for walkthrough)
- [ ] Tab 2: Dashboard with situations loaded (post-scan)
- [ ] Tab 3: DeepFocusView with analysis + solutions complete
- [ ] Tab 4: Executive Briefing (ready for Q&A and approval)
- [ ] Tab 5: Portfolio page (with at least 1 pre-approved solution)
- [ ] Hide tab bar or use separate browser window per stage if presenting on screen share

---

## Act 1: Frame the Session (2 min)

**[Don't open the app yet. Set context and expectations.]**

> "Before I show you anything, I want to set expectations. This is not a polished sales demo. I'm building something and I need your honest reaction — what resonates, what doesn't, what's missing, what would make you ignore this entirely. Your feedback shapes what we build next."

> "Here's the problem I'm trying to solve. It's Monday morning. A CFO has 14 KPIs across revenue, margins, costs, and operations. Somewhere in that data, there's a margin squeeze happening — base oil costs shifted, a product mix changed, maybe a key B2B customer churned. But she won't see it until someone builds a slide deck, schedules a meeting, and walks through 30 pages of variance analysis. By then it's two weeks old."

> "What if the system found the problem, diagnosed the root cause, and brought her a decision-ready briefing — before she even logged in?"

> "That's the thesis. Let me show you where we are, and then I want your honest take."

---

## Act 2: Login & Auto-Scan (1 min)

**[Open the app. Login screen appears.]**

**Talk track:**
> "We're logging in as Sarah Chen, CFO of a lubricants manufacturer. The system already knows her decision style — analytical — and which KPIs matter to her role."

**Actions:**
1. Client is pre-selected: **Lubricants**
2. Click **Sarah Chen** (CFO, blue/analytical badge)
3. Click **Sign In**

**[After login, switch to Tab 2 — Dashboard with situations already loaded.]**

**Talk track:**
> "The system has already scanned all 15 financial KPIs against Sarah's thresholds — revenue, margins, COGS, base oil costs, SG&A. In production, this runs automatically. Sarah would get a notification — she'd never need to log in and click 'scan.'"

**[Situation cards are visible.]**

> "Three situations detected. The system has already prioritized them by severity."

**[Pause. Let them read the cards for 3 seconds.]**

---

## Act 3: Deep Analysis (3 min)

**[Click the most severe situation card, then switch to Tab 3 — DeepFocusView with analysis complete.]**

**Talk track:**
> "Sarah clicks the top priority. The system runs a root cause analysis — no analyst needed. Let me show you what it found."

**[DeepFocusView is fully loaded with results.]**

**Walk through the left panel:**

1. **SCQA Narrative:**
   > "First, the diagnosis is framed as a narrative — Situation, Complication, Question, Answer. This is how McKinsey and BCG structure executive communication. Not charts first — story first."

2. **Is/Is Not Variance Analysis:**
   > "Here's the dimensional breakdown. The system ran an automated Is/Is Not analysis — the same framework consultants use in Kepner-Tregoe problem solving. It identified WHERE the problem is and WHERE it isn't."

   > "For example — the margin decline is concentrated in [read the actual 'where_is' segments]. But [read the 'where_is_not' segments] are healthy. That narrows the investigation immediately."

3. **Market Intelligence** (if present):
   > "The system also pulled market signals — competitor moves, commodity trends, industry shifts. This is context Sarah's team would normally spend days gathering."

**[Pause on the right panel — Action Center.]**

> "Now here's the decision point. The system has a diagnosis. But before generating solutions, it checks with Sarah."

---

## Act 4: Problem Refinement — HITL Gate 1 (3 min)

**[Click "Start Refinement Session" in the right panel.]**

**Talk track:**
> "This is the human-in-the-loop gate. The system doesn't assume it knows enough to solve the problem. It asks Sarah to validate the findings and add context that data alone can't provide."

**[The refinement chat opens. First message from the system appears with suggested responses.]**

> "Notice the suggested responses — Sarah doesn't have to type. She can tap a response or add her own context. The system walks through five topics: validating the hypothesis, defining scope, adding external context, noting constraints, and setting success criteria."

**Demo the interaction:**
1. **Click a suggested response** for hypothesis validation (e.g., "Yes, this aligns with what I'm seeing")
2. **Type a short addition** for scope: "Focus on the retail products division — I know the B2B side is already being addressed by Rachel's team"
3. **Click through** remaining topics using suggested responses (don't linger)

**Talk track while clicking:**
> "Each response refines the problem statement. The system accumulates exclusions, constraints, and context. When Sarah says 'the B2B side is handled,' the system excludes it from solution generation. This prevents redundant work."

**[Chat completes. Persona selector appears.]**

---

## Act 5: Solution Finding — Council Debate (2 min)

**Talk track:**
> "Now the system generates solutions. It uses a multi-perspective approach — three strategic personas analyze the problem independently, then synthesize."

**[Click "Run Recommended Debate" or select a council preset.]**

**[Council Debate animation plays — 3 phases, ~15 seconds.]**

**Talk track during animation:**
> "Phase one: each persona generates independent hypotheses. Phase two: they challenge each other — adversarial review. Phase three: synthesis into a consensus recommendation with trade-offs quantified."

**[Solutions appear. Green "Consensus Reached" badge.]**

> "Three strategic options, ranked. Each with estimated impact, cost, risk, and implementation timeline. The system has a recommendation, but the decision stays with Sarah."

**[Click "View Full Decision Briefing".]**

---

## Act 6: Executive Briefing & Cost of Inaction (2 min)

**[Executive Briefing page loads — full report view.]**

**Talk track:**
> "This is what Sarah receives. A complete decision briefing — the kind that would normally take a team of analysts two weeks to produce. Situation, root cause, market context, three options with trade-offs, and a clear recommendation."

**Walk through quickly:**
1. **Summary section** — one-paragraph overview
2. **Cost of Inaction banner** — scroll to it deliberately

**[Pause on the Cost of Inaction banner.]**

**Talk track:**
> "Before Sarah even looks at solutions, the system shows what happens if she does nothing. This is the Cost of Inaction — projected KPI trajectory at 30 and 90 days with no intervention."

> "If gross margin is projected to drop another 1.2 points in 30 days, that's not abstract — it's [read the estimated revenue impact]. This is what turns 'we should look into this' into 'we need to decide now.'"

3. **Options table** — point out the "REC" badge on the recommended option
4. **Right panel Q&A** — "Sarah can ask questions before deciding"

**Demo Q&A:**
> Click a suggested question: **"What are the biggest risks with Option A?"**

**[Response appears with risk analysis.]**

> "Real-time Q&A grounded in the analysis. No waiting for follow-up meetings."

---

## Act 7: Approval & Value Assurance Tracking (2 min)

**[Select the recommended option. Click "Approve & Track".]**

**Talk track:**
> "Sarah approves. But here's where Decision Studio is fundamentally different from every other tool — approving isn't the end. It's the beginning of accountability."

**[Green success badge appears: "Decision Approved · Value Assurance tracking initiated"]**

> "The system now initiates Value Assurance — automated tracking of whether this decision actually delivers the impact it promised."

**[Click "View Portfolio" link that appears after approval.]**

**[Portfolio page loads — showing the approved solution plus any pre-seeded ones.]**

**Talk track:**
> "This is Sarah's Decision Portfolio. Every decision she's approved is tracked here. The system monitors four things:"

**Walk through the Portfolio Dashboard:**

1. **Summary cards row:**
   > "Total ROI across all validated decisions. How many are validated, partial, or failed. This is the board-ready number."

2. **Solution table rows:**
   > "Each row is a decision Sarah approved. The system tracks its status — 'Measuring' means we're in the observation window, 'Validated' means the expected impact materialized, 'Partial' means it's working but below target, 'Failed' means it didn't deliver."

3. **Attribution column** (if evaluations exist):
   > "This is the key differentiator. The system doesn't just measure whether the KPI improved — it attributes HOW MUCH of the improvement came from Sarah's decision versus market recovery, seasonal effects, or other noise. It uses a Difference-in-Differences method — the same causal inference technique used in academic research and policy evaluation."

4. **Executive Attention banner** (if present):
   > "And when strategic context shifts — say, a competitor makes a move that changes the calculus — the system flags it. 'Executive attention required' means the original assumptions may no longer hold."

**Talk track (the punchline):**
> "Most organizations can tell you what decisions were made. Almost none can tell you which decisions actually worked. Forrester found that fewer than 15% of enterprises can prove ROI on their AI investments. This portfolio is how you become one of the 15%."

---

## Act 8: Feedback Conversation (5–10 min)

**[Stay on the Portfolio page. Shift from showing to listening.]**

> "That's the full cycle. Now I want your honest reaction. I have some specific questions, but first — what stood out to you? What felt useful, and what felt like noise?"

**[Let them talk first. Don't defend. Take notes.]**

### Feedback Questions — Ordered by Priority

Ask these in order. Stop when you run out of time or when conversation flows naturally. Don't rush through all of them.

**1. Problem validation:**
> "Does this match a real pain point in your world? Is the 2-to-6-week analysis cycle something you actually experience, or is it different?"

**2. Entry point / delivery model:**
> "We showed you logging into a dashboard. But our thesis is that executives shouldn't have to log in — the system should push a briefing to you. If this showed up as an email or Slack message with a summary and a 'Review Briefing' link, would you open it? What would make you ignore it?"

**3. Trust in AI diagnosis:**
> "When the system showed the root cause analysis — the Is/Is Not breakdown — did you trust it? What would need to be different for you to trust it enough to act on it?"

**4. Human-in-the-loop refinement:**
> "The chat where the system asked Sarah to validate findings and add context — is that the right interaction? Would you actually do that, or would you skip it? Would you prefer structured multiple-choice options instead of a chat?"

**5. Solution generation:**
> "Three strategic options from AI personas — is that useful or gimmicky? Would you want more options? Fewer? Would you want to see who generated each recommendation?"

**6. Cost of Inaction:**
> "The 'what happens if you do nothing' projection — does that help or does it feel manipulative? Is that something you'd show to your board?"

**7. Value Assurance / accountability:**
> "The portfolio tracking — proving whether a decision actually worked — is that something you'd use? Would you present that to your board? Who else in your organization would care about this?"

**8. Format and presentation:**
> "Is a briefing document the right output? Would you rather have a 3-minute audio summary you could listen to on the way to a meeting? A visual mind map? A Slack summary with the option to dig deeper?"

**9. What's missing:**
> "What's the first thing you'd want to see that we didn't show?"

**10. Would you use it:**
> "If this existed today, connected to your data — would you use it? What would stop you?"

### How to Handle Common Feedback

| Feedback | What it means | Action |
|----------|--------------|--------|
| "This is cool but my team already does this" | They don't see the speed/cost advantage yet | Ask: "How long does it take today? What does that cost?" |
| "I wouldn't trust AI for this" | Trust barrier — needs explainability | Ask: "What would make you trust it? Human review? Source attribution? Audit trail?" |
| "My CFO would never log into another dashboard" | They agree with your push thesis | Validate: "Exactly — that's why we're building toward push notifications. Would email work?" |
| "The chat feels like too much work" | Structured options > free-text for execs | Note it. This directly informs ProblemRefinementChat redesign |
| "I need to see this with MY data" | Strong buying signal | Offer a technical follow-up session |
| "The portfolio is the most interesting part" | VA is the differentiator — invest here | Ask: "Would you present this to your board? What would the board need to see?" |

### Close

> "Thank you — this is incredibly valuable. I'd love to follow up in [2 weeks] after I've incorporated your feedback. And if you know anyone else who deals with this problem and would give honest feedback, I'd appreciate an introduction."

**[Don't pitch. Don't sell. End on gratitude and a follow-up commitment.]**

---

## Pre-Demo: Pipeline Setup (30 min before)

The demo uses pre-loaded tabs rather than live execution. This eliminates the 3-4 minute wait for solution generation and protects against any API timeouts during the presentation.

### Step 1: Run the full pipeline (15 min)
1. Open production app, login as Sarah Chen / Lubricants
2. Let auto-scan complete — note which situations appear
3. Click the best situation card (ideally Gross Margin or Base Oil Cost)
4. Run Deep Analysis — wait for full results
5. Start Refinement Session — click through suggested responses quickly
6. Run Recommended Debate — wait for solutions (this is the slow step, ~3.5 min)
7. Click "View Full Decision Briefing"
8. On the Executive Briefing, approve a solution → note the Portfolio link works

### Step 2: Optionally run a second situation
- Repeat for a different KPI so the Portfolio has 2 tracked decisions
- Makes the Portfolio feel lived-in ("this is what it looks like after a few weeks")

### Step 3: Set up demo tabs (5 min)
Open 5 tabs in the same browser (all share localStorage/session state):

| Tab | Page | State | Used in |
|-----|------|-------|---------|
| 1 | Login page | Fresh, no principal selected | Act 1-2 |
| 2 | Dashboard | Post-scan, situations visible | Act 2 (switch to after login) |
| 3 | DeepFocusView | Analysis + solutions complete | Acts 3-5 |
| 4 | Executive Briefing | Full briefing, not yet approved | Acts 6-7 |
| 5 | Portfolio | Shows pre-approved solution(s) | Act 7 |

### Demo flow with tabs
- **Act 1:** Talk track only (no app)
- **Act 2:** Start on Tab 1 (Login), click Sarah Chen, sign in → immediately switch to **Tab 2** (Dashboard already loaded). Say: "The system has already scanned — let me show you what it found."
- **Act 3-5:** Click a situation card on Tab 2 → switch to **Tab 3** (DeepFocusView pre-loaded). Walk through analysis, refinement results, solutions. No waiting.
- **Act 6:** Click "View Full Decision Briefing" → switch to **Tab 4**. Walk through briefing, Cost of Inaction, Q&A.
- **Act 7:** Approve on Tab 4 → switch to **Tab 5** (Portfolio). Portfolio already has prior decisions.

**Key:** The tab switches feel natural because you're "clicking through" the flow. The audience sees a smooth progression, not loading spinners.

### If you want to show one step live
The safest step to run live is **Act 2 (auto-scan)** — it takes 10-15 seconds, gives a satisfying "watching it work" moment, and rarely fails. Keep Tabs 3-5 pre-loaded as fallback for everything after.

---

## Contingency Plans

### If pre-run tabs go stale (page refresh / session timeout)
- Tabs share localStorage — if one tab refreshes, the session state persists
- If a tab loses state, switch to the next pre-loaded tab and skip that step
- Worst case: you have the Executive Briefing as a permalink that always works

### If you choose to run the scan live and it returns no situations
The BigQuery data has engineered anomalies, so this shouldn't happen. If it does:
- Switch timeframe from "Year to Date" to "Current Month"
- Or switch principal to Rachel Kim (COO) — different KPI thresholds may trigger

### If you choose to run the scan live and it's slow (>30 seconds)
- Talk through the auto-scan concept: "In production, this runs on a schedule. Sarah would receive a notification, not wait for a scan."
- If it exceeds 60s, switch to your pre-loaded Tab 2

### If the audience is operations-focused (not finance)
- Login as **Rachel Kim, COO** instead
- Emphasize: base oil procurement costs, distribution efficiency, service center operations
- The system adapts language and priorities to her pragmatic decision style

### If the Portfolio page is empty
- This happens if no solutions have been approved in previous sessions
- Narrate forward: "As decisions are approved, they appear here. Over time, this becomes the CFO's accountability dashboard — total ROI, attribution, strategy alignment."
- Point to the empty state message: "Solutions appear here after HITL approval"
- Consider this a cue to circle back: "Let me approve this solution now and show you"

### If asked "How does attribution work?"
> "The system uses Difference-in-Differences — a causal inference method. It compares the KPI trajectory in the affected segment against a control group of healthy segments. This separates the impact of your decision from market recovery, seasonality, and other noise. It's the same methodology used in clinical trials and economic policy evaluation."

### If asked "Can it connect to our data?"
> "Yes. Decision Studio connects to BigQuery, PostgreSQL, DuckDB, and any SQL-compatible source. The onboarding process maps your schema to KPIs in about an hour."

### If asked about pricing
> "We're in early access. Let's schedule a deeper technical session to scope your use case and data sources."

---

## Key Numbers to Have Ready

| Metric | Value | Source |
|--------|-------|--------|
| Lubricants KPIs monitored | 15 | Seeded in Supabase |
| Typical anomaly detection | Seconds | SA Agent real-time scan |
| Root cause analysis | 30–60 seconds | DA Agent + BigQuery |
| Solution generation | 30–45 seconds | SF Agent (3 parallel LLM calls + synthesis) |
| Traditional equivalent cycle | 2–6 weeks | Industry benchmark |
| Analyst cost per issue | $50K–$150K | Management consulting rates |
| Company profile | $3.2B lubricants manufacturer | Demo context |

---

## Post-Demo Follow-Up

**Within 24 hours:**
1. Send a thank-you with 2-3 bullet summary of their key feedback points (shows you listened)
2. Share the Executive Briefing URL (it's a permalink) — "here's what we walked through"
3. If they expressed interest in their own data: propose a 30-min technical scoping call

**Within 1 week:**
4. Log feedback in a structured tracker (see Feedback Tracking Template below)
5. Identify patterns across multiple sessions — what's consistent vs. one-off
6. Prioritize build/polish based on feedback frequency and intensity

**After 3-5 sessions:**
7. Synthesize findings — what validated your thesis, what surprised you, what needs to change
8. Update the demo script based on what resonated most

### Feedback Tracking Template

For each session, capture:

```
Date:
Participant:
Role / Title:
Industry:
Key Quotes: (verbatim — most valuable data)
  -
  -
Problem Validation: (1-5, does the pain resonate?)
Trust Level: (1-5, would they act on AI output?)
Entry Point Preference: (dashboard / email / slack / other)
Refinement Chat Reaction: (engaged / would skip / wants structured options)
VA/Portfolio Reaction: (interested / indifferent / "this is the product")
Top Feature Request:
Would They Use It: (yes / yes with caveats / no)
Follow-Up Action:
```
