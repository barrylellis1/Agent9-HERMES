/**
 * SettingsLayout — thin wrapper for all Settings pages.
 *
 * Used to render its own second full-height sidebar (mode-specific nav
 * tree) alongside the app-wide LeftNav — two panels, each anchoring its
 * own brand mark, live-caught by a user screenshot 2026-08-25. That nav
 * tree (NavItem/NavGroup types, MAINTENANCE_NAV/GOVERNANCE_NAV,
 * OnboardingNav, GroupNav) moved into LeftNav.tsx the same day, indented
 * directly beneath the "Settings" destination whenever a /settings/*
 * route is active — see LeftNav.tsx's own comment for the full story.
 *
 * What's left here is just AppShell, kept as a distinct name (rather than
 * having each of the 6 Settings pages import AppShell directly) in case
 * Settings content ever needs its own distinct wrapper again — e.g. a
 * max-width or padding convention that shouldn't apply to every AppShell
 * consumer.
 */
import { AppShell } from './shared/AppShell'

interface SettingsLayoutProps {
  children: React.ReactNode
}

export function SettingsLayout({ children }: SettingsLayoutProps) {
  return <AppShell>{children}</AppShell>
}
