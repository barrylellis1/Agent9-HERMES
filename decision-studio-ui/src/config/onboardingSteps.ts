/**
 * ONBOARDING_STEPS — single source of truth for the 6-step onboarding wizard.
 *
 * Replaces the two previously-duplicated arrays:
 *   - DAY_CARDS in pages/OnboardingDayView.tsx (title/icon/summary/tips)
 *   - ONBOARDING_DAYS in components/SettingsLayout.tsx (label/route)
 *
 * `key` maps 1:1 to the step keys returned by GET /api/v1/onboarding/progress.
 */

import type { ComponentType } from 'react'
import {
  Building2, Users, Sparkles, UserCheck, Database, CheckCircle2,
} from 'lucide-react'

export interface OnboardingStepDef {
  step: number // 1-6
  key: 'workspace_setup' | 'principals' | 'kpi_library' | 'ownership' | 'connect_data' | 'validate_launch'
  label: string
  to: string // '/settings/onboarding/day-1' etc — keep this exact route pattern
  /** Icon component — render as `<step.icon className="w-6 h-6" />` (kept as a component
   *  reference rather than a rendered ReactNode so this file can stay a plain .ts module). */
  icon: ComponentType<{ className?: string }>
  summary: string
  tips?: string[]
}

export const ONBOARDING_STEPS: OnboardingStepDef[] = [
  {
    step: 1,
    key: 'workspace_setup',
    label: 'Workspace Setup',
    to: '/settings/onboarding/day-1',
    icon: Building2,
    summary: 'Create the client workspace and enter the company profile. This establishes the client_id that all subsequent registry data will be scoped to.',
    tips: [
      'The Client ID (e.g. "valvoline") is set when you create the client above. It cannot be renamed later.',
      'Industry and sub-sector here will be pre-filled in the KPI Intelligence research form on Day 3.',
      'Company Profile data feeds the Market Analysis agent — the more specific, the better the KPI benchmarks.',
    ],
  },
  {
    step: 2,
    key: 'principals',
    label: 'Principal Profiles',
    to: '/settings/onboarding/day-2',
    icon: Users,
    summary: 'Add the C-level and key operational principals who will use the system. Each principal needs a name, role, and email. Decision style and business process assignments can be completed later.',
    tips: [
      'Email is required for PIB briefing delivery. Principals without an email are excluded from briefings.',
      'Decision style (analytical / pragmatic / visionary / decisive) adapts how Solution Finder presents recommendations. It does not have to be set on Day 2.',
      'AI-assisted principal research is coming in Phase 12E — for now, add principals manually.',
    ],
  },
  {
    step: 3,
    key: 'kpi_library',
    label: 'KPI Library',
    to: '/settings/onboarding/day-3',
    icon: Sparkles,
    summary: 'Research and define the KPIs this client cares about. Start with KPI Intelligence to get a benchmark-anchored set from the company\'s public footprint, then fill in any domain-specific KPIs manually.',
    tips: [
      'KPIs committed via KPI Intelligence land with status="template". They show in the registry but are excluded from monitoring until data is connected (Day 5).',
      'The benchmark range from the research is advisory — the client\'s actual thresholds are set separately in the KPI editor.',
      'Aim for 10–20 KPIs for a first deployment. More KPIs = longer assessment runs.',
    ],
  },
  {
    step: 4,
    key: 'ownership',
    label: 'Assign Ownership',
    to: '/settings/onboarding/day-4',
    icon: UserCheck,
    summary: 'Run the AI-guided accountability interview to assign each KPI to a named owner across the leadership team. The interview uses the principals and KPIs from Days 2–3.',
    tips: [
      'The interview infers ownership from business process mappings first, then asks the admin to confirm or reassign gaps.',
      'Target 100% coverage before Day 5 — KPIs without an owner surface in assessments but briefings cannot be routed.',
      'Ownership can be updated at any time after launch via the Assign Ownership tool.',
    ],
  },
  {
    step: 5,
    key: 'connect_data',
    label: 'Connect Data',
    to: '/settings/onboarding/day-5',
    icon: Database,
    summary: 'Connect the client\'s data warehouse and map KPIs to their source tables. This promotes template KPIs to active monitoring status.',
    tips: [
      'Supported backends: BigQuery, Snowflake, SQL Server / Azure SQL, Databricks, PostgreSQL.',
      'Template KPIs (from Day 3) become active once a data product is registered and their sql_query is validated.',
      'Run the SQL validation step in the onboarding wizard before registering — it catches syntax errors against the live warehouse.',
    ],
  },
  {
    step: 6,
    key: 'validate_launch',
    label: 'Validate & Launch',
    to: '/settings/onboarding/day-6',
    icon: CheckCircle2,
    summary: 'Confirm all data connections are healthy, then trigger the first enterprise assessment. Verify that situation cards are generated and briefings route to the right principals.',
    tips: [
      'Connection Health runs a SELECT 1 (or equivalent) against each data product\'s warehouse. All should show "ok" before the first assessment.',
      'The first assessment may be slow — it evaluates every active KPI. Subsequent runs are faster as the SA agent caches results.',
      'After the first successful briefing email, the onboarding is complete. Log out of admin mode and hand off to the Product Owner.',
    ],
  },
]
