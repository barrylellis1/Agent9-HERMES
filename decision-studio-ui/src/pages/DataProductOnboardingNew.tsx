import { useState } from 'react'
import { Link } from 'react-router-dom'
import { 
    ArrowLeft, Settings, Search, Database, FileText, Check, 
    Loader2, ChevronRight, AlertCircle, Edit2, Link2, Sparkles, CheckCircle 
} from 'lucide-react'
import { KPIAssistantChat } from '../components/KPIAssistantChat'
import { ConnectionProfileManager } from '../components/ConnectionProfileManager'
import { DataProductSelector } from '../components/DataProductSelector'
import { API_BASE_URL, API_ENDPOINTS, buildUrl } from '../config/api-endpoints'
import { ConnectionProfile, markProfileAsUsed, getConnectionOverrides } from '../utils/connectionProfileStorage'

// Step definitions
const STEPS = [
    { id: 'connection', label: 'Connection Setup', icon: Settings },
    { id: 'discovery', label: 'Schema Discovery', icon: Search },
    { id: 'selection', label: 'Data Product Selection', icon: Database },
    { id: 'analysis', label: 'Metadata Analysis', icon: FileText },
    { id: 'kpis', label: 'KPI Definition', icon: Sparkles },
    { id: 'validation', label: 'Query Validation', icon: CheckCircle },
    { id: 'review', label: 'Review & Register', icon: Check },
]

interface TableInfo {
    name: string
    row_count?: number
    selected: boolean
    table_type?: string
}

interface ColumnProfile {
    name: string
    data_type: string
    is_nullable: boolean
    semantic_tags: string[]
}

interface ForeignKey {
    source_column: string
    target_table: string
    target_column: string
    confidence: number
}

interface TableProfile {
    name: string
    row_count: number
    columns: ColumnProfile[]
    primary_keys: string[]
    foreign_keys: ForeignKey[]
    table_role?: string
    view_definition?: string
}

interface InspectionResult {
    tables: TableProfile[]
    inferred_kpis: Array<{
        name: string
        expression: string
        description: string
        confidence: number
    }>
}

const SOURCE_SYSTEMS = [
    { value: 'duckdb', label: 'DuckDB (Local)', hasMetadata: false },
    { value: 'bigquery', label: 'Google BigQuery', hasMetadata: true },
    { value: 'snowflake', label: 'Snowflake', hasMetadata: true },
    { value: 'databricks', label: 'Databricks', hasMetadata: true },
]

