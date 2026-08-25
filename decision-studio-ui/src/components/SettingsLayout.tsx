/**
 * SettingsLayout — two-pane layout for all Settings pages.
 *
 * Left sidebar: 220px, renders different nav depending on SettingsMode.
 * Right content: flex-1, renders {children}.
 *
 * Mode 1 (Onboarding)  — Day 1–6 sequential steps with progress indicators
 * Mode 2 (Maintenance) — Registry / Intelligence / Ownership / Workspace groups
 * Mode 3 (Governance)  — Strategic / Registry (read-only)
 */

import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Box, Briefcase, Building2, CheckCircle2, ChevronDown, ChevronRight,
  Database, GitBranch, LogOut, ShieldCheck, Sparkles, Users,
  UserCheck, Activity, Shield, BarChart2, Target, Library,
} from 'lucide-react'
import { AppShell } from './shared/AppShell'
import { getSettingsMode, getSettingsClientId, type SettingsMode } from '../utils/settingsMode'
import { exitAdminMode } from '../utils/adminMode'
import { ONBOARDING_STEPS } from '../config/onboardingSteps'
import { useOnboardingProgress } from '../hooks/useOnboardingProgress'

// ─────────────────────────────────────────────────
// Nav item type
// ─────────────────────────────────────────────────
interface NavItem {
  label: string
  to: string
  icon: React.ReactNode
  badge?: string        // 'soon' shows a muted "soon" chip
  exact?: boolean
}

interface NavGroup {
  group: string
  items: NavItem[]
}

// ─────────────────────────────────────────────────
// Nav definitions per mode
// ─────────────────────────────────────────────────

const MAINTENANCE_NAV: NavGroup[] = [
  {
    group: 'Registry',
    items: [
      { label: 'KPIs',               to: '/settings/registry/kpis',           icon: <BarChart2 className="w-4 h-4" /> },
      { label: 'Principals',         to: '/settings/registry/principals',      icon: <Users className="w-4 h-4" /> },
      { label: 'Data Products',      to: '/settings/registry/data-products',   icon: <Database className="w-4 h-4" /> },
      { label: 'Business Processes', to: '/settings/registry/business-processes', icon: <Briefcase className="w-4 h-4" /> },
      { label: 'KPI Relationships',  to: '/settings/registry/kpi-relationships', icon: <GitBranch className="w-4 h-4" /> },
      { label: 'Assumptions',        to: '/settings/registry/assumptions',     icon: <ShieldCheck className="w-4 h-4" /> },
    ],
  },
  {
    group: 'Intelligence',
    items: [
      { label: 'Business Process Intelligence', to: '/settings/business-process-intelligence', icon: <Library className="w-4 h-4" /> },
      { label: 'KPI Intelligence', to: '/settings/kpi-intelligence', icon: <Sparkles className="w-4 h-4" /> },
      { label: 'Data Onboarding',  to: '/settings/data-onboarding',  icon: <Box className="w-4 h-4" /> },
    ],
  },
  {
    group: 'Ownership',
    items: [
      { label: 'Accountability',    to: '/settings/accountability',        icon: <Shield className="w-4 h-4" /> },
      { label: 'Assign Ownership',  to: '/settings/ownership-interview',   icon: <UserCheck className="w-4 h-4" /> },
    ],
  },
  {
    group: 'Workspace',
    items: [
      { label: 'Company Profile',    to: '/settings/company-profile',  icon: <Building2 className="w-4 h-4" /> },
      { label: 'Connection Health',  to: '/settings/connection-health', icon: <Activity className="w-4 h-4" /> },
      { label: 'Slice Validity',     to: '/settings/slice-validity',    icon: <ShieldCheck className="w-4 h-4" /> },
    ],
  },
]

const GOVERNANCE_NAV: NavGroup[] = [
  {
    group: 'Strategic',
    items: [
      { label: 'KPI Ownership Map',   to: '/settings/governance/ownership',  icon: <Target className="w-4 h-4" /> },
      { label: 'Coverage Summary',    to: '/settings/governance/coverage',   icon: <CheckCircle2 className="w-4 h-4" /> },
    ],
  },
  {
    group: 'Registry',
    items: [
      { label: 'KPI Definitions',     to: '/settings/governance/kpis',        icon: <BarChart2 className="w-4 h-4" /> },
      { label: 'Principal Directory', to: '/settings/governance/principals',  icon: <Users className="w-4 h-4" /> },
    ],
  },
  // Assessment group (Portfolio, Situation Console) removed 2026-08-25 —
  // both linked to the exact same routes as two of the app-wide LeftNav's
  // own top-level items (/portfolio, /dashboard), one column over. Live
  // approved-solutions tracking and live-monitoring are genuinely distinct
  // functions, but neither was missing from top-level nav — this group
  // duplicated the link, not the function.
]

