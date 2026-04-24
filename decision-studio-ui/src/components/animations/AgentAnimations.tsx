import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useInView } from 'framer-motion'

// ─────────────────────────────────────────────────
// Trajectory Mini Chart (VA — Value Assurance)
// ─────────────────────────────────────────────────
export function TrajectoryMiniChart() {
  const months = [0, 1, 2, 3, 4, 5, 6, 7, 8]
  const inaction = [60, 57, 54, 51, 48, 45, 42, 39, 36]
  const expected = [60, 62, 64, 66, 68, 70]
  const actual = [60, 61, 63, 66, 69]

  const w = 320
  const h = 160
  const pad = { top: 20, right: 20, bottom: 30, left: 40 }
  const plotW = w - pad.left - pad.right
  const plotH = h - pad.top - pad.bottom

  const xScale = (i: number) => pad.left + (i / (months.length - 1)) * plotW
  const yScale = (v: number) => pad.top + plotH - ((v - 30) / 50) * plotH

  const toPath = (data: number[]) =>
    data.map((v, i) => `${i === 0 ? 'M' : 'L'}${xScale(i).toFixed(1)},${yScale(v).toFixed(1)}`).join(' ')

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full max-w-sm mx-auto" style={{ fontFamily: 'Satoshi, sans-serif' }}>
      {/* Grid lines */}
      {[40, 50, 60, 70].map((v) => (
        <line key={v} x1={pad.left} x2={w - pad.right} y1={yScale(v)} y2={yScale(v)} stroke="#334155" strokeWidth={0.5} />
      ))}

      {/* Approval marker */}
      <line x1={xScale(0)} y1={pad.top} x2={xScale(0)} y2={h - pad.bottom} stroke="#6366f1" strokeWidth={1} strokeDasharray="3,3" opacity={0.4} />
      <text x={xScale(0) + 4} y={pad.top + 10} fill="#6366f1" fontSize={8} opacity={0.6}>Approval</text>

      {/* Inaction line (red, dashed) */}
      <motion.path
        d={toPath(inaction)}
        fill="none"
        stroke="#ef4444"
        strokeWidth={1.5}
        strokeDasharray="5,3"
        initial={{ pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 1.5, ease: 'easeOut' }}
      />

      {/* Expected line (blue, dashed) */}
      <motion.path
        d={toPath(expected)}
        fill="none"
        stroke="#3b82f6"
        strokeWidth={1.5}
        strokeDasharray="5,3"
        initial={{ pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 1.2, ease: 'easeOut', delay: 0.3 }}
      />

      {/* Actual line (emerald, solid) */}
      <motion.path
        d={toPath(actual)}
        fill="none"
        stroke="#10b981"
        strokeWidth={2.5}
        initial={{ pathLength: 0 }}
        whileInView={{ pathLength: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 1, ease: 'easeOut', delay: 0.6 }}
      />

      {/* Actual dots */}
      {actual.map((v, i) => (
        <motion.circle
          key={i}
          cx={xScale(i)}
          cy={yScale(v)}
          r={3}
          fill="#10b981"
          initial={{ opacity: 0, scale: 0 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 + i * 0.15 }}
        />
      ))}

      {/* Legend */}
      <g transform={`translate(${pad.left}, ${h - 8})`}>
        <line x1={0} y1={0} x2={16} y2={0} stroke="#ef4444" strokeWidth={1.5} strokeDasharray="4,2" />
        <text x={20} y={3} fill="#94a3b8" fontSize={8}>Inaction</text>
        <line x1={70} y1={0} x2={86} y2={0} stroke="#3b82f6" strokeWidth={1.5} strokeDasharray="4,2" />
        <text x={90} y={3} fill="#94a3b8" fontSize={8}>Expected</text>
        <line x1={145} y1={0} x2={161} y2={0} stroke="#10b981" strokeWidth={2} />
        <text x={165} y={3} fill="#94a3b8" fontSize={8}>Actual</text>
      </g>

      {/* Y-axis label */}
      <text x={pad.left - 8} y={pad.top - 6} fill="#64748b" fontSize={8} textAnchor="end">KPI %</text>
    </svg>
  )
}

