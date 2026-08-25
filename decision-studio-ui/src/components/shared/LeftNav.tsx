/**
 * LeftNav — the app-wide primary navigation rail.
 *
 * Built 2026-08-25 per docs/architecture/collapsible_left_nav_design.md.
 * Navigation was fragmented per-page before this: AppHeader had two icon
 * links (rendered only on /dashboard), /context and /portfolio each had
 * their own inline "Back" affordance and nothing pointing at each other,
 * and /portfolio with no query param rendered a raw developer error
 * (fixed separately, but a symptom of the same absent-navigation problem).
 *
 * Merged with Settings' own sidebar the same day (2026-08-25) — a second
 * full-height panel (`SettingsLayout`'s old `Sidebar`) sat immediately to
 * the right of this one, each anchoring its own brand mark, live-caught by
 * a user screenshot. One column now carries both: the four top-level
 * destinations, and — only while on a /settings/* route — the mode-specific
 * registry/onboarding tree indented directly beneath the Settings link.
 * `SettingsLayout` no longer renders a sidebar of its own; see its own
 * comment.
 *
 * Scope is deliberately small — four top-level destinations, matching the
 * design doc's finding that the real authenticated surface is Situations /
 * Portfolio / Context / Settings, not the 22 page components App.tsx
 * declares (most are marketing, auth, or token-handler pages that don't
 * belong in an authenticated nav). Situation-scoped deep views
 * (/debate/:id, /briefing/:id, /report/:id) are deliberately NOT wrapped in
 * this nav — they keep their own contextual back affordance, per the
 * design doc's own scoping call.
 *
 * System Admin (onboarding) is a fully separate branch, not a fifth
 * destination — an admin mid-onboarding a brand-new client has no
 * principal, no KPIs, and no data yet, so Situations/Portfolio/Context
 * would render broken or empty for them. `AdminGuard` already redirects
 * /dashboard away from them; this component goes further and simply never
 * shows those three destinations while `isAdminMode()` is true, matching
 * the old Settings-only Sidebar's behavior exactly (steps + Exit Admin,
 * nothing else).
 */
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Eye, LineChart, LayoutGrid, Settings as SettingsIcon,
  PanelLeftClose, PanelLeftOpen, ChevronDown, ChevronRight,
  Box, Briefcase, Building2, CheckCircle2, Database, GitBranch,
  LogOut, ShieldCheck, Sparkles, Users, UserCheck, Activity,
  Shield, BarChart2, Target, Library,
} from 'lucide-react';
import { BrandLogo } from '../BrandLogo';
import { getSettingsClientId, getSettingsMode, isAdminMode, exitAdminMode, type SettingsMode } from '../../utils/settingsMode';
import { ONBOARDING_STEPS } from '../../config/onboardingSteps';
import { useOnboardingProgress } from '../../hooks/useOnboardingProgress';

const NAV_COLLAPSED_KEY = 'a9_nav_collapsed';

interface NavDestination {
  label: string;
  to: string;
  icon: React.ReactNode;
  /** Extra path prefixes that should also highlight this item — e.g. the
   *  situation-scoped deep views reached FROM the dashboard. Matching here
   *  means the rail still shows "you're in the Situations flow" on those
   *  pages, even though they don't render the nav themselves. */
  alsoActiveOn?: string[];
}

const DESTINATIONS: NavDestination[] = [
  {
    label: 'Situations',
    to: '/dashboard',
    icon: <Eye className="w-5 h-5" />,
    alsoActiveOn: ['/debate', '/briefing', '/report'],
  },
  { label: 'Portfolio', to: '/portfolio', icon: <LineChart className="w-5 h-5" /> },
  { label: 'Context', to: '/context', icon: <LayoutGrid className="w-5 h-5" /> },
  { label: 'Settings', to: '/settings', icon: <SettingsIcon className="w-5 h-5" /> },
];

function isActive(pathname: string, dest: NavDestination): boolean {
  if (pathname === dest.to || pathname.startsWith(dest.to + '/')) return true;
  return (dest.alsoActiveOn ?? []).some((p) => pathname.startsWith(p));
}

