/**
 * Connection Profile Storage — Infra B (API-backed, Supabase-persisted)
 *
 * Profiles are stored in Supabase, scoped by client_id, with credentials
 * encrypted server-side.  Credential values are returned as ••••••  (never
 * the actual secret) so no sensitive data ever touches the browser.
 *
 * The public API mirrors the old localStorage interface so callers need only
 * add await and pass clientId.
 */

import {
  ConnectionProfile,
  CreateConnectionProfilePayload,
  UpdateConnectionProfilePayload,
  listConnectionProfiles as apiList,
  createConnectionProfile as apiCreate,
  updateConnectionProfile as apiUpdate,
  deleteConnectionProfile as apiDelete,
} from '../api/client';

// Re-export the shared type so consumers keep the same import path.
export type { ConnectionProfile };

function activeClientId(): string {
  return localStorage.getItem('a9_active_client_id') ?? '';
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export async function getConnectionProfiles(
  sourceSystem?: string,
): Promise<ConnectionProfile[]> {
  const cid = activeClientId();
  if (!cid) return [];
  return apiList(cid, sourceSystem);
}

export async function saveConnectionProfile(
  profile: Omit<CreateConnectionProfilePayload, 'client_id'>,
): Promise<ConnectionProfile> {
  const cid = activeClientId();
  if (!cid) throw new Error('No active client — cannot save connection profile.');
  return apiCreate({ ...profile, client_id: cid });
}

export async function updateConnectionProfileById(
  id: string,
  updates: Omit<UpdateConnectionProfilePayload, 'client_id'>,
): Promise<ConnectionProfile> {
  const cid = activeClientId();
  if (!cid) throw new Error('No active client — cannot update connection profile.');
  return apiUpdate(id, { ...updates, client_id: cid });
}

export async function deleteConnectionProfileById(id: string): Promise<void> {
  const cid = activeClientId();
  if (!cid) throw new Error('No active client — cannot delete connection profile.');
  return apiDelete(id, cid);
}

export async function markProfileAsUsed(id: string): Promise<void> {
  const cid = activeClientId();
  if (!cid) return;
  await apiUpdate(id, { client_id: cid, last_used_by: 'user' }).catch(() => {
    // Non-fatal — best-effort update.
  });
}

/**
 * Build the connection override dict that the data-product-onboarding API
 * expects.  Because credentials are always ••••••  on saved profiles, the
 * overrides only include non-credential fields (project, dataset, path, etc.).
 * The backend resolves secrets itself via the profile ID.
 */
export function getConnectionOverrides(profile: ConnectionProfile): Record<string, unknown> {
  switch (profile.source_system) {
    case 'bigquery':
      return {
        project: profile.database_name ?? '',
        dataset: profile.schema_name ?? '',
      };
    case 'duckdb':
      return { path: profile.database_name ?? '' };
    case 'snowflake':
      return {
        account: profile.host ?? '',
        warehouse: profile.schema_name ?? '',
        database: profile.database_name ?? '',
      };
    case 'databricks':
      return {
        host: profile.host ?? '',
        http_path: profile.schema_name ?? '',
      };
    default:
      return {};
  }
}