// ─────────────────────────────────────────────────
// KPI Grid Animation (SA — Situation Awareness)
// ─────────────────────────────────────────────────
export function KPIGridAnimation() {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true })
  const [showCritical, setShowCritical] = useState(false)
  const [showCard, setShowCard] = useState(false)

  useEffect(() => {
    if (!isInView) return
    const t1 = setTimeout(() => setShowCritical(true), 1000)
    const t2 = setTimeout(() => setShowCard(true), 1800)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [isInView])

  const kpis = [
    { name: 'Revenue', value: '+3.2%', critical: false },
    { name: 'Gross Margin', value: '-4.7%', critical: true },
    { name: 'COGS Ratio', value: '+2.1%', critical: false },
    { name: 'Op. Income', value: '+1.8%', critical: false },
    { name: 'Net Cash Flow', value: '-0.5%', critical: false },
    { name: 'Customer Count', value: '+0.9%', critical: false },
  ]

  const container = { hidden: {}, visible: { transition: { staggerChildren: 0.1 } } }
  const tile = { hidden: { opacity: 0, y: 8 }, visible: { opacity: 1, y: 0, transition: { duration: 0.4 } } }

  return (
    <div
      ref={ref}
      className="rounded-xl bg-slate-900 border border-slate-700/50 overflow-hidden p-4 flex flex-col gap-3"
      style={{ aspectRatio: '16/10' }}
    >
      <div className="flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-xs text-slate-500 font-mono tracking-wider">LIVE MONITORING</span>
      </div>

      <motion.div
        className="grid grid-cols-3 gap-2 flex-1"
        variants={container}
        initial="hidden"
        animate={isInView ? 'visible' : 'hidden'}
      >
        {kpis.map((kpi) => {
          const isCritical = kpi.critical && showCritical
          return (
            <motion.div
              key={kpi.name}
              variants={tile}
              className="rounded-lg border p-2 transition-all duration-700"
              style={{
                backgroundColor: isCritical ? 'rgba(239,68,68,0.08)' : '#1e293b',
                borderColor: isCritical ? '#ef4444' : '#334155',
                borderLeftWidth: isCritical ? '3px' : '1px',
              }}
            >
              <div className="text-xs text-slate-500 truncate">{kpi.name}</div>
              <div
                className="text-sm font-semibold mt-0.5 transition-colors duration-700"
                style={{ color: isCritical ? '#ef4444' : kpi.value.startsWith('+') ? '#10b981' : '#94a3b8' }}
              >
                {kpi.value}
              </div>
            </motion.div>
          )
        })}
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={showCard ? { opacity: 1, y: 0 } : { opacity: 0, y: 8 }}
        transition={{ duration: 0.5 }}
        className="rounded-lg border-l-2 border-red-500 bg-red-500/5 p-2.5"
      >
        <div className="flex items-center gap-1.5 mb-1">
          <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
          <span className="text-xs font-semibold text-red-400">CRITICAL — Situation Detected</span>
        </div>
        <p className="text-xs text-slate-300 font-medium">Gross Margin Below Threshold</p>
        <p className="text-xs text-slate-500 mt-0.5">-4.7% YoY · Southeast, Midwest · Premium Synthetics</p>
      </motion.div>
    </div>
  )
}