// ─────────────────────────────────────────────────
// Settings sub-tree — Maintenance / Governance modes
// (moved from SettingsLayout.tsx 2026-08-25 as part of the panel merge)
// ─────────────────────────────────────────────────

interface SettingsNavItem {
  label: string;
  to: string;
  icon: React.ReactNode;
}

interface SettingsNavGroup {
  group: string;
  items: SettingsNavItem[];
}

const MAINTENANCE_NAV: SettingsNavGroup[] = [
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
];

const GOVERNANCE_NAV: SettingsNavGroup[] = [
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
  // both linked to the exact same routes as two of this rail's own
  // top-level items. Live approved-solutions tracking and live-monitoring
  // are genuinely distinct functions, but neither was missing from
  // top-level nav — this group duplicated the link, not the function.
];

const SETTINGS_MODE_LABEL: Record<SettingsMode, string> = {
  onboarding: 'Onboarding',
  maintenance: 'Product Owner',
  governance: 'Executive',
};
const SETTINGS_MODE_BADGE_CLASS: Record<SettingsMode, string> = {
  onboarding: 'text-amber-400 bg-amber-950/40 border-amber-700/30',
  maintenance: 'text-indigo-300 bg-indigo-950/40 border-indigo-700/30',
  governance: 'text-emerald-300 bg-emerald-950/40 border-emerald-700/30',
};

