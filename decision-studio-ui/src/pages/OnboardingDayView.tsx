/**
 * OnboardingDayView — System Admin Mode Day-by-Day Content (Mode 1)
 *
 * Routes:
 *   /settings/onboarding/day-1  — Workspace Setup (Company Profile + client creation)
 *   /settings/onboarding/day-2  — Principal Profiles (registry editor)
 *   /settings/onboarding/day-3  — KPI Library (KPI Intelligence + registry editor)
 *   /settings/onboarding/day-4  — Assign Ownership (interview tool)
 *   /settings/onboarding/day-5  — Connect Data (data product onboarding + connection profiles)
 *   /settings/onboarding/day-6  — Validate & Launch (connection health + assessment trigger)
 */

import { Link, useParams } from 'react-router-dom'
import {
  ArrowRight, Building2, Users, Sparkles, UserCheck,
  Database, CheckCircle2, ChevronRight,
} from 'lucide-react'
import { SettingsLayout } from '../components/SettingsLayout'
import { getSettingsClientId } from '../utils/settingsMode'

// ─────────────────────────────────────────────────
// Day content card
// ─────────────────────────────────────────────────

interface DayCard {
  day: number
  title: string
  icon: React.ReactNode
  summary: string
  actions: { label: string; to: string; primary?: boolean; note?: string }[]
  tips: string[]
}

const DAY_CARDS: DayCard[] = [
  {
    day: 1,
    title: 'Workspace Setup',
    icon: <Building2 className="w-6 h-6" />,
    summary: 'Create the client workspace and enter the company profile. This establishes the client_id that all subsequent registry data will be scoped to.',
    actions: [
      { label: 'Edit Company Profile', to: '/settings/company-profile', primary: true },
    ],
    tips: [
      'The Client ID (e.g. "valvoline") is set when you create the client above. It cannot be renamed later.',
      'Industry and sub-sector here will be pre-filled in the KPI Intelligence research form on Day 3.',
      'Company Profile data feeds the Market Analysis agent — the more specific, the better the KPI benchmarks.',
    ],
  },
  {
    day: 2,
    title: 'Principal Profiles',
    icon: <Users className="w-6 h-6" />,
    summary: 'Add the C-level and key operational principals who will use the system. Each principal needs a name, role, and email. Decision style and business process assignments can be completed later.',
    actions: [
      { label: 'Manage Principals', to: '/settings?section=principals', primary: true },
    ],
    tips: [
      'Email is required for PIB briefing delivery. Principals without an email are excluded from briefings.',
      'Decision style (analytical / pragmatic / visionary / decisive) adapts how Solution Finder presents recommendations. It does not have to be set on Day 2.',
      'AI-assisted principal research is coming in Phase 12E — for now, add principals manually.',
    ],
  },
  {
    day: 3,
    title: 'KPI Library',
    icon: <Sparkles className="w-6 h-6" />,
    summary: 'Research and define the KPIs this client cares about. Start with KPI Intelligence to get a benchmark-anchored set from the company\'s public footprint, then fill in any domain-specific KPIs manually.',
    actions: [
      { label: 'KPI Intelligence (AI Research)', to: '/settings/kpi-intelligence', primary: true },
      { label: 'Manual KPI Editor', to: '/settings?section=kpis', note: 'For KPIs not in the research output' },
    ],
    tips: [
      'KPIs committed via KPI Intelligence land with status="template". They show in the registry but are excluded from monitoring until data is connected (Day 5).',
      'The benchmark range from the research is advisory — the client\'s actual thresholds are set separately in the KPI editor.',
      'Aim for 10–20 KPIs for a first deployment. More KPIs = longer assessment runs.',
    ],
  },
  {
    day: 4,
    title: 'Assign Ownership',
    icon: <UserCheck className="w-6 h-6" />,
    summary: 'Run the AI-guided accountability interview to assign each KPI to a named owner across the leadership team. The interview uses the principals and KPIs from Days 2–3.',
    actions: [
      { label: 'Start Accountability Interview', to: '/settings?section=ownership-interview', primary: true },
      { label: 'View Accountability Records', to: '/settings?section=accountability' },
    ],
    tips: [
      'The interview infers ownership from business process mappings first, then asks the admin to confirm or reassign gaps.',
      'Target 100% coverage before Day 5 — KPIs without an owner surface in assessments but briefings cannot be routed.',
      'Ownership can be updated at any time after launch via the Assign Ownership tool.',
    ],
  },
  {
    day: 5,
    title: 'Connect Data',
    icon: <Database className="w-6 h-6" />,
    summary: 'Connect the client\'s data warehouse and map KPIs to their source tables. This promotes template KPIs to active monitoring status.',
    actions: [
      { label: 'Data Product Onboarding', to: '/settings/onboarding', primary: true },
      { label: 'Connection Profiles', to: '/settings?section=connection-health', note: 'Manage warehouse credentials' },
    ],
    tips: [
      'Supported backends: BigQuery, Snowflake, SQL Server / Azure SQL, Databricks, PostgreSQL.',
      'Template KPIs (from Day 3) become active once a data product is registered and their sql_query is validated.',
      'Run the SQL validation step in the onboarding wizard before registering — it catches syntax errors against the live warehouse.',
    ],
  },
  {
    day: 6,
    title: 'Validate & Launch',
    icon: <CheckCircle2 className="w-6 h-6" />,
    summary: 'Confirm all data connections are healthy, then trigger the first enterprise assessment. Verify that situation cards are generated and briefings route to the right principals.',
    actions: [
      { label: 'Connection Health Check', to: '/settings?section=connection-health', primary: true },
      { label: 'Go to Dashboard', to: '/dashboard', note: 'Trigger first Detect Situations run' },
    ],
    tips: [
      'Connection Health runs a SELECT 1 (or equivalent) against each data product\'s warehouse. All should show "ok" before the first assessment.',
      'The first assessment may be slow — it evaluates every active KPI. Subsequent runs are faster as the SA agent caches results.',
      'After the first successful briefing email, the onboarding is complete. Log out of admin mode and hand off to the Product Owner.',
    ],
  },
]

