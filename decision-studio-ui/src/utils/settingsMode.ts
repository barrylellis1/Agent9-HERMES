/**
 * Settings mode detection.
 *
 * Three distinct modes drive the left-nav structure in Settings:
 *
 *   Mode 1 — ONBOARDING  (System Admin, one-time per client)
 *     Activated by: a9_admin_mode === 'true' in localStorage
 *     Nav: Day 1–6 sequential onboarding steps
 *
 *   Mode 2 — MAINTENANCE  (Product Owner, ongoing)
 *     Activated by: logged-in principal has metadata.settings_admin === 'true'
 *     Nav: Registry / Intelligence / Ownership / Workspace groups
 *
 *   Mode 3 — GOVERNANCE  (C-level executive, read-mostly)
 *     Activated by: all other logged-in principals
 *     Nav: Strategic / Registry (read-only) / Assessment groups
 *
 * Keys used:
 *   a9_admin_mode          'true' when in system-admin onboarding mode
 *   a9_settings_mode       'maintenance' | 'governance' — set at login
 *   a9_admin_target_client target client being onboarded (admin mode only)
 *   a9_active_client_id    session client (normal login)
 */

export type SettingsMode = 'onboarding' | 'maintenance' | 'governance';

export function getSettingsMode(): SettingsMode {
  if (localStorage.getItem('a9_admin_mode') === 'true') return 'onboarding';
  const stored = localStorage.getItem('a9_settings_mode');
  if (stored === 'maintenance') return 'maintenance';
  return 'governance';
}

export function setSettingsMode(mode: 'maintenance' | 'governance'): void {
  localStorage.setItem('a9_settings_mode', mode);
}

/** Returns the client_id to scope all Settings operations. */
export function getSettingsClientId(): string {
  if (localStorage.getItem('a9_admin_mode') === 'true') {
    return localStorage.getItem('a9_admin_target_client') ?? '';
  }
  return localStorage.getItem('a9_active_client_id') ?? '';
}

// Re-export admin helpers for convenience
export { isAdminMode, getToolTargetClientId, enterAdminMode, exitAdminMode } from './adminMode';
