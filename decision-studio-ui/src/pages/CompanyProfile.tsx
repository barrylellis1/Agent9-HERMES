import { useState, useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Loader2, Check, X, ChevronDown, ChevronUp, Building2, Lock } from 'lucide-react'
import { BrandLogo } from '../components/BrandLogo'
import { API_BASE_URL } from '../config/api-endpoints'

// ─── Types ───────────────────────────────────────────────────────────────────

const CLIENT_ID_KEY = 'a9_client_id'

/** Derive a client_id slug from a company name — mirrors the backend _slugify logic. */
function slugify(name: string): string {
  const cleaned = name
    .toLowerCase()
    .replace(/\b(inc|corp|ltd|llc|plc|gmbh|co|company|group|holdings?)\b\.?/gi, '')
  return cleaned
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40) || 'company'
}

interface BusinessContext {
  enterprise_name: string
  industry: string
  subindustry?: string
  revenue_band?: string
  employee_band?: string
  regions?: string[]
  go_to_market?: string[]
  products_services?: string[]
  primary_systems?: Record<string, string>
  data_maturity?: 'low' | 'medium' | 'high'
  risk_posture?: 'low' | 'medium' | 'high'
  compliance_requirements?: string[]
  strategic_priorities?: string[]
  operating_model?: string
  notes?: string
}

interface IndustryResearchResult {
  synthesis: string
  signals: Array<{ title?: string; [key: string]: unknown }>
  confidence: number
  benchmarks?: Record<string, unknown>
  themes?: string[]
}

// ─── Constants ───────────────────────────────────────────────────────────────

const REVENUE_BANDS = ['$10M–$50M', '$50M–$100M', '$100M–$500M', '$500M–$1B', '$1B–$5B', '$5B+']
const EMPLOYEE_BANDS = ['10–100', '100–500', '500–1k', '1k–5k', '5k–20k', '20k+']
const MATURITY_OPTIONS: Array<'low' | 'medium' | 'high'> = ['low', 'medium', 'high']
const RISK_OPTIONS: Array<'low' | 'medium' | 'high'> = ['low', 'medium', 'high']
const OPERATING_MODELS = ['Centralized', 'Decentralized', 'Hybrid']
const GTM_OPTIONS = ['B2B', 'B2C', 'B2B2C', 'D2C', 'Channel/Partner']

// ─── Reusable sub-components ─────────────────────────────────────────────────

function TagPillInput({
  label,
  values,
  onChange,
  maxItems,
  placeholder,
}: {
  label: string
  values: string[]
  onChange: (v: string[]) => void
  maxItems?: number
  placeholder?: string
}) {
  const [input, setInput] = useState('')

  const addTag = () => {
    const trimmed = input.trim()
    if (!trimmed) return
    if (maxItems && values.length >= maxItems) return
    if (values.includes(trimmed)) {
      setInput('')
      return
    }
    onChange([...values, trimmed])
    setInput('')
  }

  const removeTag = (tag: string) => {
    onChange(values.filter((v) => v !== tag))
  }

  return (
    <div>
      <label className="block text-sm font-medium text-slate-400 mb-2">{label}</label>
      <div className="flex flex-wrap gap-2 mb-2">
        {values.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-500/20 text-indigo-300 rounded-md text-sm"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(tag)}
              className="text-indigo-400 hover:text-white transition-colors ml-1"
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
      </div>
      {(!maxItems || values.length < maxItems) && (
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ',') {
                e.preventDefault()
                addTag()
              }
            }}
            placeholder={placeholder ?? 'Type and press Enter'}
            className="flex-1 p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={addTag}
            className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors"
          >
            Add
          </button>
        </div>
      )}
      {maxItems && values.length >= maxItems && (
        <p className="text-xs text-slate-500 mt-1">Maximum {maxItems} items reached.</p>
      )}
    </div>
  )
}

