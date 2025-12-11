import { useState, useEffect, useCallback, useMemo } from 'react'
import { RidgelineScanner } from '../components/visualizations/RidgelineScanner'
import { SnowflakeScanner, SnowflakeDimension } from '../components/visualizations/SnowflakeScanner'
import { detectSituations, runDeepAnalysis, runSolutionFinder } from '../api/client'
import { RefreshCw, Settings, X, ArrowRight, CheckCircle2, AlertTriangle, ChevronRight, ChevronLeft, User, Microscope, Loader2, Lightbulb, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'

// Mock Data for the Ridgeline Scanner (Simulating System Pulse)
const MOCK_HISTORY = Array.from({ length: 12 }).map((_, i) => ({
  date: `Month ${i + 1}`,
  distributions: [
    { 
      id: "kpi_revenue", 
      label: "Gross Revenue", 
      // Drifts negative significantly in later months (simulating the breach)
      data: Array.from({ length: 50 }).map(() => Math.random() * 0.6 + (i > 8 ? -0.5 : 0.1)) 
    },
    { 
      id: "kpi_payroll", 
      label: "Payroll Cost", 
      // Stable
      data: Array.from({ length: 50 }).map(() => Math.random() * 0.4 + 0.1) 
    },
    { 
      id: "kpi_margin", 
      label: "Operating Margin", 
      // Slight variance
      data: Array.from({ length: 50 }).map(() => Math.random() * 0.5 - 0.1) 
    }
  ]
}))

export function DecisionStudio() {
  const [history] = useState(MOCK_HISTORY)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const [situations, setSituations] = useState<any[]>([])
  const [scanComplete, setScanComplete] = useState(false)
  const [selectedSituation, setSelectedSituation] = useState<any | null>(null)
  
  // Deep Analysis State
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResults, setAnalysisResults] = useState<Record<string, any>>({})
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  
  // Comparison State
  const [comparing, setComparing] = useState(false)
  const [comparisonData, setComparisonData] = useState<any | null>(null)
  
  // View Mode for Deep Analysis
  const [daViewMode, setDaViewMode] = useState<"list" | "snowflake">("snowflake")

  // Transform Deep Analysis for Snowflake
  const snowflakeData = useMemo(() => {
      if (!selectedSituation || !analysisResults) return []
      const currentAnalysis = analysisResults[selectedSituation.situation_id]
      if (!currentAnalysis?.kt_is_is_not) return []
      
      const kt = currentAnalysis.kt_is_is_not
      const map = new Map<string, any[]>()
      
      const process = (list: any[]) => {
          if (!list) return
          list.forEach(item => {
              if (!item.dimension) return
              if (!map.has(item.dimension)) map.set(item.dimension, [])
              let pct = 0.0
              const prev = parseFloat(item.previous) || 0
              const curr = parseFloat(item.current) || 0
              const delta = parseFloat(item.delta) || (curr - prev)
              if (prev !== 0) pct = delta / Math.abs(prev)
              else if (delta !== 0) pct = delta > 0 ? 1 : -1

              const dimArray = map.get(item.dimension)
              if (dimArray) {
                  dimArray.push({
                      id: item.key || Math.random().toString(),
                      label: item.key || 'Unknown',
                      value: curr,
                      delta: delta,
                      deltaPct: pct
                  })
              }
          })
      }
      process(kt.where_is)
      process(kt.where_is_not)
      
      return Array.from(map.entries()).map(([dim, attrs]) => ({
          id: dim,
          label: dim,
          attributes: attrs
      }))
  }, [selectedSituation, analysisResults])

  // Solution Finder State
  const [findingSolutions, setFindingSolutions] = useState(false)
  const [solutions, setSolutions] = useState<any | null>(null)
  const [showPersonaSelector, setShowPersonaSelector] = useState(false)
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>(["CFO", "Supply Chain Expert", "Data Scientist"])
  const [principalInput, setPrincipalInput] = useState<{current_priorities: string[], known_constraints: string[]}>({
      current_priorities: [],
      known_constraints: []
  })
  const [priorityText, setPriorityText] = useState("")
  const [constraintText, setConstraintText] = useState("")

  const AVAILABLE_PERSONAS = [
    { id: "CFO", label: "CFO", icon: User, color: "text-emerald-400" },
    { id: "Supply Chain Expert", label: "Supply Chain", icon: User, color: "text-amber-400" },
    { id: "Data Scientist", label: "Data Scientist", icon: User, color: "text-blue-400" },
    { id: "Sales VP", label: "Sales VP", icon: User, color: "text-purple-400" },
    { id: "Compliance Officer", label: "Compliance", icon: User, color: "text-red-400" }
  ]

  const handleRefresh = async () => {
    setLoading(true)
    setError(null)
    setStatusMsg(null)
    setScanComplete(false)
    setAnalysisResults({})
    setAnalysisError(null)
    setComparisonData(null)
    setSolutions(null)
    setShowPersonaSelector(false)
    try {
      console.log("Calling Agent9 API...")
      const result = await detectSituations()
      console.log("Agent9 Response:", result)
      
      if (result && result.length > 0) {
        setSituations(result)
        setScanComplete(true)
        setStatusMsg(`Scan Complete: ${result.length} situations detected.`)
      } else {
        setSituations([])
        setScanComplete(true)
        setStatusMsg("Scan Complete: No anomalies detected.")
        console.log("No situations found.")
      }
    } catch (err) {
      console.error("API Error:", err)
      setError(err instanceof Error ? err.message : "Failed to connect to Agent9")
    } finally {
      setLoading(false)
    }
  }

  const handleDeepAnalysis = async () => {
    if (!selectedSituation) return
    const sitId = selectedSituation.situation_id
    
    setAnalyzing(true)
    setAnalysisError(null)
    try {
        const result = await runDeepAnalysis(sitId, selectedSituation.kpi_name)
        console.log("Deep Analysis Result:", result)
        
        if (!result || !result.execution) {
            throw new Error("Analysis completed but returned no results.")
        }

        setAnalysisResults(prev => ({
            ...prev,
            [sitId]: result.execution // Store the execution part of the response
        }))
    } catch (err) {
        console.error("Analysis Failed", err)
        setAnalysisError(err instanceof Error ? err.message : "Analysis failed unexpectedly")
    } finally {
        setAnalyzing(false)
    }
  }

  const handleCompare = async () => {
    setComparing(true)
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1200))
    
    // Dynamic Mock Data based on Deep Analysis Findings
    // If we know the top driver, we compare along that dimension
    let dimension = "Profit Center"
    let segments = [
        { name: "North America", value: 42000000, target: 45000000, status: "critical" },
        { name: "Europe", value: 38500000, target: 38000000, status: "good" },
        { name: "APAC", value: 31000000, target: 30500000, status: "good" },
        { name: "LatAm", value: 12000000, target: 12200000, status: "warning" }
    ]

    // Check current analysis for context
    const topDriver = currentAnalysis?.change_points?.[0]?.dimension
    if (topDriver === 'Customer Type Name') {
        dimension = "Customer Segment"
        segments = [
            { name: "Enterprise (B2B)", value: 85000000, target: 90000000, status: "critical" },
            { name: "SMB", value: 45000000, target: 42000000, status: "good" },
            { name: "Government", value: 28000000, target: 28000000, status: "good" }
        ]
    } else if (topDriver === 'Product Name') {
        dimension = "Product Group"
        segments = [
            { name: "Electronics", value: 12000000, target: 15000000, status: "critical" },
            { name: "Home Goods", value: 8000000, target: 8200000, status: "good" },
            { name: "Apparel", value: 5000000, target: 5100000, status: "good" }
        ]
    }

    setComparisonData({
        dimension,
        segments
    })
    setComparing(false)
  }

  const handleSolution = async () => {
    if (!currentAnalysis) return
    setShowPersonaSelector(true)
  }

  const handleStartDebate = async () => {
    setFindingSolutions(true)
    setShowPersonaSelector(false)
    try {
        const daRequestId = currentAnalysis.request_id
        // Prepare principal input object
        const pInput = {
            ...principalInput,
            // Merge current text inputs if not empty
            current_priorities: [...principalInput.current_priorities, ...(priorityText ? [priorityText] : [])],
            known_constraints: [...principalInput.known_constraints, ...(constraintText ? [constraintText] : [])]
        }
        
        const result = await runSolutionFinder(daRequestId, selectedPersonas, pInput)
        
        // Extract solutions and transcript
        const solResponse = result.solutions
        console.log("Full Solution Response:", solResponse)
        setSolutions(solResponse)
        
    } catch (err) {
        console.error("Solution Finder Failed", err)
    } finally {
        setFindingSolutions(false)
    }
  }

  // Navigation Logic
  const currentIndex = selectedSituation 
    ? situations.findIndex(s => s.situation_id === selectedSituation.situation_id)
    : -1

  const hasNext = currentIndex < situations.length - 1
  const hasPrev = currentIndex > 0

  const handleNext = useCallback(() => {
    if (hasNext) setSelectedSituation(situations[currentIndex + 1])
  }, [currentIndex, hasNext, situations])

  const handlePrev = useCallback(() => {
    if (hasPrev) setSelectedSituation(situations[currentIndex - 1])
  }, [currentIndex, hasPrev, situations])

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!selectedSituation) return
      if (e.key === 'ArrowRight') handleNext()
      if (e.key === 'ArrowLeft') handlePrev()
      if (e.key === 'Escape') setSelectedSituation(null)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedSituation, handleNext, handlePrev])


  // Derived state for summary
  const breachCount = situations.length
  const kpisScanned = 14 // Mock for now, would come from registry
  const impactLevel = breachCount > 3 ? 'High' : breachCount > 0 ? 'Medium' : 'Low'
  const impactColor = breachCount > 3 ? 'text-red-400' : breachCount > 0 ? 'text-amber-400' : 'text-green-400'
  const principalName = "Chief Financial Officer" // MVP Context

  // Current analysis result
  const currentAnalysis = selectedSituation ? analysisResults[selectedSituation.situation_id] : null

  return (
    <div className="min-h-screen bg-background text-foreground p-8 font-sans relative overflow-x-hidden">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Decision Studio</h1>
          <p className="text-slate-400">Situation Awareness Console</p>
        </div>
        <div className="flex items-start gap-4">
            <div className="flex flex-col items-end gap-2">
            <button 
                onClick={handleRefresh}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                {loading ? 'Scanning...' : 'Scan Now'}
            </button>
            {statusMsg && (
                <span className="text-xs text-emerald-400 font-medium animate-in fade-in slide-in-from-right-4">
                {statusMsg}
                </span>
            )}
            </div>
            
            <Link to="/admin" className="p-2 text-slate-400 hover:text-white transition-colors" title="Admin Console">
                <Settings className="w-5 h-5" />
            </Link>
        </div>
      </header>

      {/* KPI Evaluation Summary */}
      {scanComplete && (
        <section className="mb-8 animate-in slide-in-from-top-4 fade-in duration-500">
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 grid grid-cols-1 md:grid-cols-4 gap-6 items-center">
                <div className="col-span-1 border-r border-slate-800 pr-6">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Principal Context</h3>
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold text-xs">CF</div>
                        <div>
                            <div className="text-sm font-medium text-white">{principalName}</div>
                            <div className="text-xs text-slate-400">Finance & Strategy</div>
                        </div>
                    </div>
                </div>
                
                <div className="col-span-1 border-r border-slate-800 pr-6">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Scan Coverage</h3>
                    <div className="text-2xl font-light text-white">{kpisScanned} <span className="text-sm text-slate-500 font-normal">KPIs Evaluated</span></div>
                    <div className="text-xs text-slate-400 mt-1">Across 1 Data Product (FI Star Schema)</div>
                </div>

                <div className="col-span-1 border-r border-slate-800 pr-6">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Results</h3>
                    <div className="flex items-baseline gap-2">
                        <span className={`text-2xl font-bold ${breachCount > 0 ? 'text-red-400' : 'text-green-400'}`}>{breachCount}</span>
                        <span className="text-sm text-slate-400">Situations Detected</span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">{kpisScanned - breachCount} KPIs within normal range</div>
                </div>

                <div className="col-span-1">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Impact Category</h3>
                    <div className={`text-lg font-medium ${impactColor} flex items-center gap-2`}>
                        {impactLevel.toUpperCase()} IMPACT
                        <div className={`w-2 h-2 rounded-full ${breachCount > 3 ? 'bg-red-500' : 'bg-amber-500'}`}></div>
                    </div>
                    {situations.length > 0 && (
                        <div className="text-xs text-slate-400 mt-1 truncate">
                            Top: {situations[0].kpi_name || 'Gross Revenue'}
                        </div>
                    )}
                </div>
            </div>
        </section>
      )}

      {error && (
        <div className="mb-8 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
          Error: {error}. Is the Agent9 backend running on port 8000?
        </div>
      )}

      <main className="max-w-5xl mx-auto space-y-8 pb-20">
        
        {/* State 1: Scanner View (Initial) */}
        {!scanComplete && (
            <section className="bg-card border border-border rounded-xl p-6 shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-20 text-9xl font-bold text-slate-800 -z-0 select-none">
                    KPI
                </div>
                
                <div className="relative z-10">
                    <div className="flex justify-between items-center mb-6">
                    <div>
                        <h2 className="text-xl font-semibold text-white">Global KPI Health Monitor</h2>
                        <p className="text-sm text-slate-400">Real-time variance distribution across key performance indicators</p>
                    </div>
                    </div>

                    {/* The Ridgeline Component */}
                    <div className="h-[400px] w-full bg-slate-900/50 rounded-lg p-4 border border-border/50">
                        <RidgelineScanner history={history} />
                    </div>
                </div>
            </section>
        )}

        {/* State 2: Situation Feed (Post-Scan) */}
        {scanComplete && (
            <div className="space-y-4">
                <h2 className="text-lg font-semibold text-white mb-4">Priority Briefings</h2>
                {situations.map((sit, idx) => (
                    <div 
                        key={idx}
                        onClick={() => setSelectedSituation(sit)}
                        className="bg-card hover:bg-slate-800/50 border border-border rounded-xl p-6 cursor-pointer transition-all hover:border-slate-600 group relative overflow-hidden"
                    >
                        <div className="flex justify-between items-start">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                    <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs font-bold rounded uppercase tracking-wide">
                                        {sit.severity || 'CRITICAL'}
                                    </span>
                                    <span className="text-slate-500 text-xs uppercase tracking-wider">{sit.kpi_name}</span>
                                </div>
                                <h3 className="text-xl font-medium text-white mb-2 group-hover:text-blue-400 transition-colors">
                                    {sit.description || `${sit.kpi_name} breach detected`}
                                </h3>
                                <p className="text-slate-400 text-sm max-w-2xl line-clamp-2">
                                    {sit.business_impact || "Significant variance detected against operational thresholds. Immediate attention recommended."}
                                </p>
                            </div>
                            <div className="flex items-center text-slate-600 group-hover:text-blue-400 transition-colors">
                                <ChevronRight className="w-6 h-6" />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        )}
      </main>

      {/* Detail Panel Overlay (Analyst Briefing) */}
      <AnimatePresence>
        {selectedSituation && (
            <>
                {/* Backdrop */}
                <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.5 }}
                    exit={{ opacity: 0 }}
                    onClick={() => setSelectedSituation(null)}
                    className="fixed inset-0 bg-black z-40 backdrop-blur-sm"
                />
                
                {/* Side Panel */}
                <motion.div 
                    initial={{ x: "100%" }}
                    animate={{ x: 0 }}
                    exit={{ x: "100%" }}
                    transition={{ type: "spring", damping: 30, stiffness: 300 }}
                    className="fixed inset-y-0 right-0 w-full max-w-2xl bg-slate-900 border-l border-slate-800 z-50 shadow-2xl flex flex-col"
                >
                    {/* Panel Header */}
                    <div className="p-6 border-b border-slate-800 flex justify-between items-start bg-slate-900/50 backdrop-blur-md">
                        <div>
                            <div className="flex items-center gap-3 mb-3">
                                <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs font-bold rounded uppercase tracking-wide">
                                    {selectedSituation.severity || 'CRITICAL'}
                                </span>
                                <span className="text-slate-500 text-xs uppercase tracking-wider">ID: {selectedSituation.situation_id?.substring(0,8)}</span>
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-1">
                                {selectedSituation.kpi_name} Variance
                            </h2>
                            <p className="text-slate-400 text-sm">Detected at {new Date().toLocaleTimeString()}</p>
                        </div>
                        <div className="flex items-center gap-2">
                            {/* Navigation Buttons */}
                            <button 
                                onClick={handlePrev}
                                disabled={!hasPrev}
                                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-30"
                                title="Previous Situation (Left Arrow)"
                            >
                                <ChevronLeft className="w-6 h-6" />
                            </button>
                            <button 
                                onClick={handleNext}
                                disabled={!hasNext}
                                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-30"
                                title="Next Situation (Right Arrow)"
                            >
                                <ChevronRight className="w-6 h-6" />
                            </button>
                            <div className="w-px h-6 bg-slate-800 mx-2"></div>
                            <button 
                                onClick={() => setSelectedSituation(null)}
                                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                            >
                                <X className="w-6 h-6" />
                            </button>
                        </div>
                    </div>

                    {/* Panel Content - Scrollable */}
                    <div className="flex-1 overflow-y-auto p-8 space-y-8">
                        
                        {/* 1. Executive Summary */}
                        <section>
                            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <AlertTriangle className="w-4 h-4" />
                                Executive Briefing
                            </h3>
                            <div className="bg-slate-800/30 rounded-xl p-6 border border-slate-800 text-slate-300 leading-relaxed">
                                <p className="mb-4 text-lg text-white">
                                    {selectedSituation.description || "The system has detected a significant anomaly in this KPI."}
                                </p>
                                <p className="text-sm text-slate-400">
                                    {selectedSituation.business_impact || "This variance exceeds standard operational thresholds and may impact quarterly targets if not addressed. Primary drivers appear to be localized within specific business units."}
                                </p>
                            </div>
                        </section>

                        {/* Deep Analysis Results Injection */}
                        {analysisError && (
                            <div className="mb-4 p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-200 text-sm">
                                <strong>Analysis Error:</strong> {analysisError}
                            </div>
                        )}
                        
                        {currentAnalysis && (
                            <section className="animate-in fade-in slide-in-from-bottom-4">
                                <h3 className="text-sm font-bold text-blue-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                    <Microscope className="w-4 h-4" />
                                    Deep Analysis Findings
                                </h3>
                                <div className="bg-blue-900/10 rounded-xl p-6 border border-blue-500/20 text-slate-300">
                                    {/* Debug Output for empty results */}
                                    {!currentAnalysis.scqa_summary && !currentAnalysis.change_points?.length && (
                                        <div className="text-xs font-mono text-slate-500 mb-2">
                                            Raw Result: {JSON.stringify(currentAnalysis).substring(0, 200)}...
                                        </div>
                                    )}

                                    {currentAnalysis.scqa_summary ? (
                                        <div className="prose prose-invert prose-sm max-w-none">
                                            {/* Simple rendering for now; markdown parsing would be better */}
                                            <div className="whitespace-pre-wrap font-sans">{currentAnalysis.scqa_summary}</div>
                                        </div>
                                    ) : (
                                        <p>Analysis complete. Reviewing change points...</p>
                                    )}

                                    {/* Change Points Visualization / Snowflake Scanner */}
                                    <div className="mt-6">
                                        <div className="flex items-center justify-between mb-3">
                                            <h4 className="text-xs font-semibold text-blue-300 uppercase">Analysis View</h4>
                                            <div className="flex bg-slate-900 rounded p-1 border border-slate-800">
                                                <button 
                                                    onClick={() => setDaViewMode("list")}
                                                    className={`px-3 py-1 text-xs rounded ${daViewMode === 'list' ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'}`}
                                                >
                                                    List
                                                </button>
                                                <button 
                                                    onClick={() => setDaViewMode("snowflake")}
                                                    className={`px-3 py-1 text-xs rounded ${daViewMode === 'snowflake' ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'}`}
                                                >
                                                    Snowflake
                                                </button>
                                            </div>
                                        </div>

                                        {daViewMode === 'snowflake' ? (
                                            <div className="bg-slate-950/50 border border-slate-800 rounded-xl p-6 flex justify-center">
                                                <SnowflakeScanner 
                                                    data={snowflakeData} 
                                                    width={500} 
                                                    height={400} 
                                                    kpiName={selectedSituation.kpi_name}
                                                />
                                            </div>
                                        ) : (
                                            currentAnalysis.change_points && currentAnalysis.change_points.length > 0 && (
                                                <div className="space-y-3">
                                                    {currentAnalysis.change_points.map((cp: any, i: number) => (
                                                        <div key={i} className="flex justify-between items-center bg-slate-900/50 p-3 rounded border border-blue-500/10">
                                                            <div className="flex flex-col">
                                                                <span className="text-[10px] text-slate-500 uppercase tracking-wider">{cp.dimension}</span>
                                                                <span className="text-sm text-white font-medium">{cp.key || '(Unknown)'}</span>
                                                            </div>
                                                            <span className={`text-sm font-mono ${cp.delta < 0 ? 'text-red-400' : 'text-green-400'}`}>
                                                                {cp.delta > 0 ? '+' : ''}{cp.delta?.toLocaleString()}
                                                            </span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )
                                        )}
                                    </div>

                                    {/* Kepner-Tregoe Problem Specification */}
                                    {currentAnalysis.kt_is_is_not && (
                                        <div className="mt-8 pt-6 border-t border-blue-500/20">
                                            <h4 className="text-xs font-semibold text-blue-300 uppercase mb-4">Problem Specification (Is / Is Not)</h4>
                                            <div className="grid grid-cols-2 gap-4 text-sm">
                                                <div className="space-y-2">
                                                    <div className="text-xs text-slate-500 uppercase">Where is the problem? (IS)</div>
                                                    <div className="bg-slate-900/50 p-3 rounded border border-blue-500/10 min-h-[80px]">
                                                        {currentAnalysis.kt_is_is_not.what_is?.map((item: any, i: number) => (
                                                            <div key={i} className="mb-2 text-slate-300 border-b border-slate-800 pb-1 last:border-0 last:pb-0">
                                                                {item.text}
                                                            </div>
                                                        )) || <span className="text-slate-600 italic">No specific location identified</span>}
                                                    </div>
                                                </div>
                                                <div className="space-y-2">
                                                    <div className="text-xs text-slate-500 uppercase">Where is it NOT? (IS NOT)</div>
                                                    <div className="bg-slate-900/50 p-3 rounded border border-slate-700/50 min-h-[80px]">
                                                        {currentAnalysis.kt_is_is_not.what_is_not?.map((item: any, i: number) => (
                                                            <div key={i} className="mb-2 text-slate-400 border-b border-slate-800 pb-1 last:border-0 last:pb-0">
                                                                {item.text}
                                                            </div>
                                                        )) || <span className="text-slate-600 italic">No contrasts identified</span>}
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            {/* When / Extent */}
                                            <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                                                <div className="space-y-2">
                                                    <div className="text-xs text-slate-500 uppercase">Timing (When)</div>
                                                    <div className="bg-slate-900/50 p-3 rounded border border-blue-500/10">
                                                        {currentAnalysis.kt_is_is_not.when_is?.map((item: any, i: number) => (
                                                            <div key={i} className="mb-1 text-slate-300">{item.text}</div>
                                                        ))}
                                                        {currentAnalysis.when_started && (
                                                            <div className="mt-2 text-xs text-blue-400">
                                                                First detected: {currentAnalysis.when_started}
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="space-y-2">
                                                    <div className="text-xs text-slate-500 uppercase">Timing (When Not)</div>
                                                    <div className="bg-slate-900/50 p-3 rounded border border-slate-700/50">
                                                        {currentAnalysis.kt_is_is_not.when_is_not?.map((item: any, i: number) => (
                                                            <div key={i} className="mb-1 text-slate-400">{item.text}</div>
                                                        )) || <span className="text-slate-600 italic">Ongoing issue</span>}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </section>
                        )}

                        {/* 2. Key Evidence (Data without the Chart) */}
                        <section className="grid grid-cols-2 gap-6">
                            <div className="bg-slate-800/20 rounded-xl p-4 border border-slate-800">
                                <div className="text-xs text-slate-500 uppercase mb-1">Current Value</div>
                                <div className="text-2xl font-mono text-white">
                                    {selectedSituation.kpi_value?.value?.toLocaleString() || "0.00"}
                                </div>
                                <div className="text-xs text-red-400 mt-1 flex items-center gap-1">
                                    <ArrowRight className="w-3 h-3 rotate-45" />
                                    Below Target
                                </div>
                            </div>
                            <div className="bg-slate-800/20 rounded-xl p-4 border border-slate-800">
                                <div className="text-xs text-slate-500 uppercase mb-1">Impact</div>
                                <div className="text-2xl font-mono text-white">High</div>
                                <div className="text-xs text-slate-500 mt-1">
                                    Confidence: 94%
                                </div>
                            </div>
                        </section>

                        {/* 3. Recommended Actions (The Solution) */}
                        <section>
                            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <CheckCircle2 className="w-4 h-4" />
                                Recommended Actions
                            </h3>
                            <div className="space-y-3">
                                {selectedSituation.suggested_actions ? (
                                    selectedSituation.suggested_actions.map((action: string, i: number) => {
                                        // Wire up "Deep Analysis" action if detected
                                        if (action.toLowerCase().includes('deep analysis')) {
                                            if (currentAnalysis) return null; // Hide if already analyzed
                                            
                                            return (
                                                <button 
                                                    onClick={handleDeepAnalysis}
                                                    disabled={analyzing}
                                                    className="w-full text-left p-4 bg-blue-600/10 hover:bg-blue-600/20 border border-blue-500/20 hover:border-blue-500/40 rounded-lg transition-all group flex items-center justify-between disabled:opacity-50"
                                                >
                                                    <span className="text-blue-100 font-medium flex items-center gap-2">
                                                        {analyzing && <Loader2 className="w-4 h-4 animate-spin" />}
                                                        {analyzing ? 'Analyzing Root Causes...' : action}
                                                    </span>
                                                    {!analyzing && <Microscope className="w-4 h-4 text-blue-400 group-hover:scale-110 transition-transform" />}
                                                </button>
                                            )
                                        }

                                        // Wire up "Compare" action
                                        if (action.toLowerCase().includes('compare')) {
                                            return (
                                                <div key={i}>
                                                    {!comparisonData ? (
                                                        <button 
                                                            onClick={handleCompare}
                                                            disabled={comparing}
                                                            className="w-full text-left p-4 bg-purple-600/10 hover:bg-purple-600/20 border border-purple-500/20 hover:border-purple-500/40 rounded-lg transition-all group flex items-center justify-between disabled:opacity-50"
                                                        >
                                                            <span className="text-purple-100 font-medium flex items-center gap-2">
                                                                {comparing && <Loader2 className="w-4 h-4 animate-spin" />}
                                                                {comparing ? 'Generating Comparison...' : action}
                                                            </span>
                                                            {!comparing && <ArrowRight className="w-4 h-4 text-purple-400 group-hover:translate-x-1 transition-transform" />}
                                                        </button>
                                                    ) : (
                                                        // Render Comparison Result Inline
                                                        <div className="bg-slate-900 border border-purple-500/30 rounded-lg p-4 animate-in fade-in slide-in-from-top-2">
                                                            <div className="flex justify-between items-center mb-4">
                                                                <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider">
                                                                    Peer Benchmark: {comparisonData.dimension}
                                                                </h4>
                                                                <button onClick={() => setComparisonData(null)} className="text-slate-500 hover:text-white"><X className="w-4 h-4" /></button>
                                                            </div>
                                                            <div className="space-y-4">
                                                                {comparisonData.segments.map((seg: any, idx: number) => {
                                                                    const pct = Math.min(100, (seg.value / seg.target) * 100)
                                                                    const color = seg.status === 'critical' ? 'bg-red-500' : seg.status === 'warning' ? 'bg-amber-500' : 'bg-emerald-500'
                                                                    return (
                                                                        <div key={idx} className="space-y-1">
                                                                            <div className="flex justify-between text-xs">
                                                                                <span className={seg.status === 'critical' ? 'text-white font-medium' : 'text-slate-400'}>{seg.name}</span>
                                                                                <span className="text-slate-500">
                                                                                    {Math.round(pct)}% of Target
                                                                                </span>
                                                                            </div>
                                                                            <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                                                                                <div 
                                                                                    className={`h-full ${color} transition-all duration-1000`} 
                                                                                    style={{ width: `${pct}%` }}
                                                                                />
                                                                            </div>
                                                                            <div className="flex justify-between text-[10px] text-slate-600 font-mono">
                                                                                <span>${(seg.value/1000000).toFixed(1)}M</span>
                                                                                <span>Target: ${(seg.target/1000000).toFixed(1)}M</span>
                                                                            </div>
                                                                        </div>
                                                                    )
                                                                })}
                                                            </div>
                                                            <div className="mt-4 text-xs text-slate-400 italic border-t border-slate-800 pt-2">
                                                                Insight: Issue is localized to North America. Peer regions are performing near or above target.
                                                            </div>
                                                        </div>
                                                    )}
                                                </div>
                                            )
                                        }

                                        // Default "Dumb" Buttons for other actions
                                        return (
                                            <button key={i} className="w-full text-left p-4 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-slate-600 rounded-lg transition-all group flex items-center justify-between">
                                                <span className="text-slate-300 font-medium">{action}</span>
                                                <ArrowRight className="w-4 h-4 text-slate-500 group-hover:text-white group-hover:translate-x-1 transition-transform" />
                                            </button>
                                        )
                                    })
                                ) : (
                                    // Fallback if no actions provided by backend
                                    <>
                                        {!currentAnalysis && (
                                            <button 
                                                onClick={handleDeepAnalysis}
                                                disabled={analyzing}
                                                className="w-full text-left p-4 bg-blue-600/10 hover:bg-blue-600/20 border border-blue-500/20 hover:border-blue-500/40 rounded-lg transition-all group flex items-center justify-between disabled:opacity-50"
                                            >
                                                <span className="text-blue-100 font-medium flex items-center gap-2">
                                                    {analyzing && <Loader2 className="w-4 h-4 animate-spin" />}
                                                    {analyzing ? 'Analyzing Root Causes...' : 'Initiate Deep Analysis'}
                                                </span>
                                                {!analyzing && <Microscope className="w-4 h-4 text-blue-400 group-hover:scale-110 transition-transform" />}
                                            </button>
                                        )}
                                        <button className="w-full text-left p-4 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-all group flex items-center justify-between">
                                            <span className="text-slate-300 font-medium">Delegate to Regional Manager</span>
                                            <User className="w-4 h-4 text-slate-400" />
                                        </button>
                                    </>
                                )}

                                {/* --- SOLUTION FINDER SECTION (Always visible after analysis) --- */}
                                
                                {/* Persona Selector Mode */}
                                {showPersonaSelector && (
                                    <div className="bg-slate-900 border border-emerald-500/30 rounded-lg p-4 mb-4 animate-in fade-in slide-in-from-bottom-2">
                                        <div className="flex justify-between items-center mb-4">
                                            <h4 className="text-sm font-bold text-white flex items-center gap-2">
                                                <User className="w-4 h-4 text-emerald-400" />
                                                Select Debate Panel
                                            </h4>
                                            <button onClick={() => setShowPersonaSelector(false)} className="text-slate-500 hover:text-white"><X className="w-4 h-4" /></button>
                                        </div>
                                        <p className="text-xs text-slate-400 mb-3">Choose the expert personas to debate this solution.</p>
                                        
                                        <div className="grid grid-cols-1 gap-2 mb-4">
                                            {AVAILABLE_PERSONAS.map(persona => {
                                                const isSelected = selectedPersonas.includes(persona.id)
                                                return (
                                                    <button 
                                                        key={persona.id}
                                                        onClick={() => {
                                                            if (isSelected) setSelectedPersonas(p => p.filter(id => id !== persona.id))
                                                            else setSelectedPersonas(p => [...p, persona.id])
                                                        }}
                                                        className={`flex items-center gap-3 p-2 rounded border transition-all ${isSelected ? 'bg-slate-800 border-emerald-500/50' : 'bg-slate-900/50 border-slate-800 opacity-60 hover:opacity-100'}`}
                                                    >
                                                        <div className={`w-8 h-8 rounded-full bg-slate-900 flex items-center justify-center border ${isSelected ? 'border-emerald-500/30' : 'border-slate-700'}`}>
                                                            <persona.icon className={`w-4 h-4 ${persona.color}`} />
                                                        </div>
                                                        <span className={`text-sm ${isSelected ? 'text-white font-medium' : 'text-slate-500'}`}>{persona.label}</span>
                                                        {isSelected && <CheckCircle2 className="w-4 h-4 text-emerald-500 ml-auto" />}
                                                    </button>
                                                )
                                            })}
                                        </div>

                                        {/* Principal Input Section */}
                                        <div className="border-t border-slate-800 pt-4 mb-4">
                                            <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Priorities & Constraints</h5>
                                            
                                            {/* Priorities */}
                                            <div className="mb-3">
                                                <label className="text-xs text-slate-500 block mb-1">Strategic Priorities</label>
                                                <div className="flex gap-2 flex-wrap mb-2">
                                                    {principalInput.current_priorities.map((p, i) => (
                                                        <span key={i} className="text-[10px] bg-blue-900/30 text-blue-400 border border-blue-800 px-2 py-0.5 rounded flex items-center gap-1">
                                                            {p}
                                                            <button onClick={() => setPrincipalInput(prev => ({...prev, current_priorities: prev.current_priorities.filter((_, idx) => idx !== i)}))} className="hover:text-white"><X className="w-3 h-3" /></button>
                                                        </span>
                                                    ))}
                                                </div>
                                                <div className="flex gap-2">
                                                    <input 
                                                        type="text" 
                                                        value={priorityText}
                                                        onChange={(e) => setPriorityText(e.target.value)}
                                                        onKeyDown={(e) => {
                                                            if (e.key === 'Enter' && priorityText.trim()) {
                                                                setPrincipalInput(prev => ({...prev, current_priorities: [...prev.current_priorities, priorityText.trim()]}));
                                                                setPriorityText("");
                                                            }
                                                        }}
                                                        placeholder="e.g. Speed to value, Cost reduction..." 
                                                        className="flex-1 bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-xs text-white focus:border-blue-500 outline-none"
                                                    />
                                                    <button 
                                                        onClick={() => {
                                                            if (priorityText.trim()) {
                                                                setPrincipalInput(prev => ({...prev, current_priorities: [...prev.current_priorities, priorityText.trim()]}));
                                                                setPriorityText("");
                                                            }
                                                        }}
                                                        className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded"
                                                    >
                                                        <Plus className="w-3 h-3" />
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Constraints */}
                                            <div>
                                                <label className="text-xs text-slate-500 block mb-1">Constraints & Vetoes</label>
                                                <div className="flex gap-2 flex-wrap mb-2">
                                                    {principalInput.known_constraints.map((c, i) => (
                                                        <span key={i} className="text-[10px] bg-red-900/30 text-red-400 border border-red-800 px-2 py-0.5 rounded flex items-center gap-1">
                                                            {c}
                                                            <button onClick={() => setPrincipalInput(prev => ({...prev, known_constraints: prev.known_constraints.filter((_, idx) => idx !== i)}))} className="hover:text-white"><X className="w-3 h-3" /></button>
                                                        </span>
                                                    ))}
                                                </div>
                                                <div className="flex gap-2">
                                                    <input 
                                                        type="text" 
                                                        value={constraintText}
                                                        onChange={(e) => setConstraintText(e.target.value)}
                                                        onKeyDown={(e) => {
                                                            if (e.key === 'Enter' && constraintText.trim()) {
                                                                setPrincipalInput(prev => ({...prev, known_constraints: [...prev.known_constraints, constraintText.trim()]}));
                                                                setConstraintText("");
                                                            }
                                                        }}
                                                        placeholder="e.g. No headcount increase..." 
                                                        className="flex-1 bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-xs text-white focus:border-red-500 outline-none"
                                                    />
                                                    <button 
                                                        onClick={() => {
                                                            if (constraintText.trim()) {
                                                                setPrincipalInput(prev => ({...prev, known_constraints: [...prev.known_constraints, constraintText.trim()]}));
                                                                setConstraintText("");
                                                            }
                                                        }}
                                                        className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded"
                                                    >
                                                        <Plus className="w-3 h-3" />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>

                                        <button 
                                            onClick={handleStartDebate}
                                            disabled={selectedPersonas.length === 0}
                                            className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-medium disabled:opacity-50 transition-colors"
                                        >
                                            Start Agentic Debate
                                        </button>
                                    </div>
                                )}

                                {currentAnalysis && !solutions && !showPersonaSelector && (
                                    <button 
                                        onClick={handleSolution}
                                        disabled={findingSolutions}
                                        className="w-full text-left p-4 bg-emerald-600/10 hover:bg-emerald-600/20 border border-emerald-500/20 hover:border-emerald-500/40 rounded-lg transition-all group flex items-center justify-between disabled:opacity-50"
                                    >
                                        <span className="text-emerald-100 font-medium flex items-center gap-2">
                                            {findingSolutions && <Loader2 className="w-4 h-4 animate-spin" />}
                                            {findingSolutions ? 'Hosting Debate...' : 'Generate Solution Options'}
                                        </span>
                                        {!findingSolutions && <Lightbulb className="w-4 h-4 text-emerald-400 group-hover:scale-110 transition-transform" />}
                                    </button>
                                )}

                                {/* Render Solutions if available */}
                                {solutions && solutions.options_ranked && (
                                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 pt-4 border-t border-slate-800">
                                        
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-2">
                                                <div className="p-1.5 bg-purple-500/10 rounded-md">
                                                    <Lightbulb className="w-4 h-4 text-purple-400" />
                                                </div>
                                                <h4 className="text-sm font-bold text-white tracking-wide">DECISION BRIEFING</h4>
                                            </div>
                                            <Link 
                                                to={`/briefing/${selectedSituation.situation_id}`}
                                                className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-lg transition-colors"
                                            >
                                                View Full Briefing
                                                <ChevronRight className="w-3 h-3" />
                                            </Link>
                                        </div>
                                        
                                        <p className="text-xs text-slate-500 -mt-4 mb-4">
                                            Summary view. Click "View Full Briefing" for the complete executive document with implementation roadmap and risk analysis.
                                        </p>

                                        {/* 1. Problem Reframe (if available) */}
                                        {solutions.problem_reframe && (
                                            <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-800/60">
                                                <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Problem Reframing</h5>
                                                <div className="space-y-2 text-sm text-slate-300">
                                                    <div className="flex gap-2">
                                                        <span className="text-slate-500 w-24 flex-shrink-0">Situation:</span>
                                                        <span>{solutions.problem_reframe.situation}</span>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <span className="text-slate-500 w-24 flex-shrink-0">Complication:</span>
                                                        <span className="text-amber-400/90">{solutions.problem_reframe.complication}</span>
                                                    </div>
                                                    <div className="flex gap-2">
                                                        <span className="text-slate-500 w-24 flex-shrink-0">Key Q:</span>
                                                        <span className="font-medium text-white">{solutions.problem_reframe.question}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* 2. Options with Perspectives */}
                                        <div className="space-y-4">
                                            {solutions.options_ranked.map((opt: any, idx: number) => (
                                                <div key={idx} className="bg-slate-900 border border-slate-700 hover:border-slate-600 rounded-lg overflow-hidden transition-all group">
                                                    {/* Header */}
                                                    <div className="p-4 border-b border-slate-800/50 bg-slate-900 relative">
                                                        <div className="absolute top-4 right-4 text-xs font-mono text-slate-600">Option {String.fromCharCode(65 + idx)}</div>
                                                        <h5 className="text-base font-bold text-white mb-1 group-hover:text-emerald-400 transition-colors">{opt.title}</h5>
                                                        <p className="text-sm text-slate-400 mb-3">{opt.description}</p>
                                                        
                                                        {/* Metadata Tags */}
                                                        <div className="flex gap-2 mb-3">
                                                            {opt.time_to_value && (
                                                                <span className="px-2 py-0.5 bg-slate-800 text-slate-400 text-[10px] rounded border border-slate-700 uppercase tracking-wide">
                                                                    ⏱ {opt.time_to_value}
                                                                </span>
                                                            )}
                                                            {opt.reversibility && (
                                                                <span className={`px-2 py-0.5 text-[10px] rounded border uppercase tracking-wide ${
                                                                    opt.reversibility.toLowerCase().includes('high') ? 'bg-emerald-900/20 text-emerald-400 border-emerald-900/30' : 
                                                                    opt.reversibility.toLowerCase().includes('low') ? 'bg-red-900/20 text-red-400 border-red-900/30' :
                                                                    'bg-slate-800 text-slate-400 border-slate-700'
                                                                }`}>
                                                                    ↺ {opt.reversibility} Reversibility
                                                                </span>
                                                            )}
                                                        </div>

                                                        {/* Base Metrics */}
                                                        <div className="grid grid-cols-3 gap-2">
                                                            <div>
                                                                <div className="text-[10px] text-slate-500 uppercase">Impact</div>
                                                                <div className="h-1 bg-slate-800 rounded-full mt-1"><div className="h-full bg-emerald-500" style={{ width: `${(opt.expected_impact || 0) * 100}%` }} /></div>
                                                            </div>
                                                            <div>
                                                                <div className="text-[10px] text-slate-500 uppercase">Cost</div>
                                                                <div className="h-1 bg-slate-800 rounded-full mt-1"><div className="h-full bg-amber-500" style={{ width: `${(opt.cost || 0) * 100}%` }} /></div>
                                                            </div>
                                                            <div>
                                                                <div className="text-[10px] text-slate-500 uppercase">Risk</div>
                                                                <div className="h-1 bg-slate-800 rounded-full mt-1"><div className="h-full bg-red-500" style={{ width: `${(opt.risk || 0) * 100}%` }} /></div>
                                                            </div>
                                                        </div>
                                                    </div>

                                                    {/* Perspectives (Accordion-ish) */}
                                                    {opt.perspectives && opt.perspectives.length > 0 && (
                                                        <div className="bg-slate-950/30 p-4 space-y-3">
                                                            {opt.perspectives.map((pers: any, pIdx: number) => {
                                                                const lensLower = (pers.lens || "").toLowerCase()
                                                                let personaLabel = pers.lens
                                                                let personaColor = "text-slate-400"
                                                                if (lensLower.includes("financ")) { personaLabel = "CFO"; personaColor = "text-emerald-400" }
                                                                else if (lensLower.includes("operat")) { personaLabel = "Supply Chain Expert"; personaColor = "text-amber-400" }
                                                                else if (lensLower.includes("risk")) { personaLabel = "Compliance Officer"; personaColor = "text-red-400" }
                                                                else if (lensLower.includes("strat")) { personaLabel = "Sales VP"; personaColor = "text-purple-400" }

                                                                return (
                                                                    <div key={pIdx} className="text-xs">
                                                                        <div className="font-bold text-slate-400 mb-1 flex items-center gap-2">
                                                                            <div className={`w-4 h-4 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700`}>
                                                                                 <User className={`w-2.5 h-2.5 ${personaColor}`} />
                                                                            </div>
                                                                            <span className={personaColor}>{personaLabel}</span> 
                                                                            <span className="text-slate-600 font-normal">({pers.lens} Lens)</span>
                                                                        </div>
                                                                        <div className="grid grid-cols-2 gap-4 pl-6 border-l-2 border-slate-800 ml-2">
                                                                            <div>
                                                                                <div className="text-emerald-500/80 font-bold mb-0.5">FOR</div>
                                                                                <ul className="list-disc pl-3 text-slate-400 space-y-0.5">
                                                                                    {pers.arguments_for?.slice(0,2).map((arg: string, i: number) => (
                                                                                        <li key={i}>{arg}</li>
                                                                                    ))}
                                                                                </ul>
                                                                            </div>
                                                                            <div>
                                                                                <div className="text-red-500/80 font-bold mb-0.5">AGAINST</div>
                                                                                <ul className="list-disc pl-3 text-slate-400 space-y-0.5">
                                                                                    {pers.arguments_against?.slice(0,2).map((arg: string, i: number) => (
                                                                                        <li key={i}>{arg}</li>
                                                                                    ))}
                                                                                </ul>
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                )
                                                            })}
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                        </div>

                                        {/* 3. Unresolved Tensions & Blind Spots */}
                                        <div className="grid grid-cols-1 gap-4">
                                            {solutions.unresolved_tensions && solutions.unresolved_tensions.length > 0 && (
                                                <div className="bg-amber-900/10 border border-amber-900/30 rounded-lg p-3">
                                                    <h5 className="text-xs font-bold text-amber-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                                                        <AlertTriangle className="w-3 h-3" /> Unresolved Tensions
                                                    </h5>
                                                    <ul className="space-y-2">
                                                        {solutions.unresolved_tensions.map((t: any, i: number) => (
                                                            <li key={i} className="text-xs text-amber-200/80 flex gap-2">
                                                                <span className="text-amber-500/50">•</span>
                                                                <span>
                                                                    <span className="font-medium text-amber-200">{t.tension}</span>
                                                                    <span className="block text-amber-500/60 mt-0.5 text-[10px]">Requires: {t.requires}</span>
                                                                </span>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            )}
                                        </div>
                                        
                                        {/* Footer Disclaimer */}
                                        <div className="mt-6 p-3 bg-slate-950/50 border border-slate-800 rounded-lg">
                                            <h6 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                                                <AlertTriangle className="w-3 h-3" /> AI Analysis Limitations
                                            </h6>
                                            <p className="text-[10px] text-slate-500 leading-relaxed">
                                                This briefing is generated by AI based on available data and general expertise patterns. 
                                                It does <strong>not</strong> reflect the actual positions or votes of the individuals listed. 
                                                Principals should validate assumptions and contribute context the AI cannot access.
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </section>

                        {/* 4. Assignment Candidates */}
                        <section>
                            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">
                                Ownership
                            </h3>
                            <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex items-center gap-4">
                                <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
                                    <User className="w-5 h-5" />
                                </div>
                                <div>
                                    <div className="text-sm font-medium text-white">Sarah Jenkins</div>
                                    <div className="text-xs text-slate-400">Regional Director, NA</div>
                                </div>
                                <div className="ml-auto text-xs text-green-400 bg-green-900/20 px-2 py-1 rounded border border-green-900/30">
                                    92% Match
                                </div>
                            </div>
                        </section>
                    </div>

                    {/* Panel Footer */}
                    <div className="p-6 border-t border-slate-800 bg-slate-900/50 backdrop-blur-md flex justify-end gap-3">
                        <button className="px-4 py-2 text-slate-400 hover:text-white transition-colors">
                            Dismiss
                        </button>
                        <button className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors">
                            Approve & Execute
                        </button>
                    </div>
                </motion.div>
            </>
        )}
      </AnimatePresence>
    </div>
  )
}
