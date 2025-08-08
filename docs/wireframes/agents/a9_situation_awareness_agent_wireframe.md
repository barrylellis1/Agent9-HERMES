# A9_Situation_Awareness_Agent – Decision Studio Wireframe (MVP)

---

## 1. Overview
The Situation Awareness Agent proactively delivers actionable business insights to principals, eliminating the need for static dashboards. It orchestrates KPI monitoring, situation (anomaly/trend/threshold) detection, and structured reporting. All deep analysis (risk, opportunity, stakeholder, impact, recommendations) is delegated to specialized agents and not surfaced by this agent in MVP.

> **Compliance:** This wireframe and UI strictly follow the Agent9 Agent Design Standards and MVP PRD. See docs/Agent9_Agent_Design_Standards.md and the agent card for boundaries.

---

## 2. Decision Studio Card Layout (Simplified MVP)

```
+---------------------------------------------------------------+
| [Situation Awareness]                                         |
+---------------------------------------------------------------+
| Filters:                                                     |
| - Principal Context: [Name/Role]                             |
| - Geography: [Region/Country]                                |
| - Product Group: [Product/Line]                              |
| - Time Period: [Month/Quarter/Year]                          |
+---------------------------------------------------------------+
| KPI: [KPI Name]                                               |
|                                                               |
|   [Bar Chart: Current vs. Expected]                           |
|   ┌────────────┬────────────┐                                 |
|   │ $1.2M      │ $1.35M     │                                 |
|   │ ███████    │ █████████  │                                 |
|   │ Current    │ Expected   │                                 |
|                                                               |
| Delta: [Difference] [Trend Arrow/Indicator]                   |
| Status: [New/Existing]                                        |
| Recognized: [YYYY-MM-DD HH:MM]                                |
| Deep Analysis Requested: [Yes/No]                             |
+---------------------------------------------------------------+
| [Explain This]   [Annotate]   [Request Deep Analysis]         |
+---------------------------------------------------------------+
```

- **Filters:** Contextual filters applied to the analysis, including Principal, Geography, Product Group, and Time Period.
- **KPI Name:** e.g., Revenue, Churn Rate, etc.
- **Visualization:** Simple bar chart comparing Current vs. Expected KPI values, both bars sharing the same x, y axis for direct comparison.
- **Current/Expected:** Numeric values for current and plan/target
- **Delta:** Difference, color-coded, with up/down arrow
- **Status:** Whether this situation is newly recognized or ongoing
- **Recognized:** Timestamp when the situation was first detected
- **Deep Analysis Requested:** Indicates if a deeper investigation has been initiated (delegated to a specialized agent; not performed by this agent)
- **Explain This:** LLM-powered plain-language explanation
- **Annotate:** User comments/notes
- **Request Deep Analysis:** HITL (Human-in-the-Loop) action to initiate a deeper investigation by a specialized agent (not by this card/agent)

This card is the first swipeable card in the Decision Studio and surfaces the most relevant KPI deviation or situation for immediate awareness. The visualization is intentionally simple and actionable for MVP.

## Data-Driven Situation Detection Workflow

The Situation Awareness Agent detects actual situations using the following workflow:

1. **Load Data Sources:**
   - Uses the Data Product Agent to load relevant data files (e.g., `kpis.csv`) based on principal, business process, and KPI context.
   - Data source locations and metadata are resolved via the data registry (`data_sources.csv`).
2. **Read and Parse Data:**
   - Reads CSVs using a shared utility (e.g., `load_csv_file`).
   - Parses data into structured rows (dicts or Pydantic models).
3. **Filter for Relevant Context:**
   - Filters data for the principal's scope (e.g., geography, product group, KPI).
   - Translates business filters to technical codes via the Data Governance Agent if needed.
4. **Compare Actuals vs. Expected:**
   - Compares actual KPI values (current period) to expected/target values (previous period, forecast, or benchmark).
5. **Detect Deviations:**
   - Computes the delta (difference) and checks against business thresholds.
   - Flags significant deviations as "situations" for further action.
6. **Create or Update SituationRecord:**
   - For each detected situation, creates a `SituationRecord` with all context and computed fields.
   - Persists the record for traceability and HITL review.

### Example Table

| Step                | Mechanism/Source                |
|---------------------|---------------------------------|
| Load Data           | Data Product Agent, `load_csv_file` |
| Parse/Filter        | Python dicts or Pydantic models |
| Compare Actual/Exp. | Business logic, previous/target |
| Detect Deviation    | Threshold logic                 |
| Create Situation    | `SituationRecord` model         |

This workflow ensures that only significant, governed, and traceable KPI deviations are surfaced as actionable situations.

### Design Notes & Future-Proofing

1. **Data Source Locations**
   - Current: Data sources (e.g., `data_sources.csv`, `kpis.csv`) are specifically set up for Agent9 feature development and testing.
   - Future: These will be replaced by MCP-enabled data source tools. File paths/configs should remain flexible and not hardcoded.
