import { useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Upload, FileType, Database, Check, Loader2 } from 'lucide-react'
import { uploadFile, UploadResponse, onboardDataProduct } from '../api/client'

// Step definitions
const STEPS = [
    { id: 'upload', label: 'Upload Mock Data', icon: Upload },
    { id: 'hydrate', label: 'Provision Mock View', icon: Database },
    { id: 'complete', label: 'Complete', icon: Check },
]

export function DataProductOnboarding() {
    const [currentStep, setCurrentStep] = useState(0)
    const [uploading, setUploading] = useState(false)
    const [uploadedFile, setUploadedFile] = useState<UploadResponse | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [hydrating, setHydrating] = useState(false)
    const [logs, setLogs] = useState<string[]>([])
    const fileInputRef = useRef<HTMLInputElement>(null)

    const [tableName, setTableName] = useState("FinancialTransactions")

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setUploading(true)
            setError(null)
            try {
                const file = e.target.files[0]
                const response = await uploadFile(file)
                setUploadedFile(response)
                // Auto-guess table name from filename if not set or default
                if (tableName === "FinancialTransactions") {
                    const name = file.name.split('.')[0]
                    // Sanitize
                    setTableName(name.replace(/[^a-zA-Z0-9_]/g, ''))
                }
                setCurrentStep(1)
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Upload failed')
            } finally {
                setUploading(false)
            }
        }
    }

    const handleHydrate = async () => {
        if (!uploadedFile) return
        
        setHydrating(true)
        setLogs(prev => [...prev, `Initializing Mock Table: ${tableName}...`])
        
        try {
            // MVP Hardcoded Payload for FI_Star_Schema
            // In a real app, we would let the user configure this in a middle step
            const payload = {
                principal_id: "admin_user",
                data_product_id: "FI_Star_Schema", // Matches the ID in the YAML
                source_system: "duckdb",
                database: "agent9-hermes-api.duckdb",
                // We treat the uploaded file as the source for the table
                // We pass the path in connection_overrides for the agent to use
                connection_overrides: {
                    "file_path": uploadedFile.filepath,
                    "table_name": tableName
                },
                tables: [tableName],
                data_product_name: "Finance Star Schema",
                data_product_domain: "Finance",
                data_product_description: "Core finance data product (Simulated from CSV).",
                // Auto-generate KPIs based on columns (MVP shortcut)
                qa_enabled: true
            }

            setLogs(prev => [...prev, `Provisioning Mock Table '${tableName}' from: ${uploadedFile.filename}`])
            
            // Trigger the backend workflow
            const result = await onboardDataProduct(payload)
            
            setLogs(prev => [...prev, "Mock Table Registered!"])
            setLogs(prev => [...prev, JSON.stringify(result, null, 2)])
            
            setCurrentStep(2) // Complete
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Onboarding failed')
            setLogs(prev => [...prev, `Error: ${err instanceof Error ? err.message : 'Unknown error'}`])
        } finally {
            setHydrating(false)
        }
    }

    return (
        <div className="min-h-screen bg-background text-foreground p-8 font-sans">
            {/* Header */}
            <header className="mb-8 flex justify-between items-center max-w-5xl mx-auto">
                <div className="flex items-center gap-4">
                    <Link to="/admin" className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight text-white">New Data Product</h1>
                        <p className="text-sm text-slate-400">FI_Star_Schema Onboarding</p>
                    </div>
                </div>
            </header>

            <main className="max-w-5xl mx-auto">
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
                    </div>

                    {/* Content Area */}
                    <div className="flex-1 bg-card border border-border rounded-xl p-8 min-h-[500px] relative">
                        {error && (
                            <div className="absolute top-4 left-4 right-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                                {error}
                            </div>
                        )}

                        {currentStep === 0 && (
                            <div className="text-center py-20">
                                <input 
                                    type="file" 
                                    ref={fileInputRef}
                                    onChange={handleFileSelect}
                                    className="hidden"
                                    accept=".csv,.parquet"
                                />
                                <Upload className="w-16 h-16 text-slate-600 mx-auto mb-6" />
                                <h3 className="text-xl font-semibold text-white mb-2">Upload Source Files</h3>
                                <p className="text-slate-400 mb-8 max-w-md mx-auto">
                                    Upload raw source tables (e.g. <code>FinancialTransactions.csv</code>) to seed the local DuckDB.
                                </p>
                                <button 
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={uploading}
                                    className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2 mx-auto"
                                >
                                    {uploading && <Loader2 className="w-4 h-4 animate-spin" />}
                                    {uploading ? 'Uploading...' : 'Select Files'}
                                </button>
                            </div>
                        )}
                        
                        {currentStep === 1 && (
                            <div className="py-8">
                                <div className="flex items-center gap-4 mb-8 p-4 bg-slate-900/50 rounded-lg border border-slate-800">
                                    <FileType className="w-8 h-8 text-blue-400" />
                                    <div>
                                        <h4 className="font-medium text-white">{uploadedFile?.filename}</h4>
                                        <p className="text-sm text-slate-400">{(uploadedFile?.size || 0) / 1024} KB • {uploadedFile?.content_type}</p>
                                    </div>
                                    <div className="ml-auto text-green-400 text-sm flex items-center gap-1">
                                        <Check className="w-4 h-4" /> Ready
                                    </div>
                                </div>

                                <div className="mb-6">
                                    <label className="block text-sm font-medium text-slate-400 mb-2">Target Table Name (DuckDB)</label>
                                    <input 
                                        type="text" 
                                        value={tableName}
                                        onChange={(e) => setTableName(e.target.value)}
                                        className="w-full p-3 bg-slate-950 border border-slate-800 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:outline-none"
                                    />
                                    <p className="text-xs text-slate-500 mt-2">This table will be created in the local DuckDB instance.</p>
                                </div>

                                <div className="space-y-4">
                                    <div className="p-4 bg-slate-900 rounded-lg h-64 overflow-y-auto font-mono text-xs text-slate-300 border border-slate-800">
                                        {logs.length === 0 ? (
                                            <span className="text-slate-600">// Workflow logs will appear here...</span>
                                        ) : (
                                            logs.map((log, i) => <div key={i}>{log}</div>)
                                        )}
                                    </div>

                                    <button 
                                        onClick={handleHydrate}
                                        disabled={hydrating}
                                        className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                                    >
                                        {hydrating && <Loader2 className="w-4 h-4 animate-spin" />}
                                        {hydrating ? 'Provision Mock Table' : 'Start Provisioning'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {currentStep === 2 && (
                            <div className="text-center py-20">
                                <div className="w-16 h-16 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
                                    <Check className="w-8 h-8" />
                                </div>
                                <h3 className="text-xl font-semibold text-white mb-2">Onboarding Complete!</h3>
                                <p className="text-slate-400 mb-8 max-w-md mx-auto">
                                    The Data Product <strong>FI_Star_Schema</strong> has been registered and the data is live.
                                </p>
                                <div className="flex justify-center gap-4">
                                    <Link 
                                        to="/"
                                        className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors"
                                    >
                                        Go to Decision Studio
                                    </Link>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    )
}
