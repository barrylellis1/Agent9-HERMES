import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowLeft, Download, Share2, Printer, Clock, TrendingDown, AlertTriangle, CheckCircle, ChevronRight, Users, DollarSign, Target, Zap } from 'lucide-react'

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
          <div className="bg-slate-900 text-white p-6 rounded-lg">
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
        </section>

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
                      <h4 className="font-semibold text-slate-900">{phase.phase}: {phase.title}</h4>
                      <span className="text-sm text-slate-500 flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {phase.duration}
                      </span>
                    </div>
                    <p className="text-slate-700 text-sm mb-3">{phase.description}</p>
                    <div className="flex flex-wrap gap-2">
                      {phase.deliverables.map((d: string, j: number) => (
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
const MOCK_BRIEFING = {
  title: "Cost of Goods Sold Variance: Strategic Response Required",
  urgency: "High Priority",
  metrics: {
    financialImpact: "-$2.4M",
    timeSensitivity: "Q4 Critical",
    confidence: "94%",
    decisionDeadline: "Dec 20"
  },
  executiveSummary: `Global Bike Inc. is experiencing a significant deviation in Cost of Goods Sold (COGS), with actual costs exceeding budget by $2.4M (18.3%) in Q3 2024. This variance, if unaddressed, will erode gross margins by 340 basis points and jeopardize our FY2024 profitability targets.

Our deep analysis has identified three primary drivers: (1) raw material cost inflation in aluminum and carbon fiber components (+23% YoY), (2) supplier concentration risk with 67% of frame components sourced from a single vendor experiencing capacity constraints, and (3) inefficient inventory management leading to $890K in expedited shipping costs.

This briefing presents three strategic options ranging from tactical cost containment to strategic supply chain restructuring. Based on our analysis of financial impact, implementation feasibility, and alignment with Global Bike's growth strategy, we recommend Option B: Strategic Supplier Diversification combined with targeted inventory optimization.

Immediate action is required to prevent further margin erosion and position the company for sustainable cost management heading into FY2025.`,
  
  situation: {
    currentState: "Global Bike Inc. operates a vertically-integrated bicycle manufacturing and retail operation with 47 retail locations and an e-commerce platform generating $156M in annual revenue. The company has historically maintained gross margins of 42-45%, positioning it competitively against peers like Trek and Specialized.",
    problem: "COGS has increased by 18.3% ($2.4M) against budget in Q3 2024, driven primarily by the European Profit Center which accounts for 73% of the variance. This threatens our ability to meet FY2024 EBITDA targets and fund planned expansion into the electric bike segment.",
    rootCauses: [
      {
        driver: "Raw Material Cost Inflation",
        evidence: "Aluminum prices up 23% YoY; carbon fiber supply constrained due to aerospace demand",
        impact: "Contributing $1.1M (46%) of total variance"
      },
      {
        driver: "Supplier Concentration Risk",
        evidence: "Primary frame supplier (TaiwanCycle Corp) at 94% capacity utilization; lead times extended from 6 to 14 weeks",
        impact: "Contributing $890K (37%) through expedited shipping and production delays"
      },
      {
        driver: "Inventory Management Inefficiency",
        evidence: "Safety stock levels 40% below optimal; stockout rate increased from 3% to 11%",
        impact: "Contributing $410K (17%) in rush orders and lost sales"
      }
    ]
  },

  options: [
    {
      title: "Tactical Cost Containment",
      subtitle: "Short-term measures to reduce immediate cost pressure",
      description: "Implement immediate cost reduction measures including renegotiating existing supplier contracts, reducing SKU complexity by 20%, and implementing stricter procurement controls. This option prioritizes quick wins and cash preservation while accepting some operational constraints.",
      roi: "1.2x",
      investment: "$150K",
      timeline: "3 months",
      riskLevel: "Low",
      reversibility: "High",
      recommended: false,
      prosDetailed: [
        { point: "Quick implementation", detail: "Can begin immediately with existing resources and relationships" },
        { point: "Low capital requirement", detail: "Minimal upfront investment preserves cash for other priorities" },
        { point: "Proven playbook", detail: "Standard cost reduction techniques with predictable outcomes" }
      ],
      consDetailed: [
        { point: "Limited upside", detail: "Addresses symptoms rather than structural issues; savings plateau quickly" },
        { point: "Supplier relationship risk", detail: "Aggressive renegotiation may damage long-term partnerships" },
        { point: "SKU reduction impact", detail: "May alienate customers seeking specific configurations" }
      ],
      perspectives: [
        { role: "CFO", view: "Supports short-term margin protection but concerned about sustainability" },
        { role: "Supply Chain", view: "Feasible but warns of supplier pushback and quality risks" },
        { role: "Sales", view: "Concerned about SKU reduction impact on customer satisfaction" }
      ]
    },
    {
      title: "Strategic Supplier Diversification",
      subtitle: "Build resilient, multi-source supply chain",
      description: "Develop a diversified supplier base by qualifying 2-3 alternative frame and component suppliers in Vietnam and Mexico, while implementing advanced demand forecasting and inventory optimization. This option addresses root causes and builds long-term competitive advantage.",
      roi: "2.8x",
      investment: "$1.2M",
      timeline: "9 months",
      riskLevel: "Medium",
      reversibility: "Medium",
      recommended: true,
      prosDetailed: [
        { point: "Structural cost reduction", detail: "Projected 12-15% reduction in component costs through competitive sourcing" },
        { point: "Risk mitigation", detail: "Eliminates single-supplier dependency; improves supply chain resilience" },
        { point: "Scalability", detail: "Positions company for growth without proportional cost increases" },
        { point: "Nearshoring benefits", detail: "Mexico sourcing reduces lead times and shipping costs for North American market" }
      ],
      consDetailed: [
        { point: "Implementation complexity", detail: "Requires significant project management and supplier qualification effort" },
        { point: "Transition risk", detail: "Quality consistency during supplier onboarding period" },
        { point: "Capital requirement", detail: "Requires board approval for investment above standard OpEx" }
      ],
      perspectives: [
        { role: "CFO", view: "Strong ROI justifies investment; recommends phased funding approach" },
        { role: "Supply Chain", view: "Enthusiastically supports; has preliminary supplier candidates identified" },
        { role: "Operations", view: "Requests dedicated project manager and quality engineering support" }
      ]
    },
    {
      title: "Vertical Integration",
      subtitle: "Acquire or build internal manufacturing capability",
      description: "Acquire a frame manufacturing facility or invest in internal production capability to control costs and quality directly. This option provides maximum control but requires significant capital and operational expertise.",
      roi: "3.5x (5yr)",
      investment: "$8-12M",
      timeline: "18-24 months",
      riskLevel: "High",
      reversibility: "Low",
      recommended: false,
      prosDetailed: [
        { point: "Maximum cost control", detail: "Eliminates supplier margins; full visibility into cost structure" },
        { point: "Quality ownership", detail: "Direct control over manufacturing processes and innovation" },
        { point: "Competitive moat", detail: "Creates barrier to entry and differentiation opportunity" }
      ],
      consDetailed: [
        { point: "Capital intensive", detail: "Requires significant investment outside current strategic plan" },
        { point: "Execution risk", detail: "Manufacturing expertise not core competency; steep learning curve" },
        { point: "Market timing", detail: "Long implementation timeline may miss current market window" },
        { point: "Fixed cost exposure", detail: "Increases operating leverage and downside risk in market downturn" }
      ],
      perspectives: [
        { role: "CFO", view: "Attractive long-term economics but concerned about near-term cash impact" },
        { role: "CEO", view: "Aligns with long-term vision but questions timing given e-bike launch priorities" },
        { role: "Board", view: "Would require strategic review and likely equity raise" }
      ]
    }
  ],

  roadmap: [
    {
      phase: "Phase 1",
      title: "Foundation & Quick Wins",
      duration: "Weeks 1-4",
      description: "Implement immediate cost controls while initiating supplier qualification process",
      deliverables: ["Procurement policy updates", "Supplier RFI distribution", "Inventory audit completion"]
    },
    {
      phase: "Phase 2", 
      title: "Supplier Qualification",
      duration: "Weeks 5-16",
      description: "Evaluate and qualify alternative suppliers; negotiate terms and conduct pilot orders",
      deliverables: ["Supplier scorecards", "Quality certification", "Pilot production runs", "Contract negotiations"]
    },
    {
      phase: "Phase 3",
      title: "Transition & Optimization",
      duration: "Weeks 17-36",
      description: "Gradually shift volume to new suppliers while optimizing inventory systems",
      deliverables: ["Volume transition plan", "Demand forecasting system", "Safety stock optimization", "Performance dashboards"]
    }
  ],

  risks: [
    {
      risk: "Supplier qualification delays",
      likelihood: "Medium",
      impact: "Medium",
      mitigation: "Parallel qualification of multiple candidates; maintain buffer inventory during transition"
    },
    {
      risk: "Quality issues with new suppliers",
      likelihood: "Medium", 
      impact: "High",
      mitigation: "Rigorous qualification process; phased volume ramp; quality hold provisions in contracts"
    },
    {
      risk: "Existing supplier retaliation",
      likelihood: "Low",
      impact: "Medium",
      mitigation: "Maintain professional relationship; gradual volume reduction; long-term partnership positioning"
    },
    {
      risk: "Internal resource constraints",
      likelihood: "High",
      impact: "Medium",
      mitigation: "Dedicated project team; consider external consulting support for peak periods"
    }
  ],

  recommendation: {
    headline: "Proceed with Option B: Strategic Supplier Diversification",
    rationale: "This option offers the optimal balance of financial return (2.8x ROI), risk management, and strategic alignment. While requiring more investment than tactical measures, it addresses the structural issues driving our cost variance and positions Global Bike for sustainable competitive advantage. The 9-month timeline allows us to capture benefits before FY2025 planning while managing implementation risk through a phased approach.",
    nextSteps: [
      "Secure executive sponsorship and budget approval ($1.2M) by December 15",
      "Assign dedicated project manager from Supply Chain team",
      "Issue RFIs to pre-qualified supplier candidates in Vietnam and Mexico",
      "Establish weekly steering committee reviews with CFO and COO",
      "Communicate strategy to existing suppliers to manage relationship"
    ],
    decisionOwner: "Chief Operating Officer",
    deadline: "December 20, 2024"
  }
}

export default ExecutiveBriefing
