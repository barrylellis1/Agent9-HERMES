/**
 * Connection Profile Storage Utility
 * 
 * Manages saving, loading, and deleting connection profiles for data product onboarding.
 * Profiles are stored in browser localStorage for quick access across sessions.
 * 
 * LIMITATIONS (localStorage approach):
 * - Profiles are per-browser/device (not synced across devices)
 * - Lost if browser cache is cleared
 * - Not shared with team members
 * - Credentials stored unencrypted in browser
 * - 5-10MB storage limit
 * 
 * SUITABLE FOR:
 * - Individual developer workflows
 * - Local development and testing
 * - Personal productivity improvements
 * 
 * MIGRATION PATH:
 * - Phase 1 (Current): localStorage for MVP
 * - Phase 2 (Hardening): Migrate to backend storage with Supabase
 * - Phase 3 (Production): Add encryption, team sharing, access controls
 */

export interface ConnectionProfile {
  id: string
  name: string
  sourceSystem: 'bigquery' | 'duckdb' | 'snowflake' | 'databricks'
  createdAt: string
  lastUsedAt: string
  
  // BigQuery specific
  bigquery?: {
    project: string
    dataset?: string
    serviceAccountPath?: string
  }
  
  // DuckDB specific
  duckdb?: {
    path: string
  }
  
  // Snowflake specific (future)
  snowflake?: {
    account: string
    warehouse?: string
    database?: string
    schema?: string
  }
  
  // Databricks specific (future)
  databricks?: {
    host: string
    httpPath?: string
    catalog?: string
    schema?: string
  }
}

const STORAGE_KEY = 'agent9_connection_profiles'

/**
 * Get all saved connection profiles
 */
export function getConnectionProfiles(): ConnectionProfile[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return []
    
    const profiles = JSON.parse(stored) as ConnectionProfile[]
    return profiles.sort((a, b) => 
      new Date(b.lastUsedAt).getTime() - new Date(a.lastUsedAt).getTime()
    )
  } catch (error) {
    console.error('Error loading connection profiles:', error)
    return []
  }
}

/**
 * Save a new connection profile
 */
export function saveConnectionProfile(profile: Omit<ConnectionProfile, 'id' | 'createdAt' | 'lastUsedAt'>): ConnectionProfile {
  const profiles = getConnectionProfiles()
  
  const newProfile: ConnectionProfile = {
    ...profile,
    id: `profile_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    createdAt: new Date().toISOString(),
    lastUsedAt: new Date().toISOString(),
  }
  
  profiles.push(newProfile)
  localStorage.setItem(STORAGE_KEY, JSON.stringify(profiles))
  
  return newProfile
}

/**
 * Update an existing connection profile
 */
export function updateConnectionProfile(id: string, updates: Partial<Omit<ConnectionProfile, 'id' | 'createdAt'>>): ConnectionProfile | null {
  const profiles = getConnectionProfiles()
  const index = profiles.findIndex(p => p.id === id)
  
  if (index === -1) return null
  
  profiles[index] = {
    ...profiles[index],
    ...updates,
    lastUsedAt: new Date().toISOString(),
  }
  
  localStorage.setItem(STORAGE_KEY, JSON.stringify(profiles))
  return profiles[index]
}

/**
 * Delete a connection profile
 */
export function deleteConnectionProfile(id: string): boolean {
  const profiles = getConnectionProfiles()
  const filtered = profiles.filter(p => p.id !== id)
  
  if (filtered.length === profiles.length) return false
  
  localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
  return true
}

/**
 * Get a specific connection profile by ID
 */
export function getConnectionProfile(id: string): ConnectionProfile | null {
  const profiles = getConnectionProfiles()
  return profiles.find(p => p.id === id) || null
}

/**
 * Mark a profile as recently used (updates lastUsedAt)
 */
export function markProfileAsUsed(id: string): void {
  updateConnectionProfile(id, {})
}

/**
 * Get connection overrides from a profile for API requests
 */
export function getConnectionOverrides(profile: ConnectionProfile): Record<string, any> {
  switch (profile.sourceSystem) {
    case 'bigquery':
      return {
        service_account_json_path: profile.bigquery?.serviceAccountPath || '',
      }
    case 'duckdb':
      return {
        path: profile.duckdb?.path || '',
      }
    case 'snowflake':
      return {
        account: profile.snowflake?.account || '',
        warehouse: profile.snowflake?.warehouse,
        database: profile.snowflake?.database,
        schema: profile.snowflake?.schema,
      }
    case 'databricks':
      return {
        host: profile.databricks?.host || '',
        http_path: profile.databricks?.httpPath,
        catalog: profile.databricks?.catalog,
        schema: profile.databricks?.schema,
      }
    default:
      return {}
  }
}