export function DataProductOnboardingNew() {
    // Workflow mode
    const [workflowMode, setWorkflowMode] = useState<'select' | 'new' | 'extend'>('select')
    const [showProductSelector, setShowProductSelector] = useState(false)
    const [extendingProduct, setExtendingProduct] = useState<any>(null)
    
    const [currentStep, setCurrentStep] = useState(0)
    const [error, setError] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)
    const [logs, setLogs] = useState<string[]>([])

    // Step 1: Connection Setup
    const [sourceSystem, setSourceSystem] = useState('duckdb')
    const [database, setDatabase] = useState('')
    const [schema, setSchema] = useState('main')
    const [connectionOverrides, setConnectionOverrides] = useState<Record<string, any>>({})
    const [connectionProfiles, setConnectionProfiles] = useState<any[]>([])
    const [selectedProfile, setSelectedProfile] = useState('')
    const [profileName, setProfileName] = useState('')

    // Step 2: Schema Discovery
    const [discoveredTables, setDiscoveredTables] = useState<TableInfo[]>([])

    // Step 3: Data Product Selection
    const [dataProductId, setDataProductId] = useState('')
    const [dataProductName, setDataProductName] = useState('')
    const [dataProductDomain, setDataProductDomain] = useState('Finance')
    const [dataProductDescription, setDataProductDescription] = useState('')

    // Step 4: Metadata Analysis
    const [inspectionResult, setInspectionResult] = useState<InspectionResult | null>(null)
    const [editingColumn, setEditingColumn] = useState<{ table: string; column: string } | null>(null)

    // Step 5: KPI Definition
    const [definedKPIs, setDefinedKPIs] = useState<any[]>([])

    // Step 6: Query Validation
    const [validationResults, setValidationResults] = useState<any[]>([])
    const [validationStatus, setValidationStatus] = useState<string>('')
    const [validating, setValidating] = useState(false)

    const isPlatformMetadataRich = () => {
        return SOURCE_SYSTEMS.find(s => s.value === sourceSystem)?.hasMetadata || false
    }

    const handleQueryValidation = async () => {
        setError(null)
        setValidating(true)
        setLogs(prev => [...prev, `🔍 Validating ${definedKPIs.length} KPI queries...`])

        try {
            const response = await fetch(buildUrl(API_ENDPOINTS.workflows.dataProductOnboarding.validateQueries), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    request_id: `validate_${Date.now()}`,
                    principal_id: 'system',
                    data_product_id: dataProductId,
                    kpis: definedKPIs.map(kpi => ({
                        id: kpi.id,
                        name: kpi.name,
                        sql_query: kpi.sql_query,
                        data_product_id: dataProductId
                    })),
                    source_system: sourceSystem,
                    database: database,
                    schema: schema,
                    connection_overrides: connectionOverrides || {},
                    timeout_seconds: 30
                })
            })

            if (!response.ok) {
                const errorData = await response.json()
                throw new Error(errorData.detail || 'Validation request failed')
            }

            const data = await response.json()
            const validationData = data.data

            setValidationResults(validationData.results || [])
            setValidationStatus(validationData.overall_status || 'unknown')

            const passedCount = validationData.summary?.passed || 0
            const failedCount = validationData.summary?.failed || 0

            if (validationData.overall_status === 'all_passed') {
                setLogs(prev => [...prev, `✅ All ${passedCount} queries validated successfully`])
            } else if (validationData.overall_status === 'some_failed') {
                setLogs(prev => [...prev, `⚠️ ${passedCount} passed, ${failedCount} failed`])
            } else if (validationData.overall_status === 'all_failed') {
                setLogs(prev => [...prev, `❌ All ${failedCount} queries failed validation`])
            }

        } catch (err: any) {
            setError(`Validation failed: ${err.message}`)
            setLogs(prev => [...prev, `❌ Validation error: ${err.message}`])
        } finally {
            setValidating(false)
        }
    }

    const handleConnectionSetup = () => {
        setError(null)
        if (!sourceSystem) {
            setError('Please select a source system')
            return
        }
        if (sourceSystem === 'bigquery' && (!database || !schema)) {
            setError('Project and Dataset are required for BigQuery')
            return
        }
        setLogs(prev => [...prev, `✓ Connection configured: ${sourceSystem}`])
        setCurrentStep(1)
    }

    const handleSchemaDiscovery = async () => {
        setLoading(true)
        setError(null)
        setLogs(prev => [...prev, `🔍 Discovering tables in ${schema}...`])
        
        try {
            // Ensure connectionOverrides is always an object
            const overrides = connectionOverrides && Object.keys(connectionOverrides).length > 0 
                ? connectionOverrides 
                : {}
            
            console.log('Connection overrides:', overrides)
            
            const payload = {
                principal_id: 'admin_user',
                data_product_id: 'temp_discovery',
                source_system: sourceSystem,
                database: database || undefined,
                schema: schema,
                inspection_depth: 'basic',
                include_samples: false,
                environment: 'dev',
                connection_overrides: overrides,
            }
            
            console.log('Discovery payload:', JSON.stringify(payload, null, 2))

            const response = await fetch(buildUrl(API_ENDPOINTS.workflows.dataProductOnboarding.run), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })

            if (!response.ok) throw new Error('Discovery failed')
            
            const result = await response.json()
            const requestId = result.data.request_id
            
            // Poll for results
            let attempts = 0
            const pollInterval = setInterval(async () => {
                attempts++
                try {
                    const statusResponse = await fetch(buildUrl(API_ENDPOINTS.workflows.dataProductOnboarding.status(requestId)))
                    const statusData = await statusResponse.json()
                    
                    setLogs(prev => [...prev, `⏳ Poll ${attempts}: ${statusData.data.state}`])
                    
                    if (statusData.data.state === 'completed' || statusData.data.state === 'failed') {
                        clearInterval(pollInterval)
                        
                        // Extract tables from the inspect_source_schema step
                        const inspectionStep = statusData.data.result?.steps?.find((s: any) => s.name === 'inspect_source_schema')
                        const tables = inspectionStep?.details?.tables || []
                        
                        if (tables.length > 0) {
                            setDiscoveredTables(tables.map((t: any) => ({ 
                                name: t.name, 
                                row_count: t.row_count,
                                table_type: t.view_definition ? 'VIEW' : 'TABLE',
                                selected: false 
                            })))
                            setLogs(prev => [...prev, `✓ Discovered ${tables.length} tables/views`])
                            // Stay on step 1 to show table selection
                            setLoading(false)
                        } else if (statusData.data.state === 'failed') {
                            setError(statusData.data.result?.error_message || statusData.data.error || 'Workflow failed')
                            setLogs(prev => [...prev, `❌ Failed: ${statusData.data.result?.error_message || statusData.data.error || 'Unknown error'}`])
                            setLoading(false)
                        } else {
                            setError('No tables discovered')
                            setLogs(prev => [...prev, `⚠ No tables found in dataset`])
                            setLoading(false)
                        }
                    } else if (attempts > 60) {
                        clearInterval(pollInterval)
                        setError(`Timeout after ${attempts} seconds. Last state: ${statusData.data.state}`)
                        setLogs(prev => [...prev, `❌ Timeout at state: ${statusData.data.state}`])
                        setLoading(false)
                    }
                } catch (pollError) {
                    setLogs(prev => [...prev, `⚠ Poll error: ${pollError}`])
                }
            }, 1000)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Discovery failed')
            setLoading(false)
        }
    }

    const handleTableSelection = () => {
        const selected = discoveredTables.filter(t => t.selected)
        if (selected.length === 0) {
            setError('Please select at least one table')
            return
        }
        if (!dataProductId || !dataProductName) {
            setError('Please provide Data Product ID and Name')
            return
        }
        setError(null)
        setLogs(prev => [...prev, `✓ Selected ${selected.length} tables for ${dataProductId}`])
        setCurrentStep(3)
    }

    const handleMetadataAnalysis = async () => {
        setLoading(true)
        setError(null)
        const selectedTables = discoveredTables.filter(t => t.selected).map(t => t.name)
        setLogs(prev => [...prev, `🔬 Analyzing metadata for ${selectedTables.join(', ')}...`])
        
        try {
            const payload = {
                principal_id: 'admin_user',
                data_product_id: dataProductId,
                source_system: sourceSystem,
                database: database || undefined,
                schema: schema,
                tables: selectedTables,
                inspection_depth: 'standard',
                include_samples: false,
                environment: 'dev',
                connection_overrides: connectionOverrides,
                data_product_name: dataProductName,
                data_product_domain: dataProductDomain,
                data_product_description: dataProductDescription,
            }

            const response = await fetch(buildUrl(API_ENDPOINTS.workflows.dataProductOnboarding.run), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            })

            if (!response.ok) throw new Error('Analysis failed')
            
            const result = await response.json()
            const requestId = result.data.request_id
            
            // Poll for results
            let attempts = 0
            const pollInterval = setInterval(async () => {
                attempts++
                try {
                    const statusResponse = await fetch(buildUrl(API_ENDPOINTS.workflows.dataProductOnboarding.status(requestId)))
                    const statusData = await statusResponse.json()
                    
                    setLogs(prev => [...prev, `⏳ Poll ${attempts}: ${statusData.data.state}`])
                    
                    if (statusData.data.state === 'completed' || statusData.data.state === 'failed') {
                        clearInterval(pollInterval)
                        
                        // Extract inspection results from the inspect_source_schema step
                        const inspectionStep = statusData.data.result?.steps?.find((s: any) => s.name === 'inspect_source_schema')
                        const inspectionDetails = inspectionStep?.details
                        
                        if (inspectionDetails && inspectionDetails.tables && inspectionDetails.tables.length > 0) {
                            setInspectionResult(inspectionDetails)
                            setLogs(prev => [...prev, `✓ Analysis complete: ${inspectionDetails.tables.length} tables profiled`])
                            if (isPlatformMetadataRich()) {
                                setLogs(prev => [...prev, `✓ FK relationships extracted from catalog`])
                            } else {
                                setLogs(prev => [...prev, `⚠ FK relationships inferred (manual review recommended)`])
                            }
                            setCurrentStep(4)
                            setLoading(false)
                        } else if (statusData.data.state === 'failed') {
                            setError(statusData.data.result?.error_message || statusData.data.error || 'Analysis failed')
                            setLogs(prev => [...prev, `❌ Failed: ${statusData.data.result?.error_message || statusData.data.error || 'Unknown error'}`])
                            setLoading(false)
                        }
                    } else if (attempts > 60) {
                        clearInterval(pollInterval)
                        setError(`Timeout after ${attempts} seconds. Last state: ${statusData.data.state}`)
                        setLogs(prev => [...prev, `❌ Timeout at state: ${statusData.data.state}`])
                        setLoading(false)
                    }
                } catch (pollError) {
                    setLogs(prev => [...prev, `⚠ Poll error: ${pollError}`])
                }
            }, 1000)
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Analysis failed')
            setLoading(false)
        }
    }

    const toggleTableSelection = (tableName: string) => {
        setDiscoveredTables(prev => prev.map(t => 
            t.name === tableName ? { ...t, selected: !t.selected } : t
        ))
    }

    const updateSemanticTag = (tableName: string, columnName: string, newTags: string[]) => {
        if (!inspectionResult) return
        
        setInspectionResult({
            ...inspectionResult,
            tables: inspectionResult.tables.map(t => 
                t.name === tableName ? {
                    ...t,
                    columns: t.columns.map(c => 
                        c.name === columnName ? { ...c, semantic_tags: newTags } : c
                    )
                } : t
            )
        })
        setEditingColumn(null)
    }

    return (
        <div className="min-h-screen bg-background text-foreground p-8 font-sans">
            {/* Data Product Selector Modal */}
            {showProductSelector && (
                <DataProductSelector
                    onSelect={async (product) => {
                        setExtendingProduct(product)
                        setDataProductId(product.id)
                        setDataProductName(product.name)
                        setDataProductDomain(product.domain)
                        setSourceSystem(product.source_system)
                        setShowProductSelector(false)
                        setLogs(prev => [...prev, `Loading schema for ${product.name}...`])
                        
                        // Load product's schema from contract
                        try {
                            const response = await fetch(`http://localhost:8000/api/v1/registry/data-products/${product.id}`)
                            if (response.ok) {
                                const data = await response.json()
                                const productData = data.data
                                
                                // Extract connection info from existing KPIs for BigQuery table references
                                const existingKPIs = productData.kpis || []
                                
                                if (existingKPIs.length > 0 && productData.source_system === 'bigquery') {
                                    // Parse BigQuery table reference from first KPI's SQL
                                    const firstKPI = existingKPIs[0]
                                    const sqlQuery = firstKPI.sql_query || ''
                                    const bqTableMatch = sqlQuery.match(/`([^`]+)`/)
                                    if (bqTableMatch) {
                                        const fullTableRef = bqTableMatch[1] // e.g., "agent9-465818.SalesOrders.SalesOrderStarSchemaView"
                                        const parts = fullTableRef.split('.')
                                        if (parts.length === 3) {
                                            // Set connection profile from existing KPI (use database/schema state vars)
                                            setSourceSystem('bigquery')
                                            setDatabase(parts[0]) // BigQuery project ID
                                            setSchema(parts[1])   // BigQuery dataset ID
                                            setLogs(prev => [...prev, `✓ Extracted BigQuery connection: ${parts[0]}.${parts[1]}`])
                                        }
                                    }
                                }
                                
                                // Convert product tables to inspection result format
                                const tables = Object.entries(productData.tables || {}).map(([tableName, tableDef]: [string, any]) => ({
                                    name: tableName,
                                    row_count: 0,
                                    columns: Object.entries(tableDef.column_schema || {}).map(([colName, colType]: [string, any]) => ({
                                        name: colName,
                                        data_type: colType,
                                        semantic_tags: []
                                    })),
                                    primary_keys: tableDef.primary_keys || [],
                                    foreign_keys: []
                                }))
                                
                                setInspectionResult({ tables })
                                setDiscoveredTables(tables.map(t => ({ ...t, selected: true })))
                                setLogs(prev => [...prev, `✓ Loaded ${tables.length} tables from ${product.name}`])
                            }
                        } catch (err) {
                            console.error('Failed to load product schema:', err)
                            setLogs(prev => [...prev, `⚠ Could not load schema, proceeding with empty schema`])
                            // Set minimal inspection result to allow KPI definition
                            setInspectionResult({ tables: [] })
                        }
                        
                        setWorkflowMode('extend')
                        setCurrentStep(4) // Skip to KPI Definition
                        setLogs(prev => [...prev, `Extending data product: ${product.name} (${product.id})`])
                    }}
                    onCancel={() => {
                        setShowProductSelector(false)
                        setWorkflowMode('select')
                    }}
                />
            )}

            {/* Header */}
            <header className="mb-8 flex justify-between items-center max-w-6xl mx-auto">
                <div className="flex items-center gap-4">
                    {workflowMode === 'select' ? (
                        <Link to="/admin" className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors">
                            <ArrowLeft className="w-5 h-5" />
                        </Link>
                    ) : currentStep === 0 && workflowMode === 'new' ? (
                        <button 
                            onClick={() => {
                                setWorkflowMode('select')
                                setLogs([])
                            }}
                            className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                    ) : (
                        <Link to="/admin" className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors">
                            <ArrowLeft className="w-5 h-5" />
                        </Link>
                    )}
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight text-white">
                            {workflowMode === 'extend' ? 'Extend Data Product' : workflowMode === 'new' ? 'New Data Product' : 'Data Product Onboarding'}
                        </h1>
                        <p className="text-sm text-slate-400">
                            {workflowMode === 'extend' 
                                ? `Adding KPIs to ${extendingProduct?.name || 'existing product'}`
                                : workflowMode === 'new'
                                ? 'Platform-Adaptive Onboarding'
                                : 'Choose your workflow to get started'
                            }
                        </p>
                    </div>
                </div>
            </header>

            <main className="max-w-6xl mx-auto">
                {/* Mode Selection Screen */}
                {workflowMode === 'select' && (
                    <div className="max-w-2xl mx-auto">
                        <div className="text-center mb-8">
                            <h2 className="text-2xl font-bold text-white mb-2">Choose Your Workflow</h2>
                            <p className="text-slate-400">Create a new data product or add KPIs to an existing one</p>
                        </div>

                        <div className="grid grid-cols-2 gap-6">
                            {/* New Data Product */}
                            <button
                                onClick={() => {
                                    setWorkflowMode('new')
                                    setLogs(prev => [...prev, 'Starting new data product onboarding'])
                                }}
                                className="group p-8 bg-slate-800/50 hover:bg-slate-800 border-2 border-slate-700 hover:border-blue-500 rounded-xl transition-all text-left"
                            >
                                <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-500/20 transition-colors">
                                    <Database className="w-6 h-6 text-blue-400" />
                                </div>
                                <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors">
                                    New Data Product
                                </h3>
                                <p className="text-sm text-slate-400 mb-4">
                                    Start from scratch with schema discovery, metadata analysis, and KPI definition
                                </p>
                                <div className="flex items-center gap-2 text-sm text-blue-400">
                                    <span>Get Started</span>
                                    <ChevronRight className="w-4 h-4" />
                                </div>
                            </button>

                            {/* Extend Existing Product */}
                            <button
                                onClick={() => {
                                    setShowProductSelector(true)
                                    setLogs(prev => [...prev, 'Opening data product selector'])
                                }}
                                className="group p-8 bg-slate-800/50 hover:bg-slate-800 border-2 border-slate-700 hover:border-green-500 rounded-xl transition-all text-left"
                            >
                                <div className="w-12 h-12 bg-green-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-green-500/20 transition-colors">
                                    <Sparkles className="w-6 h-6 text-green-400" />
                                </div>
                                <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-green-400 transition-colors">
                                    Extend Existing Product
                                </h3>
                                <p className="text-sm text-slate-400 mb-4">
                                    Add new KPIs to a registered data product with pre-loaded context
                                </p>
                                <div className="flex items-center gap-2 text-sm text-green-400">
                                    <span>Select Product</span>
                                    <ChevronRight className="w-4 h-4" />
                                </div>
                            </button>
                        </div>

                        <div className="mt-8 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                            <div className="flex gap-3">
                                <div className="flex-shrink-0">
                                    <AlertCircle className="w-5 h-5 text-blue-400" />
                                </div>
                                <div className="text-sm text-blue-300">
                                    <p className="font-medium mb-1">Quick Tip</p>
                                    <p className="text-blue-300/80">
                                        Use "Extend Existing Product" to add KPIs without repeating schema discovery and metadata analysis. 
                                        Perfect for iterative KPI development!
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Main Workflow (shown when mode is 'new' or 'extend') */}
                {(workflowMode === 'new' || workflowMode === 'extend') && (
                <div className="flex gap-8">
                    {/* Stepper Sidebar */}
                    <div className="w-64 shrink-0">
                        <div className="flex flex-col gap-4">
                            {STEPS.map((step, idx) => {
                                const Icon = step.icon
                                const isActive = idx === currentStep
                                const isCompleted = idx < currentStep
                                return (
                                    <div key={step.id} className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${isActive ? 'bg-slate-800 text-white' : 'text-slate-500'}`}>
                                        <div className={`p-2 rounded-md ${isActive ? 'bg-blue-500/20 text-blue-400' : isCompleted ? 'bg-green-500/10 text-green-400' : 'bg-slate-800'}`}>
                                            <Icon className="w-4 h-4" />
                                        </div>
                                        <span className={`text-sm font-medium ${isActive ? 'text-white' : 'text-slate-400'}`}>{step.label}</span>
                                    </div>
                                )
                            })}
                        </div>

                        {/* Logs Panel */}
                        <div className="mt-8 p-4 bg-slate-900 rounded-lg border border-slate-800">
                            <h3 className="text-xs font-semibold text-slate-400 mb-2">WORKFLOW LOG</h3>
                            <div className="space-y-1 max-h-64 overflow-y-auto">
                                {logs.length === 0 ? (
                                    <p className="text-xs text-slate-600">No activity yet</p>
                                ) : (
                                    logs.map((log, i) => (
                                        <p key={i} className="text-xs text-slate-300 font-mono">{log}</p>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Content Area */}
                    <div className="flex-1 bg-card border border-border rounded-xl p-8 min-h-[600px] relative">
                        {error && (
                            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm flex items-start gap-2">
                                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                                <span>{error}</span>
                            </div>
                        )}

                        {/* Step 1: Connection Setup */}
                        {currentStep === 0 && (
                            <div className="py-8">
                                <h3 className="text-xl font-semibold text-white mb-6">Connection Setup</h3>
                                
                                <div className="space-y-6">
                                    {/* Connection Profile Manager */}
                                    <ConnectionProfileManager
                                        sourceSystem={sourceSystem}
                                        onSelectProfile={(profile) => {
                                            markProfileAsUsed(profile.id)
                                            
                                            if (profile.bigquery) {
                                                setDatabase(profile.bigquery.project)
                                                setSchema(profile.bigquery.dataset || '')
                                                setConnectionOverrides({
                                                    ...connectionOverrides,
                                                    service_account_json_path: profile.bigquery.serviceAccountPath || ''
                                                })
                                            } else if (profile.duckdb) {
                                                setSchema(profile.duckdb.path || 'main')
                                            }
                                            
                                            setLogs(prev => [...prev, `Loaded connection profile: ${profile.name}`])
                                        }}
                                        currentValues={{
                                            database,
                                            schema,
                                            serviceAccountPath: connectionOverrides.service_account_json_path,
                                        }}
                                    />

                                    <div className="border-t border-slate-800 pt-6">
                                        <h4 className="text-sm font-semibold text-slate-300 mb-4">Connection Details</h4>
                                        
                                        <div className="space-y-4">
                                            <div>
                                                <label className="block text-sm font-medium text-slate-400 mb-2">Source System</label>
                                                <select 
                                                    value={sourceSystem}
                                                    onChange={(e) => setSourceSystem(e.target.value)}
                                                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                                >
                                                    {SOURCE_SYSTEMS.map(sys => (
                                                        <option key={sys.value} value={sys.value}>{sys.label}</option>
                                                    ))}
                                                </select>
                                                {isPlatformMetadataRich() && (
                                                    <p className="text-xs text-green-400 mt-2 flex items-center gap-1">
                                                        <Check className="w-3 h-3" /> Metadata catalog available - FK relationships will be auto-extracted
                                                    </p>
                                                )}
                                            </div>

                                    {sourceSystem === 'bigquery' && (
                                        <>
                                            <div>
                                                <label className="block text-sm font-medium text-slate-400 mb-2">Project ID *</label>
                                                <input 
                                                    type="text" 
                                                    value={database}
                                                    onChange={(e) => setDatabase(e.target.value)}
                                                    placeholder="my-gcp-project"
                                                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-slate-400 mb-2">Dataset *</label>
                                                <input 
                                                    type="text" 
                                                    value={schema}
                                                    onChange={(e) => setSchema(e.target.value)}
                                                    placeholder="my_dataset"
                                                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-sm font-medium text-slate-400 mb-2">
                                                    Service Account JSON Path (Optional)
                                                </label>
                                                <input 
                                                    type="text" 
                                                    value={connectionOverrides.service_account_json_path || ''}
                                                    onChange={(e) => setConnectionOverrides({
                                                        ...connectionOverrides,
                                                        service_account_json_path: e.target.value
                                                    })}
                                                    placeholder="C:\Users\barry\.gcp\agent9-key.json"
                                                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none font-mono text-sm"
                                                />
                                                <p className="text-xs text-slate-500 mt-2">
                                                    Leave empty to use GOOGLE_APPLICATION_CREDENTIALS environment variable
                                                </p>
                                            </div>
                                        </>
                                    )}

                                    {sourceSystem === 'duckdb' && (
                                        <div>
                                            <label className="block text-sm font-medium text-slate-400 mb-2">Schema</label>
                                            <input 
                                                type="text" 
                                                value={schema}
                                                onChange={(e) => setSchema(e.target.value)}
                                                placeholder="main"
                                                className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                            />
                                            <p className="text-xs text-amber-400 mt-2 flex items-center gap-1">
                                                <AlertCircle className="w-3 h-3" /> FK relationships will be inferred - manual review recommended
                                            </p>
                                        </div>
                                    )}

                                    <button 
                                        onClick={handleConnectionSetup}
                                        className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                                    >
                                        Continue to Discovery <ChevronRight className="w-4 h-4" />
                                    </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Step 2: Schema Discovery */}
                        {currentStep === 1 && (
                            <div className="py-8">
                                <h3 className="text-xl font-semibold text-white mb-6">Schema Discovery</h3>
                                
                                {discoveredTables.length === 0 ? (
                                    <div className="text-center py-12">
                                        <Search className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                                        <p className="text-slate-400 mb-6">Ready to discover tables in <strong>{schema}</strong></p>
                                        <button 
                                            onClick={handleSchemaDiscovery}
                                            disabled={loading}
                                            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2 mx-auto"
                                        >
                                            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                                            {loading ? 'Discovering...' : 'Start Discovery'}
                                        </button>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        <p className="text-sm text-slate-400">Found {discoveredTables.length} tables/views</p>
                                        <div className="space-y-2 max-h-96 overflow-y-auto">
                                            {discoveredTables.map(table => (
                                                <div 
                                                    key={table.name}
                                                    onClick={() => toggleTableSelection(table.name)}
                                                    className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                                                        table.selected 
                                                            ? 'bg-blue-500/10 border-blue-500/30' 
                                                            : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'
                                                    }`}
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <h4 className="font-medium text-white">{table.name}</h4>
                                                            <p className="text-xs text-slate-400 mt-1">
                                                                {table.table_type} • {table.row_count?.toLocaleString() || 'Unknown'} rows
                                                            </p>
                                                        </div>
                                                        {table.selected && <Check className="w-5 h-5 text-blue-400" />}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                        <button 
                                            onClick={() => setCurrentStep(2)}
                                            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                                        >
                                            Continue to Selection <ChevronRight className="w-4 h-4" />
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Step 3: Data Product Selection */}
                        {currentStep === 2 && (
                            <div className="py-8">
                                <h3 className="text-xl font-semibold text-white mb-6">Data Product Selection</h3>
                                
                                <div className="space-y-6">
                                    <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
                                        <p className="text-sm text-slate-400 mb-2">Selected Tables:</p>
                                        <div className="flex flex-wrap gap-2">
                                            {discoveredTables.filter(t => t.selected).map(t => (
                                                <span key={t.name} className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-md text-sm">
                                                    {t.name}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-2">Data Product ID *</label>
                                        <input 
                                            type="text" 
                                            value={dataProductId}
                                            onChange={(e) => setDataProductId(e.target.value)}
                                            placeholder="dp_sales_analytics"
                                            className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-2">Data Product Name *</label>
                                        <input 
                                            type="text" 
                                            value={dataProductName}
                                            onChange={(e) => setDataProductName(e.target.value)}
                                            placeholder="Sales Analytics"
                                            className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-2">Domain</label>
                                        <select 
                                            value={dataProductDomain}
                                            onChange={(e) => setDataProductDomain(e.target.value)}
                                            className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                        >
                                            <option value="Finance">Finance</option>
                                            <option value="Operations">Operations</option>
                                            <option value="Marketing">Marketing</option>
                                            <option value="Sales">Sales</option>
                                            <option value="HR">Human Resources</option>
                                        </select>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-2">Description</label>
                                        <textarea 
                                            value={dataProductDescription}
                                            onChange={(e) => setDataProductDescription(e.target.value)}
                                            placeholder="Describe the business purpose of this data product..."
                                            rows={3}
                                            className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none"
                                        />
                                    </div>

                                    <button 
                                        onClick={handleTableSelection}
                                        className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                                    >
                                        Continue to Analysis <ChevronRight className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Step 4: Metadata Analysis */}
                        {currentStep === 3 && (
                            <div className="py-8">
                                <h3 className="text-xl font-semibold text-white mb-6">Metadata Analysis</h3>
                                
                                {!inspectionResult ? (
                                    <div className="text-center py-12">
                                        <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                                        <p className="text-slate-400 mb-6">Ready to analyze table metadata and relationships</p>
                                        <button 
                                            onClick={handleMetadataAnalysis}
                                            disabled={loading}
                                            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2 mx-auto"
                                        >
                                            {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                                            {loading ? 'Analyzing...' : 'Start Analysis'}
                                        </button>
                                    </div>
                                ) : (
                                    <div className="space-y-6">
                                        {/* Tables Overview */}
                                        {inspectionResult.tables.map(table => (
                                            <div key={table.name} className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
                                                <div className="flex items-center justify-between mb-4">
                                                    <div>
                                                        <h4 className="font-medium text-white">{table.name}</h4>
                                                        <p className="text-xs text-slate-400 mt-1">
                                                            {table.row_count?.toLocaleString()} rows • {table.columns.length} columns
                                                            {table.table_role && ` • ${table.table_role}`}
                                                        </p>
                                                    </div>
                                                </div>

                                                {/* FK Relationships */}
                                                {table.foreign_keys && table.foreign_keys.length > 0 && (
                                                    <div className="mb-4 p-3 bg-slate-950 rounded border border-slate-800">
                                                        <p className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1">
                                                            <Link2 className="w-3 h-3" /> FOREIGN KEY RELATIONSHIPS
                                                        </p>
                                                        <div className="space-y-1">
                                                            {table.foreign_keys.map((fk, idx) => (
                                                                <p key={idx} className="text-xs text-slate-300 font-mono">
                                                                    {fk.source_column} → {fk.target_table}.{fk.target_column}
                                                                    <span className={`ml-2 ${fk.confidence === 1.0 ? 'text-green-400' : 'text-amber-400'}`}>
                                                                        ({fk.confidence === 1.0 ? 'catalog' : 'inferred'})
                                                                    </span>
                                                                </p>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                {/* Columns with Semantic Tags */}
                                                <div className="space-y-2">
                                                    {table.columns.slice(0, 5).map(col => (
                                                        <div key={col.name} className="flex items-center justify-between p-2 bg-slate-950 rounded">
                                                            <div className="flex-1">
                                                                <span className="text-sm text-white font-mono">{col.name}</span>
                                                                <span className="text-xs text-slate-500 ml-2">{col.data_type}</span>
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <div className="flex gap-1">
                                                                    {col.semantic_tags.map(tag => (
                                                                        <span key={tag} className={`px-2 py-0.5 rounded text-xs ${
                                                                            tag === 'measure' ? 'bg-purple-500/20 text-purple-400' :
                                                                            tag === 'dimension' ? 'bg-blue-500/20 text-blue-400' :
                                                                            tag === 'time' ? 'bg-green-500/20 text-green-400' :
                                                                            tag === 'identifier' ? 'bg-amber-500/20 text-amber-400' :
                                                                            'bg-slate-700 text-slate-400'
                                                                        }`}>
                                                                            {tag}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                                <button 
                                                                    onClick={() => setEditingColumn({ table: table.name, column: col.name })}
                                                                    className="p-1 text-slate-500 hover:text-white transition-colors"
                                                                >
                                                                    <Edit2 className="w-3 h-3" />
                                                                </button>
                                                            </div>
                                                        </div>
                                                    ))}
                                                    {table.columns.length > 5 && (
                                                        <p className="text-xs text-slate-500 text-center">+ {table.columns.length - 5} more columns</p>
                                                    )}
                                                </div>
                                            </div>
                                        ))}

                                        <button 
                                            onClick={() => setCurrentStep(4)}
                                            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                                        >
                                            Continue to KPI Definition <ChevronRight className="w-4 h-4" />
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Step 5: KPI Definition */}
                        {currentStep === 4 && inspectionResult && (
                            <div className="py-8 h-full flex flex-col">
                                <div className="mb-6">
                                    <h3 className="text-xl font-semibold text-white mb-2">KPI Definition</h3>
                                    <p className="text-sm text-slate-400">
                                        Work with the AI assistant to define comprehensive KPIs with strategic metadata
                                    </p>
                                </div>
                                
                                <div className="flex-1 min-h-[500px]">
                                    <KPIAssistantChat
                                        dataProductId={dataProductId}
                                        domain={dataProductDomain}
                                        sourceSystem={sourceSystem}
                                        tables={discoveredTables.filter(t => t.selected).map(t => t.name)}
                                        database={database}
                                        schema={schema}
                                        schemaMetadata={{
                                            measures: inspectionResult.tables.flatMap(t => 
                                                t.columns.filter(c => c.semantic_tags.includes('measure')).map(c => ({
                                                    name: c.name,
                                                    data_type: c.data_type
                                                }))
                                            ),
                                            dimensions: inspectionResult.tables.flatMap(t => 
                                                t.columns.filter(c => c.semantic_tags.includes('dimension')).map(c => ({
                                                    name: c.name,
                                                    data_type: c.data_type
                                                }))
                                            ),
                                            time_columns: inspectionResult.tables.flatMap(t => 
                                                t.columns.filter(c => c.semantic_tags.includes('time')).map(c => ({
                                                    name: c.name,
                                                    data_type: c.data_type
                                                }))
                                            ),
                                            identifiers: inspectionResult.tables.flatMap(t => 
                                                t.columns.filter(c => c.semantic_tags.includes('identifier')).map(c => ({
                                                    name: c.name,
                                                    data_type: c.data_type
                                                }))
                                            )
                                        }}
                                        onKPIsFinalized={(kpis) => {
                                            setDefinedKPIs(kpis)
                                            setLogs(prev => [...prev, `✓ ${kpis.length} KPIs defined with strategic metadata`])
                                            setCurrentStep(5)
                                        }}
                                    />
                                </div>

                                <div className="mt-4 flex gap-4">
                                    <button 
                                        onClick={() => setCurrentStep(3)}
                                        className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors"
                                    >
                                        Back to Analysis
                                    </button>
                                    <button 
                                        onClick={() => {
                                            if (definedKPIs.length === 0) {
                                                setError('Please define at least one KPI or skip this step')
                                                return
                                            }
                                            setCurrentStep(5)
                                        }}
                                        className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                                    >
                                        Continue to Validation <ChevronRight className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Step 6: Query Validation */}
                        {currentStep === 5 && definedKPIs.length > 0 && (
                            <div className="py-8">
                                <h3 className="text-xl font-semibold text-white mb-6">Query Validation</h3>
                                <p className="text-slate-400 mb-6">
                                    Test your KPI queries against the data source to ensure they execute correctly.
                                </p>

                                {validationResults.length === 0 ? (
                                    <div className="space-y-4">
                                        <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                                            <p className="text-sm text-blue-400">
                                                Click "Test All Queries" to validate {definedKPIs.length} KPI {definedKPIs.length === 1 ? 'query' : 'queries'} against {sourceSystem}.
                                            </p>
                                        </div>

                                        <button
                                            onClick={handleQueryValidation}
                                            disabled={validating}
                                            className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                                        >
                                            {validating ? (
                                                <>
                                                    <Loader2 className="w-5 h-5 animate-spin" />
                                                    Validating Queries...
                                                </>
                                            ) : (
                                                <>
                                                    <CheckCircle className="w-5 h-5" />
                                                    Test All Queries
                                                </>
                                            )}
                                        </button>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {/* Validation Summary */}
                                        <div className={`p-4 rounded-lg border ${
                                            validationStatus === 'all_passed' 
                                                ? 'bg-green-500/10 border-green-500/20' 
                                                : validationStatus === 'some_failed'
                                                ? 'bg-yellow-500/10 border-yellow-500/20'
                                                : 'bg-red-500/10 border-red-500/20'
                                        }`}>
                                            <p className={`text-sm font-medium ${
                                                validationStatus === 'all_passed' 
                                                    ? 'text-green-400' 
                                                    : validationStatus === 'some_failed'
                                                    ? 'text-yellow-400'
                                                    : 'text-red-400'
                                            }`}>
                                                {validationStatus === 'all_passed' && '✅ All queries validated successfully'}
                                                {validationStatus === 'some_failed' && '⚠️ Some queries failed validation'}
                                                {validationStatus === 'all_failed' && '❌ All queries failed validation'}
                                            </p>
                                        </div>

                                        {/* Individual Query Results */}
                                        {validationResults.map((result: any) => (
                                            <div key={result.kpi_id} className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
                                                <div className="flex items-start justify-between mb-2">
                                                    <div className="flex items-center gap-2">
                                                        {result.status === 'success' ? (
                                                            <CheckCircle className="w-5 h-5 text-green-400 shrink-0" />
                                                        ) : (
                                                            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
                                                        )}
                                                        <h4 className="font-medium text-white">{result.kpi_name}</h4>
                                                    </div>
                                                    <span className="text-xs text-slate-400">{result.execution_time_ms}ms</span>
                                                </div>

                                                {result.status === 'success' ? (
                                                    <div className="mt-3">
                                                        <p className="text-sm text-slate-400 mb-2">
                                                            {result.row_count} {result.row_count === 1 ? 'row' : 'rows'} returned
                                                        </p>
                                                        {result.sample_rows && result.sample_rows.length > 0 && (
                                                            <div className="mt-2 p-3 bg-slate-950 rounded border border-slate-800 overflow-x-auto">
                                                                <table className="w-full text-xs">
                                                                    <thead>
                                                                        <tr className="text-slate-400 border-b border-slate-800">
                                                                            {Object.keys(result.sample_rows[0]).map((key: string) => (
                                                                                <th key={key} className="text-left py-1 px-2 font-medium">{key}</th>
                                                                            ))}
                                                                        </tr>
                                                                    </thead>
                                                                    <tbody>
                                                                        {result.sample_rows.slice(0, 5).map((row: any, idx: number) => (
                                                                            <tr key={idx} className="border-b border-slate-800/50">
                                                                                {Object.values(row).map((val: any, vidx: number) => (
                                                                                    <td key={vidx} className="py-1 px-2 text-slate-300">
                                                                                        {val !== null && val !== undefined ? String(val) : 'null'}
                                                                                    </td>
                                                                                ))}
                                                                            </tr>
                                                                        ))}
                                                                    </tbody>
                                                                </table>
                                                            </div>
                                                        )}
                                                    </div>
                                                ) : (
                                                    <div className="mt-3">
                                                        <p className="text-sm text-red-400 mb-1">
                                                            Error: {result.error_type || 'unknown'}
                                                        </p>
                                                        <p className="text-xs text-slate-400 font-mono bg-slate-950 p-2 rounded border border-slate-800">
                                                            {result.error_message}
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        ))}

                                        {/* Re-test Button */}
                                        <button
                                            onClick={handleQueryValidation}
                                            disabled={validating}
                                            className="w-full py-2 bg-slate-800 hover:bg-slate-700 disabled:bg-slate-900 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                                        >
                                            {validating ? (
                                                <>
                                                    <Loader2 className="w-4 h-4 animate-spin" />
                                                    Re-testing...
                                                </>
                                            ) : (
                                                <>
                                                    <CheckCircle className="w-4 h-4" />
                                                    Re-test Queries
                                                </>
                                            )}
                                        </button>
                                    </div>
                                )}

                                <div className="mt-6 flex gap-4">
                                    <button 
                                        onClick={() => setCurrentStep(4)}
                                        className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors"
                                    >
                                        Back to KPIs
                                    </button>
                                    <button 
                                        onClick={() => {
                                            if (validationResults.length === 0) {
                                                setError('Please run query validation before proceeding')
                                                return
                                            }
                                            setCurrentStep(6)
                                        }}
                                        disabled={validationResults.length === 0}
                                        className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                                    >
                                        Continue to Review <ChevronRight className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Step 7: Review & Register */}
                        {currentStep === 6 && inspectionResult && (
                            <div className="py-8">
                                <h3 className="text-xl font-semibold text-white mb-6">Review & Register</h3>
                                
                                <div className="space-y-6">
                                    <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800">
                                        <h4 className="font-medium text-white mb-2">Data Product Summary</h4>
                                        <dl className="space-y-2 text-sm">
                                            <div className="flex justify-between">
                                                <dt className="text-slate-400">ID:</dt>
                                                <dd className="text-white font-mono">{dataProductId}</dd>
                                            </div>
                                            <div className="flex justify-between">
                                                <dt className="text-slate-400">Name:</dt>
                                                <dd className="text-white">{dataProductName}</dd>
                                            </div>
                                            <div className="flex justify-between">
                                                <dt className="text-slate-400">Domain:</dt>
                                                <dd className="text-white">{dataProductDomain}</dd>
                                            </div>
                                            <div className="flex justify-between">
                                                <dt className="text-slate-400">Source System:</dt>
                                                <dd className="text-white">{sourceSystem}</dd>
                                            </div>
                                            <div className="flex justify-between">
                                                <dt className="text-slate-400">Tables:</dt>
                                                <dd className="text-white">{inspectionResult.tables.length}</dd>
                                            </div>
                                            <div className="flex justify-between">
                                                <dt className="text-slate-400">FK Relationships:</dt>
                                                <dd className="text-white">
                                                    {inspectionResult.tables.reduce((sum, t) => sum + (t.foreign_keys?.length || 0), 0)}
                                                </dd>
                                            </div>
                                            <div className="flex justify-between">
                                                <dt className="text-slate-400">Defined KPIs:</dt>
                                                <dd className="text-white">{definedKPIs.length}</dd>
                                            </div>
                                        </dl>
                                    </div>

                                    <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
                                        <p className="text-sm text-green-400 flex items-center gap-2">
                                            <Check className="w-4 h-4" />
                                            Ready to register data product to Agent9 registry
                                        </p>
                                    </div>

                                    <div className="flex gap-4">
                                        <button 
                                            onClick={() => setCurrentStep(4)}
                                            className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors"
                                        >
                                            Back to KPIs
                                        </button>
                                        <button 
                                            onClick={async () => {
                                                try {
                                                    setLogs(prev => [...prev, `Finalizing KPIs and registering data product...`])
                                                    
                                                    // Finalize KPIs - write them to the contract YAML
                                                    const finalizeResponse = await fetch(buildUrl(API_ENDPOINTS.kpiAssistant.finalize), {
                                                        method: 'POST',
                                                        headers: { 'Content-Type': 'application/json' },
                                                        body: JSON.stringify({
                                                            data_product_id: dataProductId,
                                                            kpis: definedKPIs,
                                                            extend_mode: workflowMode === 'extend'
                                                        })
                                                    })
                                                    
                                                    const finalizeData = await finalizeResponse.json()
                                                    console.log('Finalize response:', finalizeData)
                                                    
                                                    if (!finalizeResponse.ok || finalizeData.status === 'error') {
                                                        const errorMsg = finalizeData.error || finalizeData.detail || 'Failed to finalize KPIs'
                                                        throw new Error(errorMsg)
                                                    }
                                                    
                                                    setLogs(prev => [...prev, `✓ ${definedKPIs.length} KPIs persisted to contract YAML`])
                                                    setLogs(prev => [...prev, `✓ Data product ${dataProductId} registered successfully!`])
                                                } catch (error) {
                                                    console.error('Registration error:', error)
                                                    setLogs(prev => [...prev, `❌ Error registering data product: ${error}`])
                                                }
                                            }}
                                            className="flex-1 py-3 bg-green-600 hover:bg-green-500 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                                        >
                                            <Check className="w-4 h-4" />
                                            Register Data Product
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
                )}
            </main>
        </div>
    )
}