// ─────────────────────────────────────────────────
// IS/IS NOT Animation (DA — Deep Analysis)
// ─────────────────────────────────────────────────
export function IsIsNotAnimation() {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true })
  const [showScqa, setShowScqa] = useState(false)

  const rows = [
    { dimension: 'Region', is: 'SE · Midwest', isNot: 'NE · West', insight: '2 of 4 regions' },
    { dimension: 'Product', is: 'Premium Synth.', isNot: 'Standard · Economy', insight: 'Premium line only' },
    { dimension: 'Customer', is: 'Industrial B2B', isNot: 'Retail · Fleet', insight: 'Segment specific' },
    { dimension: 'Time', is: 'Last 90 days', isNot: 'Prior period', insight: 'Recent onset' },
  ]

  useEffect(() => {
    if (!isInView) return
    const t = setTimeout(() => setShowScqa(true), rows.length * 300 + 800)
    return () => clearTimeout(t)
  }, [isInView])

  return (
    <div
      ref={ref}
      className="rounded-xl bg-slate-900 border border-slate-700/50 overflow-hidden p-4 flex flex-col gap-3"
      style={{ aspectRatio: '16/10' }}
    >
      <span className="text-xs text-slate-500 font-mono tracking-wider">IS / IS NOT ANALYSIS</span>

      <div className="flex-1 flex flex-col gap-px rounded-lg overflow-hidden" style={{ backgroundColor: '#334155' }}>
        <div className="grid grid-cols-4" style={{ backgroundColor: '#1e293b' }}>
          {['Dimension', 'IS', 'IS NOT', 'Insight'].map(h => (
            <div key={h} className="px-2 py-1.5 text-xs font-semibold text-indigo-400">{h}</div>
          ))}
        </div>
        {rows.map((row, i) => (
          <motion.div
            key={row.dimension}
            className="grid grid-cols-4"
            style={{ backgroundColor: '#0f172a' }}
            initial={{ opacity: 0, x: -6 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -6 }}
            transition={{ delay: i * 0.3 + 0.2, duration: 0.4 }}
          >
            <div className="px-2 py-1.5 text-xs text-slate-300">{row.dimension}</div>
            <div className="px-2 py-1.5 text-xs text-red-400 font-medium">{row.is}</div>
            <div className="px-2 py-1.5 text-xs text-emerald-400">{row.isNot}</div>
            <div className="px-2 py-1.5 text-xs text-slate-400">{row.insight}</div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={showScqa ? { opacity: 1 } : { opacity: 0 }}
        transition={{ duration: 0.5 }}
        className="rounded-lg border border-slate-700/50 p-2.5"
        style={{ backgroundColor: '#1e293b' }}
      >
        <div className="text-xs font-semibold text-indigo-400 mb-1">SCQA Diagnostic Summary</div>
        <p className="text-xs text-slate-400 leading-relaxed">
          <span className="text-amber-400 font-medium">Complication: </span>
          Premium Synthetics margin compressed in SE/MW industrial accounts — not elsewhere. Recent onset, accelerating.
        </p>
      </motion.div>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Market Context Animation (MA — Market Analysis)
// ─────────────────────────────────────────────────
export function MarketContextAnimation() {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true })

  const signals = [
    { label: 'Competitor', color: '#f59e0b', text: 'ChemCorp launched economy-tier synthetic in SE — 15% price undercut on standard grade.' },
    { label: 'Market', color: '#3b82f6', text: 'Raw material index forecast to plateau Q4 — cost pressure likely temporary.' },
    { label: 'Signal', color: '#8b5cf6', text: '3 of 5 industry peers now pursuing value-bundling strategy.' },
  ]

  return (
    <div
      ref={ref}
      className="rounded-xl bg-slate-900 border border-slate-700/50 overflow-hidden p-4 flex flex-col gap-3"
      style={{ aspectRatio: '16/10' }}
    >
      <div className="flex items-center gap-2">
        <div className="w-5 h-5 rounded bg-blue-600/20 flex items-center justify-center text-xs text-blue-400 font-bold">MA</div>
        <span className="text-xs font-semibold text-blue-400">Market Intelligence</span>
        <span className="text-xs text-slate-500 ml-auto">Perplexity + Claude synthesis</span>
      </div>

      <div className="flex-1 flex flex-col gap-2">
        {signals.map((s, i) => (
          <motion.div
            key={s.label}
            className="rounded-lg border p-2.5 flex gap-2.5 items-start flex-1"
            style={{ backgroundColor: '#1e293b', borderColor: '#334155' }}
            initial={{ opacity: 0, x: -8 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -8 }}
            transition={{ delay: i * 0.4 + 0.2, duration: 0.4 }}
          >
            <div className="text-xs font-semibold mt-0.5 w-16 shrink-0" style={{ color: s.color }}>{s.label}</div>
            <p className="text-xs text-slate-400 leading-relaxed">{s.text}</p>
          </motion.div>
        ))}
      </div>

      <motion.div
        className="text-xs text-slate-500 text-center"
        initial={{ opacity: 0 }}
        animate={isInView ? { opacity: 1 } : { opacity: 0 }}
        transition={{ delay: 1.6, duration: 0.4 }}
      >
        Scanned 47 sources · Updated 2 hours ago
      </motion.div>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Refinement Chat Animation (SF — HITL Refinement)
// ─────────────────────────────────────────────────
export function RefinementChatAnimation() {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true })
  const [q1chars, setQ1chars] = useState(0)
  const [showResp, setShowResp] = useState(false)
  const [showChips, setShowChips] = useState(false)

  const question = 'Which accounts are driving the margin decline?'

  useEffect(() => {
    if (!isInView) return
    const delay = setTimeout(() => {
      let count = 0
      const interval = setInterval(() => {
        count++
        setQ1chars(count)
        if (count >= question.length) {
          clearInterval(interval)
          setTimeout(() => setShowResp(true), 500)
          setTimeout(() => setShowChips(true), 1300)
        }
      }, 38)
      return () => clearInterval(interval)
    }, 400)
    return () => clearTimeout(delay)
  }, [isInView])

  const accounts = [
    { name: 'Meridian Manufacturing', region: 'SE', delta: '-6.2pp' },
    { name: 'Great Lakes Industrial', region: 'MW', delta: '-5.8pp' },
    { name: 'Southern Fabricators', region: 'SE', delta: '-4.1pp' },
  ]

  const chips = ['Show competitor pricing in SE', 'Break down by SKU', 'What if we held pricing?']

  return (
    <div
      ref={ref}
      className="rounded-xl bg-slate-900 border border-slate-700/50 overflow-hidden p-4 flex flex-col gap-2.5"
      style={{ aspectRatio: '16/10' }}
    >
      <span className="text-xs text-slate-500 font-mono tracking-wider">PROBLEM REFINEMENT</span>

      <div className="flex-1 flex flex-col gap-2.5 justify-end">
        {/* User question */}
        {q1chars > 0 && (
          <div className="flex justify-end">
            <div className="rounded-2xl rounded-br-sm px-3 py-2 max-w-xs bg-indigo-600">
              <p className="text-xs text-white font-medium">
                {question.substring(0, q1chars)}
                {q1chars < question.length && (
                  <span className="inline-block w-px h-3 ml-0.5 align-middle bg-white opacity-80" />
                )}
              </p>
            </div>
          </div>
        )}

        {/* DS response */}
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={showResp ? { opacity: 1, y: 0 } : { opacity: 0, y: 6 }}
          transition={{ duration: 0.4 }}
          className="rounded-lg border border-slate-700/50 p-2.5"
          style={{ backgroundColor: '#1e293b' }}
        >
          <div className="flex items-center gap-1.5 mb-2">
            <div className="w-4 h-4 rounded bg-indigo-600 flex items-center justify-center text-white text-xs font-bold">DS</div>
            <span className="text-xs font-semibold text-indigo-400">Live Data Query</span>
            <span className="text-xs text-slate-500 ml-1">· 1.2s</span>
          </div>
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700/50">
                {['Account', 'Region', 'Margin Δ'].map(h => (
                  <th key={h} className="text-left py-1 text-xs text-slate-500 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {accounts.map((a, i) => (
                <motion.tr
                  key={a.name}
                  initial={{ opacity: 0 }}
                  animate={showResp ? { opacity: 1 } : { opacity: 0 }}
                  transition={{ delay: i * 0.15 + 0.1 }}
                >
                  <td className="py-1 text-xs text-slate-300 truncate max-w-[120px]">{a.name}</td>
                  <td className="py-1 text-xs text-slate-400">{a.region}</td>
                  <td className="py-1 text-xs font-semibold text-red-400">{a.delta}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-slate-500 mt-1.5">Top 3 of 14 affected accounts</p>
        </motion.div>

        {/* Suggested follow-ups */}
        <motion.div
          className="flex flex-wrap gap-1.5"
          initial={{ opacity: 0 }}
          animate={showChips ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.4 }}
        >
          {chips.map(chip => (
            <div
              key={chip}
              className="rounded-full border border-slate-700/50 px-2.5 py-1 text-xs text-indigo-400"
              style={{ backgroundColor: '#0f172a' }}
            >
              {chip}
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Council Debate Animation (SF — Solution Finder)
// ─────────────────────────────────────────────────
export function CouncilDebateAnimation() {
  const ref = useRef<HTMLDivElement>(null)
  const isInView = useInView(ref, { once: true })
  const [showSynth, setShowSynth] = useState(false)

  const personas = [
    { label: 'Operations', color: '#3b82f6', impact: '+2.8pp', text: 'Renegotiate supplier contracts for affected regions.' },
    { label: 'Financial', color: '#10b981', impact: '+3.5pp', text: 'Tiered pricing for industrial accounts.' },
    { label: 'Strategic', color: '#8b5cf6', impact: '+4.1pp', text: 'Bundle with maintenance contracts.' },
  ]

  useEffect(() => {
    if (!isInView) return
    const t = setTimeout(() => setShowSynth(true), personas.length * 350 + 800)
    return () => clearTimeout(t)
  }, [isInView])

  return (
    <div
      ref={ref}
      className="rounded-xl bg-slate-900 border border-slate-700/50 overflow-hidden p-4 flex flex-col gap-3"
      style={{ aspectRatio: '16/10' }}
    >
      <span className="text-xs text-slate-500 font-mono tracking-wider">STRATEGY COUNCIL</span>

      <div className="flex-1 grid grid-cols-3 gap-2">
        {personas.map((p, i) => (
          <motion.div
            key={p.label}
            className="rounded-lg border p-2.5 flex flex-col"
            style={{
              backgroundColor: '#1e293b',
              borderColor: '#334155',
              borderTopWidth: '2px',
              borderTopColor: p.color,
            }}
            initial={{ opacity: 0, y: 10 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
            transition={{ delay: i * 0.35 + 0.1, duration: 0.4 }}
          >
            <div className="text-xs font-semibold mb-1" style={{ color: p.color }}>{p.label}</div>
            <p className="text-xs text-slate-400 leading-relaxed flex-1">{p.text}</p>
            <div className="mt-2 pt-2 border-t border-slate-700/50">
              <div className="text-xs font-bold text-emerald-400">{p.impact}</div>
              <div className="text-xs text-slate-500">expected recovery</div>
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={showSynth ? { opacity: 1, y: 0 } : { opacity: 0, y: 6 }}
        transition={{ duration: 0.5 }}
        className="rounded-lg border border-indigo-500/30 p-2.5"
        style={{ backgroundColor: 'rgba(79,70,229,0.06)' }}
      >
        <div className="flex items-center gap-2 mb-1">
          <div className="w-4 h-4 rounded flex items-center justify-center bg-indigo-600 text-white text-xs font-bold">∑</div>
          <span className="text-xs font-semibold text-indigo-400">Synthesized Recommendation</span>
          <span className="ml-auto text-xs text-emerald-400 font-bold">+3.8pp · 90 days</span>
        </div>
        <p className="text-xs text-slate-400">Tiered pricing → supplier renegotiation → bundled contracts pilot.</p>
      </motion.div>
    </div>
  )
}
