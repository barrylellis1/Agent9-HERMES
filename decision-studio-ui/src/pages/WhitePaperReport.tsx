import { useState, useEffect, useCallback, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import html2pdf from 'html2pdf.js'
import { ArrowLeft, Download, Printer, CheckCircle2, AlertTriangle } from 'lucide-react'
import { BrandLogo } from '../components/BrandLogo'

// ─────────────────────────────────────────────────
// White-Paper Report — Narrative Arc for cold-eyes review
// Route: /report/:situationId
// ─────────────────────────────────────────────────

export function WhitePaperReport() {
  const { situationId } = useParams<{ situationId: string }>()
  const [data, setData] = useState<any>(null)
  const [approveState, setApproveState] = useState<string>('draft')
  const reportRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!situationId) return
    const raw = localStorage.getItem(`briefing_${situationId}`)
    if (raw) {
      try { setData(JSON.parse(raw)) } catch { /* ignore */ }
    }
    const storedVaId = localStorage.getItem(`va_solution_${situationId}`)
    if (storedVaId) setApproveState('approved')
  }, [situationId])

  const handlePrint = useCallback(() => window.print(), [])

  const handleExportPDF = useCallback(() => {
    const element = reportRef.current
    if (!element) return
    const filename = `Decision-Report-${situationId || 'export'}.pdf`
    const options = {
      margin: [15, 15] as [number, number],
      filename,
      image: { type: 'jpeg' as const, quality: 0.95 },
      html2canvas: { scale: 2, useCORS: true, scrollY: 0 },
      jsPDF: { unit: 'mm' as const, format: 'a4' as const, orientation: 'portrait' as const },
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
    }
    html2pdf().set(options).from(element).save()
  }, [situationId])

  if (!data) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-slate-800 mb-2">No Report Data</h2>
          <p className="text-sm text-slate-500 mb-4">
            Navigate through the Decision Studio workflow to generate a briefing first.
          </p>
          <Link to={`/briefing/${situationId}`} className="text-sm text-blue-600 hover:underline">
            ← Back to Executive Briefing
          </Link>
        </div>
      </div>
    )
  }

  const reportDate = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
  const kpiName = data.kpiData?.kpi_name || 'KPI'
  const isApproved = approveState === 'approved'

  return (
    <div className="min-h-screen bg-white print:bg-white">
      {/* ── Screen-only toolbar ── */}
      <nav className="print:hidden sticky top-0 z-50 flex items-center justify-between px-6 py-3 bg-slate-900 border-b border-slate-700">
        <Link to={`/briefing/${situationId}`} className="flex items-center gap-2 text-slate-300 hover:text-white text-sm">
          <ArrowLeft className="w-4 h-4" />
          Back to Briefing
        </Link>
        <div className="flex items-center gap-2">
          <button onClick={handlePrint} className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors">
            <Printer className="w-3.5 h-3.5" />
            Print
          </button>
          <button onClick={handleExportPDF} className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors">
            <Download className="w-3.5 h-3.5" />
            Download PDF
          </button>
        </div>
      </nav>

      {/* ── Report body ── */}
      <div ref={reportRef} className="max-w-4xl mx-auto px-8 py-12 print:px-12 print:py-8">

        {/* ═══════════════════════════════════════════
            [A] COVER BLOCK
            ═══════════════════════════════════════════ */}
        <header className="mb-10 pb-6 border-b-2 border-slate-300">
          <div className="flex items-center justify-between mb-6">
            <BrandLogo size={28} scheme="dark" />
            <span className={`px-3 py-1 text-xs font-semibold uppercase tracking-widest rounded-full ${
              isApproved
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-amber-50 text-amber-700 border border-amber-200'
            }`}>
              {isApproved ? 'Approved' : 'Draft'}
            </span>
          </div>

          <h1 className="text-2xl font-serif font-bold text-slate-900 leading-tight mb-4">
            {data.title || 'Decision Report'}
          </h1>

          <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-slate-500 font-mono">
            <span>{kpiName}</span>
            {data.principalId && <span>Principal: {data.principalId}</span>}
            <span>{reportDate}</span>
            <span className="text-slate-400">Internal — Decision Sensitive</span>
          </div>
        </header>

        {/* ═══════════════════════════════════════════
            [B] EXECUTIVE SUMMARY
            ═══════════════════════════════════════════ */}
        <section className="mb-10">
          <h2 className="text-lg font-serif font-bold text-slate-900 mb-3 pb-1 border-b border-slate-200">
            Executive Summary
          </h2>
          <div className="text-sm text-slate-700 leading-relaxed whitespace-pre-line">
            {data.executiveSummary}
          </div>
          <div className="mt-4 flex flex-wrap gap-x-8 gap-y-2 text-xs text-slate-500">
            <span><strong className="text-slate-700">Severity:</strong> {data.urgency}</span>
            <span><strong className="text-slate-700">Confidence:</strong> {data.metrics?.confidence}</span>
            <span><strong className="text-slate-700">Decision Deadline:</strong> {data.metrics?.decisionDeadline}</span>
          </div>
        </section>

        {/* ═══════════════════════════════════════════
            [C] SECTION 1: SITUATION & CONTEXT
            ═══════════════════════════════════════════ */}
        <section className="mb-10">
          <h2 className="text-lg font-serif font-bold text-slate-900 mb-3 pb-1 border-b border-slate-200">
            1. Situation &amp; Context
          </h2>
          <p className="text-sm text-slate-700 leading-relaxed mb-3">
            {data.situation?.currentState}
          </p>
          {data.situation?.problem && (
            <p className="text-sm text-slate-700 leading-relaxed mb-4">
              {data.situation.problem}
            </p>
          )}

          {data.situation?.keyQuestion && (
            <div className="border-l-4 border-slate-400 bg-slate-50 px-4 py-3 mb-4">
              <p className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-1">Key Question</p>
              <p className="text-sm text-slate-800 font-medium italic">
                {data.situation.keyQuestion}
              </p>
            </div>
          )}

          {data.situation?.assumptions?.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-2">Key Assumptions</p>
              <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                {data.situation.assumptions.map((a: string, i: number) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {/* ═══════════════════════════════════════════
            [D] SECTION 2: ROOT CAUSE ANALYSIS
            ═══════════════════════════════════════════ */}
        {data.situation?.rootCauses?.length > 0 && (
          <section className="mb-10">
            <h2 className="text-lg font-serif font-bold text-slate-900 mb-3 pb-1 border-b border-slate-200">
              2. Root Cause Analysis
            </h2>
            <table className="w-full text-sm border-collapse mb-3">
              <thead>
                <tr className="bg-slate-100 text-left">
                  <th className="px-3 py-2 text-xs font-semibold text-slate-700 border-b border-slate-200">Driver</th>
                  <th className="px-3 py-2 text-xs font-semibold text-slate-700 border-b border-slate-200">Dimension</th>
                  <th className="px-3 py-2 text-xs font-semibold text-slate-700 border-b border-slate-200">Evidence</th>
                  <th className="px-3 py-2 text-xs font-semibold text-slate-700 border-b border-slate-200">Impact</th>
                </tr>
              </thead>
              <tbody>
                {data.situation.rootCauses.map((rc: any, i: number) => (
                  <tr key={i} className="border-b border-slate-100">
                    <td className="px-3 py-2 text-slate-800 font-medium">{rc.driver}</td>
                    <td className="px-3 py-2 text-slate-600">{rc.dimension}</td>
                    <td className="px-3 py-2 text-slate-600">{rc.evidence}</td>
                    <td className="px-3 py-2 text-slate-600 font-mono text-xs">{rc.impact}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        {/* ═══════════════════════════════════════════
            [E] SECTION 3: MARKET CONTEXT (conditional)
            ═══════════════════════════════════════════ */}
        {data.market_signals && data.market_signals.length > 0 && (
          <section className="mb-10">
            <h2 className="text-lg font-serif font-bold text-slate-900 mb-3 pb-1 border-b border-slate-200">
              3. Market Context
            </h2>
            <div className="space-y-4">
              {data.market_signals.slice(0, 4).map((signal: any, i: number) => (
                <div key={i} className="border-l-2 border-slate-300 pl-4">
                  <p className="text-sm font-semibold text-slate-800">{signal.title || signal.headline}</p>
                  <p className="text-sm text-slate-600 leading-relaxed mt-1">{signal.summary || signal.description}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ═══════════════════════════════════════════
            [F] SECTION 4: OPTIONS EVALUATED
            ═══════════════════════════════════════════ */}
        {data.options?.length > 0 && (
          <section className="mb-10">
            <h2 className="text-lg font-serif font-bold text-slate-900 mb-3 pb-1 border-b border-slate-200">
              {data.market_signals?.length > 0 ? '4' : '3'}. Options Evaluated
            </h2>
            <div className="space-y-6">
              {data.options.map((opt: any, i: number) => (
                <div key={i} className={`border rounded-lg p-5 ${opt.recommended ? 'border-emerald-300 bg-emerald-50/30' : 'border-slate-200'}`}>
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-base font-semibold text-slate-900">
                      Option {i + 1}: {opt.title}
                    </h3>
                    {opt.recommended && (
                      <span className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide bg-emerald-100 text-emerald-700 rounded-full">
                        <CheckCircle2 className="w-3 h-3" /> Recommended
                      </span>
                    )}
                  </div>
                  {opt.subtitle && <p className="text-xs text-slate-500 mb-2">{opt.subtitle}</p>}
                  <p className="text-sm text-slate-700 leading-relaxed mb-3">{opt.description}</p>

                  {/* Metrics row */}
                  <div className="grid grid-cols-4 gap-3 mb-3">
                    <div className="text-center p-2 bg-slate-50 rounded">
                      <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-0.5">ROI</div>
                      <div className="text-xs font-semibold text-slate-800">{opt.roi || '—'}</div>
                    </div>
                    <div className="text-center p-2 bg-slate-50 rounded">
                      <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-0.5">Timeline</div>
                      <div className="text-xs font-semibold text-slate-800">{opt.timeline || '—'}</div>
                    </div>
                    <div className="text-center p-2 bg-slate-50 rounded">
                      <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-0.5">Investment</div>
                      <div className="text-xs font-semibold text-slate-800">{opt.investment || '—'}</div>
                    </div>
                    <div className="text-center p-2 bg-slate-50 rounded">
                      <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-0.5">Risk</div>
                      <div className={`text-xs font-semibold ${
                        opt.riskLevel === 'High' ? 'text-red-600' : opt.riskLevel === 'Medium' ? 'text-amber-600' : 'text-emerald-600'
                      }`}>{opt.riskLevel || '—'}</div>
                    </div>
                  </div>

                  {/* Pros / Cons */}
                  {(opt.prosDetailed?.length > 0 || opt.consDetailed?.length > 0) && (
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      {opt.prosDetailed?.length > 0 && (
                        <div>
                          <p className="font-semibold text-emerald-700 mb-1">Strengths</p>
                          <ul className="list-disc list-inside text-slate-600 space-y-0.5">
                            {opt.prosDetailed.map((p: any, j: number) => (
                              <li key={j}>{p.point}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {opt.consDetailed?.length > 0 && (
                        <div>
                          <p className="font-semibold text-red-700 mb-1">Considerations</p>
                          <ul className="list-disc list-inside text-slate-600 space-y-0.5">
                            {opt.consDetailed.map((c: any, j: number) => (
                              <li key={j}>{c.point}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ═══════════════════════════════════════════
            [G] SECTION 5: RECOMMENDATION & RATIONALE
            ═══════════════════════════════════════════ */}
        {data.recommendation && (
          <section className="mb-10">
            <h2 className="text-lg font-serif font-bold text-slate-900 mb-3 pb-1 border-b border-slate-200">
              {data.market_signals?.length > 0 ? '5' : '4'}. Recommendation &amp; Rationale
            </h2>
            <div className="border-l-4 border-emerald-500 bg-emerald-50/40 px-5 py-4 rounded-r-lg mb-4">
              <p className="text-base font-semibold text-slate-900 mb-2">{data.recommendation.headline}</p>
              <p className="text-sm text-slate-700 leading-relaxed">{data.recommendation.rationale}</p>
            </div>

            <div className="flex gap-8 text-xs text-slate-600 mb-4">
              <span><strong className="text-slate-800">Decision Owner:</strong> {data.recommendation.decisionOwner}</span>
              <span><strong className="text-slate-800">Deadline:</strong> {data.recommendation.deadline}</span>
            </div>

            {data.recommendation.nextSteps?.length > 0 && (
              <div>
                <p className="text-xs font-mono uppercase tracking-widest text-slate-500 mb-2">Next Steps</p>
                <ol className="list-decimal list-inside text-sm text-slate-700 space-y-1.5">
                  {data.recommendation.nextSteps.map((step: string, i: number) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </div>
            )}
          </section>
        )}

        {/* ═══════════════════════════════════════════
            [H] SECTION 6: IMPLEMENTATION ROADMAP
            ═══════════════════════════════════════════ */}
        {data.roadmap?.length > 0 && (
          <section className="mb-10">
            <h2 className="text-lg font-serif font-bold text-slate-900 mb-3 pb-1 border-b border-slate-200">
              {data.market_signals?.length > 0 ? '6' : '5'}. Implementation Roadmap
            </h2>
            <div className="space-y-5">
              {data.roadmap.map((phase: any, i: number) => (
                <div key={i} className="relative pl-6 border-l-2 border-slate-300">
                  <div className="absolute -left-[7px] top-0 w-3 h-3 rounded-full bg-slate-400 border-2 border-white" />
                  <div className="flex items-baseline gap-3 mb-2">
                    <h3 className="text-sm font-semibold text-slate-800">{phase.phase}</h3>
                    <span className="text-xs text-slate-500 font-mono">{phase.timeline}</span>
                  </div>
                  <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                    {phase.items?.map((item: string, j: number) => (
                      <li key={j}>{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ═══════════════════════════════════════════
            [I] SECTION 7: RISKS & MITIGATIONS
            ═══════════════════════════════════════════ */}
        {data.risks?.length > 0 && (
          <section className="mb-10">
            <h2 className="text-lg font-serif font-bold text-slate-900 mb-3 pb-1 border-b border-slate-200">
              {data.market_signals?.length > 0 ? '7' : '6'}. Risks &amp; Mitigations
            </h2>
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-slate-100 text-left">
                  <th className="px-3 py-2 text-xs font-semibold text-slate-700 border-b border-slate-200">Risk</th>
                  <th className="px-3 py-2 text-xs font-semibold text-slate-700 border-b border-slate-200 w-20">Likelihood</th>
                  <th className="px-3 py-2 text-xs font-semibold text-slate-700 border-b border-slate-200 w-20">Impact</th>
                  <th className="px-3 py-2 text-xs font-semibold text-slate-700 border-b border-slate-200">Mitigation</th>
                </tr>
              </thead>
              <tbody>
                {data.risks.map((r: any, i: number) => (
                  <tr key={i} className="border-b border-slate-100">
                    <td className="px-3 py-2 text-slate-800">{r.risk}</td>
                    <td className="px-3 py-2 text-slate-600">{r.likelihood}</td>
                    <td className="px-3 py-2 text-slate-600">{r.impact}</td>
                    <td className="px-3 py-2 text-slate-600">{r.mitigation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}

        {/* ═══════════════════════════════════════════
            [J] APPENDIX
            ═══════════════════════════════════════════ */}
        {(data.blind_spots?.length > 0 || data.unresolved_tensions?.length > 0) && (
          <section className="mb-10">
            <h2 className="text-lg font-serif font-bold text-slate-900 mb-3 pb-1 border-b border-slate-200">
              Appendix
            </h2>

            {data.blind_spots?.length > 0 && (
              <div className="mb-5">
                <h3 className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                  Identified Blind Spots
                </h3>
                <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                  {data.blind_spots.map((bs: string, i: number) => (
                    <li key={i}>{bs}</li>
                  ))}
                </ul>
              </div>
            )}

            {data.unresolved_tensions?.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-800 mb-2">Unresolved Tensions</h3>
                <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                  {data.unresolved_tensions.map((t: any, i: number) => (
                    <li key={i}>
                      <strong>{t.tension || t}:</strong>{' '}
                      {t.requires || ''}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        {/* ═══════════════════════════════════════════
            [K] FOOTER
            ═══════════════════════════════════════════ */}
        <footer className="mt-12 pt-4 border-t border-slate-200 text-center">
          <p className="text-xs text-slate-400 font-mono">
            Generated by Decision Studio &nbsp;|&nbsp; {reportDate} &nbsp;|&nbsp; {isApproved ? 'Approved' : 'Draft'}
          </p>
        </footer>
      </div>
    </div>
  )
}