// ─────────────────────────────────────────────────
// Sidebar components
// ─────────────────────────────────────────────────

function NavLink({ item, active }: { item: NavItem; active: boolean }) {
  return (
    <Link
      to={item.to}
      className={`group flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
        active
          ? 'bg-indigo-600/20 text-white'
          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
      }`}
    >
      <span className={active ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-400'}>
        {item.icon}
      </span>
      <span className="flex-1">{item.label}</span>
      {item.badge === 'soon' && (
        <span className="text-[10px] text-slate-600 font-medium uppercase tracking-wider">soon</span>
      )}
    </Link>
  )
}

// Persisted across navigations, not just component state — each Settings
// page wraps itself in <SettingsLayout> independently (same pattern as
// AppShell), so GroupNav remounts on every route change within Settings.
// Without this, a manually-opened group would silently re-collapse the
// moment you clicked one of its own links.
const SETTINGS_NAV_OPEN_GROUPS_KEY = 'a9_settings_nav_open_groups'

function loadOpenGroups(): Set<string> {
  try {
    const raw = localStorage.getItem(SETTINGS_NAV_OPEN_GROUPS_KEY)
    const arr = raw ? JSON.parse(raw) : []
    return new Set(Array.isArray(arr) ? arr : [])
  } catch {
    return new Set()
  }
}

function saveOpenGroups(groups: Set<string>): void {
  try {
    localStorage.setItem(SETTINGS_NAV_OPEN_GROUPS_KEY, JSON.stringify([...groups]))
  } catch {
    /* private mode / blocked storage — open state just won't persist */
  }
}

// Collapsible groups (2026-08-25) — Maintenance mode's Registry/Intelligence/
// Ownership/Workspace is 14 leaf items; rendered flat, that forced an
// internal scrollbar in this w-56 column, one panel over from the app-wide
// LeftNav's own w-56. Caught live. The group containing the current page
// always renders open regardless of stored state, so navigating here never
// hides the active link.
function GroupNav({ groups }: { groups: NavGroup[] }) {
  const { pathname } = useLocation()
  const activeGroup = groups.find((g) =>
    g.items.some((item) => pathname === item.to || pathname.startsWith(item.to + '/'))
  )?.group

  const [openGroups, setOpenGroups] = useState<Set<string>>(() => loadOpenGroups())

  function toggleGroup(name: string) {
    setOpenGroups((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      saveOpenGroups(next)
      return next
    })
  }

  return (
    <div className="space-y-1">
      {groups.map((g) => {
        const isOpen = g.group === activeGroup || openGroups.has(g.group)
        return (
          <div key={g.group}>
            <button
              type="button"
              onClick={() => toggleGroup(g.group)}
              className="w-full flex items-center justify-between gap-2 px-3 py-1.5 rounded-lg text-[10px] font-semibold uppercase tracking-widest text-slate-600 hover:text-slate-400 hover:bg-slate-800/40 transition-colors"
            >
              <span>{g.group}</span>
              <ChevronDown className={`w-3 h-3 flex-shrink-0 transition-transform duration-150 ${isOpen ? '' : '-rotate-90'}`} />
            </button>
            {isOpen && (
              <div className="space-y-0.5 mb-3">
                {g.items.map((item) => (
                  <NavLink
                    key={item.to}
                    item={item}
                    active={pathname === item.to || pathname.startsWith(item.to + '/')}
                  />
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

function OnboardingNav({ clientId }: { clientId: string }) {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { progress, isStepUnlocked } = useOnboardingProgress(clientId || null)

  function handleExit() {
    exitAdminMode()
    navigate('/login')
  }

  return (
    <div className="space-y-1">
      {/* Client badge */}
      {clientId && (
        <div className="px-3 py-2 mb-4 rounded-lg bg-amber-950/40 border border-amber-700/30">
          <p className="text-[10px] text-amber-500 uppercase tracking-wider font-medium">Onboarding</p>
          <p className="text-sm font-semibold text-amber-200 font-mono truncate">{clientId}</p>
        </div>
      )}

      {/* Step nav — completion is server-derived (GET /api/v1/onboarding/progress),
          not a route-position heuristic. Non-linear jumps are never blocked here —
          the dismissible "jumping ahead" warning lives in OnboardingDayView. */}
      {ONBOARDING_STEPS.map((step) => {
        const isActive = pathname === step.to || pathname.startsWith(step.to)
        const isComplete = progress?.steps[step.key]?.complete ?? false
        const unlocked = isStepUnlocked(step.step)

        return (
          <Link
            key={step.to}
            to={step.to}
            className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              isActive
                ? 'bg-indigo-600/20 text-white'
                : isComplete
                ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                : unlocked
                ? 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/40'
                : 'text-slate-600 hover:text-slate-400 hover:bg-slate-800/30'
            }`}
          >
            {/* Step indicator */}
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                isActive
                  ? 'bg-indigo-500 text-white'
                  : isComplete
                  ? 'bg-emerald-600/80 text-white'
                  : 'bg-slate-700/60 text-slate-400'
              }`}
            >
              {isComplete ? <CheckCircle2 className="w-3.5 h-3.5" /> : step.step}
            </div>
            <span className="flex-1">{step.label}</span>
            {isActive && <ChevronRight className="w-3.5 h-3.5 text-indigo-400" />}
          </Link>
        )
      })}

      {/* Exit */}
      <button
        onClick={handleExit}
        className="w-full mt-4 flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-slate-500 hover:text-slate-300 hover:bg-slate-800/40 transition-colors"
      >
        <LogOut className="w-3.5 h-3.5" />
        Exit Admin
      </button>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Sidebar shell
// ─────────────────────────────────────────────────

function Sidebar({ mode, clientId }: { mode: SettingsMode; clientId: string }) {
  const modeLabel: Record<SettingsMode, string> = {
    onboarding: 'Onboarding',
    maintenance: 'Product Owner',
    governance: 'Executive',
  }
  const modeBadgeClass: Record<SettingsMode, string> = {
    onboarding: 'text-amber-400 bg-amber-950/40 border-amber-700/30',
    maintenance: 'text-indigo-300 bg-indigo-950/40 border-indigo-700/30',
    governance: 'text-emerald-300 bg-emerald-950/40 border-emerald-700/30',
  }

  return (
    <aside className="w-56 flex-shrink-0 flex flex-col h-full border-r border-slate-800/60 bg-slate-950/80">
      {/* Header — no BrandLogo here (2026-08-25): the app-wide LeftNav one
          column over already anchors brand identity; repeating it here
          rendered "Decision Studio" twice side by side, caught live. */}
      <div className="px-4 pt-6 pb-4 border-b border-slate-800/60 flex flex-col items-start gap-3">
        <span className="text-base font-bold text-white tracking-tight">Settings</span>
        <span className={`inline-flex items-center text-[10px] font-semibold uppercase tracking-widest px-2 py-0.5 rounded border ${modeBadgeClass[mode]}`}>
          {modeLabel[mode]}
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 min-h-0">
        {mode === 'onboarding' && <OnboardingNav clientId={clientId} />}
        {mode === 'maintenance' && <GroupNav groups={MAINTENANCE_NAV} />}
        {mode === 'governance' && <GroupNav groups={GOVERNANCE_NAV} />}
      </nav>

      {/* Footer back-link removed 2026-08-25 — redundant now that the
          app-wide LeftNav's own "Situations" destination sits one level
          up, always visible, on every Settings page (not just non-onboarding
          modes as this link was scoped to). */}
    </aside>
  )
}

// ─────────────────────────────────────────────────
// Public layout component
// ─────────────────────────────────────────────────

interface SettingsLayoutProps {
  children: React.ReactNode
  /** Override mode detection (useful for page-level control) */
  modeOverride?: SettingsMode
}

export function SettingsLayout({ children, modeOverride }: SettingsLayoutProps) {
  const mode = modeOverride ?? getSettingsMode()
  const clientId = getSettingsClientId()

  return (
    <AppShell>
    {/* h-full, not h-screen — this is now the second nesting level inside
        AppShell's own h-screen shell (2026-08-25); h-screen here would
        double-count against it and either overflow or double-scroll. */}
    <div className="flex h-full bg-background text-foreground overflow-hidden font-sans">
      <Sidebar mode={mode} clientId={clientId} />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
    </AppShell>
  )
}

// Export types for consumers
export type { SettingsMode }