// ─────────────────────────────────────────────────
// Component
// ─────────────────────────────────────────────────

export function OnboardingDayView() {
  const { day: dayParam } = useParams<{ day?: string }>()
  const dayNum = parseInt(dayParam?.replace('day-', '') ?? '1', 10)
  const card = DAY_CARDS.find((c) => c.day === dayNum) ?? DAY_CARDS[0]
  const clientId = getSettingsClientId()
  const nextDay = DAY_CARDS.find((c) => c.day === dayNum + 1)

  return (
    <SettingsLayout>
      <div className="p-8 font-sans min-h-full max-w-3xl">

        {/* Day header */}
        <div className="mb-6 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 flex-shrink-0">
            {card.icon}
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-0.5">
              Day {card.day} of 6
            </p>
            <h1 className="text-2xl font-bold text-white">{card.title}</h1>
          </div>
        </div>

        {clientId && (
          <div className="mb-4 flex items-center gap-2">
            <span className="text-xs text-slate-500">Onboarding client:</span>
            <span className="text-xs font-mono text-amber-300 bg-amber-950/40 border border-amber-700/30 px-2 py-0.5 rounded">{clientId}</span>
          </div>
        )}

        {/* Summary */}
        <div className="mb-6 p-5 rounded-xl bg-card border border-border">
          <p className="text-sm text-slate-300 leading-relaxed">{card.summary}</p>
        </div>

        {/* Actions */}
        <div className="mb-6 space-y-3">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">Actions</p>
          {card.actions.map((a) => (
            <Link
              key={a.to}
              to={a.to}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-colors ${
                a.primary
                  ? 'bg-indigo-600/15 border-indigo-500/40 text-white hover:bg-indigo-600/25'
                  : 'bg-slate-900/40 border-slate-700/60 text-slate-300 hover:bg-slate-800/60'
              }`}
            >
              <span className="flex-1 text-sm font-medium">{a.label}</span>
              {a.note && <span className="text-xs text-slate-500">{a.note}</span>}
              <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0" />
            </Link>
          ))}
        </div>

        {/* Tips */}
        <div className="mb-8 space-y-2">
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500">Tips for this step</p>
          <ul className="space-y-2">
            {card.tips.map((tip, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-slate-400">
                <span className="mt-1.5 w-1 h-1 rounded-full bg-slate-600 flex-shrink-0" />
                {tip}
              </li>
            ))}
          </ul>
        </div>

        {/* Next day */}
        {nextDay && (
          <div className="pt-6 border-t border-slate-800/60">
            <p className="text-xs text-slate-500 mb-2">Next</p>
            <Link
              to={`/settings/onboarding/day-${nextDay.day}`}
              className="inline-flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
            >
              Day {nextDay.day} — {nextDay.title}
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}

        {!nextDay && (
          <div className="pt-6 border-t border-slate-800/60 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <p className="text-sm text-emerald-200 font-medium">
              All 6 days complete — client onboarding finished.
            </p>
          </div>
        )}
      </div>
    </SettingsLayout>
  )
}
