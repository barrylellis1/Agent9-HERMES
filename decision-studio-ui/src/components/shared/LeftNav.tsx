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
 * Scope is deliberately small — four top-level destinations, matching the
 * design doc's finding that the real authenticated surface is Situations /
 * Portfolio / Context / Settings, not the 22 page components App.tsx
 * declares (most are marketing, auth, or token-handler pages that don't
 * belong in an authenticated nav). Situation-scoped deep views
 * (/debate/:id, /briefing/:id, /report/:id) are deliberately NOT wrapped in
 * this nav — they keep their own contextual back affordance, per the
 * design doc's own scoping call.
 *
 * Two states, matching SettingsLayout's existing w-56 sidebar width so the
 * two navs read as one system rather than two competing widths: expanded
 * (icon + label) and collapsed (icon rail, ~w-14), persisted per-viewer in
 * localStorage — this is the first WIDTH-collapse pattern in the codebase
 * (the only prior collapse pattern, DeepFocusView's accordions, is
 * CONTENT-collapse — hide a panel's contents in place, not shrink the
 * panel itself). See DESIGN_SYSTEM.md for the documented pattern.
 */
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Eye, LineChart, LayoutGrid, Settings as SettingsIcon,
  PanelLeftClose, PanelLeftOpen,
} from 'lucide-react';
import { BrandLogo } from '../BrandLogo';
import { getSettingsClientId } from '../../utils/settingsMode';

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

export function LeftNav() {
  const { pathname } = useLocation();
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem(NAV_COLLAPSED_KEY) === 'true';
    } catch {
      return false;
    }
  });
  const clientId = (() => {
    try {
      return getSettingsClientId();
    } catch {
      return '';
    }
  })();

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

      {/* Client badge — the one surface present on every authenticated page.
          Closes the "no visible client indicator" gap named in
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
              <span className="block text-[10px] font-bold uppercase text-indigo-300">
                {clientId.slice(0, 2)}
              </span>
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
          return (
            <Link
              key={dest.to}
              to={dest.to}
              title={collapsed ? dest.label : undefined}
              className={`group flex items-center rounded-lg text-sm transition-colors ${
                collapsed ? 'justify-center px-0 py-2.5' : 'gap-2.5 px-3 py-2'
              } ${
                active
                  ? 'bg-indigo-600/20 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <span className={active ? 'text-indigo-400' : 'text-slate-500 group-hover:text-slate-400'}>
                {dest.icon}
              </span>
              {!collapsed && <span className="flex-1">{dest.label}</span>}
            </Link>
          );
        })}
      </nav>

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
