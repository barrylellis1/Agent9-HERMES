/**
 * Connection Profile Manager — Infra B
 *
 * Profiles are now stored in Supabase (not browser localStorage).
 * Credentials are encrypted server-side and returned as ••••••  — the
 * browser never sees the actual secret values.
 */

import { useState, useEffect, useCallback } from 'react'
import { Database, Plus, Trash2, Check, Clock, RefreshCw, AlertTriangle } from 'lucide-react'
import {
  ConnectionProfile,
  getConnectionProfiles,
  saveConnectionProfile,
  deleteConnectionProfileById,
  markProfileAsUsed,
  getConnectionOverrides,
} from '../utils/connectionProfileStorage'

interface ConnectionProfileManagerProps {
  sourceSystem: string
  onSelectProfile: (profile: ConnectionProfile, overrides: Record<string, unknown>) => void
  currentValues?: {
    database?: string
    schema?: string
    serviceAccountPath?: string
    duckdbPath?: string
    host?: string
    port?: number
    password?: string
  }
}

export function ConnectionProfileManager({
  sourceSystem,
  onSelectProfile,
  currentValues,
}: ConnectionProfileManagerProps) {
  const [profiles, setProfiles] = useState<ConnectionProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [profileName, setProfileName] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const loadProfiles = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const all = await getConnectionProfiles(sourceSystem)
      setProfiles(all)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load profiles')
    } finally {
      setLoading(false)
    }
  }, [sourceSystem])

  useEffect(() => {
    loadProfiles()
  }, [loadProfiles])

  const handleSaveProfile = async () => {
    if (!profileName.trim()) return
    setSaving(true)
    setError(null)
    try {
      const credentials: Record<string, string> = {}

      if (sourceSystem === 'bigquery') {
        if (currentValues?.serviceAccountPath)
          credentials['service_account_path'] = currentValues.serviceAccountPath
      } else if (sourceSystem === 'snowflake' || sourceSystem === 'sqlserver') {
        if (currentValues?.password) credentials['password'] = currentValues.password
      }

      await saveConnectionProfile({
        name: profileName.trim(),
        source_system: sourceSystem,
        host: currentValues?.host,
        port: currentValues?.port,
        database_name: currentValues?.database,
        schema_name: currentValues?.schema,
        credentials: Object.keys(credentials).length > 0 ? credentials : undefined,
      })

      setShowSaveDialog(false)
      setProfileName('')
      await loadProfiles()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save profile')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteProfile = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!confirm('Delete this connection profile?')) return
    try {
      await deleteConnectionProfileById(id)
      if (selectedId === id) setSelectedId(null)
      await loadProfiles()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete profile')
    }
  }

  const handleSelectProfile = async (profile: ConnectionProfile) => {
    setSelectedId(profile.id)
    await markProfileAsUsed(profile.id)
    onSelectProfile(profile, getConnectionOverrides(profile))
  }

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '—'
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)
    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="space-y-4">
      {/* Security notice */}
      <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
        <p className="text-xs text-red-300">
          <strong>Credentials are encrypted server-side</strong> and never stored in the browser.
          Saved values shown as ••••••. Profiles are scoped to the active client tenant.
        </p>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Connection Profiles</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadProfiles}
            disabled={loading}
            className="p-1.5 text-slate-400 hover:text-white transition-colors"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => { setShowSaveDialog(true); setProfileName('') }}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Save Current
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-2 bg-red-900/30 border border-red-700 rounded text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Profile list */}
      {loading ? (
        <div className="p-6 text-center text-slate-500 text-sm">Loading profiles…</div>
      ) : profiles.length > 0 ? (
        <div className="space-y-2">
          {profiles.map((profile) => (
            <div
              key={profile.id}
              className={`p-4 rounded-lg border transition-all cursor-pointer ${
                selectedId === profile.id
                  ? 'bg-blue-500/10 border-blue-500'
                  : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
              }`}
              onClick={() => handleSelectProfile(profile)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-white">{profile.name}</h4>
                    {selectedId === profile.id && <Check className="w-4 h-4 text-blue-400" />}
                    {profile.is_default && (
                      <span className="text-xs bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded">default</span>
                    )}
                  </div>
                  <div className="mt-1 space-y-0.5">
                    {profile.host && (
                      <p className="text-sm text-slate-400">Host: {profile.host}</p>
                    )}
                    {profile.database_name && (
                      <p className="text-sm text-slate-400">Database: {profile.database_name}</p>
                    )}
                    {profile.schema_name && (
                      <p className="text-sm text-slate-400">Schema: {profile.schema_name}</p>
                    )}
                    {profile.credentials && Object.keys(profile.credentials).length > 0 && (
                      <p className="text-sm text-slate-500">
                        Credentials: {Object.keys(profile.credentials).join(', ')} (encrypted)
                      </p>
                    )}
                  </div>
                  <div className="mt-2 flex items-center gap-1 text-xs text-slate-500">
                    <Clock className="w-3 h-3" />
                    Last used {formatDate(profile.last_used_at ?? profile.updated_at)}
                  </div>
                </div>
                <button
                  onClick={(e) => handleDeleteProfile(profile.id, e)}
                  className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-8 text-center border border-dashed border-slate-700 rounded-lg">
          <Database className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400 mb-2">No saved profiles for {sourceSystem}</p>
          <p className="text-sm text-slate-500">Save your current connection to reuse it across sessions</p>
        </div>
      )}

      {/* Save dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 w-full max-w-md border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-1">Save Connection Profile</h3>
            <p className="text-xs text-slate-400 mb-4">
              Credentials are encrypted before storage. The browser never holds the raw secret.
            </p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Profile Name</label>
                <input
                  type="text"
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSaveProfile()}
                  placeholder="e.g., Production BigQuery"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  autoFocus
                />
              </div>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => { setShowSaveDialog(false); setProfileName('') }}
                  className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveProfile}
                  disabled={!profileName.trim() || saving}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                  {saving ? 'Saving…' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
