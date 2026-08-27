import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link, useSearchParams, useNavigate } from 'react-router-dom'
import { motion, useReducedMotion } from 'framer-motion'
import html2pdf from 'html2pdf.js'
import {
  ArrowLeft, ArrowRight, Download, Printer, AlertTriangle, CheckCircle, ChevronRight,
  Users, Target, Zap, TrendingUp, ShieldCheck, Loader2, CheckCircle2,
  ChevronDown, Send, MessageSquare, FileText
} from 'lucide-react'
import { approveSolution, askBriefingQuestion, BriefingQAResponse, storeBriefingSnapshot, getBriefingSnapshot, getVASolution, listPrincipals } from '../api/client'
import { CostOfInactionBanner } from '../components/CostOfInactionBanner'
import { projectKpiTrend, condenseTimeToValue, truncateProse, endsSentence, axisDiscrimination } from '../utils/briefingUtils'
import { ValueAssurancePanel } from '../components/ValueAssurancePanel'
import { AttributionBreakdown } from '../components/AttributionBreakdown'
import { BrandLogo } from '../components/BrandLogo'
import { DecisionAskBlock } from '../components/briefing/DecisionAskBlock'
import { ImmediateActionsChecklist } from '../components/briefing/ImmediateActionsChecklist'
import { AssumptionsPanel } from '../components/briefing/AssumptionsPanel'
import { OptionDetailDrawer } from '../components/briefing/OptionDetailDrawer'
import { ContradictionBanner } from '../components/briefing/ContradictionBanner'
import { councilCompositionLabel } from '../utils/personaLabels'
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
  const panelId = `accordion-panel-${id}`
  const headerId = `accordion-header-${id}`
  /* The standard disclosure pattern: a heading whose only child is the toggle
     button. Ten sections inherit this, and until 2026-08-27 none of them
     announced anything — no aria-expanded, no aria-controls, and the title was
     a <span>, so a screen-reader user toggling a section got no confirmation
     that anything happened and the page exposed no outline to navigate by. */
  return (
    <div id={`accordion-${id}`} className="mb-3 rounded-xl overflow-hidden border border-slate-800 print:border-0 print:mb-8">
      <h2 className="print:hidden">
        <button
          id={headerId}
          onClick={() => onToggle(id)}
          aria-expanded={isOpen}
          aria-controls={panelId}
          className="w-full flex items-center justify-between px-5 py-3 bg-slate-900 text-white hover:bg-slate-800 transition-colors border-b border-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:ring-inset"
        >
          <span className="flex items-center gap-2">
            {icon}
            <span className="font-semibold text-sm">{title}</span>
            {badge && <span className="px-2 py-0.5 text-[10px] bg-indigo-600 text-white rounded-full">{badge}</span>}
          </span>
          <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>
      </h2>
      <div
        id={panelId}
        role="region"
        aria-labelledby={headerId}
        className={`accordion-content ${isOpen ? 'block' : 'hidden'} print:block bg-slate-950 print:bg-white`}
      >
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

  // Two guards, both needed once the workspace stacks BELOW the briefing on
  // narrow screens instead of sitting in its own independently-scrolling rail.
  //
  //  - Empty check: this used to fire on first render with no conversation to
  //    scroll to. Inside the old 320px rail that was a harmless no-op; with the
  //    document itself scrolling on mobile it dragged the reader to y=8504 of
  //    9786, so the briefing opened on its own footer. Caught by rendering at
  //    390px — no type or lint check sees this.
  //    Guard on the message count, NOT a didMount ref: StrictMode runs effects
  //    twice against the same refs in dev, so a mount flag is already spent by
  //    the second pass and the scroll fires anyway.
  //  - `block: 'nearest'`: scrolls the chat's own container only, and does
  //    nothing when the anchor is already visible, so answering a question
  //    never jerks the whole page.
  useEffect(() => {
    if (messages.length === 0) return
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
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
      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-3" aria-live="polite" aria-atomic="false">
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
            <div className="bg-slate-800 rounded-lg px-3 py-2" role="status">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" aria-hidden="true" />
              <span className="sr-only">Answering your question…</span>
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
              aria-label="Ask a question about this briefing"
              disabled={loading}
              className="flex-1 px-3 py-1.5 text-xs bg-slate-800 text-white border border-slate-600 rounded-lg focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder-slate-500 disabled:opacity-50"
            />
            <button
              onClick={() => sendQuestion(input)}
              disabled={!input.trim() || loading}
              aria-label="Send question"
              className="p-1.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-40 transition-colors"
            >
              <Send className="w-4 h-4" aria-hidden="true" />
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
          ) : data?.analysis_degraded ? (
            // The red banner further up the page explains WHY; this is where the
            // reader would otherwise act on it anyway. A warning that can be
            // scrolled past while the button beneath it still works is not a
            // guard — this is the discoverable half, handleApprove's own check
            // is the one that cannot be bypassed.
            <div className="flex items-start gap-2 px-3 py-2 bg-red-950/40 border border-red-700/60 rounded-lg">
              <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-[10px] text-red-300 leading-snug">
                Approval is disabled — these options were not produced by the analysis.
                Re-run once the underlying problem is resolved.
              </p>
            </div>
          ) : (
            <button
              onClick={() => onApprove(selectedOption)}
              disabled={approveState === 'approving' || !selectedOption}
              aria-live="polite"
              className="w-full py-2 bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-300"
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

// The "supporting analysis" sections that move together as one group behind
// the single "Show/Hide the analysis" toggle.
//
// Was seven ids. Now three: market/stage1/crossreview/moderator moved off this
// page entirely (see the note where they were rendered). What remains is what
// actually bears on the DECISION — the situation, the risks, and the blind
// spots — rather than the record of how the council argued.
const ANALYSIS_SECTION_IDS = ['situation', 'risks', 'blindspots']

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
  // Index into data.options; null = closed. Held as an index rather than the
  // option object so a re-fetch cannot leave a stale copy open.
  const [drawerIdx, setDrawerIdx] = useState<number | null>(null)
  const [showAllRisks, setShowAllRisks] = useState(false)
  const [openSections, setOpenSections] = useState<Set<string>>(
    new Set(['options', 'recommendation', 'roadmap'])
  )
  // Honours the OS "reduce motion" setting. Nothing in this codebase consulted
  // it before 2026-08-27 — grep for prefers-reduced-motion returned zero files
  // across the whole src tree while a drawer slid a full viewport width.
  const reduceMotion = useReducedMotion()

  // Stage 9 role-default effect lives further down, right after principalId
  // is resolved from the briefing payload — see there.
  const roleDefaultApplied = useRef(false)

  const toggleSection = (id: string) => {
    setOpenSections(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const analysisAllOpen = ANALYSIS_SECTION_IDS.every(id => openSections.has(id))

  // Open every analysis section at once. Shared by the toolbar toggle and the
  // divider toggle, which previously carried byte-identical copies of this
  // logic in two places.
  const setAllAnalysisSections = (open: boolean) => {
    setOpenSections(prev => {
      const next = new Set(prev)
      ANALYSIS_SECTION_IDS.forEach(id => open ? next.add(id) : next.delete(id))
      return next
    })
  }

  // ContradictionBanner's "see the full analysis" link (move #1) — force-open
  // (not toggle: clicking twice must not re-close it) then scroll, since the
  // section's content is display:none while collapsed and a plain href anchor
  // would scroll to an invisible target.
  //
  // Scrolls to #accordion-blindspots, NOT the group divider. Stage 9 retargeted
  // this at the divider when blindspots was folded into a seven-section group,
  // but the link's own label says "in Blind Spots & Tensions" — so the reader
  // clicked it and landed seven sections short of the thing it named. This is
  // the only path from the page's headline finding to its evidence; it has to
  // land on the evidence.
  const openBlindSpotsAndScroll = () => {
    setAllAnalysisSections(true)
    requestAnimationFrame(() => {
      document.getElementById('accordion-blindspots')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
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
      /* Risks 4+ are collapsed on screen. html2pdf rasterises the live DOM and
         sees no print media, so without this the export inherits the collapse
         and silently ships a shorter risk list than the briefing on screen. */
      .pdf-export-mode .risk-overflow-row { display: table-row !important; }
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
    // REAL guard, not just the banner. `analysis_degraded` runs (llm_yielded_no_options
    // in particular) return status="completed" with the fabricated
    // "Tighten spend controls"/"Optimize pricing" stub still sitting in `options` —
    // by design, so Stage 1 hypotheses survive a truncated synthesis rather than
    // being discarded. The red banner at the top of this page said so, but nothing
    // stopped the click: a user could approve the stub into real Value Assurance
    // tracking with nothing to distinguish it from a genuine recommendation
    // afterward. This function is the one place that actually calls
    // approveSolution(), so it is the one place a refusal cannot be bypassed —
    // the disabled button below is the discoverable half, this is the load-bearing
    // half. Checked here rather than trusting the UI state alone.
    if (briefing?.analysis_degraded) {
      console.error(
        '[ExecutiveBriefing] Blocked approve on a degraded run — options were not produced by the analysis.',
        { degraded_reason: briefing?.degraded_reason }
      )
      return
    }
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

  const canonicalTitle = briefing?.kpiData?.kpi_name
    ? `${briefing.kpiData.kpi_name} — Executive Briefing`
    : briefing?.title || 'Executive Briefing'

  useEffect(() => {
    document.title = canonicalTitle
    return () => { document.title = 'Decision Studio' }
  }, [canonicalTitle])

  // Stage 9 (Decision Framer/Decision Maker split, 2026-08-26) — the single
  // "Show the analysis" toggle (situation/market/stage1/crossreview/moderator/
  // risks/blindspots, consolidated below) defaults OPEN for a framer, closed
  // for a decision_maker. Applied once, the moment the role is known — a
  // ref guard so it never fights a reader's own manual toggle afterward.
  // This page has no other route into a Principal object (principalId is
  // only ever a bare string here), so it fetches the list itself rather
  // than threading a new prop through every caller.
  useEffect(() => {
    if (roleDefaultApplied.current || !principalId) return
    const clientId = localStorage.getItem('a9_active_client_id') || undefined
    listPrincipals(clientId)
      .then((rows: any[]) => {
        if (roleDefaultApplied.current) return
        const match = rows.find((p) => p.id === principalId)
        if (match?.workflow_role === 'framer') {
          setOpenSections((prev) => {
            const next = new Set(prev)
            ANALYSIS_SECTION_IDS.forEach((id) => next.add(id))
            return next
          })
        }
        roleDefaultApplied.current = true
      })
      .catch(() => { roleDefaultApplied.current = true })
  }, [principalId])

  if (loading) {
    return (
      <div className="h-screen bg-slate-950 flex items-center justify-center" role="status">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400" aria-hidden="true" />
        <span className="sr-only">Loading briefing…</span>
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

  // Council persona ORDER, still needed by the audit footer's
  // councilCompositionLabel(). The per-persona colour palette and conviction
  // badge styles that used to sit here went with the Stage 1 / Stage 2
  // accordions — that five-hue palette (indigo/teal/amber/sky/violet, each with
  // a light-mode badge) was also the largest single source of non-semantic
  // colour on a page whose brand rule is that colour is scarce.
  const personaOrder: string[] = Object.keys(data.stage_1_hypotheses || {})

  return (
    <div className="min-h-screen lg:h-screen flex flex-col bg-slate-950 lg:overflow-hidden print:h-auto print:overflow-visible print:text-black print:bg-white">
      {/* Nav */}
      {/* The title span that sat in here was the ONLY place this page named
          itself on screen — at text-sm, truncated, in the chrome. The document
          now opens with a real <h1>, so repeating it here is duplication; it
          stays from `lg` up purely as a scroll anchor and is dropped below that
          where the space is needed. */}
      <nav className="flex-shrink-0 bg-slate-900 border-b border-slate-800 py-3 px-4 sm:px-6 flex flex-wrap gap-y-2 justify-between items-center print:hidden z-50">
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors text-sm">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Link>
          <BrandLogo size={24} />
        </div>
        <div className="flex items-center gap-2">
          <span className="hidden lg:block text-sm font-semibold text-white truncate max-w-xs mr-3">{canonicalTitle}</span>
          <button
            onClick={() => setAllAnalysisSections(!analysisAllOpen)}
            className="px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
          >
            {analysisAllOpen ? 'Hide the analysis' : 'Show the analysis'}
          </button>
          {/* Print and Export both produce a document and were competing with
              View Report for the same intent with no hierarchy between them.
              Export (a real file) is the one that survives at narrow widths;
              Print stays on wider screens for hardcopy. */}
          <button
            onClick={() => window.print()}
            className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
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
            <span className="hidden sm:inline">Export</span>
          </button>
          <button
            onClick={() => navigate(`/report/${situationId}`)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg transition-colors"
            title="Open narrative-arc white-paper report"
          >
            <FileText className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">View </span>Report
          </button>
        </div>
      </nav>

      {/* Two-panel body */}
      <div className="flex-1 min-h-0 flex flex-col lg:flex-row lg:overflow-hidden print:overflow-visible print:block">
        {/* ── Left: Briefing content ── */}
        <div className="briefing-content flex-1 lg:overflow-y-auto bg-slate-950 p-4 sm:p-6 print:p-0 print:bg-white print:overflow-visible">
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

            {/* ── Narrative accuracy caveat ─────────────────────────────────────
                Renders ABOVE the flash briefing and on print, because it is a
                caveat ON that prose and must travel with it.

                Deliberately does NOT correct the text. A silent auto-correction
                would hide that the generator produced a figure contradicting the
                data — the reader is entitled to know the narrative and the
                measurements disagree, and which one is measured. Suppressing the
                sentence outright would be worse still: it would leave a gap with
                no explanation. */}
            {/* Analysis did not actually run. RED, not amber, and above the
                narrative warning: this is not "treat the prose with caution", it is
                "these are not recommendations at all".

                The generic stub ("Tighten spend controls" / "Optimize pricing") is
                indistinguishable from real model output to a reader, and its very
                blandness is what a sceptic expects a weak AI tool to produce — so it
                discredits the product precisely when it is not working. Observed live
                2026-08-09 with an exhausted API quota: state=completed, error=None,
                two plausible options, no signal anywhere the reader could see. */}
            {(data as any).analysis_degraded && (
              <div className="mb-6 rounded-lg border-2 border-red-500/60 bg-red-950/30 p-4 print:bg-red-50 print:border-red-400">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5 print:text-red-700" />
                  <div>
                    <p className="text-sm font-bold text-red-300 mb-1 print:text-red-900">
                      These options were not produced by the analysis
                    </p>
                    <p className="text-xs text-red-200/90 print:text-red-800">
                      {(data as any).degraded_reason === 'llm_unavailable'
                        ? 'The language model was unavailable for this run — an outage, a credentials problem, or an exhausted quota. No analysis took place.'
                        : 'The model responded but its output could not be read as a set of options, most often because the response was cut short.'}
                      {' '}The options shown below are generic placeholders. Do not act on them, and do not
                      read the absence of a specific recommendation as a finding. Re-run once the
                      underlying problem is resolved.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {Array.isArray((data as any).narrative_warnings) && (data as any).narrative_warnings.length > 0 && (
              <div className="mb-6 rounded-lg border border-amber-500/40 bg-amber-950/20 p-4 print:bg-amber-50 print:border-amber-300">
                <div className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5 print:text-amber-700" />
                  <div>
                    <p className="text-sm font-semibold text-amber-300 mb-1 print:text-amber-900">
                      Narrative figures disagree with the measured data
                    </p>
                    <p className="text-xs text-amber-200/80 mb-2 print:text-amber-800">
                      The written summary below asserts {(data as any).narrative_warnings.length === 1 ? 'a figure that does' : 'figures that do'} not
                      match what the pipeline measured. The measured values are authoritative; treat the prose with caution.
                    </p>
                    <ul className="space-y-1">
                      {(data as any).narrative_warnings.map((w: any, i: number) => (
                        <li key={i} className="text-xs text-amber-200/70 print:text-amber-800">
                          <span className="font-mono text-[10px] uppercase tracking-wider text-amber-400/80 print:text-amber-700">
                            {String(w?.kind || 'mismatch').replace(/_/g, ' ')}
                          </span>
                          {' — '}{w?.detail}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* ── Flash Briefing (print-only) ───────────────────────────────── */}
            {(() => {
              const scqa = data.executiveSummary || data.situation?.currentState || ''
              const rec = data.recommendation?.title || data.options?.find((o: any) => o.recommended)?.title || ''
              const rationale = data.recommendation?.rationale || data.recommendation_rationale || ''
              const topDrivers: string[] = data.situation?.topDrivers?.slice(0, 2).map((d: any) => d.label || d.segment || '') ?? []
              const roi = data.options?.find((o: any) => o.recommended)?.roi || ''

              const sentences: string[] = []
              // Boundary-aware: raw slice() shipped "...also underperform…" and
              // "...because it…." to a live print view.
              // 200 chars clipped this pipeline's prose mid-clause, because it is
              // written as long em-dash-joined sentences. Wider budget + the
              // clause-boundary fallback lets the opening thought finish.
              if (scqa) sentences.push(truncateProse(scqa, 320))
              if (topDrivers.length) sentences.push(`Primary drivers: ${topDrivers.join(' and ')}.`)
              if (rec) {
                const why = rationale ? `: ${truncateProse(rationale, 180)}` : ''
                const line = `The council recommends ${rec}${why}`
                // Only add a period when the text does not already end one —
                // otherwise a truncated clause renders as "because it…."
                sentences.push(endsSentence(line) ? line : `${line}.`)
              }
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
                  Problem Statement &amp; Largest Variance Contributors
                </div>
                <p className="text-xs font-semibold text-slate-800 mb-3 border-l-2 border-slate-400 pl-3">
                  Key Question: {data.situation.keyQuestion}
                </p>
                {data.situation?.rootCauses?.length > 0 && (
                  <ol className="space-y-2">
                    {data.situation.rootCauses.map((cause: any, i: number) => (
                      <li key={i} className="text-xs text-slate-700">
                        <span className="font-semibold">{i + 1}. {cause.driver}</span>
                        {cause.dimension && (
                          <span className="text-slate-500 ml-1">({cause.dimension})</span>
                        )}
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

            {/* ── Above the fold: situation, the ask, the path, the impact ─────
                Phase 13 Cat 3. The 2-minute read. Everything below this — the
                options table, the council stages, the risk section — is
                supporting detail for a reader who wants it.

                Screen only. The print path already opens with its own Flash
                Briefing and Situation & Context blocks above; rendering this as
                well would put the same three facts on the page twice, which is
                the duplicate-recommendation defect Cat 1 fixed once already. */}
            {/* ── THE FOLD ──────────────────────────────────────────────────
                Order here is load-bearing, and it is the fix for the defect
                the Aug 2026 design critique scored hardest (19/40).

                The page used to open: situation bullets → decision ask →
                recommended path → owner → Cost of Inaction → "Recommendation
                at a glance" → and only THEN the contradiction, one full scroll
                below the fold. So it asserted an answer twice before admitting
                the question was still open — the exact inverse of BLUF, and it
                defeated move #1 of executive_briefing_redesign.md ("the
                contradiction becomes the headline") while technically shipping
                the component.

                Now: open question → the decision it forces → why now →
                the options. Four beats, each saying one thing once.
                Do not reintroduce a block above the contradiction. */}
            {data.unresolved_tensions?.[0] ? (
              <ContradictionBanner
                tension={data.unresolved_tensions[0]}
                onViewDetail={openBlindSpotsAndScroll}
                variant="headline"
              />
            ) : (
              /* No tension in this run — the page still needs exactly one <h1>,
                 both for the document outline and because assistive tech had
                 nothing to anchor on here before. */
              <h1 className="text-xl sm:text-2xl font-semibold text-white leading-snug tracking-tight mb-6 print:text-slate-900">
                {canonicalTitle}
              </h1>
            )}

            {/* Problem vs. opportunity framing — added 2026-08-26, found live
                ("no problem or opportunity situational statement?"). Kept
                OUTSIDE DecisionAskBlock rather than added as a prop to it:
                that component's own M1 invariant comment says it "is
                IDENTICAL for every principal" and stays untouched; this is a
                framing label about the SITUATION, not a per-principal
                variation of the ask. Only rendered for opportunity — a
                problem situation is the majority case and already reads
                correctly with no badge at all. */}
            {data.cardType === 'opportunity' && (
              <div className="print:hidden mb-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-900/30 border border-emerald-700/40 text-[11px] font-semibold uppercase tracking-wider text-emerald-300">
                <TrendingUp className="w-3 h-3" /> Opportunity — upside available, not a problem to fix
              </div>
            )}

            <div className="print:hidden">
              {(() => {
                const recOption = data.options?.find((o: any) => o.recommended) ?? data.options?.[0]
                // At most three, and the problem statement leads. Variance
                // contributors carry their dimension label for the same reason
                // the detail section does — "National Auto Parts Chain A" without
                // it reads as a division.
                const bullets: string[] = []
                if (data.situation?.problem) bullets.push(String(data.situation.problem))
                ;(data.situation?.rootCauses ?? []).slice(0, 2).forEach((c: any) => {
                  const dim = c?.dimension ? ` (${c.dimension})` : ''
                  const impact = c?.impact ? ` — ${c.impact}` : ''
                  if (c?.driver) bullets.push(`${c.driver}${dim}${impact}`)
                })
                return (
                  <DecisionAskBlock
                    situationBullets={bullets.slice(0, 3)}
                    decisionAsk={data.decision_ask ?? null}
                    recommendedPath={recOption?.title ?? null}
                    impactRange={recOption?.roi ?? null}
                    fallbackOwner={data.recommendation?.decisionOwner}
                    fallbackDeadline={data.recommendation?.deadline}
                  />
                )
              })()}
            </div>

            {/* Cost of Inaction — the "why now" behind the decision above.
                Was gated on `approveState !== 'approved'`, which deleted the
                justification from the page at the exact moment it started
                mattering: getBriefingSnapshot sets approved on load, so a
                Portfolio replay of this briefing could NEVER show the cost of
                waiting that drove the decision. The most persuasive artifact
                in the record was the one thing the record dropped. It now
                renders in both states. */}
            {data.kpiData?.current_value != null && (() => {
              const kd = data.kpiData
              // Projection + trend live in briefingUtils.projectKpiTrend so the
              // number an executive reads first is unit-testable rather than
              // buried in JSX. Two sign traps are handled there — see its
              // docstring; both were live in a real briefing.
              const { projected30d, projected90d, trend: trendDir } =
                projectKpiTrend(kd.current_value, kd.percent_change, kd.comparison_value)
              const confidenceLevelMap: Record<string, 'HIGH' | 'MODERATE' | 'LOW'> = {
                'Low': 'LOW', 'Medium': 'MODERATE', 'High': 'HIGH', 'Very High': 'HIGH',
              }
              return (
                <div className="mb-4">
                  <CostOfInactionBanner
                    kpiName={kd.kpi_name}
                    currentValue={kd.current_value}
                    projected30d={projected30d}
                    projected90d={projected90d}
                    trendDirection={trendDir}
                    trendConfidence={confidenceLevelMap[data.metrics?.confidence] || 'LOW'}
                    kpiUnit={kd.unit}
                  />
                </div>
              )
            })()}

            {/* The "Recommendation at a glance" hero card stood here and was
                DELETED in the Aug 2026 composition pass. It was the third
                statement of one recommendation: DecisionAskBlock already gives
                the recommended path and impact range above it, and every
                option card below carries the same four metrics per option.

                It was also the source of the page's colour problem. Its four
                tiles rendered emerald / amber / blue / white — and "Investment"
                was blue for no semantic reason at all, purely because it was
                the fourth tile and the other three hues were taken. The brand
                rule is that colour is scarce and strictly semantic; a
                four-metric row is exactly where that rule quietly dies.

                The approved badge it carried is not lost: the approval
                confirmation card below and the workspace rail both already
                report that state. Three simultaneous confirmations was itself
                a finding. Do not restore this card. */}

            {/* [D] Strategic Options */}
            <AccordionSection id="options" title="Strategic Options" openSections={openSections} onToggle={toggleSection}
              badge={`${data.options?.length || 0} options`}
              icon={<Target className="w-4 h-4 text-slate-400" />}>
              <div className="p-5">
                {/* Was hardcoded to "Three strategic pathways" regardless of how
                    many the run produced. */}
                <p className="text-slate-400 text-sm mb-4 print:text-slate-600">
                  {data.options?.length || 0} strategic pathway{data.options?.length === 1 ? '' : 's'} evaluated against
                  financial impact, complexity, risk, and priority alignment
                  {data.statusQuo ? ', measured against doing nothing (Option 0)' : ''}.
                </p>
                {/* Option 0 — mobile only.
                    The comparison table below is hidden under `lg` (see there).
                    Every proposed option survives that, because the option cards
                    further down carry the same per-option metrics. The status quo
                    does NOT: it exists only as the table's leading column. So it
                    gets a compact card here rather than silently vanishing on a
                    phone — it is the reference the other options are measured
                    against, and a comparison that quietly drops its baseline is
                    worse than one that scrolls. */}
                {data.statusQuo && (
                  <div className="lg:hidden mb-4 rounded-lg border border-slate-700 bg-slate-800/40 p-4">
                    <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Baseline · Option 0</p>
                    <p className="text-sm font-semibold text-white mb-2">{data.statusQuo.title}</p>
                    <dl className="grid grid-cols-2 gap-x-3 gap-y-2">
                      {[
                        { k: 'Est. ROI', v: data.statusQuo.roi },
                        { k: 'Timeline', v: data.statusQuo.timeline },
                        { k: 'Investment', v: data.statusQuo.investment },
                        { k: 'Risk', v: data.statusQuo.riskLevel },
                      ].filter(x => x.v).map(({ k, v }) => (
                        <div key={k} className="min-w-0">
                          <dt className="text-[10px] text-slate-400 uppercase">{k}</dt>
                          <dd className="text-xs text-slate-200 break-words">{v}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                )}

                {/* Comparison table — desktop and print only.
                    Its columns declare 120 + 150 + 160-per-option of minimum
                    width, so it was already clipping Option C mid-word at 1440px
                    and needed horizontal scrolling on the one exhibit most likely
                    to be shown to a board. Below `lg` the option cards below carry
                    the identical per-option data, so this is hidden rather than
                    duplicated into a stacked variant. */}
                <div className="hidden lg:block overflow-x-auto rounded-lg border border-slate-700 mb-6 print:!block print:border-slate-200">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-800 text-slate-300 font-bold uppercase print:bg-slate-100 print:text-slate-900">
                      <tr>
                        <th className="p-3 border-b border-slate-700 min-w-[120px] print:border-slate-200">Criteria</th>
                        {/* Option 0 leads, on the left, because it is the reference
                            the other columns are measured against — not a fourth
                            candidate appended after them. */}
                        {data.statusQuo && (
                          <th data-testid="status-quo-column" className="p-3 border-b border-r-2 border-slate-700 border-r-slate-600 min-w-[150px] bg-slate-800/40 print:border-slate-200 print:bg-slate-50">
                            <div className="text-[9px] text-slate-400 mb-0.5 print:text-slate-500">BASELINE</div>
                            Option 0
                          </th>
                        )}
                        {data.options?.map((opt: any, i: number) => {
                          // Move #2 (executive_briefing_redesign.md §4) — a
                          // dominated option is LABELLED, not hidden. Found
                          // live 2026-08-24: two options modelled at an
                          // identical recovery range while one was strictly
                          // worse on speed and reversibility, invisible as
                          // table rows. dominated_by is another option's id;
                          // resolve it to that option's display letter.
                          const dominatorIdx = opt.dominated_by
                            ? data.options.findIndex((o: any) => o.id === opt.dominated_by)
                            : -1;
                          return (
                            <th key={i} className={`p-3 border-b border-slate-700 min-w-[160px] print:border-slate-200 ${opt.recommended ? 'bg-emerald-900/30 print:bg-emerald-50 print:text-emerald-800' : ''}`}>
                              {opt.recommended && <div className="text-[9px] text-emerald-400 mb-0.5 flex items-center gap-1 print:text-emerald-600"><CheckCircle className="w-2.5 h-2.5" /> RECOMMENDED</div>}
                              Option {String.fromCharCode(65 + i)}
                              {dominatorIdx >= 0 && (
                                <div className="text-[9px] font-normal text-amber-500/90 mt-0.5 normal-case print:text-amber-700"
                                     title="Matches or is worse than another option on modelled impact, cost, and risk.">
                                  dominated by Option {String.fromCharCode(65 + dominatorIdx)}
                                </div>
                              )}
                            </th>
                          );
                        })}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 print:divide-slate-100">
                      {[
                        { label: 'Strategy', key: 'title', cls: 'font-medium text-slate-200 print:text-slate-900' },
                        { label: 'Est. ROI', key: 'roi', cls: 'font-bold text-emerald-400 print:text-emerald-600' },
                        { label: 'Investment', key: 'investment', cls: 'text-slate-400 print:text-slate-600' },
                        { label: 'Timeline', key: 'timeline', cls: 'text-slate-400 print:text-slate-600' },
                        // Reversibility varies (high/medium/low) and was already on the
                        // payload but absent from this table — so the exhibit showed
                        // three criteria that separated nothing while omitting one that did.
                        { label: 'Reversibility', key: 'reversibility', cls: 'text-slate-400 print:text-slate-600 capitalize' },
                      ].map(({ label, key, cls }) => {
                        // Say plainly when a criterion cannot inform the choice. Laying
                        // out identical values as though they were a comparison is what
                        // made this table misleading — two options carried the SAME Est.
                        // ROI and all three the same effort and risk.
                        const shown = (data.options ?? []).map((o: any) => key === 'roi' ? formatROI(o[key]) : o[key])
                        // Discrimination is computed over the PROPOSED options only.
                        // Option 0 is a reference, and its values differ from all of
                        // them almost by construction ($0 investment, a negative
                        // return) — folding it in would turn "all three proposals
                        // score the same here" into a cheerful "3 of 4 distinct" and
                        // suppress the exact finding this annotation exists to make.
                        const disc = axisDiscrimination(shown)
                        const sqValue = data.statusQuo ? (data.statusQuo as any)[key] : null
                        return (
                        <tr key={key}>
                          <td className="p-3 font-semibold text-slate-400 bg-slate-900/50 print:text-slate-700 print:bg-slate-50">
                            {label}
                            {disc.uniform && (
                              <div className="text-[9px] font-normal text-amber-500/90 mt-0.5 print:text-amber-700"
                                   title="Every proposed option scores the same here, so this row cannot separate them.">
                                same for all — does not inform the choice
                              </div>
                            )}
                            {disc.partial && (
                              <div className="text-[9px] font-normal text-slate-500 mt-0.5 print:text-slate-500"
                                   title="Some proposed options are identical on this criterion.">
                                {disc.distinct} of {disc.total} distinct
                              </div>
                            )}
                          </td>
                          {data.statusQuo && (
                            <td className="p-3 border-r-2 border-slate-600 bg-slate-800/20 text-slate-400 print:bg-slate-50 print:text-slate-600">
                              {sqValue ?? '—'}
                            </td>
                          )}
                          {data.options?.map((opt: any, i: number) => (
                            <td key={i} className={`p-3 ${cls} ${opt.recommended ? 'bg-emerald-900/10 print:bg-emerald-50/30' : ''}`}>
                              {shown[i] ?? '—'}
                              {/* Move #3 — scope travels with every number. The
                                  `roi` string above already bakes scope into its
                                  own prose (formatImpactEstimate); this chip makes
                                  it visible even at a glance, not just on a close
                                  read of the cell text. */}
                              {key === 'roi' && (
                                <div className="mt-1">
                                  {opt.scopeQualifier?.scope === 'enterprise' ? (
                                    <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide bg-slate-700/60 text-slate-300 print:bg-slate-200 print:text-slate-700">
                                      Enterprise
                                    </span>
                                  ) : opt.scopeQualifier?.scope === 'segment' ? (
                                    <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide bg-indigo-900/40 text-indigo-300 print:bg-indigo-100 print:text-indigo-700">
                                      Segment{opt.scopeQualifier.label ? `: ${opt.scopeQualifier.label}` : ''}
                                    </span>
                                  ) : (
                                    <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide bg-amber-900/30 text-amber-500/90 print:bg-amber-100 print:text-amber-700">
                                      Scope unverified
                                    </span>
                                  )}
                                </div>
                              )}
                            </td>
                          ))}
                        </tr>
                      )})}
                      <tr>
                        <td className="p-3 font-semibold text-slate-400 bg-slate-900/50 print:text-slate-700 print:bg-slate-50">Risk</td>
                        {data.statusQuo && (
                          <td className="p-3 border-r-2 border-slate-600 bg-slate-800/20 print:bg-slate-50">
                            {/* Deliberately NOT badged Low/Medium/High. The status
                                quo's risk is a trajectory, not a score on the same
                                scale as an intervention's execution risk, and giving
                                it a matching pill would invite a comparison that the
                                two quantities do not support. */}
                            <span className="text-[10px] text-slate-400 print:text-slate-600">{data.statusQuo.riskLevel}</span>
                          </td>
                        )}
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
                {/* Option 0's caveat travels with the column. A baseline showing
                    "Flat — no measured drift" or "Improving without intervention"
                    changes how every other column should be read, and that is
                    exactly the case where the reader must not have to infer it. */}
                {data.statusQuo?.caveat && (
                  <p className="-mt-4 mb-6 text-xs text-slate-500 print:text-slate-600">
                    <span className="font-semibold text-slate-400 print:text-slate-700">Option 0 — </span>
                    {data.statusQuo.caveat}
                  </p>
                )}
                {/* Option detail cards */}
                <div className="space-y-6">
                  {data.options?.map((option: any, i: number) => (
                    <motion.div key={i}
                      initial={reduceMotion ? false : { opacity: 0, y: 12 }}
                      animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
                      transition={{ delay: reduceMotion ? 0 : i * 0.05 }}
                      // print:overflow-visible only — NOT break-inside-avoid. These
                      // cards are frequently taller than a page, and forbidding a break
                      // would push the whole card past the page end and clip more, not
                      // less. Releasing overflow lets the content flow across pages.
                      className={`rounded-xl overflow-hidden border print:overflow-visible ${option.recommended ? 'border-slate-600 border-l-4 border-l-emerald-500 bg-slate-900' : 'border-slate-700 bg-slate-900'} print:bg-white print:border-slate-200 ${option.recommended ? 'print:border-l-slate-800' : ''}`}>
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
                            {option.dominated_by && (() => {
                              const dominatorIdx = data.options.findIndex((o: any) => o.id === option.dominated_by);
                              return dominatorIdx >= 0 ? (
                                <p className="text-[11px] text-amber-500/90 mt-1 print:text-amber-700"
                                   title="Matches or is worse than another option on modelled impact, cost, and risk.">
                                  dominated by Option {String.fromCharCode(65 + dominatorIdx)}
                                </p>
                              ) : null;
                            })()}
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-slate-500">Est. ROI</p>
                            <p className="text-xl font-bold text-emerald-400 print:text-emerald-600">{formatROI(option.roi)}</p>
                            {option.scopeQualifier?.scope === 'enterprise' ? (
                              <span className="inline-block mt-1 px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide bg-slate-700/60 text-slate-300 print:bg-slate-200 print:text-slate-700">
                                Enterprise
                              </span>
                            ) : option.scopeQualifier?.scope === 'segment' ? (
                              <span className="inline-block mt-1 px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide bg-indigo-900/40 text-indigo-300 print:bg-indigo-100 print:text-indigo-700">
                                Segment{option.scopeQualifier.label ? `: ${option.scopeQualifier.label}` : ''}
                              </span>
                            ) : (
                              <span className="inline-block mt-1 px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide bg-amber-900/30 text-amber-500/90 print:bg-amber-100 print:text-amber-700">
                                Scope unverified
                              </span>
                            )}
                          </div>
                        </div>
                        <p className="text-slate-300 text-sm leading-relaxed mb-4 print:text-slate-700">{option.description}</p>
{/* Timeline is condensed here for the same reason it is in the
                            table: the model writes time_to_value as prose and is
                            often expansive, and a full sentence wrapped to six
                            lines inside a 160px tile is not a metric. Full text
                            stays on hover and in the drawer. */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                          {[{ label: 'Investment', val: option.investment },
                            { label: 'Timeline', val: condenseTimeToValue(option.timeline), title: option.timeline },
                            { label: 'Risk', val: option.riskLevel, cls: option.riskLevel === 'Low' ? 'text-emerald-400 print:text-emerald-600' : option.riskLevel === 'Medium' ? 'text-amber-400 print:text-amber-600' : 'text-red-400 print:text-red-600' },
                            { label: 'Reversibility', val: option.reversibility, cls: 'capitalize' }].map(({ label, val, cls, title }) => (
                            <div key={label} className="text-center p-2 bg-slate-800/60 rounded-lg print:bg-slate-100 min-w-0">
                              <p className="text-[10px] text-slate-400 uppercase">{label}</p>
                              <p className={`font-bold text-xs text-slate-200 print:text-slate-900 break-words ${cls || ''}`} title={title}>{val}</p>
                            </div>
                          ))}
                        </div>
                        {/* ── Full narrative: PRINT ONLY ────────────────────────
                            On screen this moves into the option drawer. Three
                            complete analyses expanded inline is what pushed the
                            briefing past a 2-minute read (Cat 3). On paper there is
                            no drawer to open, so print keeps them where they were —
                            the exported PDF loses nothing. */}
                        <div className="hidden print:block">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                        {option.lens_views && (
                          <div className="mt-4 pt-4 border-t border-slate-700 print:border-slate-200">
                            <h4 className="font-semibold text-slate-200 mb-2 flex items-center gap-1.5 text-sm print:text-slate-900">
                              <Users className="w-3.5 h-3.5" /> Council Lenses
                            </h4>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                              {option.lens_views.map((p: any, j: number) => (
                                <div key={j} className="bg-slate-800/60 p-2.5 rounded-lg print:bg-slate-50">
                                  <p className="font-medium text-slate-200 text-xs print:text-slate-900">{p.role}</p>
                                  <p className="text-xs text-slate-400 mt-0.5 print:text-slate-600">{p.view}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        </div>

                        {/* Critic-pass findings stay ON the card, not behind the
                            drawer click. A flagged side effect is a reason to look
                            harder at an option; hiding it one interaction deeper
                            than the option's own sales pitch inverts that. */}
                        {option.flagged_side_effects?.length > 0 && (
                          <div data-testid="side-effects-chip" className="print:hidden mt-3 flex items-start gap-2 rounded-lg border border-amber-700/50 bg-amber-950/20 px-3 py-2">
                            <Zap className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
                            <p className="text-xs text-amber-200/90">
                              {option.flagged_side_effects.length} side effect{option.flagged_side_effects.length === 1 ? '' : 's'} flagged
                              against the causal model — see full analysis.
                            </p>
                          </div>
                        )}

                        {/* M6: the ROI range above does not stand alone — and that
                            has to hold on the exported PDF too, which is the copy
                            that gets forwarded and challenged. The panel prints
                            fully expanded (its toggle is print:hidden, its body
                            print:block), so it is deliberately NOT wrapped in a
                            print:hidden div like the rest of the screen-only chrome. */}
                        <AssumptionsPanel assumptions={option.key_assumptions || []} impactLabel={formatROI(option.roi)} />

                        <button
                          onClick={() => setDrawerIdx(i)}
                          className="print:hidden mt-4 inline-flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-800 hover:text-white"
                        >
                          View full analysis
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </AccordionSection>

            {/* "Before you approve" — Executive Briefing redesign, 2026-08-26.
                narrative_warnings (data-vs-prose mismatches) already rendered
                above the fold; blind_spots did not — they only ever lived in
                the collapsed accordion at the bottom, alongside a full
                Supporting Analysis a reader would have to open to find them.
                Genuine caveats that could change a reader's confidence belong
                above the fold; that is a different axis from "is this
                technical detail", which the rest of Supporting Analysis
                correctly stays collapsed for. Shows at most 2 — a link to the
                same Supporting Analysis toggle (already wired for
                ContradictionBanner above) surfaces the rest, never silently
                drops them. */}
            {data.blind_spots?.length > 0 && (
              <div className="print:hidden mb-6 rounded-xl border border-amber-700/40 bg-amber-950/10 p-4">
                <p className="text-[10px] font-semibold uppercase tracking-widest text-amber-500/90 mb-2">
                  Before you approve
                </p>
                <ul className="space-y-1.5">
                  {data.blind_spots.slice(0, 2).map((bs: string, i: number) => (
                    <li key={i} className="text-sm text-amber-100/90 leading-relaxed flex items-start gap-2">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                      <span>{bs}</span>
                    </li>
                  ))}
                </ul>
                {data.blind_spots.length > 2 && (
                  <button
                    type="button"
                    onClick={openBlindSpotsAndScroll}
                    className="text-xs text-amber-400 hover:text-amber-300 underline mt-2"
                  >
                    {data.blind_spots.length - 2} more consideration{data.blind_spots.length - 2 === 1 ? '' : 's'} in the full analysis ↓
                  </button>
                )}
              </div>
            )}

            {/* [E] Next Steps & Implementation */}
            <AccordionSection id="recommendation" title="Next Steps & Implementation" openSections={openSections} onToggle={toggleSection}
              icon={<CheckCircle2 className="w-4 h-4 text-slate-400" />}>
              <div className="p-5">
                {/* Screen: gradient blue card / Print: monochrome left-border callout */}
                <div className="bg-slate-900 border border-slate-700 text-white p-6 rounded-xl print:bg-white print:border-l-4 print:border-slate-800 print:rounded-none print:pl-5 print:pr-0 print:py-3">
                  <h3 className="text-lg font-bold mb-3 print:text-slate-900">{data.recommendation?.headline}</h3>
                  <p className="text-slate-300 leading-relaxed text-sm mb-5 print:text-slate-700">{data.recommendation?.rationale}</p>
                  {/* Cat 3 / M5. The typed List[ImmediateAction] wins when the run
                      produced one — it carries an owner and a deadline per action.
                      `nextSteps` is the legacy prose list and is partly assembled by
                      briefingUtils itself (a KPI-tracking step, a leadership-review
                      step), so it is a fallback, never a merge: mixing model-authored
                      actions with UI-authored ones in one numbered list makes the two
                      indistinguishable to the reader. */}
                  <div className="bg-slate-800/60 rounded-lg p-4 mb-5 print:bg-transparent print:p-0">
                    <ImmediateActionsChecklist
                      actions={data.immediate_actions || []}
                      fallbackSteps={data.recommendation?.nextSteps || []}
                    />
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
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
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
                          <li>Results will appear in your Solutions Portfolio</li>
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

            {/* Implementation Roadmap was here. Moved out — WhitePaperReport
                already renders `data.roadmap` from the same localStorage
                payload (WhitePaperReport.tsx §"Implementation Roadmap"), so
                this was the same content on two surfaces. See the "rest of the
                analysis" block at the end of this page. */}

            {/* Supporting Analysis divider — the same toggle as the toolbar's
                "Show/Hide the analysis", reachable from two places rather than
                two competing controls. Both now call setAllAnalysisSections;
                they previously carried byte-identical copies of the logic. */}
            <div id="accordion-analysis" className="print:hidden flex items-center gap-3 mt-6 mb-2">
              <div className="h-px flex-1 bg-slate-800" />
              <button
                onClick={() => setAllAnalysisSections(!analysisAllOpen)}
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
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                      {/* NOT "Root Cause Analysis". Deep Analysis produces a KT
                          Is/Is-Not dimensional decomposition — it locates WHERE
                          the variance concentrated, which is association, not an
                          established cause. The theory layer is explicit that
                          only VA's DiD/Granger testing reaches a causal claim,
                          so the briefing must not promote a ranked delta list to
                          "root cause" in front of an executive. */}
                      <Zap className="w-4 h-4 text-amber-400" /> Largest Variance Contributors
                    </h3>
                    {/* Segments from DIFFERENT dimensions are not disjoint, so they
                        cannot be read as a single ranking. A live briefing listed four
                        profit centres and one CUSTOMER together; that customer's revenue
                        sits inside one of those divisions, so the same margin loss appears
                        twice and the entries are not comparable, let alone additive.
                        Stated only when it applies — a single-dimension list needs no
                        caveat, and a caveat that always shows gets ignored. */}
                    {new Set((data.situation.rootCauses as any[])
                      .map(c => c?.dimension).filter(Boolean)).size > 1 && (
                      <p className="text-[11px] text-amber-400/80 mb-3 print:text-amber-700">
                        These come from different dimensions and overlap — a customer's result is
                        already counted inside its division. Compare within a dimension, not down the list.
                      </p>
                    )}
                    <div className="space-y-3">
                      {data.situation.rootCauses.map((cause: any, i: number) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="w-5 h-5 bg-amber-500 text-slate-900 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">{i + 1}</div>
                          <div>
                            {/* The dimension is NOT decoration. This list mixes
                                dimensions -- four profit centres and one customer in the
                                live briefing -- and without a label "National Auto Parts
                                Chain A" reads as a sixth division. */}
                            <p className="font-medium text-white text-sm">
                              {cause.driver}
                              {cause.dimension && (
                                <span className="ml-2 text-[10px] font-normal uppercase tracking-wider text-slate-500 print:text-slate-500">
                                  {cause.dimension}
                                </span>
                              )}
                            </p>
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

            {/* Market Intelligence, Stage 1: Independent Proposals, Stage 2:
                Cross-Review and Moderator Verdicts were four accordions here.
                All four moved out in the Aug 2026 composition pass.

                They are process transparency — how the council reached the
                answer — and this page is where the answer gets DECIDED. A
                Decision Maker was scrolling past seven collapsed accordions
                with names like "Stage 1: Independent Proposals" that exist for
                the other persona entirely. Measured before the change: 6,635px
                of content in an 847px viewport, 7.8 screens, at the COLLAPSED
                default.

                Both destinations already existed and already read the same
                localStorage briefing payload, so this was deletion, not
                migration:
                  - stage_1_hypotheses / cross_review -> /debate/:situationId
                    (CouncilDebatePage already renders both)
                  - market_signals -> /report/:situationId
                    (WhitePaperReport already renders it)
                The briefing had no link to the debate page at all before now —
                that surface was orphaned. See the block at the end of the
                page. */}

            {/* The "Risk & Considerations" divider stood here and was removed.
                It toggled ['risks','blindspots','inaction'] — a set that now
                overlaps ANALYSIS_SECTION_IDS almost exactly, so two dividers
                claimed the same two sections and either one could leave the
                other's label lying about what was open. One group, one
                control. */}

            {/* [M] Risk Analysis */}
            {data.risks?.length > 0 && (
              <AccordionSection id="risks" title="Risk Analysis & Mitigation" openSections={openSections} onToggle={toggleSection}
                icon={<AlertTriangle className="w-4 h-4 text-slate-400" />}>
                <div className="p-5">
                  {/* Cat 3: top 3 in the main view, the rest behind "See all risks".
                      Rows 4+ carry `risk-overflow-row` rather than a bare `hidden`,
                      because this page has TWO output paths and they do not share a
                      mechanism: window.print() honours `print:` variants, while the
                      Export button rasterises the live DOM via html2pdf and sees no
                      print media at all. The class is unhidden explicitly in the
                      pdf-export-mode stylesheet so a collapsed section cannot silently
                      ship a shorter risk list than the one on screen. */}
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
                          <tr key={i} className={`border-t border-slate-700 print:border-slate-200 ${
                            i >= 3 && !showAllRisks ? 'risk-overflow-row hidden print:table-row' : ''}`}>
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
                  {data.risks.length > 3 && (
                    <button
                      onClick={() => setShowAllRisks(v => !v)}
                      className="print:hidden mt-3 text-xs font-medium text-slate-400 transition-colors hover:text-slate-200"
                    >
                      {showAllRisks ? 'Show top 3 only' : `See all ${data.risks.length} risks`}
                    </button>
                  )}
                </div>
              </AccordionSection>
            )}

            {/* [N] Blind Spots & Tensions — SCREEN ONLY.
                The print-only appendix immediately below renders the same
                content in a print-appropriate layout. Both were previously
                visible when printing, so every exported briefing carried Blind
                Spots and Unresolved Tensions twice, back to back on one page. */}
            {((data.blind_spots?.length > 0) || (data.unresolved_tensions?.length > 0)) && (
              <div className="print:hidden">
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
              </div>
            )}

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

            {/* Where the rest of the analysis lives.
                Replaces four accordions (Market Intelligence, Stage 1, Stage 2,
                Moderator Verdicts) and the Implementation Roadmap. Both targets
                read the same localStorage briefing payload this page does, so
                these are real destinations for this exact run, not generic nav.
                Screen only: the print path already carries its own appendices,
                and a "click here" on paper is dead text. */}
            <div className="print:hidden mt-8 pt-5 border-t border-slate-800">
              <p className="text-xs text-slate-400 mb-3">
                This page carries the decision. The full record sits alongside it:
              </p>
              <div className="flex flex-col sm:flex-row gap-2">
                <Link
                  to={`/report/${situationId}`}
                  className="flex-1 flex items-center justify-between gap-3 px-4 py-3 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/60 transition-colors group"
                >
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold text-white">Full report</span>
                    <span className="block text-xs text-slate-400 mt-0.5">
                      Situation, market context, roadmap, risks — the narrative version
                    </span>
                  </span>
                  <ArrowRight className="w-4 h-4 text-slate-500 shrink-0 group-hover:text-slate-300 transition-colors" />
                </Link>
                <Link
                  to={`/debate/${situationId}`}
                  className="flex-1 flex items-center justify-between gap-3 px-4 py-3 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 hover:bg-slate-800/60 transition-colors group"
                >
                  <span className="min-w-0">
                    <span className="block text-sm font-semibold text-white">How the council decided</span>
                    <span className="block text-xs text-slate-400 mt-0.5">
                      Independent proposals, cross-review, and the moderator's grades
                    </span>
                  </span>
                  <ArrowRight className="w-4 h-4 text-slate-500 shrink-0 group-hover:text-slate-300 transition-colors" />
                </Link>
              </div>
            </div>

            {/* Mobile-only jump to the Decision Workspace, which now stacks
                below this column instead of pinning a 320px rail beside it.
                A link, not a second Approve control — one commit affordance
                per page. */}
            <div className="lg:hidden sticky bottom-0 -mx-4 mt-6 px-4 py-3 bg-slate-900/95 backdrop-blur border-t border-slate-800 print:hidden">
              <a
                href="#decision-workspace"
                className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white text-sm font-semibold transition-colors"
              >
                Review &amp; approve
                <ChevronDown className="w-4 h-4" />
              </a>
            </div>

            {/* Footer */}
            <footer className="py-6 text-center text-xs text-slate-500 print:block print:border-t print:border-slate-300 print:pt-4 print:text-slate-600">
              <p>This briefing was generated by Decision Studio using AI-assisted analysis.</p>
              <p className="mt-1 print:text-slate-500">
                Provided as decision support. Human judgment is required for final decisions.
              </p>
              {/* ── Audit metadata (Cat 3) ──────────────────────────────────────
                  Every field is read from the payload. Nothing here is a constant
                  dressed as provenance: the spec's example line named a specific
                  model version and a specific data window, and hardcoding either
                  would make the audit strip assert something no run established.
                  Where a fact is absent it is omitted, not filled in.

                  Council names are de-branded via personaLabels — see that module
                  for the Phase 13 M3 / Phase 18 reconciliation. This footer used to
                  title-case the raw persona ids, printing "Mckinsey · Bcg · Bain"
                  onto the exported PDF. */}
              <div className="mt-3 flex flex-wrap justify-center gap-x-4 gap-y-1 text-[10px] text-slate-400 font-mono print:text-slate-600">
                {data.kpiData?.kpi_name && <span>KPI: {data.kpiData.kpi_name}</span>}
                {(() => {
                  const ctx = data.kpiData?.context
                  if (!ctx?.window_start && !ctx?.source_system) return null
                  const window = ctx?.window_start && ctx?.window_end
                    ? `${ctx.window_start} → ${ctx.window_end}`
                    : null
                  const comparison = ctx?.comparison_window_start && ctx?.comparison_window_end
                    ? ` vs ${ctx.comparison_window_start} → ${ctx.comparison_window_end}`
                    : ''
                  return (
                    <span>
                      Data: {ctx?.source_system || 'source not stated'}
                      {window ? ` ${window}${comparison}` : ''}
                      {ctx?.version ? ` (${ctx.version})` : ''}
                    </span>
                  )
                })()}
                {councilCompositionLabel(personaOrder) && (
                  <span>Council: {councilCompositionLabel(personaOrder)}</span>
                )}
                <span>Model: Claude (Anthropic)</span>
                {data.metrics?.confidence && <span>Confidence: {data.metrics.confidence}</span>}
                <span>Generated: {new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
              </div>
            </footer>
          </div>
        </div>

        {/* Option narrative, on demand. Index-addressed so a stale object can
            never be left open behind a re-render. */}
        <OptionDetailDrawer
          option={drawerIdx != null ? (data.options?.[drawerIdx] ?? null) : null}
          optionLabel={drawerIdx != null ? `Option ${String.fromCharCode(65 + drawerIdx)}` : ''}
          onClose={() => setDrawerIdx(null)}
        />

        {/* ── Right: Decision Workspace ── */}
        <div id="decision-workspace" className="w-full lg:w-80 flex-shrink-0 border-t lg:border-t-0 lg:border-l border-slate-800 print:hidden">
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
