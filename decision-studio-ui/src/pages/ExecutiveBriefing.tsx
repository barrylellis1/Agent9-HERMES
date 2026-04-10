import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link, useSearchParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import html2pdf from 'html2pdf.js'
import {
  ArrowLeft, Download, Printer, AlertTriangle, CheckCircle, ChevronRight,
  Users, Target, Zap, Clock, Sparkles, ShieldCheck, Loader2, CheckCircle2,
  ChevronDown, Send, MessageSquare, FileText
} from 'lucide-react'
import { approveSolution, askBriefingQuestion, BriefingQAResponse, storeBriefingSnapshot, getBriefingSnapshot, getVASolution } from '../api/client'
import { CostOfInactionBanner } from '../components/CostOfInactionBanner'
import { ValueAssurancePanel } from '../components/ValueAssurancePanel'
import { AttributionBreakdown } from '../components/AttributionBreakdown'
import { BrandLogo } from '../components/BrandLogo'
import type { AcceptedSolution as VASolution } from '../types/valueAssurance'

// ─────────────────────────────────────────────────
// Format ROI values: "+28500000.0USD to +38200000.0USD" → "+$28.5M to +$38.2M"
// ─────────────────────────────────────────────────
const formatROI = (roi: any): string => {
  if (!roi || roi === '—') return roi || '—'
  const roiStr = String(roi)
  return roiStr.replace(/([+\-]?)(\d+)(\.\d)?/g, (match, sign, num) => {
    const numVal = parseInt(num)
    if (numVal >= 1000000) {
      return `${sign}$${(numVal / 1000000).toFixed(1)}M`
    } else if (numVal >= 1000) {
      return `${sign}$${(numVal / 1000).toFixed(0)}K`
    }
    return match
  }).replace(/USD/gi, '')
}

