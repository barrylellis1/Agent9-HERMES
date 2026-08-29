/**
 * AppShell — wraps a page's content with the app-wide LeftNav.
 *
 * Deliberately a thin wrapper component each page imports itself, rather
 * than a parent route in App.tsx's <Routes> tree. App.tsx is a flat route
 * list (no nested layouts/<Outlet>) already carrying an admin guard, legacy
 * redirects, and a documented React Router 7.10.1 hyphen-segment quirk —
 * restructuring it into nested routes to introduce a shared layout is a
 * materially riskier change than four pages each wrapping themselves.
 *
 * Owns the full viewport height. A page rendered inside it must use
 * min-h-screen or min-h-full (a floor, compatible with sitting in a
 * flex-1 child) rather than h-screen (a fixed height, which double-counts
 * against this wrapper's own h-screen and either overflows or
 * double-scrolls). SettingsLayout is a thin pass-through of this
 * component — it no longer has a shell of its own (see its own comment).
 */
import { LeftNav } from './LeftNav';

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen bg-slate-950 overflow-hidden">
      <LeftNav />
      <div className="flex-1 min-w-0 overflow-y-auto">
        {children}
      </div>
    </div>
  );
}
