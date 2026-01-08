import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Download, Share2, Printer, AlertTriangle, CheckCircle, ChevronRight, Users, Target, Zap, Clock } from 'lucide-react'

// Full-page Executive Briefing - Consultant-style deliverable
export function ExecutiveBriefing() {
  const { situationId } = useParams()
  const [briefing, setBriefing] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Load briefing data from localStorage or fetch from API
    const stored = localStorage.getItem(`briefing_${situationId}`)
    if (stored) {
      setBriefing(JSON.parse(stored))
      setLoading(false)
    } else {
      // Fetch from API if not cached
      setLoading(false)
    }
  }, [situationId])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-pulse text-slate-400">Loading briefing...</div>
      </div>
    )
  }

  if (!briefing) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-8">
        <div className="max-w-xl w-full bg-slate-900/60 border border-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-2">Briefing not generated yet</h2>
          <p className="text-slate-400 mb-6">
            Go back to Decision Studio, run Deep Analysis, then click "Generate Solution Options" to create the Executive Briefing.
          </p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Decision Studio
          </Link>
        </div>
      </div>
    )
  }

  const data = briefing

  return (
    <div className="min-h-screen bg-white text-slate-900 print:bg-white">
      {/* Top Navigation Bar (hidden on print) */}
      <nav className="bg-slate-900 text-white py-4 px-6 flex justify-between items-center print:hidden sticky top-0 z-50">
        <Link to="/" className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Back to Decision Studio
        </Link>
        <div className="flex items-center gap-4">
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
            <Share2 className="w-4 h-4" />
            Share
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
            <Download className="w-4 h-4" />
            Export PDF
          </button>
          <button 
            onClick={() => window.print()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
          >
            <Printer className="w-4 h-4" />
            Print
          </button>
        </div>
      </nav>

      {/* Document Container */}
      <div className="max-w-4xl mx-auto py-12 px-8 print:py-0 print:px-0">
        
        {/* Document Header */}
        <header className="mb-12 border-b-4 border-slate-900 pb-8">
          <div className="flex justify-between items-start mb-6">
            <div>
              <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">
                Executive Decision Briefing
              </p>
              <h1 className="text-4xl font-bold text-slate-900 leading-tight">
                {data.title}
              </h1>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-500">Prepared by Agent9 Decision Studio</p>
              <p className="text-sm text-slate-500">{new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
              <div className="mt-2 inline-flex items-center gap-2 px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
                <AlertTriangle className="w-4 h-4" />
                {data.urgency}
              </div>
            </div>
          </div>
          
          {/* Key Metrics Strip */}
          <div className="grid grid-cols-4 gap-4 mt-8">
            <div className="bg-slate-100 rounded-lg p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Financial Impact</p>
              <p className="text-2xl font-bold text-red-600">{data.metrics.financialImpact}</p>
            </div>
            <div className="bg-slate-100 rounded-lg p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Time Sensitivity</p>
              <p className="text-2xl font-bold text-amber-600">{data.metrics.timeSensitivity}</p>
            </div>
            <div className="bg-slate-100 rounded-lg p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Confidence Level</p>
              <p className="text-2xl font-bold text-blue-600">{data.metrics.confidence}</p>
            </div>
            <div className="bg-slate-100 rounded-lg p-4">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Decision Required By</p>
              <p className="text-2xl font-bold text-slate-900">{data.metrics.decisionDeadline}</p>
            </div>
          </div>
        </header>

        {/* Executive Summary */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 text-white rounded flex items-center justify-center text-sm font-bold">1</div>
            Executive Summary
          </h2>
          <div className="bg-blue-50 border-l-4 border-blue-600 p-6 rounded-r-lg">
            <p className="text-lg text-slate-700 leading-relaxed whitespace-pre-line">
              {data.executiveSummary}
            </p>
          </div>
        </section>

        {/* Situation Analysis */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 text-white rounded flex items-center justify-center text-sm font-bold">2</div>
            Situation Analysis
          </h2>
          
          <div className="grid grid-cols-2 gap-6 mb-6">
            <div className="bg-slate-50 p-6 rounded-lg">
              <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-600" />
                Current State
              </h3>
              <p className="text-slate-700 leading-relaxed">{data.situation.currentState}</p>
            </div>
            <div className="bg-red-50 p-6 rounded-lg">
              <h3 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-red-600" />
                The Problem
              </h3>
              <p className="text-slate-700 leading-relaxed">{data.situation.problem}</p>
            </div>
          </div>

          {/* Root Cause Analysis */}
          {data.situation.rootCauses && data.situation.rootCauses.length > 0 && (
            <div className="bg-slate-900 text-white p-6 rounded-lg mb-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-400" />
                Root Cause Analysis (Data-Driven)
              </h3>
              <div className="space-y-3">
                {data.situation.rootCauses.map((cause: any, i: number) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="w-6 h-6 bg-amber-500 text-slate-900 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">
                      {i + 1}
                    </div>
                    <div>
                      <p className="font-medium text-white">{cause.driver}</p>
                      <p className="text-slate-400 text-sm">{cause.evidence}</p>
                      <p className="text-amber-400 text-sm font-medium mt-1">Impact: {cause.impact}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Key Question */}
          {data.situation.keyQuestion && (
            <div className="bg-blue-50 border-l-4 border-blue-600 p-4 rounded-r-lg mb-6">
              <h3 className="font-semibold text-blue-900 mb-2">Key Question</h3>
              <p className="text-blue-800 italic">{data.situation.keyQuestion}</p>
            </div>
          )}

          {/* Key Assumptions */}
          {data.situation.assumptions && data.situation.assumptions.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
              <h3 className="font-semibold text-amber-900 mb-2">Key Assumptions</h3>
              <ul className="space-y-1">
                {data.situation.assumptions.map((assumption: string, i: number) => (
                  <li key={i} className="text-amber-800 text-sm flex items-start gap-2">
                    <span className="text-amber-500">•</span>
                    {assumption}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {/* Stage 1: Initial Hypotheses */}
        {data.stage_1_hypotheses && (
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
              <div className="w-8 h-8 bg-indigo-600 text-white rounded flex items-center justify-center text-sm font-bold">1</div>
              Stage 1: Initial Hypotheses
            </h2>
            <p className="text-slate-600 mb-6">
              Each consulting firm independently analyzed the problem using their signature frameworks.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(data.stage_1_hypotheses).map(([firmId, hyp]: [string, any]) => (
                <div key={firmId} className="bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-200 rounded-lg p-5">
                  <h4 className="font-bold text-slate-900 capitalize mb-2">{firmId.replace(/_/g, ' ')}</h4>
                  <p className="text-xs text-indigo-600 font-medium mb-2">{hyp.framework}</p>
                  <p className="text-sm text-slate-700 mb-3">{hyp.hypothesis}</p>
                  {hyp.recommended_focus && (
                    <div className="bg-white p-2 rounded border border-slate-200">
                      <p className="text-xs text-slate-500 uppercase">Recommended Focus</p>
                      <p className="text-sm font-medium text-slate-800">{hyp.recommended_focus}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Stage 2: Council Cross-Review */}
        {data.cross_review && (
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
              <div className="w-8 h-8 bg-purple-600 text-white rounded flex items-center justify-center text-sm font-bold">2</div>
              Stage 2: Cross-Review
            </h2>
            <p className="text-slate-600 mb-6">
              Each firm reviewed the others' hypotheses to surface blind spots and tensions.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(data.cross_review).map(([personaId, review]: [string, any]) => (
                <div key={personaId} className="bg-slate-50 border border-slate-200 rounded-lg p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                      <Users className="w-4 h-4 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 capitalize">{personaId.replace(/_/g, ' ')}</h4>
                      <p className="text-xs text-slate-500">Council Member</p>
                    </div>
                  </div>
                  
                  {review.critiques && review.critiques.length > 0 && (
                    <div className="mb-3">
                      <h5 className="text-xs font-semibold text-red-600 uppercase tracking-wider mb-2">Key Critiques</h5>
                      <ul className="space-y-2">
                        {review.critiques.map((c: any, i: number) => (
                          <li key={i} className="text-sm text-slate-700 bg-white p-2 rounded border border-slate-100">
                            <span className="font-medium text-slate-900 block mb-0.5">Re: {c.target}</span>
                            "{c.concern}"
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {review.endorsements && review.endorsements.length > 0 && (
                    <div>
                      <h5 className="text-xs font-semibold text-emerald-600 uppercase tracking-wider mb-2">Endorsements</h5>
                      <ul className="space-y-2">
                        {review.endorsements.map((e: any, i: number) => (
                          <li key={i} className="text-sm text-slate-700 bg-white p-2 rounded border border-slate-100">
                            <span className="font-medium text-slate-900 block mb-0.5">Re: {e.target}</span>
                            "{e.reason}"
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Strategic Options */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 text-white rounded flex items-center justify-center text-sm font-bold">3</div>
            Strategic Options
          </h2>
          <p className="text-slate-600 mb-6">
            Based on the analysis, we have identified three strategic pathways. Each option has been evaluated 
            against financial impact, implementation complexity, risk profile, and alignment with stated priorities.
          </p>

          {/* Comparative Table */}
          <div className="overflow-x-auto rounded-lg border border-slate-200 mb-8">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-100 text-slate-900 font-bold uppercase text-xs">
                <tr>
                  <th className="p-4 border-b border-slate-200 min-w-[150px]">Criteria</th>
                  {data.options.map((opt: any, i: number) => (
                    <th key={i} className={`p-4 border-b border-slate-200 min-w-[200px] ${opt.recommended ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : ''}`}>
                      {opt.recommended && <div className="text-[10px] text-emerald-600 mb-1 flex items-center gap-1"><CheckCircle className="w-3 h-3"/> RECOMMENDED</div>}
                      Option {String.fromCharCode(65 + i)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="p-4 font-semibold text-slate-700 bg-slate-50">Strategy</td>
                  {data.options.map((opt: any, i: number) => (
                    <td key={i} className={`p-4 font-medium text-slate-900 ${opt.recommended ? 'bg-emerald-50/30' : ''}`}>
                      {opt.title}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-4 font-semibold text-slate-700 bg-slate-50">Est. ROI</td>
                  {data.options.map((opt: any, i: number) => (
                    <td key={i} className={`p-4 font-bold text-emerald-600 ${opt.recommended ? 'bg-emerald-50/30' : ''}`}>
                      {opt.roi}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-4 font-semibold text-slate-700 bg-slate-50">Investment</td>
                  {data.options.map((opt: any, i: number) => (
                    <td key={i} className={`p-4 text-slate-600 ${opt.recommended ? 'bg-emerald-50/30' : ''}`}>
                      {opt.investment}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-4 font-semibold text-slate-700 bg-slate-50">Timeline</td>
                  {data.options.map((opt: any, i: number) => (
                    <td key={i} className={`p-4 text-slate-600 ${opt.recommended ? 'bg-emerald-50/30' : ''}`}>
                      {opt.timeline}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-4 font-semibold text-slate-700 bg-slate-50">Risk Level</td>
                  {data.options.map((opt: any, i: number) => (
                    <td key={i} className={`p-4 ${opt.recommended ? 'bg-emerald-50/30' : ''}`}>
                       <span className={`px-2 py-1 rounded text-xs font-bold ${
                          opt.riskLevel === 'Low' ? 'bg-emerald-100 text-emerald-700' : 
                          opt.riskLevel === 'Medium' ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
                       }`}>
                         {opt.riskLevel}
                       </span>
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-4 font-semibold text-slate-700 bg-slate-50">Reversibility</td>
                  {data.options.map((opt: any, i: number) => (
                    <td key={i} className={`p-4 text-slate-600 capitalize ${opt.recommended ? 'bg-emerald-50/30' : ''}`}>
                      {opt.reversibility}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>

          <div className="space-y-8">
            {data.options.map((option: any, i: number) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`border-2 rounded-xl overflow-hidden ${
                  option.recommended ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 bg-white'
                }`}
              >
                {option.recommended && (
                  <div className="bg-emerald-500 text-white px-4 py-2 text-sm font-semibold flex items-center gap-2">
                    <CheckCircle className="w-4 h-4" />
                    RECOMMENDED OPTION
                  </div>
                )}
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-xl font-bold text-slate-900">
                        Option {String.fromCharCode(65 + i)}: {option.title}
                      </h3>
                      <p className="text-slate-600 mt-1">{option.subtitle}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-slate-500">Est. ROI</p>
                      <p className="text-2xl font-bold text-emerald-600">{option.roi}</p>
                    </div>
                  </div>

                  <p className="text-slate-700 leading-relaxed mb-6">{option.description}</p>

                  {/* Option Metrics */}
                  <div className="grid grid-cols-4 gap-4 mb-6">
                    <div className="text-center p-3 bg-slate-100 rounded-lg">
                      <p className="text-xs text-slate-500 uppercase">Investment</p>
                      <p className="font-bold text-slate-900">{option.investment}</p>
                    </div>
                    <div className="text-center p-3 bg-slate-100 rounded-lg">
                      <p className="text-xs text-slate-500 uppercase">Timeline</p>
                      <p className="font-bold text-slate-900">{option.timeline}</p>
                    </div>
                    <div className="text-center p-3 bg-slate-100 rounded-lg">
                      <p className="text-xs text-slate-500 uppercase">Risk Level</p>
                      <p className={`font-bold ${option.riskLevel === 'Low' ? 'text-emerald-600' : option.riskLevel === 'Medium' ? 'text-amber-600' : 'text-red-600'}`}>
                        {option.riskLevel}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-slate-100 rounded-lg">
                      <p className="text-xs text-slate-500 uppercase">Reversibility</p>
                      <p className="font-bold text-slate-900">{option.reversibility}</p>
                    </div>
                  </div>

                  {/* Pros and Cons */}
                  <div className="grid grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-emerald-700 mb-2 flex items-center gap-2">
                        <CheckCircle className="w-4 h-4" />
                        Arguments For
                      </h4>
                      <ul className="space-y-2">
                        {option.prosDetailed.map((pro: any, j: number) => (
                          <li key={j} className="text-sm text-slate-700 flex items-start gap-2">
                            <ChevronRight className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                            <span><strong>{pro.point}:</strong> {pro.detail}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <h4 className="font-semibold text-red-700 mb-2 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4" />
                        Arguments Against
                      </h4>
                      <ul className="space-y-2">
                        {option.consDetailed.map((con: any, j: number) => (
                          <li key={j} className="text-sm text-slate-700 flex items-start gap-2">
                            <ChevronRight className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                            <span><strong>{con.point}:</strong> {con.detail}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Stakeholder Perspectives */}
                  {option.perspectives && (
                    <div className="mt-6 pt-6 border-t border-slate-200">
                      <h4 className="font-semibold text-slate-900 mb-3 flex items-center gap-2">
                        <Users className="w-4 h-4" />
                        Stakeholder Perspectives
                      </h4>
                      <div className="grid grid-cols-3 gap-4">
                        {option.perspectives.map((p: any, j: number) => (
                          <div key={j} className="bg-slate-50 p-3 rounded-lg">
                            <p className="font-medium text-slate-900 text-sm">{p.role}</p>
                            <p className="text-xs text-slate-600 mt-1">{p.view}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* Implementation Roadmap */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 text-white rounded flex items-center justify-center text-sm font-bold">4</div>
            Implementation Roadmap
          </h2>
          <p className="text-slate-600 mb-6">
            Should the recommended option be approved, the following phased approach is proposed:
          </p>

          <div className="relative">
            {/* Timeline Line */}
            <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-300"></div>
            
            <div className="space-y-6">
              {data.roadmap.map((phase: any, i: number) => (
                <div key={i} className="relative pl-16">
                  <div className={`absolute left-4 w-5 h-5 rounded-full border-2 ${
                    i === 0 ? 'bg-blue-600 border-blue-600' : 'bg-white border-slate-300'
                  }`}></div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-slate-900">{phase.phase}</h4>
                      <span className="text-sm text-slate-500 flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {phase.timeline || phase.duration}
                      </span>
                    </div>
                    {phase.description && <p className="text-slate-700 text-sm mb-3">{phase.description}</p>}
                    <div className="flex flex-wrap gap-2">
                      {(phase.items || phase.deliverables || []).map((d: string, j: number) => (
                        <span key={j} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Risk Analysis */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 text-white rounded flex items-center justify-center text-sm font-bold">5</div>
            Risk Analysis & Mitigation
          </h2>

          <div className="overflow-hidden rounded-lg border border-slate-200">
            <table className="w-full">
              <thead className="bg-slate-100">
                <tr>
                  <th className="text-left p-4 font-semibold text-slate-900">Risk</th>
                  <th className="text-left p-4 font-semibold text-slate-900">Likelihood</th>
                  <th className="text-left p-4 font-semibold text-slate-900">Impact</th>
                  <th className="text-left p-4 font-semibold text-slate-900">Mitigation Strategy</th>
                </tr>
              </thead>
              <tbody>
                {data.risks.map((risk: any, i: number) => (
                  <tr key={i} className="border-t border-slate-200">
                    <td className="p-4 text-slate-700">{risk.risk}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        risk.likelihood === 'High' ? 'bg-red-100 text-red-700' :
                        risk.likelihood === 'Medium' ? 'bg-amber-100 text-amber-700' :
                        'bg-emerald-100 text-emerald-700'
                      }`}>
                        {risk.likelihood}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        risk.impact === 'High' ? 'bg-red-100 text-red-700' :
                        risk.impact === 'Medium' ? 'bg-amber-100 text-amber-700' :
                        'bg-emerald-100 text-emerald-700'
                      }`}>
                        {risk.impact}
                      </span>
                    </td>
                    <td className="p-4 text-slate-700 text-sm">{risk.mitigation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Blind Spots & Unresolved Tensions */}
        {((data.blind_spots && data.blind_spots.length > 0) || (data.unresolved_tensions && data.unresolved_tensions.length > 0)) && (
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
              <div className="w-8 h-8 bg-amber-600 text-white rounded flex items-center justify-center text-sm font-bold">
                <AlertTriangle className="w-4 h-4" />
              </div>
              Considerations & Blind Spots
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {data.blind_spots && data.blind_spots.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 p-5 rounded-lg">
                  <h3 className="font-semibold text-amber-900 mb-3">Potential Blind Spots</h3>
                  <ul className="space-y-2">
                    {data.blind_spots.map((bs: string, i: number) => (
                      <li key={i} className="text-amber-800 text-sm flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                        {bs}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {data.unresolved_tensions && data.unresolved_tensions.length > 0 && (
                <div className="bg-purple-50 border border-purple-200 p-5 rounded-lg">
                  <h3 className="font-semibold text-purple-900 mb-3">Unresolved Tensions</h3>
                  <ul className="space-y-3">
                    {data.unresolved_tensions.map((t: any, i: number) => (
                      <li key={i} className="text-purple-800 text-sm">
                        <p className="font-medium">{t.tension || t}</p>
                        {t.requires && (
                          <p className="text-purple-600 text-xs mt-1">Requires: {t.requires}</p>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </section>
        )}

        {/* Call to Action */}
        <section className="mb-12">
          <h2 className="text-2xl font-bold text-slate-900 mb-4 flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 text-white rounded flex items-center justify-center text-sm font-bold">6</div>
            Recommendation & Next Steps
          </h2>

          <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white p-8 rounded-xl">
            <h3 className="text-xl font-bold mb-4">{data.recommendation.headline}</h3>
            <p className="text-blue-100 leading-relaxed mb-6">{data.recommendation.rationale}</p>
            
            <div className="bg-white/10 backdrop-blur rounded-lg p-4 mb-6">
              <h4 className="font-semibold mb-3">Immediate Actions Required:</h4>
              <ol className="space-y-2">
                {data.recommendation.nextSteps.map((step: string, i: number) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-6 h-6 bg-white text-blue-600 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                      {i + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-white/20">
              <div>
                <p className="text-sm text-blue-200">Decision Owner</p>
                <p className="font-semibold">{data.recommendation.decisionOwner}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-blue-200">Decision Deadline</p>
                <p className="font-semibold">{data.recommendation.deadline}</p>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-slate-200 pt-8 text-center text-sm text-slate-500">
          <p>This briefing was generated by Agent9 Decision Studio using AI-assisted analysis.</p>
          <p className="mt-2">
            Data sources: Deep Analysis Engine, KPI Registry, Business Context Registry
          </p>
          <p className="mt-4 text-xs">
            <strong>Disclaimer:</strong> This analysis is provided as decision support and should be validated 
            against current business conditions. AI-generated insights require human judgment for final decisions.
          </p>
        </footer>
      </div>
    </div>
  )
}

// Mock data for demonstration - this would come from the LLM in production
// const MOCK_BRIEFING = { ... } (Removed to fix lint)

export default ExecutiveBriefing