// ─────────────────────────────────────────────────
// Accordion section wrapper
// ─────────────────────────────────────────────────
function AccordionSection({
  id, title, icon, badge,
  openSections, onToggle, children,
}: {
  id: string; title: string; icon?: React.ReactNode; badge?: string;
  openSections: Set<string>; onToggle: (id: string) => void; children: React.ReactNode;
}) {
  const isOpen = openSections.has(id)
  return (
    <div className="mb-3 rounded-xl overflow-hidden border border-slate-800 print:border-0 print:mb-8">
      <button
        onClick={() => onToggle(id)}
        className="w-full flex items-center justify-between px-5 py-3 bg-slate-900 text-white hover:bg-slate-800 transition-colors border-b border-slate-800 print:hidden"
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-semibold text-sm">{title}</span>
          {badge && <span className="px-2 py-0.5 text-[10px] bg-indigo-600 text-white rounded-full">{badge}</span>}
        </div>
        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      <div className={`accordion-content ${isOpen ? 'block' : 'hidden'} print:block bg-slate-950 print:bg-white`}>
        {children}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Decision Chat (right panel)
// ─────────────────────────────────────────────────
const TIER_BADGE_COLORS: Record<number, string> = {
  1: 'bg-slate-800 text-slate-400',
  2: 'bg-slate-800 text-slate-400',
  3: 'bg-slate-800 text-amber-600',
  4: 'bg-slate-800 text-red-500',
}

function DecisionChat({
  data, situationId, principalId,
  approveState, onApprove,
}: {
  data: any; situationId: string | undefined; principalId: string;
  approveState: 'idle' | 'approving' | 'approved' | 'error';
  onApprove: (optionId: string) => void;
}) {
  const [messages, setMessages] = useState<Array<{ role: string; content: string; qa?: BriefingQAResponse }>>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedOption, setSelectedOption] = useState<string>(() => {
    const rec = data?.options?.find((o: any) => o.recommended)
    return rec?.id || data?.recommendation?.optionId || data?.options?.[0]?.id || 'opt_1'
  })
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendQuestion = async (question: string) => {
    if (!question.trim() || loading) return
    const userMsg = { role: 'user', content: question }
    const newHistory = [...messages.filter(m => m.role !== 'assistant' || !m.qa).map(m => ({ role: m.role, content: m.content })), { role: 'user', content: question }]
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)
    try {
      const requestId = localStorage.getItem(`solution_request_${situationId}`)
      if (!requestId) throw new Error('No request ID found')
      const qa = await askBriefingQuestion(requestId, question, principalId, newHistory)
      setMessages(prev => [...prev, { role: 'assistant', content: qa.answer, qa }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Q&A service unavailable. Please refer to the briefing content for details.',
        qa: { answer: '', transparency_tier: 4, tier_label: 'Unavailable', sources: [], suggested_followups: [] }
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuestion(input) }
  }

  const SUGGESTED_QUESTIONS = [
    'What is the primary root cause driving this KPI decline?',
    'Which option has the fastest time to impact?',
    'What are the biggest risks with the recommended option?',
    'Are there any internal benchmarks we can replicate?',
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-slate-700 bg-slate-800">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-semibold text-white">Decision Workspace</h3>
        </div>
        <p className="text-[10px] text-slate-400 mt-0.5">Ask questions · Select your initiative · Approve</p>
      </div>

      {/* Messages */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="space-y-2 pt-2">
            <p className="text-xs text-slate-400 text-center mb-3">Ask a question about this briefing</p>
            {SUGGESTED_QUESTIONS.map((q, i) => (
              <button
                key={i}
                onClick={() => sendQuestion(q)}
                className="w-full text-left text-xs px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[90%] rounded-lg px-3 py-2 ${msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-100'}`}>
              <p className="text-xs whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              {msg.qa && msg.qa.tier_label && (
                <span className={`inline-block text-[9px] uppercase tracking-wide px-1.5 py-0.5 rounded mt-1 ${TIER_BADGE_COLORS[msg.qa.transparency_tier] ?? 'bg-slate-800 text-slate-400'}`}>
                  {msg.qa.tier_label}
                  {msg.qa.sources?.length > 0 && ` · ${msg.qa.sources.join(', ')}`}
                </span>
              )}
              {msg.qa?.suggested_followups && msg.qa.suggested_followups.length > 0 && (
                <div className="mt-2 space-y-1">
                  {msg.qa.suggested_followups.map((f, j) => (
                    <button key={j} onClick={() => sendQuestion(f)}
                      className="block w-full text-left text-[10px] text-indigo-300 hover:text-indigo-200 truncate">
                      → {f}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 rounded-lg px-3 py-2">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Sticky footer: initiative selection + approve */}
      <div className="flex-shrink-0 border-t border-slate-700">
        {/* Input */}
        <div className="px-3 py-2 border-b border-slate-700">
          <div className="flex gap-1.5">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about this briefing..."
              disabled={loading}
              className="flex-1 px-3 py-1.5 text-xs bg-slate-800 text-white border border-slate-600 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder-slate-500 disabled:opacity-50"
            />
            <button
              onClick={() => sendQuestion(input)}
              disabled={!input.trim() || loading}
              className="p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-40 transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Initiative selection */}
        {data?.options && data.options.length > 0 && approveState !== 'approved' && (
          <div className="px-3 py-2 border-b border-slate-700">
            <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">Select Initiative</p>
            <div className="space-y-1.5">
              {data.options.map((opt: any, i: number) => {
                const optId = opt.id || `opt_${i + 1}`
                const label = String.fromCharCode(65 + i)
                return (
                  <label key={optId} className={`flex items-start gap-2 p-2 rounded-lg cursor-pointer transition-colors ${selectedOption === optId ? 'bg-indigo-900/40 border border-indigo-600' : 'bg-slate-800 border border-slate-700 hover:border-slate-600'}`}>
                    <input
                      type="radio"
                      name="initiative"
                      value={optId}
                      checked={selectedOption === optId}
                      onChange={() => setSelectedOption(optId)}
                      className="mt-0.5 accent-indigo-500"
                    />
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-bold text-slate-400">{label}</span>
                        {opt.recommended && <span className="text-[9px] bg-emerald-700 text-emerald-100 px-1 rounded">REC</span>}
                      </div>
                      <p className="text-xs text-slate-200 leading-snug truncate">{opt.title}</p>
                      {opt.roi && <p className="text-[10px] text-emerald-400">{formatROI(opt.roi)}</p>}
                    </div>
                  </label>
                )
              })}
            </div>
          </div>
        )}

        {/* Approve button */}
        <div className="px-3 py-2">
          {approveState === 'approved' ? (
            <div className="flex items-center gap-2 px-3 py-2 bg-emerald-900/40 border border-emerald-700 rounded-lg">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <div>
                <p className="text-xs font-semibold text-emerald-300">Decision Approved</p>
                <p className="text-[10px] text-emerald-500">Value Assurance tracking initiated</p>
              </div>
            </div>
          ) : (
            <button
              onClick={() => onApprove(selectedOption)}
              disabled={approveState === 'approving' || !selectedOption}
              className="w-full py-2 bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {approveState === 'approving' ? (
                <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Registering...</>
              ) : approveState === 'error' ? (
                <><AlertTriangle className="w-3.5 h-3.5" /> Retry Approval</>
              ) : (
                <><ShieldCheck className="w-3.5 h-3.5" /> Approve &amp; Track</>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────
export function ExecutiveBriefing() {
  const { situationId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const solutionIdParam = searchParams.get('solution_id')
  const [briefing, setBriefing] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [approveState, setApproveState] = useState<'idle' | 'approving' | 'approved' | 'error'>('idle')
  const [vaSolutionId, setVaSolutionId] = useState<string | null>(null)
  const [vaData, setVaData] = useState<VASolution | null>(null)
  const [showAttribution, setShowAttribution] = useState(false)
  const [openSections, setOpenSections] = useState<Set<string>>(
    new Set(['options', 'recommendation', 'roadmap'])
  )

  const toggleSection = (id: string) => {
    setOpenSections(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleExportPDF = useCallback(() => {
    const element = (document.querySelector('.briefing-content') || document.body) as HTMLElement
    const filename = `Decision-Briefing-${situationId || 'export'}.pdf`

    // Inject temporary print-mode styles so html2pdf captures white-paper format
    const printStyle = document.createElement('style')
    printStyle.id = 'pdf-export-style'
    printStyle.textContent = `
      .pdf-export-mode, .pdf-export-mode * { color-adjust: exact; -webkit-print-color-adjust: exact; }
      .pdf-export-mode { background: white !important; color: black !important; overflow: visible !important; }
      .pdf-export-mode .print\\:hidden { display: none !important; }
      .pdf-export-mode .hidden.print\\:block { display: block !important; }
      .pdf-export-mode .accordion-content { display: block !important; background: white !important; }
      .pdf-export-mode .accordion-content button { display: none !important; }
      .pdf-export-mode [class*="bg-slate-9"], .pdf-export-mode [class*="bg-slate-8"] { background: white !important; }
      .pdf-export-mode [class*="border-slate-7"], .pdf-export-mode [class*="border-slate-8"] { border-color: #e2e8f0 !important; }
      .pdf-export-mode [class*="text-slate-2"], .pdf-export-mode [class*="text-slate-3"] { color: #1e293b !important; }
      .pdf-export-mode [class*="text-slate-4"], .pdf-export-mode [class*="text-slate-5"] { color: #475569 !important; }
      .pdf-export-mode [class*="text-emerald-4"] { color: #059669 !important; }
      .pdf-export-mode [class*="text-amber-4"] { color: #d97706 !important; }
      .pdf-export-mode [class*="text-red-4"] { color: #dc2626 !important; }
      .pdf-export-mode table thead { background: #f1f5f9 !important; }
      .pdf-export-mode table thead th { color: #0f172a !important; }
      .pdf-export-mode table td { color: #334155 !important; }
    `
    document.head.appendChild(printStyle)
    element.classList.add('pdf-export-mode')

    const options = {
      margin: [10, 15] as [number, number],
      filename,
      image: { type: 'jpeg' as const, quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true },
      jsPDF: { orientation: 'portrait' as const, unit: 'mm', format: 'a4' },
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
    }

    html2pdf().set(options).from(element).save().then(() => {
      element.classList.remove('pdf-export-mode')
      printStyle.remove()
    })
  }, [situationId])

  const handleApprove = useCallback(async (optionId: string) => {
    const requestId = localStorage.getItem(`solution_request_${situationId}`)
    if (!requestId) return
    setApproveState('approving')
    try {
      const result = await approveSolution(requestId, optionId)
      // Extract VA solution ID from the last action entry
      const actions = result?.actions || []
      const lastAction = actions[actions.length - 1]
      const vaId = lastAction?.va_solution_id || null
      setVaSolutionId(vaId)
      if (vaId) {
        localStorage.setItem(`va_solution_${situationId}`, vaId)
        // Store briefing snapshot to Supabase for portfolio replay
        if (briefing) {
          storeBriefingSnapshot(vaId, briefing).catch(() => {
            // Non-fatal — briefing replay won't work but approval is fine
          })
        }
      }
      setApproveState('approved')
    } catch (err) {
      console.error('Approve failed:', err)
      setApproveState('error')
    }
  }, [situationId, briefing])

  // Fetch VA solution data after approval
  useEffect(() => {
    if (approveState === 'approved' && vaSolutionId) {
      getVASolution(vaSolutionId)
        .then(setVaData)
        .catch(() => {}) // VA data is supplementary — don't break the page
    }
  }, [approveState, vaSolutionId])

  useEffect(() => {
    // If loading from a VA solution snapshot (Portfolio replay)
    if (solutionIdParam) {
      getBriefingSnapshot(solutionIdParam)
        .then((snapshot) => {
          setBriefing(snapshot as any)
          setApproveState('approved')  // Show as already approved (read-only replay)
          setVaSolutionId(solutionIdParam)
        })
        .catch(() => {
          // Fall through to localStorage
          const stored = localStorage.getItem(`briefing_${situationId}`)
          if (stored) {
            setBriefing(JSON.parse(stored))
          }
        })
        .finally(() => setLoading(false))
      return
    }

    const stored = localStorage.getItem(`briefing_${situationId}`)
    if (stored) {
      setBriefing(JSON.parse(stored))
    }
    // Restore approval state from localStorage
    const storedVaId = localStorage.getItem(`va_solution_${situationId}`)
    if (storedVaId) {
      setVaSolutionId(storedVaId)
      setApproveState('approved')
    }
    setLoading(false)
  }, [situationId, solutionIdParam])

  const principalId = briefing?.principalId || briefing?.principal_id || 'cfo_001'

  if (loading) {
    return (
      <div className="h-screen bg-slate-950 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    )
  }

  if (!briefing) {
    return (
      <div className="h-screen bg-slate-950 flex items-center justify-center p-8">
        <div className="max-w-xl w-full bg-slate-900/60 border border-slate-800 rounded-xl p-6">
          <h2 className="text-xl font-bold text-white mb-2">Briefing not generated yet</h2>
          <p className="text-slate-400 mb-6">
            Go back to Decision Studio, run Deep Analysis, then click "Generate Solution Options".
          </p>
          <Link to="/dashboard"
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Decision Studio
          </Link>
        </div>
      </div>
    )
  }

  const data = briefing

  const FIRM_DISPLAY_NAMES: Record<string, string> = {
    mckinsey: 'McKinsey & Company', bcg: 'BCG', bain: 'Bain & Company', mbb: 'MBB Council',
  }
  const FIRM_STYLES: Record<string, { bar: string; border: string; badge: string; dot: string }> = {
    mckinsey:     { bar: 'bg-blue-700',    border: 'border-l-blue-700',    badge: 'bg-blue-50 text-blue-800',      dot: 'bg-blue-700' },
    bcg:          { bar: 'bg-emerald-600', border: 'border-l-emerald-600', badge: 'bg-emerald-50 text-emerald-800', dot: 'bg-emerald-600' },
    bain:         { bar: 'bg-red-600',     border: 'border-l-red-600',     badge: 'bg-red-50 text-red-800',         dot: 'bg-red-600' },
    deloitte:     { bar: 'bg-green-700',   border: 'border-l-green-700',   badge: 'bg-green-50 text-green-800',     dot: 'bg-green-700' },
    accenture:    { bar: 'bg-purple-600',  border: 'border-l-purple-600',  badge: 'bg-purple-50 text-purple-800',   dot: 'bg-purple-600' },
    ey_parthenon: { bar: 'bg-yellow-600',  border: 'border-l-yellow-600',  badge: 'bg-yellow-50 text-yellow-800',   dot: 'bg-yellow-600' },
    kpmg:         { bar: 'bg-sky-700',     border: 'border-l-sky-700',     badge: 'bg-sky-50 text-sky-800',         dot: 'bg-sky-700' },
    pwc_strategy: { bar: 'bg-orange-600',  border: 'border-l-orange-600',  badge: 'bg-orange-50 text-orange-800',   dot: 'bg-orange-600' },
  }
  const convictionStyle: Record<string, string> = {
    High: 'bg-emerald-100 text-emerald-800', Medium: 'bg-amber-100 text-amber-800', Low: 'bg-slate-100 text-slate-600',
  }
  const defaultFirmStyle = { bar: 'bg-indigo-600', border: 'border-l-indigo-600', badge: 'bg-indigo-50 text-indigo-800', dot: 'bg-indigo-600' }

  return (
    <div className="h-screen flex flex-col bg-slate-950 overflow-hidden print:h-auto print:overflow-visible print:text-black print:bg-white">
      {/* Nav */}
      <nav className="flex-shrink-0 bg-slate-900 border-b border-slate-800 py-3 px-6 flex justify-between items-center print:hidden z-50">
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors text-sm">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Link>
          <BrandLogo size={24} />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white truncate max-w-xs mr-3">{data.title}</span>
          <button
            onClick={() => {
              const allIds = ['situation', 'market', 'stage1', 'crossreview', 'options', 'roadmap', 'risks', 'blindspots', 'inaction', 'recommendation']
              const allOpen = allIds.every(id => openSections.has(id))
              setOpenSections(allOpen ? new Set(['options', 'recommendation', 'roadmap']) : new Set(allIds))
            }}
            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
          >
            {['situation', 'market', 'stage1', 'crossreview', 'risks', 'blindspots', 'inaction'].every(id => openSections.has(id)) ? 'Collapse All' : 'Expand All'}
          </button>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
            title="Opens print dialog for multi-page PDF or hardcopy"
          >
            <Printer className="w-3.5 h-3.5" />
            Print
          </button>
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
            title="Download as standalone PDF file"
          >
            <Download className="w-3.5 h-3.5" />
            Export
          </button>
          <button
            onClick={() => navigate(`/report/${situationId}`)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors"
            title="Open narrative-arc white-paper report"
          >
            <FileText className="w-3.5 h-3.5" />
            View Report
          </button>
        </div>
      </nav>

      {/* Two-panel body */}
      <div className="flex-1 min-h-0 flex overflow-hidden print:overflow-visible print:block">
        {/* ── Left: Briefing content ── */}
        <div className="briefing-content flex-1 overflow-y-auto bg-slate-950 p-4 print:p-0 print:bg-white print:overflow-visible">
          <div className="max-w-3xl mx-auto">

            {/* ── Print-only header ─────────────────────────────────────────── */}
            <div className="hidden print:block mb-8 pb-4 border-b border-slate-300">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <BrandLogo size={28} scheme="dark" />
                  <div>
                    <div className="text-xs text-slate-500 uppercase tracking-widest font-mono">Decision Studio</div>
                    <div className="text-xs text-slate-400 font-mono">Executive Debrief</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-slate-500 font-mono">{situationId}</div>
                  <div className="text-[10px] text-slate-500 font-mono">{new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</div>
                </div>
              </div>

              {/* KPI / Principal / Classification row */}
              <div className="mt-2 flex items-center gap-4 text-[10px] font-mono text-slate-500">
                <span>KPI: {data.kpiData?.kpi_name || '—'}</span>
                <span>|</span>
                <span>Principal: {principalId}</span>
                <span>|</span>
                <span className="px-1.5 py-0.5 border border-slate-400 text-slate-600 rounded text-[9px] uppercase tracking-wider">Internal — Decision Sensitive</span>
              </div>

              {/* Monochrome metadata strip */}
              {(() => {
                const recOption = data.options?.find((o: any) => o.recommended)
                const roi = recOption?.roi || recOption?.expected_roi || '—'
                const timeline = recOption?.timeline || '—'
                const investment = recOption?.investment || recOption?.effort || 'Moderate'
                return (
                  <div className="mt-4 grid grid-cols-4 gap-3">
                    <div>
                      <div className="text-[9px] text-slate-500 uppercase tracking-wider font-mono">Est. ROI</div>
                      <div className="text-xs text-slate-800 font-semibold">{formatROI(roi)}</div>
                    </div>
                    <div>
                      <div className="text-[9px] text-slate-500 uppercase tracking-wider font-mono">Timeline</div>
                      <div className="text-xs text-slate-800 font-semibold">{timeline}</div>
                    </div>
                    <div>
                      <div className="text-[9px] text-slate-500 uppercase tracking-wider font-mono">Investment</div>
                      <div className="text-xs text-slate-800 font-semibold">{investment}</div>
                    </div>
                    <div>
                      <div className="text-[9px] text-slate-500 uppercase tracking-wider font-mono">Decision By</div>
                      <div className="text-xs text-slate-800 font-semibold">{data.metrics?.decisionDeadline || '—'}</div>
                    </div>
                  </div>
                )
              })()}
            </div>

            {/* ── Flash Briefing (print-only) ───────────────────────────────── */}
            {(() => {
              const scqa = data.executiveSummary || data.situation?.currentState || ''
              const rec = data.recommendation?.title || data.options?.find((o: any) => o.recommended)?.title || ''
              const rationale = data.recommendation?.rationale || data.recommendation_rationale || ''
              const topDrivers: string[] = data.situation?.topDrivers?.slice(0, 2).map((d: any) => d.label || d.segment || '') ?? []
              const roi = data.options?.find((o: any) => o.recommended)?.roi || ''

              const sentences: string[] = []
              if (scqa) sentences.push(scqa.length > 200 ? scqa.slice(0, 200).trimEnd() + '…' : scqa)
              if (topDrivers.length) sentences.push(`Primary drivers: ${topDrivers.join(' and ')}.`)
              if (rec) sentences.push(`The council recommends ${rec}${rationale ? ': ' + (rationale.length > 120 ? rationale.slice(0, 120).trimEnd() + '…' : rationale) : ''}.`)
              if (roi) sentences.push(`Expected return: ${formatROI(roi)}.`)
              if (sentences.length < 3) sentences.push('Review the full analysis below before making a decision.')

              if (sentences.length === 0) return null
              return (
                <div className="hidden print:block mb-6 p-4 border-l-2 border-slate-400 bg-slate-50">
                  <div className="text-[9px] text-slate-500 uppercase tracking-wider font-mono mb-2">Flash Briefing</div>
                  <p className="text-xs text-slate-700 leading-relaxed">{sentences.join(' ')}</p>
                </div>
              )
            })()}

            {/* Print-only: Situation & Context */}
            <div className="hidden print:block mb-6">
              <div className="text-[9px] text-slate-500 uppercase tracking-wider font-mono mb-2 border-b border-slate-200 pb-1">
                Situation &amp; Context
              </div>
              <p className="text-xs text-slate-700 mb-2 leading-relaxed">{data.situation?.currentState}</p>
              <p className="text-xs text-slate-700 leading-relaxed">{data.situation?.problem}</p>
            </div>

            {/* Print-only: Problem Statement & Root Causes */}
            {data.situation?.keyQuestion && (
              <div className="hidden print:block mb-6">
                <div className="text-[9px] text-slate-500 uppercase tracking-wider font-mono mb-2 border-b border-slate-200 pb-1">
                  Problem Statement &amp; Root Causes
                </div>
                <p className="text-xs font-semibold text-slate-800 mb-3 border-l-2 border-slate-400 pl-3">
                  Key Question: {data.situation.keyQuestion}
                </p>
                {data.situation?.rootCauses?.length > 0 && (
                  <ol className="space-y-2">
                    {data.situation.rootCauses.map((cause: any, i: number) => (
                      <li key={i} className="text-xs text-slate-700">
                        <span className="font-semibold">{i + 1}. {cause.driver}</span>
                        {cause.evidence && <span className="text-slate-500 ml-1">— {cause.evidence}</span>}
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            )}

            {/* Print-only: Market Context */}
            {data.market_signals?.length > 0 && (
              <div className="hidden print:block mb-6">
                <div className="text-[9px] text-slate-500 uppercase tracking-wider font-mono mb-2 border-b border-slate-200 pb-1">
                  Market Context
                </div>
                <div className="space-y-2">
                  {data.market_signals.slice(0, 4).map((signal: any, i: number) => (
                    <div key={i} className="text-xs text-slate-700">
                      <span className="font-semibold">{signal.title}</span>
                      {signal.summary && <span className="ml-1 text-slate-600">— {signal.summary}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Hero Recommendation Card */}
            {(() => {
              const recOption = data.options?.find((o: any) => o.recommended) ?? data.options?.[0]
              if (!recOption) return null
              const roi = recOption?.roi || recOption?.expected_roi || '—'
              const timeline = recOption?.timeline || '—'
              const investment = recOption?.investment || recOption?.effort || 'Moderate'
              const risk = recOption?.riskLevel || recOption?.risk || '—'
              const riskColor = risk === 'Low' ? 'text-emerald-400' : risk === 'Medium' ? 'text-amber-400' : risk === 'High' ? 'text-red-400' : 'text-slate-300'
              return (
                <div className="print:hidden mb-4">
                  {/* Kicker */}
                  <div className="flex items-center gap-3 mb-3">
                    <div className="h-px flex-1 bg-slate-700" />
                    <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500">Council Recommendation</span>
                    <div className="h-px flex-1 bg-slate-700" />
                  </div>
                  {/* Main card */}
                  <div className="border border-slate-700 border-l-4 border-l-emerald-500 bg-slate-900 rounded-xl p-6">
                    {/* Top row */}
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div className="flex-1 min-w-0">
                        <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-1">Recommended Path</p>
                        <h2 className="text-lg font-bold text-white leading-snug">{recOption.title}</h2>
                      </div>
                      {approveState === 'approved' && (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-900/50 border border-emerald-600 rounded-full flex-shrink-0">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-xs font-semibold text-emerald-300">Approved</span>
                        </div>
                      )}
                    </div>
                    {/* Rationale */}
                    {data.recommendation?.rationale && (
                      <p className="text-sm text-slate-300 leading-relaxed mb-5">{data.recommendation.rationale}</p>
                    )}
                    {/* 4-metric grid */}
                    <div className="grid grid-cols-4 gap-3 mb-5">
                      <div className="bg-slate-800/60 rounded-lg p-3">
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Est. ROI</p>
                        <p className="text-sm font-bold text-emerald-400">{formatROI(roi)}</p>
                      </div>
                      <div className="bg-slate-800/60 rounded-lg p-3">
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Time to Value</p>
                        <p className="text-sm font-bold text-amber-400">{timeline}</p>
                      </div>
                      <div className="bg-slate-800/60 rounded-lg p-3">
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Investment</p>
                        <p className="text-sm font-bold text-blue-400">{investment}</p>
                      </div>
                      <div className="bg-slate-800/60 rounded-lg p-3">
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Risk Level</p>
                        <p className={`text-sm font-bold ${riskColor}`}>{risk}</p>
                      </div>
                    </div>
                    {/* Footer strip */}
                    {(data.recommendation?.decisionOwner || data.recommendation?.deadline) && (
                      <div className="flex items-center justify-between pt-4 border-t border-slate-700 text-xs text-slate-400">
                        {data.recommendation?.decisionOwner && (
                          <div>
                            <span className="text-slate-600 uppercase tracking-wider text-[10px] font-mono">Decision Owner</span>
                            <p className="text-slate-300 font-semibold mt-0.5">{data.recommendation.decisionOwner}</p>
                          </div>
                        )}
                        {data.recommendation?.deadline && (
                          <div className="text-right">
                            <span className="text-slate-600 uppercase tracking-wider text-[10px] font-mono">Deadline</span>
                            <p className="text-slate-300 font-semibold mt-0.5">{data.recommendation.deadline}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )
            })()}

            {/* [D] Strategic Options */}
            <AccordionSection id="options" title="Strategic Options" openSections={openSections} onToggle={toggleSection}
              badge={`${data.options?.length || 0} options`}
              icon={<Target className="w-4 h-4 text-slate-400" />}>
              <div className="p-5">
                <p className="text-slate-400 text-sm mb-4 print:text-slate-600">Three strategic pathways evaluated against financial impact, complexity, risk, and priority alignment.</p>
                {/* Comparison table */}
                <div className="overflow-x-auto rounded-lg border border-slate-700 mb-6 print:border-slate-200">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-800 text-slate-300 font-bold uppercase print:bg-slate-100 print:text-slate-900">
                      <tr>
                        <th className="p-3 border-b border-slate-700 min-w-[120px] print:border-slate-200">Criteria</th>
                        {data.options?.map((opt: any, i: number) => (
                          <th key={i} className={`p-3 border-b border-slate-700 min-w-[160px] print:border-slate-200 ${opt.recommended ? 'bg-emerald-900/30 print:bg-emerald-50 print:text-emerald-800' : ''}`}>
                            {opt.recommended && <div className="text-[9px] text-emerald-400 mb-0.5 flex items-center gap-1 print:text-emerald-600"><CheckCircle className="w-2.5 h-2.5" /> RECOMMENDED</div>}
                            Option {String.fromCharCode(65 + i)}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 print:divide-slate-100">
                      {[
                        { label: 'Strategy', key: 'title', cls: 'font-medium text-slate-200 print:text-slate-900' },
                        { label: 'Est. ROI', key: 'roi', cls: 'font-bold text-emerald-400 print:text-emerald-600' },
                        { label: 'Investment', key: 'investment', cls: 'text-slate-400 print:text-slate-600' },
                        { label: 'Timeline', key: 'timeline', cls: 'text-slate-400 print:text-slate-600' },
                      ].map(({ label, key, cls }) => (
                        <tr key={key}>
                          <td className="p-3 font-semibold text-slate-400 bg-slate-900/50 print:text-slate-700 print:bg-slate-50">{label}</td>
                          {data.options?.map((opt: any, i: number) => (
                            <td key={i} className={`p-3 ${cls} ${opt.recommended ? 'bg-emerald-900/10 print:bg-emerald-50/30' : ''}`}>
                              {key === 'roi' ? formatROI(opt[key]) : opt[key]}
                            </td>
                          ))}
                        </tr>
                      ))}
                      <tr>
                        <td className="p-3 font-semibold text-slate-400 bg-slate-900/50 print:text-slate-700 print:bg-slate-50">Risk</td>
                        {data.options?.map((opt: any, i: number) => (
                          <td key={i} className={`p-3 ${opt.recommended ? 'bg-emerald-900/10 print:bg-emerald-50/30' : ''}`}>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              opt.riskLevel === 'Low' ? 'bg-emerald-900/40 text-emerald-400 print:bg-emerald-100 print:text-emerald-700' :
                              opt.riskLevel === 'Medium' ? 'bg-amber-900/40 text-amber-400 print:bg-amber-100 print:text-amber-700' : 'bg-red-900/40 text-red-400 print:bg-red-100 print:text-red-700'}`}>
                              {opt.riskLevel}
                            </span>
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
                {/* Option detail cards */}
                <div className="space-y-6">
                  {data.options?.map((option: any, i: number) => (
                    <motion.div key={i} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                      className={`rounded-xl overflow-hidden border ${option.recommended ? 'border-slate-600 border-l-4 border-l-emerald-500 bg-slate-900' : 'border-slate-700 bg-slate-900'} print:bg-white print:border-slate-200 ${option.recommended ? 'print:border-l-slate-800' : ''}`}>
                      {option.recommended && (
                        <div className="bg-emerald-900/40 text-emerald-300 px-4 py-1.5 text-xs font-semibold flex items-center gap-2 print:bg-slate-800 print:text-white">
                          <CheckCircle className="w-3.5 h-3.5" /> RECOMMENDED
                        </div>
                      )}
                      <div className="p-5">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="text-lg font-bold text-white print:text-slate-900">Option {String.fromCharCode(65 + i)}: {option.title}</h3>
                            <p className="text-slate-400 text-sm mt-0.5 print:text-slate-600">{option.subtitle}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-slate-500">Est. ROI</p>
                            <p className="text-xl font-bold text-emerald-400 print:text-emerald-600">{formatROI(option.roi)}</p>
                          </div>
                        </div>
                        <p className="text-slate-300 text-sm leading-relaxed mb-4 print:text-slate-700">{option.description}</p>
                        <div className="grid grid-cols-4 gap-3 mb-4">
                          {[{ label: 'Investment', val: option.investment }, { label: 'Timeline', val: option.timeline },
                            { label: 'Risk', val: option.riskLevel, cls: option.riskLevel === 'Low' ? 'text-emerald-400 print:text-emerald-600' : option.riskLevel === 'Medium' ? 'text-amber-400 print:text-amber-600' : 'text-red-400 print:text-red-600' },
                            { label: 'Reversibility', val: option.reversibility }].map(({ label, val, cls }) => (
                            <div key={label} className="text-center p-2 bg-slate-800/60 rounded-lg print:bg-slate-100">
                              <p className="text-[10px] text-slate-500 uppercase">{label}</p>
                              <p className={`font-bold text-xs text-slate-200 print:text-slate-900 ${cls || ''}`}>{val}</p>
                            </div>
                          ))}
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <h4 className="font-semibold text-slate-300 mb-2 flex items-center gap-1.5 text-sm print:text-slate-700">
                              <CheckCircle className="w-3.5 h-3.5 text-slate-500" /> Arguments For
                            </h4>
                            <ul className="space-y-1.5">
                              {option.prosDetailed?.map((pro: any, j: number) => (
                                <li key={j} className="text-xs text-slate-400 flex items-start gap-1.5 print:text-slate-700">
                                  <ChevronRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0 mt-0.5" />
                                  <span>{pro.point?.replace(/[:]+$/, '')}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <h4 className="font-semibold text-slate-300 mb-2 flex items-center gap-1.5 text-sm print:text-slate-700">
                              <AlertTriangle className="w-3.5 h-3.5 text-slate-500" /> Arguments Against
                            </h4>
                            <ul className="space-y-1.5">
                              {option.consDetailed?.map((con: any, j: number) => (
                                <li key={j} className="text-xs text-slate-400 flex items-start gap-1.5 print:text-slate-700">
                                  <ChevronRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0 mt-0.5" />
                                  <span>{con.point?.replace(/[:]+$/, '')}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                        {option.perspectives && (
                          <div className="mt-4 pt-4 border-t border-slate-700 print:border-slate-200">
                            <h4 className="font-semibold text-slate-200 mb-2 flex items-center gap-1.5 text-sm print:text-slate-900">
                              <Users className="w-3.5 h-3.5" /> Stakeholder Perspectives
                            </h4>
                            <div className="grid grid-cols-3 gap-3">
                              {option.perspectives.map((p: any, j: number) => (
                                <div key={j} className="bg-slate-800/60 p-2.5 rounded-lg print:bg-slate-50">
                                  <p className="font-medium text-slate-200 text-xs print:text-slate-900">{p.role}</p>
                                  <p className="text-xs text-slate-400 mt-0.5 print:text-slate-600">{p.view}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </AccordionSection>

            {/* [E] Next Steps & Implementation */}
            <AccordionSection id="recommendation" title="Next Steps & Implementation" openSections={openSections} onToggle={toggleSection}
              icon={<CheckCircle2 className="w-4 h-4 text-slate-400" />}>
              <div className="p-5">
                {/* Screen: gradient blue card / Print: monochrome left-border callout */}
                <div className="bg-slate-900 border border-slate-700 text-white p-6 rounded-xl print:bg-white print:border-l-4 print:border-slate-800 print:rounded-none print:pl-5 print:pr-0 print:py-3">
                  <h3 className="text-lg font-bold mb-3 print:text-slate-900">{data.recommendation?.headline}</h3>
                  <p className="text-slate-300 leading-relaxed text-sm mb-5 print:text-slate-700">{data.recommendation?.rationale}</p>
                  <div className="bg-slate-800/60 rounded-lg p-4 mb-5 print:bg-transparent print:p-0">
                    <h4 className="font-semibold mb-2 text-sm text-slate-200 print:text-slate-800">Immediate Actions Required:</h4>
                    <ol className="space-y-1.5">
                      {(data.recommendation?.nextSteps || []).map((step: string, i: number) => (
                        <li key={i} className="flex items-start gap-2.5">
                          <span className="w-5 h-5 bg-emerald-600 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 print:bg-slate-800">{i + 1}</span>
                          <span className="text-sm text-slate-300 print:text-slate-700">{step}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                  <div className="flex items-center justify-between pt-3 border-t border-slate-700 text-sm print:border-slate-300">
                    <div>
                      <p className="text-slate-500 text-xs uppercase tracking-wider font-mono print:text-slate-500">Decision Owner</p>
                      <p className="font-semibold text-slate-200 print:text-slate-900">{data.recommendation?.decisionOwner}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-slate-500 text-xs uppercase tracking-wider font-mono print:text-slate-500">Decision Deadline</p>
                      <p className="font-semibold text-slate-200 print:text-slate-900">{data.recommendation?.deadline}</p>
                    </div>
                  </div>
                </div>

                {/* Approval confirmation (shown after approval) */}
                {approveState === 'approved' && (() => {
                  const approvedOption = data.options?.find((o: any) => o.recommended) || data.options?.[0]
                  return (
                    <div className="mt-4 bg-emerald-50 border-2 border-emerald-300 rounded-xl p-5 print:hidden">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-9 h-9 bg-emerald-600 rounded-full flex items-center justify-center">
                          <CheckCircle2 className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h3 className="text-base font-bold text-emerald-900">Decision Approved</h3>
                          <p className="text-xs text-emerald-700">Value Assurance tracking has been initiated</p>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-3 mb-3">
                        {[
                          { label: 'Approved Strategy', val: approvedOption?.title || data.recommendation?.headline },
                          { label: 'Expected Recovery', val: formatROI(approvedOption?.roi || '') || 'See option details' },
                          { label: 'Monitoring Window', val: approvedOption?.timeline || '30 days' },
                        ].map(({ label, val }) => (
                          <div key={label} className="bg-white rounded-lg p-2.5 border border-emerald-200">
                            <p className="text-[10px] text-slate-500 uppercase mb-0.5">{label}</p>
                            <p className="text-xs font-semibold text-slate-900">{val}</p>
                          </div>
                        ))}
                      </div>
                      {vaSolutionId && (
                        <div className="bg-white rounded-lg p-2.5 border border-emerald-200 mb-3">
                          <p className="text-[10px] text-slate-500 uppercase mb-0.5">VA Reference</p>
                          <p className="text-xs font-mono text-slate-700">{vaSolutionId.slice(0, 8)}...</p>
                        </div>
                      )}
                      <div className="bg-emerald-100/50 rounded-lg p-3 text-xs text-emerald-800">
                        <p className="font-medium mb-1">What happens next:</p>
                        <ol className="space-y-0.5 text-emerald-700 list-decimal list-inside">
                          <li>Value Assurance Agent monitors KPI performance against the expected recovery range</li>
                          <li>Difference-in-Differences attribution separates your intervention's impact from market movements</li>
                          <li>Results will appear on your Solutions Portfolio dashboard</li>
                        </ol>
                      </div>
                      <Link
                        to={`/portfolio?principal=${encodeURIComponent(principalId)}`}
                        className="mt-3 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 text-white text-xs font-semibold rounded-lg hover:bg-emerald-500 transition-colors"
                      >
                        View Portfolio <ChevronRight className="w-3.5 h-3.5" />
                      </Link>

                      {/* Value Assurance Panel — live tracking data */}
                      {vaData && (
                        <div className="mt-4">
                          <ValueAssurancePanel
                            solutionId={vaData.solution_id}
                            solutionDescription={vaData.solution_description}
                            approvedAt={vaData.approved_at}
                            status={vaData.status}
                            evaluation={vaData.impact_evaluation ?? undefined}
                            compositeVerdict={vaData.impact_evaluation?.composite_verdict ?? undefined}
                            onViewAttribution={() => setShowAttribution(!showAttribution)}
                          />
                          {showAttribution && vaData.impact_evaluation && (
                            <div className="mt-3">
                              <AttributionBreakdown
                                totalChange={vaData.impact_evaluation.total_kpi_change}
                                attributableImpact={vaData.impact_evaluation.attributable_impact}
                                marketDrivenRecovery={vaData.impact_evaluation.market_driven_recovery}
                                seasonalComponent={vaData.impact_evaluation.seasonal_component}
                                controlGroupChange={vaData.impact_evaluation.control_group_change}
                                expectedLower={vaData.impact_evaluation.expected_impact_lower}
                                expectedUpper={vaData.impact_evaluation.expected_impact_upper}
                                controlGroupDescription={vaData.impact_evaluation.control_group_description ?? undefined}
                              />
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )
                })()}
              </div>
            </AccordionSection>

            {/* [F] Implementation Roadmap */}
            {data.roadmap?.length > 0 && (
              <AccordionSection id="roadmap" title="Implementation Roadmap" openSections={openSections} onToggle={toggleSection}
                icon={<Clock className="w-4 h-4 text-slate-400" />}>
                <div className="p-5">
                  <div className="relative">
                    <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-slate-700 print:bg-slate-300" />
                    <div className="space-y-4">
                      {data.roadmap.map((phase: any, i: number) => (
                        <div key={i} className="relative pl-12">
                          <div className={`absolute left-3.5 w-4 h-4 rounded-full border-2 ${i === 0 ? 'bg-emerald-600 border-emerald-600 print:bg-blue-600 print:border-blue-600' : 'bg-slate-900 border-slate-600 print:bg-white print:border-slate-300'}`} />
                          <div className="bg-slate-900 border border-slate-700 p-3 rounded-lg print:bg-slate-50 print:border-0">
                            <div className="flex justify-between items-start mb-1.5">
                              <h4 className="font-semibold text-slate-200 text-sm print:text-slate-900">{phase.phase}</h4>
                              <span className="text-xs text-slate-500 flex items-center gap-1">
                                <Clock className="w-3 h-3" />{phase.timeline || phase.duration}
                              </span>
                            </div>
                            {phase.description && <p className="text-slate-400 text-xs mb-2 print:text-slate-700">{phase.description}</p>}
                            <div className="flex flex-wrap gap-1.5">
                              {(phase.items || phase.deliverables || []).map((d: string, j: number) => (
                                <span key={j} className="px-2 py-0.5 bg-slate-800 text-slate-300 text-xs rounded-full print:bg-blue-100 print:text-blue-700">{d}</span>
                              ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </AccordionSection>
            )}

            {/* [G] Supporting Analysis divider */}
            <div className="print:hidden flex items-center gap-3 mt-6 mb-2">
              <div className="h-px flex-1 bg-slate-800" />
              <button
                onClick={() => {
                  const ids = ['situation', 'market', 'stage1', 'crossreview']
                  const allOpen = ids.every(id => openSections.has(id))
                  setOpenSections(prev => {
                    const next = new Set(prev)
                    ids.forEach(id => allOpen ? next.delete(id) : next.add(id))
                    return next
                  })
                }}
                className="text-[10px] font-mono uppercase tracking-widest text-slate-500 hover:text-slate-300 flex items-center gap-1.5 transition-colors"
              >
                <ChevronDown className="w-3 h-3" /> Supporting Analysis
              </button>
              <div className="h-px flex-1 bg-slate-800" />
            </div>

            {/* [H] Situation Analysis */}
            <AccordionSection id="situation" title="Situation Analysis" openSections={openSections} onToggle={toggleSection}
              icon={<Zap className="w-4 h-4 text-slate-400" />}>
              <div className="p-5 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-900 border border-slate-700 p-5 rounded-lg print:bg-slate-50 print:border-slate-200">
                    <h3 className="font-semibold text-slate-200 mb-2 flex items-center gap-2 text-sm print:text-slate-900">
                      <Target className="w-4 h-4 text-slate-400 print:text-blue-600" /> Current State
                    </h3>
                    <p className="text-slate-400 text-sm leading-relaxed print:text-slate-700">{data.situation?.currentState}</p>
                  </div>
                  <div className="bg-slate-900 border border-slate-700 p-5 rounded-lg print:bg-red-50 print:border-red-200">
                    <h3 className="font-semibold text-slate-200 mb-2 flex items-center gap-2 text-sm print:text-slate-900">
                      <AlertTriangle className="w-4 h-4 text-red-400 print:text-red-600" /> The Problem
                    </h3>
                    <p className="text-slate-400 text-sm leading-relaxed print:text-slate-700">{data.situation?.problem}</p>
                  </div>
                </div>
                {data.situation?.rootCauses?.length > 0 && (
                  <div className="bg-slate-800/60 border border-slate-700 text-white p-5 rounded-lg print:bg-slate-900">
                    <h3 className="font-semibold mb-3 flex items-center gap-2 text-sm">
                      <Zap className="w-4 h-4 text-amber-400" /> Root Cause Analysis
                    </h3>
                    <div className="space-y-3">
                      {data.situation.rootCauses.map((cause: any, i: number) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="w-5 h-5 bg-amber-500 text-slate-900 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">{i + 1}</div>
                          <div>
                            <p className="font-medium text-white text-sm">{cause.driver}</p>
                            <p className="text-slate-400 text-xs">{cause.evidence}</p>
                            <p className="text-amber-400 text-xs font-medium mt-0.5">Impact: {cause.impact}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {data.situation?.keyQuestion && (
                  <div className="bg-slate-900 border-l-4 border-slate-500 p-4 rounded-r-lg print:bg-blue-50 print:border-blue-600">
                    <h3 className="font-semibold text-slate-200 mb-1 text-sm print:text-blue-900">Key Question</h3>
                    <p className="text-slate-400 italic text-sm print:text-blue-800">{data.situation.keyQuestion}</p>
                  </div>
                )}
                {data.situation?.assumptions?.length > 0 && (
                  <div className="bg-slate-900 border border-slate-700 p-4 rounded-lg print:bg-amber-50 print:border-amber-200">
                    <h3 className="font-semibold text-slate-200 mb-2 text-sm print:text-amber-900">Key Assumptions</h3>
                    <ul className="space-y-1">
                      {data.situation.assumptions.map((a: string, i: number) => (
                        <li key={i} className="text-slate-400 text-sm flex items-start gap-2 print:text-amber-800">
                          <span className="text-slate-600 print:text-amber-500">•</span>{a}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </AccordionSection>

            {/* [I] Market Intelligence */}
            {data.market_signals?.length > 0 && (
              <AccordionSection id="market" title="Market Intelligence" openSections={openSections} onToggle={toggleSection}
                badge={`${data.market_signals.length} signals`}
                icon={<Sparkles className="w-4 h-4 text-amber-400" />}>
                <div className="p-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {data.market_signals.map((signal: any, i: number) => (
                      <div key={i} className="bg-slate-900 border border-slate-700 rounded-lg p-4 print:bg-amber-50 print:border-amber-200">
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <h3 className="font-semibold text-slate-200 text-sm leading-snug print:text-slate-900">{signal.title}</h3>
                          {signal.relevance_score != null && (
                            <span className="shrink-0 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-900/40 text-amber-400 print:bg-amber-200 print:text-amber-800">
                              {Math.round(signal.relevance_score * 100)}%
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-slate-400 leading-relaxed mb-2 print:text-slate-700">{signal.summary}</p>
                        {signal.source && <p className="text-xs text-slate-500">Source: {signal.source}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              </AccordionSection>
            )}

            {/* [J] Stage 1: Independent Firm Proposals */}
            {data.stage_1_hypotheses && (
              <AccordionSection id="stage1" title="Stage 1: Independent Firm Proposals" openSections={openSections} onToggle={toggleSection}
                icon={<Users className="w-4 h-4 text-slate-400" />}>
                <div className="p-5">
                  <p className="text-slate-400 text-sm mb-4 print:text-slate-600">Each firm independently analyzed the problem and proposed an intervention using their signature framework.</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(data.stage_1_hypotheses).map(([firmId, hyp]: [string, any]) => {
                      const s = FIRM_STYLES[firmId] ?? defaultFirmStyle
                      const conviction = hyp.conviction || 'High'
                      const displayName = FIRM_DISPLAY_NAMES[firmId.toLowerCase()] ?? (firmId.charAt(0).toUpperCase() + firmId.slice(1).replace(/_/g, ' '))
                      return (
                        <div key={firmId} className="bg-slate-900 border border-slate-700 rounded-xl overflow-hidden flex flex-col print:bg-white print:border-slate-200 print:shadow-sm">
                          <div className={`h-1.5 w-full ${s.bar}`} />
                          <div className="p-4 flex flex-col flex-1">
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <div className={`w-2 h-2 rounded-full ${s.dot}`} />
                                <h4 className="font-bold text-slate-200 text-sm print:text-slate-900">{displayName}</h4>
                              </div>
                              {conviction && (
                                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${convictionStyle[conviction] ?? convictionStyle.Medium}`}>
                                  {conviction}
                                </span>
                              )}
                            </div>
                            {hyp.framework && (
                              <span className={`self-start text-xs font-medium px-2 py-0.5 rounded-full mb-2 ${s.badge}`}>{hyp.framework}</span>
                            )}
                            <p className="text-sm text-slate-400 leading-relaxed mb-3 flex-1 print:text-slate-700">{hyp.hypothesis}</p>
                            {Array.isArray(hyp.key_evidence) && hyp.key_evidence.length > 0 && (
                              <div className="bg-slate-800/60 rounded-lg p-2 mb-3 print:bg-slate-50">
                                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-1">Evidence</p>
                                <ul className="space-y-1">
                                  {hyp.key_evidence.slice(0, 3).map((ev: string, i: number) => (
                                    <li key={i} className="flex items-start gap-1 text-xs text-slate-400 print:text-slate-600">
                                      <span className="text-slate-600 shrink-0 print:text-slate-400">▸</span><span>{ev}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {hyp.recommended_focus && (
                              <div className={`border-l-4 ${s.border} pl-2 mt-auto`}>
                                <p className="text-[10px] font-semibold text-slate-500 uppercase">Primary Focus</p>
                                <p className="text-sm font-semibold text-slate-200 print:text-slate-900">{hyp.recommended_focus}</p>
                              </div>
                            )}
                            {hyp.proposed_option?.title && (
                              <div className="mt-2">
                                <p className="text-[10px] font-semibold text-slate-500 uppercase">Proposed Action</p>
                                <p className="text-sm font-semibold text-indigo-400 leading-snug print:text-blue-700">{hyp.proposed_option.title}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              </AccordionSection>
            )}

            {/* [K] Stage 2: Cross-Review */}
            {data.cross_review && (
              <AccordionSection id="crossreview" title="Stage 2: Cross-Review" openSections={openSections} onToggle={toggleSection}
                icon={<ShieldCheck className="w-4 h-4 text-slate-400" />}>
                <div className="p-5">
                  <p className="text-slate-400 text-sm mb-4 print:text-slate-600">Each firm reviewed the others' hypotheses to surface blind spots and tensions.</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(data.cross_review).map(([personaId, review]: [string, any]) => (
                      <div key={personaId} className="bg-slate-900 border border-slate-700 rounded-lg p-4 print:bg-slate-50 print:border-slate-200">
                        <div className="flex items-center gap-2 mb-3">
                          <div className="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center print:bg-purple-100">
                            <Users className="w-3.5 h-3.5 text-slate-400 print:text-purple-600" />
                          </div>
                          <div>
                            <h4 className="font-bold text-slate-200 text-sm print:text-slate-900">
                              {FIRM_DISPLAY_NAMES[personaId.toLowerCase()] ?? (personaId.charAt(0).toUpperCase() + personaId.slice(1).replace(/_/g, ' '))}
                            </h4>
                            <p className="text-xs text-slate-500">Council Member</p>
                          </div>
                        </div>
                        {review.critiques?.length > 0 && (
                          <div className="mb-2">
                            <h5 className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-1 print:text-red-600">Critiques</h5>
                            <ul className="space-y-1">
                              {review.critiques.map((c: any, i: number) => (
                                <li key={i} className="text-xs text-slate-400 bg-slate-800/60 p-2 rounded border border-slate-700 print:text-slate-700 print:bg-white print:border-slate-100">
                                  <span className="font-medium text-slate-200 block mb-0.5 print:text-slate-900">Re: {c.target}</span>
                                  "{c.concern}"
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {review.endorsements?.length > 0 && (
                          <div>
                            <h5 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1 print:text-emerald-600">Endorsements</h5>
                            <ul className="space-y-1">
                              {review.endorsements.map((e: any, i: number) => (
                                <li key={i} className="text-xs text-slate-400 bg-slate-800/60 p-2 rounded border border-slate-700 print:text-slate-700 print:bg-white print:border-slate-100">
                                  <span className="font-medium text-slate-200 block mb-0.5 print:text-slate-900">Re: {e.target}</span>
                                  "{e.reason}"
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </AccordionSection>
            )}

            {/* [L] Risk & Considerations divider */}
            <div className="print:hidden flex items-center gap-3 mt-6 mb-2">
              <div className="h-px flex-1 bg-slate-800" />
              <button
                onClick={() => {
                  const ids = ['risks', 'blindspots', 'inaction']
                  const allOpen = ids.every(id => openSections.has(id))
                  setOpenSections(prev => {
                    const next = new Set(prev)
                    ids.forEach(id => allOpen ? next.delete(id) : next.add(id))
                    return next
                  })
                }}
                className="text-[10px] font-mono uppercase tracking-widest text-slate-500 hover:text-slate-300 flex items-center gap-1.5 transition-colors"
              >
                <ChevronDown className="w-3 h-3" /> Risk &amp; Considerations
              </button>
              <div className="h-px flex-1 bg-slate-800" />
            </div>

            {/* [M] Risk Analysis */}
            {data.risks?.length > 0 && (
              <AccordionSection id="risks" title="Risk Analysis & Mitigation" openSections={openSections} onToggle={toggleSection}
                icon={<AlertTriangle className="w-4 h-4 text-slate-400" />}>
                <div className="p-5">
                  <div className="overflow-hidden rounded-lg border border-slate-700 print:border-slate-200">
                    <table className="w-full text-xs">
                      <thead className="bg-slate-800 print:bg-slate-100">
                        <tr>
                          {['Risk', 'Likelihood', 'Impact', 'Mitigation'].map(h => (
                            <th key={h} className="text-left p-3 font-semibold text-slate-300 print:text-slate-900">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.risks.map((risk: any, i: number) => (
                          <tr key={i} className="border-t border-slate-700 print:border-slate-200">
                            <td className="p-3 text-slate-400 print:text-slate-700">{risk.risk}</td>
                            <td className="p-3">
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${risk.likelihood === 'High' ? 'bg-red-900/40 text-red-400 print:bg-red-100 print:text-red-700' : risk.likelihood === 'Medium' ? 'bg-amber-900/40 text-amber-400 print:bg-amber-100 print:text-amber-700' : 'bg-emerald-900/40 text-emerald-400 print:bg-emerald-100 print:text-emerald-700'}`}>{risk.likelihood}</span>
                            </td>
                            <td className="p-3">
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${risk.impact === 'High' ? 'bg-red-900/40 text-red-400 print:bg-red-100 print:text-red-700' : risk.impact === 'Medium' ? 'bg-amber-900/40 text-amber-400 print:bg-amber-100 print:text-amber-700' : 'bg-emerald-900/40 text-emerald-400 print:bg-emerald-100 print:text-emerald-700'}`}>{risk.impact}</span>
                            </td>
                            <td className="p-3 text-slate-400 print:text-slate-700">{risk.mitigation}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </AccordionSection>
            )}

            {/* [N] Blind Spots & Tensions */}
            {((data.blind_spots?.length > 0) || (data.unresolved_tensions?.length > 0)) && (
              <AccordionSection id="blindspots" title="Considerations & Blind Spots" openSections={openSections} onToggle={toggleSection}
                icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}>
                <div className="p-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {data.blind_spots?.length > 0 && (
                      <div className="bg-slate-900 border border-slate-700 p-4 rounded-lg print:bg-amber-50 print:border-amber-200">
                        <h3 className="font-semibold text-amber-400 mb-2 text-sm print:text-amber-900">Potential Blind Spots</h3>
                        <ul className="space-y-1.5">
                          {data.blind_spots.map((bs: string, i: number) => (
                            <li key={i} className="text-slate-400 text-xs flex items-start gap-1.5 print:text-amber-800">
                              <AlertTriangle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />{bs}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {data.unresolved_tensions?.length > 0 && (
                      <div className="bg-slate-900 border border-slate-700 p-4 rounded-lg print:bg-purple-50 print:border-purple-200">
                        <h3 className="font-semibold text-slate-200 mb-2 text-sm print:text-purple-900">Unresolved Tensions</h3>
                        <ul className="space-y-2">
                          {data.unresolved_tensions.map((t: any, i: number) => (
                            <li key={i} className="text-slate-400 text-xs print:text-purple-800">
                              <p className="font-medium text-slate-300 print:text-purple-800">{t.tension || t}</p>
                              {t.requires && <p className="text-slate-500 mt-0.5 print:text-purple-600">Requires: {t.requires}</p>}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              </AccordionSection>
            )}

            {/* [O] Cost of Inaction — shown pre-approval when KPI data is available */}
            {approveState !== 'approved' && data.kpiData?.current_value != null && (() => {
              const kd = data.kpiData
              const slope = kd.comparison_value != null
                ? kd.current_value - kd.comparison_value
                : 0
              const projected30d = kd.current_value + slope * 1
              const projected90d = kd.current_value + slope * 3
              const trendDir: 'deteriorating' | 'stable' | 'recovering' =
                slope < -0.001 ? 'deteriorating' : slope > 0.001 ? 'recovering' : 'stable'
              return (
                <AccordionSection id="inaction" title="Cost of Inaction" openSections={openSections} onToggle={toggleSection}
                  icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}>
                  <div className="p-5">
                    <CostOfInactionBanner
                      kpiName={kd.kpi_name}
                      currentValue={kd.current_value}
                      projected30d={projected30d}
                      projected90d={projected90d}
                      trendDirection={trendDir}
                      trendConfidence="LOW"
                      kpiUnit={kd.unit}
                    />
                  </div>
                </AccordionSection>
              )
            })()}

            {/* Print-only: Appendix — Blind Spots & Unresolved Tensions */}
            {((data.blind_spots?.length > 0) || (data.unresolved_tensions?.length > 0)) && (
              <div className="hidden print:block mb-6">
                <div className="text-[9px] text-slate-500 uppercase tracking-wider font-mono mb-2 border-b border-slate-200 pb-1">
                  Appendix: Blind Spots &amp; Unresolved Tensions
                </div>
                {data.blind_spots?.length > 0 && (
                  <div className="mb-3">
                    <p className="text-[10px] font-semibold text-slate-600 uppercase mb-1">Potential Blind Spots</p>
                    <ul className="space-y-1">
                      {data.blind_spots.map((bs: string, i: number) => (
                        <li key={i} className="text-xs text-slate-700">• {bs}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {data.unresolved_tensions?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-semibold text-slate-600 uppercase mb-1">Unresolved Tensions</p>
                    <ul className="space-y-1">
                      {data.unresolved_tensions.map((t: any, i: number) => (
                        <li key={i} className="text-xs text-slate-700">
                          <span className="font-medium">{t.tension || t}</span>
                          {t.requires && <span className="text-slate-500"> — Requires: {t.requires}</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Footer */}
            <footer className="py-6 text-center text-xs text-slate-500 print:block print:border-t print:border-slate-300 print:pt-4 print:text-slate-600">
              <p>This briefing was generated by Decision Studio using AI-assisted analysis.</p>
              <p className="mt-1 print:text-slate-500">
                Provided as decision support. Human judgment is required for final decisions.
              </p>
            </footer>
          </div>
        </div>

        {/* ── Right: Decision Workspace ── */}
        <div className="w-80 flex-shrink-0 border-l border-slate-800 print:hidden">
          <DecisionChat
            data={data}
            situationId={situationId}
            principalId={principalId}
            approveState={approveState}
            onApprove={handleApprove}
          />
        </div>
      </div>
    </div>
  )
}

export default ExecutiveBriefing