2. **Thresholds & Expected Value Logic**
   - Current: Business thresholds and expected value logic are not fixed; they could be dynamically set by standards in Data Product or Data Governance policy.
   - Future: These may be set at startup or via policy/configuration. Agent logic should accept these as parameters or configs.
3. **Governance Checks**
   - Every time a data source is loaded, the Data Governance Agent should be consulted for context translation, as sources may change.
4. **SituationRecord Persistence**
   - Situation persistence is assumed implemented. Ensure mechanisms are robust, auditable, and documented.
5. **Test Datasets**
   - Datasets with intentional 'easter eggs' exist for validation and regression testing.

These notes ensure the design remains flexible, dynamic, and ready for future extensibility with strong governance integration.
## Human-in-the-Loop (HITL) Stopping Point

After the Situation Awareness Agent creates and persists a new situation, the system presents a HITL prompt to the human user (e.g., principal, analyst, operator). The prompt summarizes the situation and offers next actions:
- **Request Deep Analysis**
- **Acknowledge/Annotate**
- **Dismiss/Defer**

No automated downstream agent action (such as triggering the Deep Analysis Agent) is taken until the human explicitly requests it. This ensures the MVP workflow is user-driven, auditable, and avoids unnecessary escalations.

---

## Future Considerations (Post-MVP)

The following topics are **out of scope for MVP** but are documented here for future enhancement and planning:

- **Multi-agent workflows:** Support for atomic updates, locking, and concurrent access to situation records by multiple agents.
- **Database persistence:** Migrating from CSV to a database (e.g., SQLite/Postgres) for scalability and reliability.
- **Data retention and privacy:** Implementing retention policies, archival, and privacy controls for situation history.
- **Advanced notification:** Configurable triggers, channels (email, Slack, Teams), and escalation paths for situation updates.
- **Status log format:** Enforcing strict JSON or structured format for `status_log`.
- **Edge case/concurrency testing:** Simulating corrupted CSVs, duplicate situations, time zone issues, and concurrent updates.
- **Extensible schema:** Adding fields for resolution notes, escalation, or more complex situation types.
- **Security and access control:** File encryption, access restrictions, and audit logging for sensitive data.
- **Complex situation types:** Supporting more advanced or hierarchical situation models as requirements evolve.

---

## Modification History

- **2025-06-07:** Updated for MVP agent refactor. Removed all risk, opportunity, stakeholder, impact, and recommendation UI elements and clarified that these are delegated to specialized agents. UI, workflow, and documentation now strictly reflect KPI monitoring, anomaly/trend/threshold detection, and structured reporting only. Added compliance note referencing Agent9 Agent Design Standards and MVP PRD.
- **2025-05-13:** Refactored persistent situation tracking utilities. The `SituationRecord` model and CSV utilities were moved to a new shared module (`situation_tracking_utils.py`) for orchestrator-wide and agent-wide use. This maintains strict Pydantic validation and improves modularity. All agents and the orchestrator now import these utilities from the new module. No changes to data model or validation logic.

---

## 3. Key Features
- **Cross-Agent Context:** The Deep Analysis Agent will use the shared situation tracking utility for persistent context. The `situation_id` (hashed, unique) is the canonical reference for all situations and should be included in all agent-to-agent communication regarding situations. This enables traceability, updates, and annotation across agents.
- **Proactive Insights:** No static dashboard; agent surfaces issues as they arise.
- **Context Awareness:** Filters and highlights situations by principal's control, concern, or influence.
- **Visualization:** Simple bar chart (Current vs. Expected KPI). No risk/opportunity/stakeholder/impact visuals in MVP.
- **Explainability:** "Explain This" button for plain-language output.
- **Annotation:** User can add notes or comments for collaboration or audit.
- **Audit Log:** Timeline of all surfaced situations and actions taken.
- **Progressive Disclosure:** Summary view with option to expand for more detail.

---

## 4. Communication Channels
- **Scheduled Email:** Regular summary to principal (daily/weekly) of situations needing attention.
- **In-App Notification:** Alerts for urgent or high-impact situations.

---

## 5. Navigation/UX Elements
- **Swipeable Card:** First card in the Decision Studio flow (Situation → Deep Analysis → ...)
- **Context Indicator:** Always visible (shows whose perspective, what scope)
- **Expand/Collapse:** For detailed view
- **Help/Info:** Tooltips or info icons for each section

---

## 6. Future Enhancements
- **Value/Innovation Summary:** Placeholder for future quantification of value realized or missed.
- **Integration:** Links to related agent cards (e.g., Deep Analysis, Solution Finder)

---

*This wireframe is intended as a Decision Studio-aligned UI/UX blueprint for the Situation Awareness Agent. Visual design and implementation may evolve as requirements mature.*
