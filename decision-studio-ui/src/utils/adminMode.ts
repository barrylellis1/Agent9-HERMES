/**
 * System Admin mode utilities.
 *
 * Two localStorage keys:
 *   a9_admin_mode           = 'true' when logged in as system admin
 *   a9_admin_target_client  = the client_id currently being worked on
 *
 * Admin tools (KPI Intelligence, Principal Intelligence, Data Onboarding) read
 * from getAdminTargetClient() instead of a9_active_client_id so their writes
 * always target the new client being onboarded, never the demo session client.
 *
 * The dashboard / SA / DA / SF pipeline requires a real principal and will
 * redirect admins back to /settings when they try to access it.
 */

export const ADMIN_MODE_KEY = 'a9_admin_mode';
export const ADMIN_TARGET_CLIENT_KEY = 'a9_admin_target_client';

export function isAdminMode(): boolean {
  return localStorage.getItem(ADMIN_MODE_KEY) === 'true';
}

export function getAdminTargetClient(): string {
  return localStorage.getItem(ADMIN_TARGET_CLIENT_KEY) ?? '';
}

export function setAdminTargetClient(clientId: string): void {
  localStorage.setItem(ADMIN_TARGET_CLIENT_KEY, clientId);
}

export function enterAdminMode(): void {
  localStorage.setItem(ADMIN_MODE_KEY, 'true');
  // Clear any active principal session so admin never accidentally runs
  // SA/DA/SF as a stale demo principal
  localStorage.removeItem('a9_auth_email');
}

export function exitAdminMode(): void {
  localStorage.removeItem(ADMIN_MODE_KEY);
  localStorage.removeItem(ADMIN_TARGET_CLIENT_KEY);
}

/**
 * Returns the client_id that admin tools should write to.
 * Falls back to a9_active_client_id for backward compatibility when
 * admin mode is not active (e.g. in unit tests or direct navigation).
 */
export function getToolTargetClientId(): string {
  if (isAdminMode()) {
    return getAdminTargetClient();
  }
  return localStorage.getItem('a9_active_client_id') ?? '';
}
