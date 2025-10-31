# Phase 0 Discovery Brief – Agent9 MUI Interface

## 1. Purpose
Summarize discovery findings for the upcoming Material UI interface covering Registry CRUD and orchestrated workflows (Situation Awareness, Deep Analysis, Solution Finder). This brief aligns stakeholders on goals, constraints, and next steps prior to Phase 1 execution.

## 2. Stakeholders & Roles
- **Product / UX** (Barry Ellis, UX lead): Define user journeys, wireframes, and visual priorities.
- **Backend / Orchestrator Engineering** (Data Product & Orchestrator owners): Provide API contracts, ensure lifecycle compliance.
- **Compliance / Agent Standards** (Agent9 design custodian): Enforce adherence to `docs/Agent9_Agent_Design_Standards.md` and HITL requirements.
- **QA / Ops** (Decision Studio operators): Validate test strategy, monitoring, and deployment readiness.

## 3. Scope Summary
- Registry CRUD interface spanning KPI, Principal Profiles, Data Products, Business Glossary, Business Processes.
- Workflow-centric experiences for:
  - A9_Situation_Awareness_Agent (situation narratives, KPI deltas, HITL actions).
  - A9_Deep_Analysis_Agent (analysis request lifecycle, narrative reports, actionable recommendations).
  - A9_Solution_Finder_Agent (intake → generation → evaluation → recommendation) with human approvals.
- Shared MUI layout, navigation, and API integration layer focused on situation/deep-analysis/solution journeys rather than generic dashboards.

## 3.1 Dashboardless Vision
- Deliver insights through narrative-first cards, conversational prompts, and workflow steppers instead of persistent metric grids.
- Visualizations remain contextual (e.g., single KPI delta chart) and tied directly to situations, deep analyses, or solutions.
- Each workspace should summarize supporting data via LLM-generated explanations with links to underlying evidence for HITL review.
- Success criteria: users resolve situations and approve solutions without needing traditional dashboard navigation.

## 4. Existing Assets
- **Wireframes**:
  - `docs/wireframes/agents/a9_situation_awareness_agent_wireframe.md`
  - `docs/wireframes/agents/a9_solution_finder_agent_wireframe.md`
- **Backend Reference**: `src/api/main.py` (orchestrator runtime & `/agents/state` endpoint).
- **Design Standards**: `docs/Agent9_Agent_Design_Standards.md`.
- **Current UI Baseline**: `admin-ui/src/pages/Dashboard.jsx`.

## 5. Interview Highlights
### 5.1 Product / UX
- MVP focuses on contextual KPIs with actionable deviations; reuse existing textual wireframes as baseline.
- Expect tabbed or workflow-specific navigation to avoid dashboard overload.
- Emphasize human-in-the-loop escalation, annotations, and audit trails.

### 5.2 Backend / Orchestrator
- FastAPI should expose CRUD endpoints per registry provider with Pydantic schemas.
- Workflow triggers need predictable REST interfaces (e.g., POST `/workflows/deep-analysis/run`).
- Prefer React Query-compatible responses with clear status fields.

### 5.3 Compliance / Standards
- UI must reinforce HITL controls (no auto-escalation without user approval).
- Ensure UI surfaces compliance metadata (timestamps, status, provenance).
- Maintain ConfigDict patterns and align with agent cards for terminology.

## 6. Requirements & Constraints
- **Functional**: CRUD operations, workflow initiation, status polling, annotation capture.
- **Non-Functional**: Auditability, consistent Agent9 naming, responsive layout, testability.
- **Data Sources**: YAML registries in `src/registry/`, orchestrator runtime data via API extensions.
- **Risks**:
  - Missing registry endpoints (needs backend uplift).
  - Potential complexity of multi-step workflows requiring polling or WebSockets.
  - Ensuring consistency with both Decision Studio and future MUI app.

## 7. Open Questions
1. Do we require role-based access controls in Phase 1?
2. Should registry edits support version history or diff previews at launch?
3. Preferred visualization library for KPI charts (MUI charts vs. custom)?
4. How will long-running analyses communicate progress (polling vs. streaming)?

## 8. Phase 1 Prep – Proposed Epics
- **API Extensions**: Registry CRUD + workflow endpoints in FastAPI.
- **Narrative MUI Shell & Navigation**: Layout, routing, shared components that support card-based narratives and workflow steppers.
- **Registry Admin UI**: Data grids, forms, validation, audit log.
- **Situation Narrative Workspace**: Situation-focused cards with contextual visual snippets, explanations, and HITL actions.
- **Deep Analysis Workspace**: Guided analysis request flow, narrative results, optional evidence visualizations.
- **Solution Decision Workspace**: Multi-step recommendation review with comparisons, approvals, and exports.
- **Quality & Documentation**: Testing strategy, runbooks, usage docs.

## 9. Next Actions
1. **Review Brief** – Stakeholders to validate findings and open questions.
2. **Answer Open Questions** – Assign owners for RBAC, visualization choices, and workflow telemetry design.
3. **Backlog Grooming** – Break epics into stories, estimate, and sequence.
4. **Prepare Wireframe Annotations** – Update existing wireframes with interview feedback and new requirements.
5. **Schedule Phase 1 Kickoff** – Align team on timeline and deliverables once backlog is ready.

## 10. Review Plan
- Circulate this brief to stakeholders (Product, UX, Backend, Compliance).
- Collect feedback within 3 business days.
- Incorporate revisions and finalize before Phase 1 kickoff meeting.
