/**
 * SettingsLayout — two-pane layout for all Settings pages.
 *
 * Left sidebar: 220px, renders different nav depending on SettingsMode.
 * Right content: flex-1, renders {children}.
 *
 * Mode 1 (Onboarding)  — Day 1–6 sequential steps with progress indicators
 * Mode 2 (Maintenance) — Registry / Intelligence / Ownership / Workspace groups
 * Mode 3 (Governance)  — Strategic / Registry / Assessment (read-only)
 */

import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  Box, Briefcase, Building2, CheckCircle2, ChevronRight,
  Database, Eye, LineChart, LogOut, Sparkles, Users,
  UserCheck, Activity, Shield, BarChart2, Target,
} from 'lucide-react'
import { BrandLogo } from './BrandLogo'
import { getSettingsMode, getSettingsClientId, type SettingsMode } from '../utils/settingsMode'
import { exitAdminMode } from '../utils/adminMode'

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
// Day step type (Onboarding mode only)
// ─────────────────────────────────────────────────
interface DayStep {
  day: number
  label: string
  to: string
  icon: React.ReactNode
}

// ─────────────────────────────────────────────────
// Nav definitions per mode
// ─────────────────────────────────────────────────

const ONBOARDING_DAYS: DayStep[] = [
  { day: 1, label: 'Workspace Setup',   to: '/settings/onboarding/day-1', icon: <Building2 className="w-4 h-4" /> },
  { day: 2, label: 'Principal Profiles', to: '/settings/onboarding/day-2', icon: <Users className="w-4 h-4" /> },
  { day: 3, label: 'KPI Library',        to: '/settings/onboarding/day-3', icon: <Sparkles className="w-4 h-4" /> },
  { day: 4, label: 'Assign Ownership',   to: '/settings/onboarding/day-4', icon: <UserCheck className="w-4 h-4" /> },
  { day: 5, label: 'Connect Data',       to: '/settings/onboarding/day-5', icon: <Database className="w-4 h-4" /> },
  { day: 6, label: 'Validate & Launch',  to: '/settings/onboarding/day-6', icon: <CheckCircle2 className="w-4 h-4" /> },
]

const MAINTENANCE_NAV: NavGroup[] = [
  {
    group: 'Registry',
    items: [
      { label: 'KPIs',               to: '/settings/registry/kpis',           icon: <BarChart2 className="w-4 h-4" /> },
      { label: 'Principals',         to: '/settings/registry/principals',      icon: <Users className="w-4 h-4" /> },
      { label: 'Data Products',      to: '/settings/registry/data-products',   icon: <Database className="w-4 h-4" /> },
      { label: 'Business Processes', to: '/settings/registry/business-processes', icon: <Briefcase className="w-4 h-4" /> },
    ],
  },
  {
    group: 'Intelligence',
    items: [
      { label: 'KPI Intelligence', to: '/settings/kpi-intelligence', icon: <Sparkles className="w-4 h-4" /> },
      { label: 'Data Onboarding',  to: '/settings/onboarding',       icon: <Box className="w-4 h-4" /> },
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
  {
    group: 'Assessment',
    items: [
      { label: 'Portfolio',    to: '/portfolio',                     icon: <LineChart className="w-4 h-4" /> },
      { label: 'Situation Console', to: '/dashboard',                icon: <Eye className="w-4 h-4" /> },
    ],
  },
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

function GroupNav({ groups }: { groups: NavGroup[] }) {
  const { pathname } = useLocation()
  return (
    <div className="space-y-5">
      {groups.map((g) => (
        <div key={g.group}>
          <p className="px-3 mb-1 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
            {g.group}
          </p>
          <div className="space-y-0.5">
            {g.items.map((item) => (
              <NavLink
                key={item.to}
                item={item}
                active={pathname === item.to || pathname.startsWith(item.to + '/')}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function OnboardingNav({ clientId }: { clientId: string }) {
  const { pathname } = useLocation()
  const navigate = useNavigate()

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

      {/* Day steps */}
      {ONBOARDING_DAYS.map((step, i) => {
        const isActive = pathname === step.to || pathname.startsWith(step.to)
        // Mark as complete if a later step is active (simple visited heuristic)
        const currentDayIndex = ONBOARDING_DAYS.findIndex(
          (s) => pathname === s.to || pathname.startsWith(s.to)
        )
        const isComplete = currentDayIndex > i

        return (
          <Link
            key={step.to}
            to={step.to}
            className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              isActive
                ? 'bg-indigo-600/20 text-white'
                : isComplete
                ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/40'
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
              {isComplete ? <CheckCircle2 className="w-3.5 h-3.5" /> : step.day}
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
      {/* Header */}
      <div className="px-4 pt-6 pb-4 border-b border-slate-800/60">
        <div className="flex items-center gap-2.5 mb-3">
          <BrandLogo size={28} />
          <span className="text-base font-bold text-white tracking-tight">Settings</span>
        </div>
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

      {/* Footer — back link */}
      {mode !== 'onboarding' && (
        <div className="px-3 py-4 border-t border-slate-800/60">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-500 hover:text-slate-300 hover:bg-slate-800/40 transition-colors"
          >
            <Eye className="w-4 h-4" />
            Back to Situation Console
          </Link>
        </div>
      )}
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
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans">
      <Sidebar mode={mode} clientId={clientId} />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  )
}

// Export types for consumers
export type { SettingsMode }