function SaveButton({
  onClick,
  isSaving,
  saved,
}: {
  onClick: () => void
  isSaving: boolean
  saved: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isSaving}
      className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white rounded-lg text-sm font-medium transition-colors"
    >
      {isSaving ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : saved ? (
        <Check className="w-4 h-4" />
      ) : null}
      {saved ? 'Saved' : 'Save'}
    </button>
  )
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function CompanyProfile() {
  // ── Profile state ──
  const [isNew, setIsNew] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)

  // Client ID — assigned on first create, locked after
  const [clientId, setClientId] = useState('')
  const [isClientIdLocked, setIsClientIdLocked] = useState(false)

  // Section 1 — Identity
  const [enterpriseName, setEnterpriseName] = useState('')
  const [industry, setIndustry] = useState('')
  const [subindustry, setSubindustry] = useState('')
  const [regions, setRegions] = useState<string[]>([])

  // Section 2 — Scale
  const [revenueBand, setRevenueBand] = useState('')
  const [employeeBand, setEmployeeBand] = useState('')

  // Section 3 — Strategy
  const [strategicPriorities, setStrategicPriorities] = useState<string[]>([])
  const [goToMarket, setGoToMarket] = useState<string[]>([])
  const [operatingModel, setOperatingModel] = useState('')

  // Section 4 — Governance
  const [riskPosture, setRiskPosture] = useState<'low' | 'medium' | 'high' | ''>('')
  const [dataMaturity, setDataMaturity] = useState<'low' | 'medium' | 'high' | ''>('')
  const [complianceRequirements, setComplianceRequirements] = useState<string[]>([])

  // Section 5 — Systems & Notes
  const [productsServices, setProductsServices] = useState<string[]>([])
  const [primarySystems, setPrimarySystems] = useState<Array<{ type: string; name: string }>>([])
  const [newSystemType, setNewSystemType] = useState('')
  const [newSystemName, setNewSystemName] = useState('')
  const [notes, setNotes] = useState('')

  // Save state per section
  const [saving, setSaving] = useState<Record<string, boolean>>({})
  const [saved, setSaved] = useState<Record<string, boolean>>({})

  // Industry research
  const [industryResearch, setIndustryResearch] = useState<IndustryResearchResult | null>(null)
  const [researchLoading, setResearchLoading] = useState(false)
  const [signalsOpen, setSignalsOpen] = useState(false)
  const [lastResearchedIndustry, setLastResearchedIndustry] = useState('')

  // Auto-derive client_id from enterprise name (only when not yet locked)
  const handleEnterpriseNameChange = (value: string) => {
    setEnterpriseName(value)
    if (!isClientIdLocked) {
      setClientId(slugify(value))
    }
  }

  // ── Populate form from loaded context ──
  const populateForm = (ctx: BusinessContext & { client_id?: string }) => {
    if (ctx.client_id) {
      setClientId(ctx.client_id)
      setIsClientIdLocked(true)
      localStorage.setItem(CLIENT_ID_KEY, ctx.client_id)
    }
    setEnterpriseName(ctx.enterprise_name ?? '')
    setIndustry(ctx.industry ?? '')
    setSubindustry(ctx.subindustry ?? '')
    setRegions(ctx.regions ?? [])
    setRevenueBand(ctx.revenue_band ?? '')
    setEmployeeBand(ctx.employee_band ?? '')
    setStrategicPriorities(ctx.strategic_priorities ?? [])
    setGoToMarket(ctx.go_to_market ?? [])
    setOperatingModel(ctx.operating_model ?? '')
    setRiskPosture((ctx.risk_posture as 'low' | 'medium' | 'high' | '') ?? '')
    setDataMaturity((ctx.data_maturity as 'low' | 'medium' | 'high' | '') ?? '')
    setComplianceRequirements(ctx.compliance_requirements ?? [])
    setProductsServices(ctx.products_services ?? [])
    setPrimarySystems(
      Object.entries(ctx.primary_systems ?? {}).map(([type, name]) => ({ type, name }))
    )
    setNotes(ctx.notes ?? '')
  }

  // ── On mount: load existing profile scoped to active client ──
  useEffect(() => {
    const load = async () => {
      try {
        // Use the client selected at login, falling back to the previously stored profile client
        const activeClientId = localStorage.getItem('a9_active_client_id') || localStorage.getItem(CLIENT_ID_KEY)
        const url = activeClientId
          ? `${API_BASE_URL}/api/v1/company-profile?client_id=${encodeURIComponent(activeClientId)}`
          : `${API_BASE_URL}/api/v1/company-profile`
        const res = await fetch(url)
        if (!res.ok) {
          setIsNew(true)
          return
        }
        const data = await res.json()
        if (!data || Object.keys(data).length === 0) {
          setIsNew(true)
        } else {
          populateForm(data as BusinessContext)
          setIsNew(false)
        }
      } catch {
        setLoadError('Could not reach the API. Using empty form.')
        setIsNew(true)
      }
    }
    load()
  }, [])

  // ── Build payload helpers ──
  const buildFullPayload = (): BusinessContext & { client_id?: string } => {
    const payload: BusinessContext & { client_id?: string } = {
      enterprise_name: enterpriseName,
      industry,
    }
    if (clientId) payload.client_id = clientId
    if (subindustry) payload.subindustry = subindustry
    if (revenueBand) payload.revenue_band = revenueBand
    if (employeeBand) payload.employee_band = employeeBand
    if (regions.length) payload.regions = regions
    if (goToMarket.length) payload.go_to_market = goToMarket
    if (productsServices.length) payload.products_services = productsServices
    if (primarySystems.length)
      payload.primary_systems = Object.fromEntries(primarySystems.map((s) => [s.type, s.name]))
    if (dataMaturity) payload.data_maturity = dataMaturity
    if (riskPosture) payload.risk_posture = riskPosture
    if (complianceRequirements.length) payload.compliance_requirements = complianceRequirements
    if (strategicPriorities.length) payload.strategic_priorities = strategicPriorities
    if (operatingModel) payload.operating_model = operatingModel
    if (notes) payload.notes = notes
    return payload
  }

  const flashSaved = (sectionId: string) => {
    setSaved((prev) => ({ ...prev, [sectionId]: true }))
    setTimeout(() => setSaved((prev) => ({ ...prev, [sectionId]: false })), 3000)
  }

  const saveSection = async (sectionId: string, partial: Partial<BusinessContext>) => {
    setSaving((prev) => ({ ...prev, [sectionId]: true }))
    try {
      if (isNew) {
        // First save — POST so that client_id is accepted and assigned
        const res = await fetch(`${API_BASE_URL}/api/v1/company-profile`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(buildFullPayload()),
        })
        if (res.ok) {
          const created = await res.json() as BusinessContext & { client_id?: string }
          if (created.client_id) {
            setClientId(created.client_id)
            setIsClientIdLocked(true)
            localStorage.setItem(CLIENT_ID_KEY, created.client_id)
          }
        }
        setIsNew(false)
      } else {
        await fetch(`${API_BASE_URL}/api/v1/company-profile`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(partial),
        })
      }
      flashSaved(sectionId)
    } catch {
      // Silently fail — don't crash the page on API errors during early dev
    } finally {
      setSaving((prev) => ({ ...prev, [sectionId]: false }))
    }
  }

  // ── Industry research ──
  const fetchIndustryResearch = useCallback(async () => {
    if (!industry || industry === lastResearchedIndustry) return
    setLastResearchedIndustry(industry)
    setResearchLoading(true)
    setIndustryResearch(null)
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/company-profile/industry-research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ industry, subindustry: subindustry || undefined }),
      })
      if (res.ok) {
        const data = await res.json() as IndustryResearchResult
        setIndustryResearch(data)
        // Persist benchmarks in localStorage so KPI assistant can use them for threshold calibration
        if (data.benchmarks && Object.keys(data.benchmarks).length > 0) {
          localStorage.setItem('a9_industry_benchmarks', JSON.stringify(data.benchmarks))
        }
      }
    } catch {
      // Sidebar is optional — don't show error
    } finally {
      setResearchLoading(false)
    }
  }, [industry, subindustry, lastResearchedIndustry])

  // ── GTM checkbox toggle ──
  const toggleGTM = (option: string) => {
    setGoToMarket((prev) =>
      prev.includes(option) ? prev.filter((v) => v !== option) : [...prev, option]
    )
  }

  // ── Primary systems helpers ──
  const addSystem = () => {
    if (!newSystemType.trim() || !newSystemName.trim()) return
    setPrimarySystems((prev) => [...prev, { type: newSystemType.trim(), name: newSystemName.trim() }])
    setNewSystemType('')
    setNewSystemName('')
  }

  const removeSystem = (idx: number) => {
    setPrimarySystems((prev) => prev.filter((_, i) => i !== idx))
  }

  // ── Input classes ──
  const inputCls =
    'w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none'
  const selectCls =
    'w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none'

  return (
    <div className="min-h-screen bg-background text-foreground p-8 font-sans">
      {/* Header */}
      <header className="mb-8 flex justify-between items-center max-w-6xl mx-auto">
        <div className="flex items-center gap-4">
          <Link
            to="/settings"
            className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Company Profile</h1>
            <p className="text-sm text-slate-400">
              Business context used for KPI suggestions and situational analysis
            </p>
          </div>
        </div>
        <BrandLogo size={32} />
      </header>

      {loadError && (
        <div className="max-w-6xl mx-auto mb-4 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-300 text-sm">
          {loadError}
        </div>
      )}

      <main className="max-w-6xl mx-auto">
        <div className="flex gap-8 items-start">
          {/* ── Left column: form ── */}
          <div className="flex-1 space-y-6">
            {/* Section 1 — Company Identity */}
            <div className="bg-card border border-border rounded-xl p-6">
              <div className="flex items-center gap-2 mb-5">
                <Building2 className="w-4 h-4 text-indigo-400" />
                <h2 className="text-base font-semibold text-white">Company Identity</h2>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">
                    Company Name <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    value={enterpriseName}
                    onChange={(e) => handleEnterpriseNameChange(e.target.value)}
                    placeholder="Acme Corporation"
                    className={inputCls}
                  />
                </div>

                {/* Client ID — auto-derived, editable before first save, locked after */}
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">
                    Client ID
                    {isClientIdLocked && (
                      <span className="ml-2 inline-flex items-center gap-1 text-xs text-slate-500 font-normal">
                        <Lock className="w-3 h-3" /> Locked — used as registry key across all data
                      </span>
                    )}
                    {!isClientIdLocked && (
                      <span className="ml-2 text-xs text-slate-500 font-normal">
                        Auto-derived · edit before first save
                      </span>
                    )}
                  </label>
                  {isClientIdLocked ? (
                    <div className="flex items-center gap-3 px-3 py-2.5 bg-slate-900/60 border border-slate-700 rounded-lg">
                      <code className="text-indigo-300 text-sm font-mono">{clientId}</code>
                      <span className="ml-auto text-xs text-slate-600">
                        stamps every KPI · principal · data product
                      </span>
                    </div>
                  ) : (
                    <input
                      type="text"
                      value={clientId}
                      onChange={(e) =>
                        setClientId(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-'))
                      }
                      placeholder="acme-corporation"
                      className={`${inputCls} font-mono`}
                    />
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">
                      Industry <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="text"
                      value={industry}
                      onChange={(e) => setIndustry(e.target.value)}
                      onBlur={fetchIndustryResearch}
                      placeholder="e.g. Oil & Gas, Manufacturing"
                      className={inputCls}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">
                      Sub-industry
                    </label>
                    <input
                      type="text"
                      value={subindustry}
                      onChange={(e) => setSubindustry(e.target.value)}
                      onBlur={fetchIndustryResearch}
                      placeholder="e.g. Lubricants, Exploration"
                      className={inputCls}
                    />
                  </div>
                </div>

                <TagPillInput
                  label="Regions (max 5)"
                  values={regions}
                  onChange={setRegions}
                  maxItems={5}
                  placeholder="e.g. North America, EMEA"
                />
              </div>

              <div className="mt-5 flex justify-end">
                <SaveButton
                  onClick={() =>
                    saveSection('identity', {
                      enterprise_name: enterpriseName,
                      industry,
                      subindustry: subindustry || undefined,
                      regions: regions.length ? regions : undefined,
                    })
                  }
                  isSaving={saving['identity'] ?? false}
                  saved={saved['identity'] ?? false}
                />
              </div>
            </div>

            {/* Section 2 — Scale */}
            <div className="bg-card border border-border rounded-xl p-6">
              <h2 className="text-base font-semibold text-white mb-5">Scale</h2>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">
                    Revenue Range
                  </label>
                  <select
                    value={revenueBand}
                    onChange={(e) => setRevenueBand(e.target.value)}
                    className={selectCls}
                  >
                    <option value="">Select range</option>
                    {REVENUE_BANDS.map((b) => (
                      <option key={b} value={b}>
                        {b}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">
                    Employee Count
                  </label>
                  <select
                    value={employeeBand}
                    onChange={(e) => setEmployeeBand(e.target.value)}
                    className={selectCls}
                  >
                    <option value="">Select range</option>
                    {EMPLOYEE_BANDS.map((b) => (
                      <option key={b} value={b}>
                        {b}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-5 flex justify-end">
                <SaveButton
                  onClick={() =>
                    saveSection('scale', {
                      revenue_band: revenueBand || undefined,
                      employee_band: employeeBand || undefined,
                    })
                  }
                  isSaving={saving['scale'] ?? false}
                  saved={saved['scale'] ?? false}
                />
              </div>
            </div>

            {/* Section 3 — Strategy */}
            <div className="bg-card border border-border rounded-xl p-6">
              <h2 className="text-base font-semibold text-white mb-5">Strategy</h2>

              <div className="space-y-4">
                <TagPillInput
                  label="Strategic Priorities (max 3)"
                  values={strategicPriorities}
                  onChange={setStrategicPriorities}
                  maxItems={3}
                  placeholder="e.g. Margin expansion, Geographic growth"
                />

                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">
                    Go-to-Market
                  </label>
                  <div className="flex flex-wrap gap-3">
                    {GTM_OPTIONS.map((opt) => (
                      <label
                        key={opt}
                        className="flex items-center gap-2 cursor-pointer select-none"
                      >
                        <input
                          type="checkbox"
                          checked={goToMarket.includes(opt)}
                          onChange={() => toggleGTM(opt)}
                          className="w-4 h-4 accent-indigo-500"
                        />
                        <span className="text-sm text-slate-300">{opt}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">
                    Operating Model
                  </label>
                  <select
                    value={operatingModel}
                    onChange={(e) => setOperatingModel(e.target.value)}
                    className={selectCls}
                  >
                    <option value="">Select model</option>
                    {OPERATING_MODELS.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-5 flex justify-end">
                <SaveButton
                  onClick={() =>
                    saveSection('strategy', {
                      strategic_priorities: strategicPriorities.length
                        ? strategicPriorities
                        : undefined,
                      go_to_market: goToMarket.length ? goToMarket : undefined,
                      operating_model: operatingModel || undefined,
                    })
                  }
                  isSaving={saving['strategy'] ?? false}
                  saved={saved['strategy'] ?? false}
                />
              </div>
            </div>

            {/* Section 4 — Governance */}
            <div className="bg-card border border-border rounded-xl p-6">
              <h2 className="text-base font-semibold text-white mb-5">Governance</h2>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">
                      Risk Posture
                    </label>
                    <select
                      value={riskPosture}
                      onChange={(e) =>
                        setRiskPosture(e.target.value as 'low' | 'medium' | 'high' | '')
                      }
                      className={selectCls}
                    >
                      <option value="">Select</option>
                      {RISK_OPTIONS.map((o) => (
                        <option key={o} value={o}>
                          {o.charAt(0).toUpperCase() + o.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">
                      Data Maturity
                    </label>
                    <select
                      value={dataMaturity}
                      onChange={(e) =>
                        setDataMaturity(e.target.value as 'low' | 'medium' | 'high' | '')
                      }
                      className={selectCls}
                    >
                      <option value="">Select</option>
                      {MATURITY_OPTIONS.map((o) => (
                        <option key={o} value={o}>
                          {o.charAt(0).toUpperCase() + o.slice(1)}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <TagPillInput
                  label="Compliance Requirements"
                  values={complianceRequirements}
                  onChange={setComplianceRequirements}
                  placeholder="e.g. SOX, HIPAA, GDPR"
                />
              </div>

              <div className="mt-5 flex justify-end">
                <SaveButton
                  onClick={() =>
                    saveSection('governance', {
                      risk_posture: riskPosture || undefined,
                      data_maturity: dataMaturity || undefined,
                      compliance_requirements: complianceRequirements.length
                        ? complianceRequirements
                        : undefined,
                    })
                  }
                  isSaving={saving['governance'] ?? false}
                  saved={saved['governance'] ?? false}
                />
              </div>
            </div>

            {/* Section 5 — Systems & Notes */}
            <div className="bg-card border border-border rounded-xl p-6">
              <h2 className="text-base font-semibold text-white mb-5">Systems & Notes</h2>

              <div className="space-y-4">
                <TagPillInput
                  label="Products & Services (max 5)"
                  values={productsServices}
                  onChange={setProductsServices}
                  maxItems={5}
                  placeholder="e.g. Industrial Lubricants, Greases"
                />

                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">
                    Primary Systems
                  </label>
                  {primarySystems.length > 0 && (
                    <div className="space-y-2 mb-3">
                      {primarySystems.map((sys, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-3 p-3 bg-slate-900/50 border border-slate-800 rounded-lg"
                        >
                          <span className="text-xs font-medium text-slate-400 w-24 shrink-0">
                            {sys.type}
                          </span>
                          <span className="flex-1 text-sm text-white">{sys.name}</span>
                          <button
                            type="button"
                            onClick={() => removeSystem(idx)}
                            className="text-slate-500 hover:text-red-400 transition-colors"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newSystemType}
                      onChange={(e) => setNewSystemType(e.target.value)}
                      placeholder="System type (e.g. ERP)"
                      className="w-40 p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    />
                    <input
                      type="text"
                      value={newSystemName}
                      onChange={(e) => setNewSystemName(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && addSystem()}
                      placeholder="System name (e.g. SAP S/4HANA)"
                      className="flex-1 p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={addSystem}
                      className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors"
                    >
                      Add
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">
                    Notes
                    <span className="ml-2 text-slate-600 font-normal">
                      {notes.length}/160
                    </span>
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value.slice(0, 160))}
                    maxLength={160}
                    rows={3}
                    placeholder="Any additional context relevant to KPI analysis..."
                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none"
                  />
                </div>
              </div>

              <div className="mt-5 flex justify-end">
                <SaveButton
                  onClick={() =>
                    saveSection('systems', {
                      products_services: productsServices.length ? productsServices : undefined,
                      primary_systems: primarySystems.length
                        ? Object.fromEntries(primarySystems.map((s) => [s.type, s.name]))
                        : undefined,
                      notes: notes || undefined,
                    })
                  }
                  isSaving={saving['systems'] ?? false}
                  saved={saved['systems'] ?? false}
                />
              </div>
            </div>
          </div>

          {/* ── Right column: Industry Intelligence sidebar ── */}
          <div className="w-80 shrink-0 sticky top-8">
            <div className="bg-card border border-border rounded-xl p-5">
              <h2 className="text-base font-semibold text-white mb-4">Industry Benchmarks</h2>

              {!industry && !researchLoading && !industryResearch && (
                <p className="text-sm text-slate-400 leading-relaxed">
                  Enter your industry to see relevant benchmarks and KPI suggestions.
                </p>
              )}

              {researchLoading && (
                <div className="flex items-center gap-2 text-slate-400 py-4">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Researching {industry}...</span>
                </div>
              )}

              {industryResearch && !researchLoading && (
                <div className="space-y-4">
                  {/* Confidence badge */}
                  <div>
                    {industryResearch.confidence >= 0.7 ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-green-500/15 text-green-400 rounded-full text-xs font-medium">
                        <Check className="w-3 h-3" />
                        High confidence
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-1 bg-amber-500/15 text-amber-400 rounded-full text-xs font-medium">
                        Moderate
                      </span>
                    )}
                  </div>

                  {/* Themes as section headings */}
                  {industryResearch.themes && industryResearch.themes.length > 0 && (
                    <div className="space-y-1">
                      {industryResearch.themes.map((theme, i) => (
                        <div key={i} className="flex items-start gap-2 text-xs text-indigo-300">
                          <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
                          {theme}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Synthesis narrative — collapsible to avoid wall of text */}
                  <details className="group">
                    <summary className="cursor-pointer text-xs font-medium text-slate-400 hover:text-white transition-colors list-none flex items-center gap-1">
                      <ChevronDown className="w-3 h-3 group-open:rotate-180 transition-transform" />
                      Read full analysis
                    </summary>
                    <p className="mt-3 text-xs text-slate-300 leading-relaxed whitespace-pre-line border-l-2 border-slate-700 pl-3">
                      {industryResearch.synthesis}
                    </p>
                  </details>

                  {/* Key quantitative benchmarks — used by KPI assistant for threshold calibration */}
                  {industryResearch.benchmarks && Object.keys(industryResearch.benchmarks).length > 0 && (
                    <div className="border border-indigo-500/20 bg-indigo-500/5 rounded-lg p-3">
                      <p className="text-xs font-semibold text-indigo-300 mb-2">
                        Key Benchmarks → KPI Thresholds
                      </p>
                      <div className="space-y-1.5">
                        {Object.entries(industryResearch.benchmarks).slice(0, 8).map(([key, val]) => {
                          const formatVal = (v: unknown): string => {
                            if (v === null || v === undefined) return 'N/A'
                            if (typeof v === 'object') {
                              // Flatten nested objects: join their values with ' – '
                              const parts = Object.entries(v as Record<string, unknown>)
                                .map(([k, vv]) => `${k.replace(/_/g, ' ')}: ${vv}`)
                              return parts.join(' | ')
                            }
                            return String(v)
                          }
                          return (
                          <div key={key} className="flex justify-between gap-2 items-start">
                            <span className="text-xs text-slate-400 leading-relaxed">
                              {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                            </span>
                            <span className="text-xs text-white font-mono shrink-0 text-right max-w-[55%]">{formatVal(val)}</span>
                          </div>
                          )
                        })}
                      </div>
                      <p className="text-xs text-slate-500 mt-2 italic">
                        These benchmarks will pre-calibrate KPI thresholds during onboarding.
      </p>
                    </div>
                  )}

                  {/* Market signals collapsible */}
                  {industryResearch.signals.length > 0 && (
                    <div className="border-t border-slate-800 pt-3">
                      <button
                        type="button"
                        onClick={() => setSignalsOpen((prev) => !prev)}
                        className="flex items-center justify-between w-full text-sm font-medium text-slate-300 hover:text-white transition-colors"
                      >
                        <span>Market Signals ({industryResearch.signals.length})</span>
                        {signalsOpen ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>

                      {signalsOpen && (
                        <ul className="mt-3 space-y-2">
                          {industryResearch.signals.map((signal, idx) => (
                            <li key={idx} className="text-xs text-slate-400 flex items-start gap-2">
                              <span className="mt-0.5 w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
                              {signal.title ?? `Signal ${idx + 1}`}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
