# Phase 1 Backlog – Agent9 Narrative MUI Interface

## Review Workflow (Solopreneur)
- **Prepare**: Draft deliverable and capture decisions inline.
- **Self-Review**: Verify against Agent9 standards, dashboardless goals, and Phase 0 brief.
- **Sign-Off**: Record approval note in this file and move item to "Completed".
- **Retro**: Log lessons or follow-ups after each major epic.

Use the checkboxes below to track progress. Update dates and notes as work advances.

## Epic A – API Extensions for Narrative Workflows
- **Goal**: Expose REST endpoints enabling registry CRUD and workflow narratives without dashboard dependencies.
- **Milestones**:
  1. *Registry CRUD parity* — `/api/v1/registry/*` routes live with provider upsert/delete helpers, OpenAPI documented.
  2. *Workflow triggers* — Situation, Deep Analysis, Solution endpoints wired to orchestrator with status polling.
  3. *Validation suite* — pytest + httpx integration coverage and updated `mui_api_contracts.md` notes.
- [ ] Story A1: Define OpenAPI contracts for registry CRUD (KPI, principal, data product, glossary, business process).
- [ ] Story A2: Implement FastAPI routes with Pydantic v2 models and orchestrator integration.
- [ ] Story A3: Add workflow trigger endpoints (`/workflows/situation`, `/workflows/deep-analysis`, `/workflows/solution`).
- [ ] Story A4: Write integration tests and documentation for new endpoints.
- **Retro Note**: _Pending_

## Epic B – Narrative MUI Shell & Navigation
- **Goal**: Build layout emphasizing situation/deep-analysis/solution journeys with minimal chrome.
- [ ] Story B1: Create shell layout with navigation to `Situations`, `Deep Analysis`, `Solutions`, `Registry`.
- [ ] Story B2: Implement shared components (narrative card, timeline, approval footer).
- [ ] Story B3: Integrate API client layer (React Query hooks) with error handling and loading states.
- [ ] Story B4: Ensure accessibility and responsive behavior.
- **Retro Note**: _Pending_

## Epic C – Registry Admin UI (CRUD)
- **Goal**: Provide CRUD management via MUI tables/dialogs aligned with registry providers.
- [ ] Story C1: Inventory registry schemas and validation rules.
- [ ] Story C2: Build DataGrid view with filters and inline indicators.
- [ ] Story C3: Implement create/edit dialogs with validation and diff preview.
- [ ] Story C4: Add audit sidebar showing recent edits and timestamps.
- **Retro Note**: _Pending_

## Epic D – Situation Narrative Workspace
- **Goal**: Replace dashboards with narrative cards summarizing KPI situations and actions.
- [ ] Story D1: Design Situation card layout (filters, narrative, contextual visualization).
- [ ] Story D2: Implement HITL actions (Explain, Annotate, Request Deep Analysis) with orchestrator calls.
- [ ] Story D3: Add situation timeline showing recognition, deltas, annotations.
- [ ] Story D4: Write unit/UI tests covering narrative rendering and action flows.
- **Retro Note**: _Pending_

## Epic E – Deep Analysis Workspace
- **Goal**: Offer guided analysis requests and narrative results with supporting evidence links.
- [ ] Story E1: Create request builder form (scope, KPIs, hypotheses) with validation.
- [ ] Story E2: Implement progress tracker (stepper with polling status).
- [ ] Story E3: Render narrative results, optional charts, and downloadable evidence.
- [ ] Story E4: Capture feedback loop (request revision, escalate to Solution Finder).
- **Retro Note**: _Pending_

## Epic F – Solution Decision Workspace
- **Goal**: Guide user from problem intake to solution approval without reliance on dashboards.
- [ ] Story F1: Implement intake panel referencing Deep Analysis outputs.
- [ ] Story F2: Build solution comparison matrix with narrative scoring and optional visuals.
- [ ] Story F3: Add approval workflow (Approve, Request Changes, Iterate) with comment log.
- [ ] Story F4: Export narrative report (PDF/Markdown) summarizing decisions.
- **Retro Note**: _Pending_

## Epic G – Quality, Testing, and Documentation
- **Goal**: Ensure stability, auditability, and handoff readiness.
- [ ] Story G1: Establish automated test suite (unit, integration, UI) for new components and APIs.
- [ ] Story G2: Document developer setup, runbooks, and HITL procedures.
- [ ] Story G3: Add monitoring/logging hooks for workflow endpoints.
- [ ] Story G4: Conduct self-retro and finalize Phase 1 close-out summary.
- **Retro Note**: _Pending_

## Sign-Off Log
- 2025-10-15 – Approved Phase 1 backlog scope and workflow. — Barry Ellis

## Parking Lot / Future Enhancements
- [ ] LLM-assisted KPI synonym harvesting during data product onboarding (coordinate DG + DP + LLM agents; capture steward approval flow before registry persistence).