function SettingsSubLink({ item, active }: { item: SettingsNavItem; active: boolean }) {
  return (
    <Link
      to={item.to}
      className={`group flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-[13px] transition-colors ${
        active ? 'bg-indigo-600/20 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
      }`}
    >
      <span className={active ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-400'}>{item.icon}</span>
      <span className="flex-1">{item.label}</span>
    </Link>
  );
}

// Persisted across navigations, not just component state — each Settings
// page wraps itself in <SettingsLayout> independently, which remounts this
// tree on every route change within Settings. Without this, a manually-
// opened group would silently re-collapse the moment you clicked one of
// its own links.
const SETTINGS_NAV_OPEN_GROUPS_KEY = 'a9_settings_nav_open_groups';

function loadOpenGroups(): Set<string> {
  try {
    const raw = localStorage.getItem(SETTINGS_NAV_OPEN_GROUPS_KEY);
    const arr = raw ? JSON.parse(raw) : [];
    return new Set(Array.isArray(arr) ? arr : []);
  } catch {
    return new Set();
  }
}

function saveOpenGroups(groups: Set<string>): void {
  try {
    localStorage.setItem(SETTINGS_NAV_OPEN_GROUPS_KEY, JSON.stringify([...groups]));
  } catch {
    /* private mode / blocked storage — open state just won't persist */
  }
}

// Collapsible groups (2026-08-25) — Maintenance mode's Registry/Intelligence/
// Ownership/Workspace is 14 leaf items; rendered flat that forced an
// internal scrollbar. The group containing the current page always renders
// open regardless of stored state, so navigating here never hides the
// active link.
function SettingsGroupNav({ groups }: { groups: SettingsNavGroup[] }) {
  const { pathname } = useLocation();
  const activeGroup = groups.find((g) =>
    g.items.some((item) => pathname === item.to || pathname.startsWith(item.to + '/'))
  )?.group;

  const [openGroups, setOpenGroups] = useState<Set<string>>(() => loadOpenGroups());

  function toggleGroup(name: string) {
    setOpenGroups((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      saveOpenGroups(next);
      return next;
    });
  }

  return (
    <div className="space-y-1">
      {groups.map((g) => {
        const isOpen = g.group === activeGroup || openGroups.has(g.group);
        return (
          <div key={g.group}>
            <button
              type="button"
              onClick={() => toggleGroup(g.group)}
              className="w-full flex items-center justify-between gap-2 px-2.5 py-1 rounded-lg text-[9px] font-semibold uppercase tracking-widest text-slate-600 hover:text-slate-400 hover:bg-slate-800/40 transition-colors"
            >
              <span>{g.group}</span>
              <ChevronDown className={`w-3 h-3 flex-shrink-0 transition-transform duration-150 ${isOpen ? '' : '-rotate-90'}`} />
            </button>
            {isOpen && (
              <div className="space-y-0.5 mb-2">
                {g.items.map((item) => (
                  <SettingsSubLink
                    key={item.to}
                    item={item}
                    active={pathname === item.to || pathname.startsWith(item.to + '/')}
                  />
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─────────────────────────────────────────────────
// System Admin (onboarding) — a fully separate branch, see file header
// ─────────────────────────────────────────────────

function OnboardingRailContent({ collapsed, clientId }: { collapsed: boolean; clientId: string }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { progress, isStepUnlocked } = useOnboardingProgress(clientId || null);

  function handleExit() {
    exitAdminMode();
    navigate('/login');
  }

  return (
    <>
      {clientId && !collapsed && (
        <div className="mx-2 mt-2 mb-1 px-3 py-2 rounded-lg bg-amber-950/40 border border-amber-700/30">
          <p className="text-[9px] text-amber-500 uppercase tracking-wider font-medium">Onboarding</p>
          <p className="text-sm font-semibold text-amber-200 font-mono truncate">{clientId}</p>
        </div>
      )}
      <nav className="flex-1 overflow-y-auto px-2 py-2 min-h-0 space-y-0.5">
        {ONBOARDING_STEPS.map((step) => {
          const active = pathname === step.to || pathname.startsWith(step.to);
          const isComplete = progress?.steps[step.key]?.complete ?? false;
          const unlocked = isStepUnlocked(step.step);
          return (
            <Link
              key={step.to}
              to={step.to}
              title={collapsed ? step.label : undefined}
              className={`group flex items-center rounded-lg text-sm transition-colors ${
                collapsed ? 'justify-center px-0 py-2.5' : 'gap-2.5 px-3 py-2'
              } ${
                active
                  ? 'bg-indigo-600/20 text-white'
                  : isComplete
                  ? 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  : unlocked
                  ? 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/40'
                  : 'text-slate-600 hover:text-slate-400 hover:bg-slate-800/30'
              }`}
            >
              <div
                className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0 ${
                  active ? 'bg-indigo-500 text-white' : isComplete ? 'bg-emerald-600/80 text-white' : 'bg-slate-700/60 text-slate-400'
                }`}
              >
                {isComplete ? <CheckCircle2 className="w-3 h-3" /> : step.step}
              </div>
              {!collapsed && <span className="flex-1">{step.label}</span>}
              {!collapsed && active && <ChevronRight className="w-3.5 h-3.5 text-indigo-400" />}
            </Link>
          );
        })}
      </nav>
      <div className="flex-shrink-0 border-t border-slate-800/60 p-2">
        <button
          onClick={handleExit}
          title={collapsed ? 'Exit Admin' : undefined}
          className={`w-full flex items-center rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800/40 transition-colors ${
            collapsed ? 'justify-center px-0 py-2.5' : 'gap-2.5 px-3 py-2'
          }`}
        >
          <LogOut className="w-4 h-4" />
          {!collapsed && <span className="text-xs">Exit Admin</span>}
        </button>
      </div>
    </>
  );
}

export function LeftNav() {
  const { pathname } = useLocation();
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem(NAV_COLLAPSED_KEY) === 'true';
    } catch {
      return false;
    }
  });
  const adminMode = (() => {
    try {
      return isAdminMode();
    } catch {
      return false;
    }
  })();
  const clientId = (() => {
    try {
      return getSettingsClientId();
    } catch {
      return '';
    }
  })();
  // Only 'maintenance' | 'governance' ever reach here — the admin-mode
  // branch above already covers 'onboarding' with its own step tree.
  const settingsMode = !adminMode ? getSettingsMode() : null;

  function toggle() {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(NAV_COLLAPSED_KEY, String(next));
      } catch {
        /* private mode / blocked storage — collapse state just won't persist */
      }
      return next;
    });
  }

  return (
    <aside
      className={`flex-shrink-0 flex flex-col h-full border-r border-slate-800/60 bg-slate-950/80 transition-[width] duration-150 ${
        collapsed ? 'w-14' : 'w-56'
      }`}
    >
      {/* Brand — mark only; BrandLogo's own default variant="full" already
          renders the "Decision Studio" wordmark itself, so pairing it with
          another label here duplicated the text (caught live, 2026-08-25). */}
      <div className={`flex items-center h-16 flex-shrink-0 border-b border-slate-800/60 ${collapsed ? 'justify-center px-0' : 'px-4 gap-2.5'}`}>
        <BrandLogo variant="mark" size={28} />
        {!collapsed && <span className="text-base font-bold text-white tracking-tight truncate">Decision Studio</span>}
      </div>

      {adminMode ? (
        <OnboardingRailContent collapsed={collapsed} clientId={clientId} />
      ) : (
        <>
          {/* Client badge — the one surface present on every authenticated
              page. Closes the "no visible client indicator" gap named in
              ui_refinement_plan.md §4.2 as a side effect of this build. */}
          {clientId && (
            <div className={`flex-shrink-0 ${collapsed ? 'px-2 py-2' : 'px-4 py-3'}`}>
              <div
                className={`rounded-lg border border-indigo-700/30 bg-indigo-950/30 ${
                  collapsed ? 'px-1.5 py-1.5 text-center' : 'px-3 py-2'
                }`}
                title={`Active client: ${clientId}`}
              >
                {collapsed ? (
                  <span className="block text-[10px] font-bold uppercase text-indigo-300">{clientId.slice(0, 2)}</span>
                ) : (
                  <>
                    <p className="text-[9px] text-indigo-500 uppercase tracking-wider font-medium">Client</p>
                    <p className="text-sm font-semibold text-indigo-200 font-mono truncate">{clientId}</p>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Nav */}
          <nav className="flex-1 overflow-y-auto px-2 py-2 min-h-0 space-y-0.5">
            {DESTINATIONS.map((dest) => {
              const active = isActive(pathname, dest);
              const isSettings = dest.to === '/settings';
              return (
                <div key={dest.to}>
                  <Link
                    to={dest.to}
                    title={collapsed ? dest.label : undefined}
                    className={`group flex items-center rounded-lg text-sm transition-colors ${
                      collapsed ? 'justify-center px-0 py-2.5' : 'gap-2.5 px-3 py-2'
                    } ${active ? 'bg-indigo-600/20 text-white' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'}`}
                  >
                    <span className={active ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-400'}>{dest.icon}</span>
                    {!collapsed && <span className="flex-1">{dest.label}</span>}
                  </Link>

                  {/* Settings' own mode-specific tree, indented directly
                      beneath it — merged 2026-08-25 from what used to be a
                      second full-height sidebar panel. Hidden while
                      collapsed: an icon rail has no room for a sub-tree,
                      same trade-off the rail already makes for labels. */}
                  {isSettings && active && !collapsed && settingsMode && (
                    <div className="mt-1 mb-2 pl-2 border-l border-slate-800/60 ml-5">
                      <span
                        className={`inline-flex items-center text-[9px] font-semibold uppercase tracking-widest px-2 py-0.5 mb-2 rounded border ${SETTINGS_MODE_BADGE_CLASS[settingsMode]}`}
                      >
                        {SETTINGS_MODE_LABEL[settingsMode]}
                      </span>
                      <SettingsGroupNav groups={settingsMode === 'maintenance' ? MAINTENANCE_NAV : GOVERNANCE_NAV} />
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
        </>
      )}

      {/* Collapse toggle */}
      <div className="flex-shrink-0 border-t border-slate-800/60 p-2">
        <button
          onClick={toggle}
          title={collapsed ? 'Expand navigation' : 'Collapse navigation'}
          className={`w-full flex items-center rounded-lg text-slate-500 hover:text-slate-300 hover:bg-slate-800/40 transition-colors ${
            collapsed ? 'justify-center px-0 py-2.5' : 'gap-2.5 px-3 py-2'
          }`}
        >
          {collapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
          {!collapsed && <span className="text-xs">Collapse</span>}
        </button>
      </div>
    </aside>
  );
}
