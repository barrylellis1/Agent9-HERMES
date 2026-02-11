# Executive Demo Script: Agent9 Situation Awareness & Solutions
**Theme:** "From Signal to Solution across the C-Suite"
**Duration:** 15 Minutes
**Version:** 1.0

## Overview
This demo showcases how Agent9 adapts to different executive personas (CFO, COO, CEO), identifying specific internal and external issues and guiding them from **Situation Awareness** (Detection) to **Deep Analysis** (Diagnosis) to **Solution Finding** (Action).

---

## 🛑 Pre-Demo Context: Data Quality Note
> **Presenter Note:** Before beginning, acknowledge the "Data Quality" Roadmap.
>
> *"While Agent9 currently detects anomalies in real-time, in a full production environment, our **Data Quality Agent** (currently in PRD) would pre-validate these inputs. This ensures we are solving real business problems, not chasing data entry errors. Today, we assume the data is valid."*

---

## Scenario A: The CFO (Analytical) — "The Margin Leak"
**Persona:** Analytical, rigorous, focused on variance decomposition and financial precision.
**Context:** Internal Issue. Profitability is eroding despite revenue growth.

### 1. Situation Awareness (The Alert)
*   **Action:** Select **CFO Context** in the top right.
*   **Action:** Ensure Timeframe is **YTD** (Year-to-Date).
*   **Observation:** The "Sales Deductions" KPI card is **Red**.
    *   *Headline:* "Sales Deductions 15% above plan YTD."
    *   *Presenter:* "The CFO immediately sees the cumulative pain. A 15% variance in deductions is eating our margin."

### 2. Deep Analysis (The Diagnosis)
*   **Action:** Click **[Request Deep Analysis]** on the Sales Deductions card.
*   **Action:** Agent runs KT (Kepner-Tregoe) IS/IS-NOT Analysis.
*   **Action:** **Drill Down:** Change Timeframe to **Q3** (or relevant specific window) to isolate the spike.
*   **Result (IS):**
    *   **Where:** Customer Type `Z1` (Specific Segment).
    *   **When:** Spiked significantly in June/July (The "Summer Spikes").
    *   **Is Not:** Customer Type `Z2` is stable.
*   **Presenter:** "Agent9 isolates the noise. This isn't a broad market issue; it is specifically `Z1` customers during the summer months."

### 3. Solution Finder (The Action)
*   **Action:** Click **[Find Solutions]**.
*   **Council Selection:** Select **"MBB Strategy Council"** (McKinsey, Bain, BCG).
    *   *Note:* This brings in the "Big Three" perspectives.
*   **Debate Highlight:** 
    *   **CFO (Analytical):** Focus on **McKinsey's** input (Governance/Structure).
*   **Recommendation:** "Revise Discount Authority Matrix."
*   **Trade-off Analysis:**
    *   *Option A:* Hard Lock (High Control, High Friction).
    *   *Option B:* Manager Approval Threshold (Balanced).
*   **Presenter:** "The Agent proposes a governance fix to stop the bleeding without killing sales velocity."

---

## Scenario B: The COO (Pragmatic) — "The Supply Chain Choke"
**Persona:** Pragmatic, action-oriented, focused on bottlenecks, owners, and timelines.
**Context:** Internal Operational Issue. Missing shipments despite having raw materials.

### 1. Situation Awareness (The Alert)
*   **Action:** Select **COO Context**.
*   **Action:** Switch Timeframe to **Current Month** (or "Last 30 Days").
*   **Observation:** "Production Throughput" or "Net Revenue" for specific centers is **Red**.
    *   *Headline:* "Profit Center `US10_PCC3S` underperforming by 15%."
    *   *Presenter:* "The COO cares about *now*. The YTD view hides the immediate fire. Switching to 'Current Month' reveals the bottleneck."

### 2. Deep Analysis (The Diagnosis)
*   **Action:** Click **[Request Deep Analysis]** on the Revenue/Throughput card.
*   **Result (IS):**
    *   **Where:** Profit Center `US10_PCC3S`.
    *   **When:** Persistent drag since Jan, but acute now.
    *   **Is Not:** Other Profit Centers (`US10_PCY1L`) are hitting targets.
*   **Interpretation:** "This isolates the issue to a specific facility/line. It's not a demand issue; it's a 'QA Bottleneck' (Story 1)."

### 3. Solution Finder (The Action)
*   **Action:** Click **[Find Solutions]**.
*   **Council Selection:** Select **"MBB Strategy Council"**.
*   **Debate Highlight:** Focus on **Bain's** input (Results Delivery/Operational Excellence).
*   **Recommendation:** "Temporary Shift Restructuring & Outsourcing."
*   **Rationale:** "Immediate capacity relief required while QA process is audited."
*   **Presenter:** "Agent9 suggests a pragmatic, 90-day fix to unblock the line."

---

## Scenario C: The CEO (Visionary) — "The Market Headwind"
**Persona:** Visionary, strategic, focused on external factors, competition, and portfolio health.
**Context:** External/Political Issue. Regional revenue miss.

### 1. Situation Awareness (The Alert)
*   **Action:** Select **CEO Context**.
*   **Action:** Timeframe **YTD**.
*   **Observation:** "Gross Revenue" is **Yellow/Red** in a specific Region (e.g., Euro Zone or a specific Customer Group).
    *   *Presenter:* "The CEO sees a strategic drag. It's not operational; it's market-based."

### 2. Deep Analysis (The Diagnosis)
*   **Action:** Click **[Request Deep Analysis]**.
*   **Context Injection:**
    *   *Prompt:* "Include external market factors for 2025."
*   **Result (IS):**
    *   **Where:** Region X / Customer Group Y.
    *   **External Correlation:** Coincides with new competitor entry or tariff introduction.
    *   **Is Not:** Product quality issue (Returns are low).
*   **Presenter:** "Agent9 confirms our products are fine (low returns), but sales are down. This points to an external competitive or political pressure."

### 3. Solution Finder (The Action)
*   **Action:** Click **[Find Solutions]**.
*   **Council Selection:** Select **"MBB Strategy Council"**.
*   **Debate Highlight:** Focus on **BCG's** input (Growth-Share/Strategy).
*   **Recommendation:** "Strategic Pivot / Lobbying Effort."
*   **Trade-off:**
    *   *Option A:* Price War (Margin Risk).
    *   *Option B:* Value-Add/Bundle Strategy (Longer Timeline).
*   **Presenter:** "For the CEO, the Agent shifts from 'fix it' to 'strategize it', offering high-level portfolio moves."

---

## Summary
1.  **Context-Aware:** The same data yields different alerts for different roles.
2.  **Temporal Intelligence:** Shifting from YTD to Current Month changes the story.
3.  **End-to-End Workflow:** We don't just admire the problem; we solve it with evidence-based recommendations.
