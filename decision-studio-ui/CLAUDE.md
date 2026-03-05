# Decision Studio UI — decision-studio-ui/

## MANDATORY: Never Run npm run dev Directly

```
NEVER:  cd decision-studio-ui && npm run dev
ALWAYS: .\restart_decision_studio_ui.ps1  (from project root, in PowerShell)
```

The restart script handles Supabase, FastAPI (port 8000), and React (port 5173) startup
in the correct order with port cleanup. Running React independently connects to a dead backend.

## Tech Stack

- React 18 + TypeScript + Vite + Tailwind CSS
- React Router 7, Framer Motion, Visx (D3 wrapper), Lucide icons
- **No test suite** — no jest/vitest configured
- npm scripts: `dev`, `build`, `lint`, `preview` (but use restart script for dev)

## Directory Map

```
src/
├── pages/                      — full-page route views
│   ├── DecisionStudio.tsx      — main SA → DA → Solutions workflow
│   ├── ExecutiveBriefing.tsx   — briefing output (print/export view)
│   ├── AdminConsole.tsx        — data product onboarding + connection profiles
│   ├── RegistryExplorer.tsx    — registry maintenance (placeholder UI)
│   ├── PrincipalManagement.tsx — principal CRUD
│   └── Login.tsx
├── components/
│   ├── visualizations/         — DivergingBarChart, TradeOffAnalysis, etc.
│   ├── dashboard/KPITile.tsx   — KPI display tile
│   └── (root)                  — CouncilDebate, VarianceDrawer, SituationCard, etc.
├── hooks/
│   └── useDecisionStudio.ts    — 3-stage debate flow + full SA→DA→Solutions state
├── utils/
│   └── briefingUtils.ts        — impact/cost/risk display logic for Executive Briefing
├── api/
│   ├── client.ts               — axios base client (base URL: http://localhost:8000)
│   └── types.ts                — all TypeScript API response types
└── config/                     — frontend configuration
```

## Key Files

**`hooks/useDecisionStudio.ts`**
Owns the full workflow state: selected principal, situations, DA results, debate output.
The 3-stage debate flow (`hypothesis` → `cross_review` → `synthesis`) is managed here.
Any change to debate sequencing or state flow starts here.

**`utils/briefingUtils.ts`**
Formats `impact_estimate`, `cost`, and `risk` scores into display strings for the briefing.
- `recovery_range` → `"+1.2 to +2.8%"` (if non-zero)
- Fallback: `expected_impact` float → `"High Impact Potential"` / `"Moderate"` / `"Incremental"`
- `cost` float → `"High Effort"` (≥0.7) / `"Moderate Effort"` (≥0.4) / `"Low Effort"`
If scores display incorrectly in the Executive Briefing, check here first.

**`api/types.ts`**
Single source of truth for all TypeScript API response shapes. Must stay in sync with
FastAPI Pydantic response models in `src/agents/models/`. When adding new API fields,
update types here first, then consume in components.

**`api/client.ts`**
Axios base client. Base URL defaults to `http://localhost:8000`. Do not hardcode URLs
in components — import from client.ts.

## State Management

No Redux or Zustand. State is:
- **Workflow state**: owned by `useDecisionStudio` hook, passed via props
- **Session context** (principal, business processes): lifted to `App.tsx`, passed via props
- **Admin Console**: own local state (no shared state needed)

## What Is NOT Built in UI

- KPI Assistant chat panel — API routes exist at `/api/v1/data-product-onboarding/kpi-assistant/` but no UI
- Registry Maintenance panel — placeholder "coming soon"
- Data Governance Admin panel — placeholder "coming soon"
- Offline / scheduled SA triggers — UI only supports manual "Detect Situations" button
