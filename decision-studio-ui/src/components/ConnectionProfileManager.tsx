/**
 * Connection Profile Manager Component
 * 
 * Allows users to save, load, edit, and delete connection profiles
 * for reuse across data product onboarding sessions.
 */

import { useState } from 'react'
import { Database, Plus, Edit2, Trash2, Check, X, Clock } from 'lucide-react'
import {
  ConnectionProfile,
  getConnectionProfiles,
  saveConnectionProfile,
  updateConnectionProfile,
  deleteConnectionProfile,
  getConnectionOverrides,
} from '../utils/connectionProfileStorage'

interface ConnectionProfileManagerProps {
  sourceSystem: string
  onSelectProfile: (profile: ConnectionProfile) => void
  currentValues?: {
    database?: string
    schema?: string
    serviceAccountPath?: string
    duckdbPath?: string
  }
}

export function ConnectionProfileManager({
  sourceSystem,
  onSelectProfile,
  currentValues,
}: ConnectionProfileManagerProps) {
  const [profiles, setProfiles] = useState<ConnectionProfile[]>(getConnectionProfiles())
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [profileName, setProfileName] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const filteredProfiles = profiles.filter(p => p.sourceSystem === sourceSystem)

  const handleSaveProfile = () => {
    if (!profileName.trim()) return

    const profileData: any = {
      name: profileName.trim(),
      sourceSystem,
    }

    if (sourceSystem === 'bigquery') {
      profileData.bigquery = {
        project: currentValues?.database || '',
        dataset: currentValues?.schema || '',
        serviceAccountPath: currentValues?.serviceAccountPath || '',
      }
    } else if (sourceSystem === 'duckdb') {
      profileData.duckdb = {
        path: currentValues?.duckdbPath || '',
      }
    }

    if (editingId) {
      updateConnectionProfile(editingId, profileData)
    } else {
      saveConnectionProfile(profileData)
    }

    setProfiles(getConnectionProfiles())
    setShowSaveDialog(false)
    setProfileName('')
    setEditingId(null)
  }

  const handleDeleteProfile = (id: string) => {
    if (confirm('Are you sure you want to delete this connection profile?')) {
      deleteConnectionProfile(id)
      setProfiles(getConnectionProfiles())
      if (selectedId === id) {
        setSelectedId(null)
      }
    }
  }

  const handleSelectProfile = (profile: ConnectionProfile) => {
    setSelectedId(profile.id)
    onSelectProfile(profile)
  }

  const formatDate = (dateStr: string) => {
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
      {/* Info Banner */}
      <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
        <p className="text-xs text-blue-300">
          <strong>Note:</strong> Profiles are saved locally in your browser. They won't sync across devices or be shared with your team. 
          For production use, backend storage will be added in a future update.
        </p>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Connection Profiles</h3>
        </div>
        <button
          onClick={() => {
            setShowSaveDialog(true)
            setEditingId(null)
            setProfileName('')
          }}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-sm rounded-lg transition-colors flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Save Current
        </button>
      </div>

      {/* Profile List */}
      {filteredProfiles.length > 0 ? (
        <div className="space-y-2">
          {filteredProfiles.map((profile) => (
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
                    {selectedId === profile.id && (
                      <Check className="w-4 h-4 text-blue-400" />
                    )}
                  </div>
                  <div className="mt-1 space-y-1">
                    {profile.bigquery && (
                      <>
                        <p className="text-sm text-slate-400">
                          Project: {profile.bigquery.project}
                        </p>
                        {profile.bigquery.dataset && (
                          <p className="text-sm text-slate-400">
                            Dataset: {profile.bigquery.dataset}
                          </p>
                        )}
                      </>
                    )}
                    {profile.duckdb && (
                      <p className="text-sm text-slate-400">
                        Path: {profile.duckdb.path}
                      </p>
                    )}
                  </div>
                  <div className="mt-2 flex items-center gap-1 text-xs text-slate-500">
                    <Clock className="w-3 h-3" />
                    Last used {formatDate(profile.lastUsedAt)}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setEditingId(profile.id)
                      setProfileName(profile.name)
                      setShowSaveDialog(true)
                    }}
                    className="p-2 text-slate-400 hover:text-blue-400 transition-colors"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteProfile(profile.id)
                    }}
                    className="p-2 text-slate-400 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-8 text-center border border-dashed border-slate-700 rounded-lg">
          <Database className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400 mb-2">No saved profiles for {sourceSystem}</p>
          <p className="text-sm text-slate-500">
            Save your current connection to reuse it later
          </p>
        </div>
      )}

      {/* Save Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-6 w-full max-w-md border border-slate-700">
            <h3 className="text-lg font-semibold text-white mb-4">
              {editingId ? 'Edit Profile' : 'Save Connection Profile'}
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Profile Name
                </label>
                <input
                  type="text"
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  placeholder="e.g., Production BigQuery"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  autoFocus
                />
              </div>
              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => {
                    setShowSaveDialog(false)
                    setProfileName('')
                    setEditingId(null)
                  }}
                  className="px-4 py-2 text-slate-400 hover:text-white transition-colors flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  Cancel
                </button>
                <button
                  onClick={handleSaveProfile}
                  disabled={!profileName.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <Check className="w-4 h-4" />
                  {editingId ? 'Update' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
