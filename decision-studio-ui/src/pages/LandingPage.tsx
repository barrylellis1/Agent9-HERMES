import { useState, useRef, useEffect, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { motion, useScroll, useTransform } from 'framer-motion'
import {
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  Eye,
  Globe,
  MessageCircle,
  Search,
  Shield,
  Users,
  LineChart,
} from 'lucide-react'

// ─────────────────────────────────────────────────
// Satoshi font (loaded from Fontshare CDN)
// ─────────────────────────────────────────────────
const SATOSHI_CSS = 'https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700,900&display=swap'

function useSatoshiFont() {
  useEffect(() => {
    if (document.querySelector(`link[href="${SATOSHI_CSS}"]`)) return
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = SATOSHI_CSS
    document.head.appendChild(link)
  }, [])
}

// ─────────────────────────────────────────────────
// Animation variants
// ─────────────────────────────────────────────────
const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] } },
}

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.15 } },
}

// ─────────────────────────────────────────────────
// Smooth-scroll helper
// ─────────────────────────────────────────────────
function scrollTo(id: string) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// ─────────────────────────────────────────────────
// Animated counter (counts up on scroll)
// ─────────────────────────────────────────────────
function AnimatedStat({ value, suffix, label }: { value: string; suffix?: string; label: string }) {
  return (
    <motion.div variants={fadeUp} className="text-center">
      <div className="text-3xl sm:text-4xl font-bold text-white tracking-tight" style={{ fontFamily: 'Satoshi, sans-serif' }}>
        {value}
        {suffix && <span className="text-indigo-400">{suffix}</span>}
      </div>
      <div className="text-sm text-slate-400 mt-1">{label}</div>
    </motion.div>
  )
}

// ─────────────────────────────────────────────────
// Screenshot frame — use src prop with an image path,
// or omit src to show the labelled placeholder.
// Images live in: decision-studio-ui/public/screenshots/
// ─────────────────────────────────────────────────
function ScreenshotFrame({ label, src, aspect = '16/10' }: { label: string; src?: string; aspect?: string }) {
  if (src) {
    return (
      <div
        className="rounded-xl overflow-hidden border border-slate-700/40 shadow-2xl shadow-slate-950/60"
        style={{ aspectRatio: aspect }}
      >
        <img
          src={src}
          alt={label}
          className="w-full h-full object-cover object-top"
          loading="lazy"
        />
      </div>
    )
  }
  return (
    <div
      className="rounded-xl bg-slate-800/60 border border-slate-700/50 overflow-hidden"
      style={{ aspectRatio: aspect }}
    >
      <div className="w-full h-full flex items-center justify-center">
        <span className="text-slate-500 text-sm">{label}</span>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Trajectory mini-chart (SVG — shows the accountability loop concept)
// ─────────────────────────────────────────────────
function TrajectoryMiniChart() {
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

// ═══════════════════════════════════════════════════
// LANDING PAGE
// ═══════════════════════════════════════════════════
export function LandingPage() {
  useSatoshiFont()

  // Nav opacity on scroll
  const [navSolid, setNavSolid] = useState(false)
  useEffect(() => {
    const onScroll = () => setNavSolid(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  // Parallax for hero gradient
  const heroRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ['start start', 'end start'] })
  const gradientY = useTransform(scrollYProgress, [0, 1], ['0%', '40%'])

  // Conversation form
  const [form, setForm] = useState({ name: '', company: '', email: '', message: '' })
  const [submitted, setSubmitted] = useState(false)
  const onChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }))
  const onSubmit = (e: FormEvent) => { e.preventDefault(); setSubmitted(true) }

  const font = { fontFamily: 'Satoshi, sans-serif' }

  return (
    <div className="min-h-screen bg-slate-950 text-white" style={{ ...font, scrollBehavior: 'smooth' }}>

      {/* ── NAVIGATION ── */}
      <nav
        className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
          navSolid ? 'bg-slate-950/95 backdrop-blur border-b border-slate-800/60' : 'bg-transparent'
        }`}
      >
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-lg font-bold tracking-tight text-white" style={font}>
            Decision Studio
          </span>
          <div className="flex items-center gap-6">
            <Link
              to="/how-it-works"
              className="text-sm text-slate-400 hover:text-white transition-colors hidden sm:block"
            >
              How It Works
            </Link>
            <Link
              to="/insights/bi-modernization"
              className="text-sm text-slate-400 hover:text-white transition-colors hidden sm:block"
            >
              Insights
            </Link>
            <Link
              to="/data-onboarding"
              className="text-sm text-slate-400 hover:text-white transition-colors hidden sm:block"
            >
              Data Onboarding
            </Link>
            <button
              onClick={() => scrollTo('conversation')}
              className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
            >
              Request a Conversation
            </button>
          </div>
        </div>
      </nav>

      {/* ═══════════════════════════════════════════
          1. HERO
      ═══════════════════════════════════════════ */}
      <section ref={heroRef} className="relative min-h-screen flex flex-col items-center justify-center px-6 pt-24 pb-20 overflow-hidden">
        {/* Subtle gradient background with parallax */}
        <motion.div
          className="absolute inset-0 pointer-events-none"
          style={{
            y: gradientY,
            background: 'radial-gradient(ellipse 70% 50% at 50% 35%, rgba(99,102,241,0.08) 0%, transparent 70%)',
          }}
        />

        <motion.div
          className="relative max-w-3xl text-center"
          variants={stagger}
          initial="hidden"
          animate="visible"
        >
          <motion.h1
            variants={fadeUp}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.1] tracking-tight text-white mb-6"
          >
            Your data platform is built. Your KPIs are governed.{' '}
            <span className="text-indigo-400">So why are decisions still made the same way?</span>
          </motion.h1>

          <motion.p
            variants={fadeUp}
            className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto mb-12 leading-relaxed"
          >
            You've invested years in your data infrastructure. Decision Studio is what
            makes that investment finally pay off — automated monitoring, structured
            root-cause analysis, and proof that your actions worked. You stay in control
            of every decision.
          </motion.p>

          <motion.div
            variants={fadeUp}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <button
              onClick={() => scrollTo('conversation')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors text-sm"
            >
              Request a Conversation
            </button>
            <button
              onClick={() => scrollTo('walkthrough')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-semibold transition-colors text-sm border border-slate-700/60 flex items-center justify-center gap-2"
            >
              See It In Action <ArrowRight className="w-4 h-4" />
            </button>
          </motion.div>
        </motion.div>
      </section>

      {/* ═══════════════════════════════════════════
          1b. THE AI INVESTMENT GAP (bridge)
      ═══════════════════════════════════════════ */}
      <section className="py-20 px-6 border-t border-slate-800/40">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <motion.p variants={fadeUp} className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-4">
              The AI investment gap
            </motion.p>
            <motion.h2
              variants={fadeUp}
              className="text-2xl sm:text-3xl font-bold text-white mb-4 leading-snug"
            >
              Your board wants AI that moves the P&amp;L. Not another chatbot.
            </motion.h2>
            <motion.p
              variants={fadeUp}
              className="text-slate-300 leading-relaxed mb-4 max-w-3xl"
            >
              Every executive team is under pressure to show AI investment. Most options —
              copilots, assistants, prompt playgrounds — can't tie their output to a financial
              outcome. Decision Studio connects directly to your governed data, delivers
              actionable analysis in hours, and tracks whether its recommendations actually
              moved the KPI. AI that earns its keep.
            </motion.p>
            <motion.div variants={fadeUp} className="mt-5 flex items-center gap-2 text-xs text-slate-500">
              <span className="inline-block w-1 h-1 rounded-full bg-slate-600" />
              Only 15% of AI decision-makers can tie AI value to P&amp;L changes — Forrester 2026
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          2. THE THREE PROBLEMS
      ═══════════════════════════════════════════ */}
      <section className="py-28 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}>

            {/* Problem 1 */}
            <motion.div variants={fadeUp} className="mb-20">
              <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-4">The monitoring gap</p>
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4 leading-snug">
                You're always reacting, never anticipating.
              </h2>
              <p className="text-slate-300 leading-relaxed mb-4 max-w-3xl">
                Your KPIs get reviewed weekly or monthly. By the time someone spots a margin drop,
                it's already expensive. You commission analysis — that takes weeks. By the time
                you have answers, the market has moved again.
              </p>
              <p className="text-slate-400 text-sm leading-relaxed max-w-3xl">
                Your KPI views are there — refreshed daily, queryable, governed. The data is
                trustworthy. But nobody is watching it proactively. And when they do look, they're
                looking backward.
              </p>
              <p className="text-slate-400 text-sm leading-relaxed max-w-3xl mt-3">
                Dashboards show you what happened. They don't watch for you. Alerts fire on
                thresholds without context — is this a blip or a trend? Is it one product line
                or systemic? You still need an analyst to figure out what it means.
              </p>
              <div className="mt-5 flex items-center gap-2 text-xs text-slate-500">
                <span className="inline-block w-1 h-1 rounded-full bg-slate-600" />
                87% of organizations have low BI/analytics maturity — Gartner
              </div>
            </motion.div>

            {/* Problem 2 */}
            <motion.div variants={fadeUp} className="mb-20">
              <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-4">The analysis gap</p>
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4 leading-snug">
                Deep analysis is locked behind consulting economics.
              </h2>
              <p className="text-slate-300 leading-relaxed mb-4 max-w-3xl">
                Structured root-cause analysis — the kind that isolates exactly where, when,
                and what changed — costs $500K+ and takes 12–24 weeks. You get one firm's
                perspective, a static deck, and monitoring stops when the engagement ends.
              </p>
              <p className="text-slate-400 text-sm leading-relaxed max-w-3xl">
                BI tools show you the "what" but not the "why." AI copilots generate
                plausible-sounding narratives but can't prove them — they don't run
                dimensional isolation against your actual data. You're choosing between
                expensive rigor and cheap guessing.
              </p>
              <div className="mt-5 flex items-center gap-2 text-xs text-slate-500">
                <span className="inline-block w-1 h-1 rounded-full bg-slate-600" />
                $500K–$2M per engagement, 12–24 weeks, one perspective
              </div>
            </motion.div>

            {/* Problem 3 */}
            <motion.div variants={fadeUp} className="mb-4">
              <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-4">The proof gap</p>
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4 leading-snug">
                Nobody can prove their decisions worked.
              </h2>
              <p className="text-slate-300 leading-relaxed mb-4 max-w-3xl">
                Every company claims to be data-driven. But ask "did that initiative actually
                move the KPI, or did the market recover on its own?" and nobody has an answer.
                Decisions get made, the team moves on, and outcomes are never traced back.
              </p>
              <p className="text-slate-400 text-sm leading-relaxed max-w-3xl">
                Attribution requires counterfactual thinking — what would have happened
                without the action? Dashboards can't do this. Even advanced analytics teams
                rarely set up control groups before acting.
              </p>
              <div className="mt-5 flex items-center gap-2 text-xs text-slate-500">
                <span className="inline-block w-1 h-1 rounded-full bg-slate-600" />
                Only 15% of AI decision-makers can tie value to P&L changes — Forrester 2026
              </div>
            </motion.div>

          </motion.div>
        </div>
      </section>

      {/* ── Transition ── */}
      <section className="py-16 px-6 border-t border-slate-800/40">
        <motion.div
          className="max-w-3xl mx-auto text-center"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <p className="text-2xl sm:text-3xl font-bold text-white leading-snug">
            What if you could close all three gaps —{' '}
            <span className="text-indigo-400">and prove it?</span>
          </p>
        </motion.div>
      </section>

      {/* ═══════════════════════════════════════════
          3. PRODUCT WALKTHROUGH ("See It In Action")
      ═══════════════════════════════════════════ */}
      <section id="walkthrough" className="py-28 px-6 bg-slate-900/30">
        <div className="max-w-5xl mx-auto">
          <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}>

            <motion.div variants={fadeUp} className="text-center mb-20">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">See it in action</h2>
              <p className="text-slate-400 max-w-xl mx-auto">
                Six AI-driven steps from detection to proof — with you in the loop at every decision point.
              </p>
            </motion.div>

            {/* Step 1 */}
            <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center mb-24">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
                    <Eye className="w-4 h-4 text-indigo-400" />
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-widest text-indigo-400">Step 01</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">AI-Driven Monitoring</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  AI agents watch your KPIs around the clock. When something meaningful
                  changes — not just a threshold breach, but a contextual shift — the system surfaces
                  a situation card with the analysis already started.
                </p>
              </div>
              <ScreenshotFrame label="Situation Awareness Console" src="/screenshots/01-situation-cards.png" />
            </motion.div>

            {/* Step 2 */}
            <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center mb-24">
              <div className="md:order-2">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
                    <Search className="w-4 h-4 text-indigo-400" />
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-widest text-indigo-400">Step 02</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">AI-Powered Root Cause Analysis</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  AI runs dimensional IS/IS NOT analysis to isolate exactly where, when, and what
                  changed — deterministically, against your real data. Not a chatbot
                  guessing. Structured diagnosis you can audit and challenge.
                </p>
              </div>
              <div className="md:order-1">
                <ScreenshotFrame label="Deep Analysis — Is / Is Not" src="/screenshots/02-deep-analysis.png" />
              </div>
            </motion.div>

            {/* Step 3 — Market Context (MA agent) */}
            <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center mb-24">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
                    <Globe className="w-4 h-4 text-indigo-400" />
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-widest text-indigo-400">Step 03</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">Automatic Market Context</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  AI scans external sources — competitor moves, industry trends, regulatory
                  shifts — and weaves market context directly into the analysis. You see
                  whether a problem is internal or part of a broader market pattern, without
                  commissioning separate research.
                </p>
              </div>
              <ScreenshotFrame label="Market Context" src="/screenshots/03-market-context.png" />
            </motion.div>

            {/* Step 4 — HITL Refinement */}
            <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center mb-24">
              <div className="md:order-2">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
                    <MessageCircle className="w-4 h-4 text-indigo-400" />
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-widest text-indigo-400">Step 04</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">You Refine, You Challenge</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  This isn't a black box. You ask follow-up questions, challenge assumptions,
                  and steer the analysis with your domain knowledge. The AI adapts — your
                  expertise shapes the outcome. Human-in-the-loop by design, not as an afterthought.
                </p>
              </div>
              <div className="md:order-1">
                <ScreenshotFrame label="Problem Refinement Chat" src="/screenshots/04-problem-refinement.png" />
              </div>
            </motion.div>

            {/* Step 5 — Multi-Perspective Recommendations */}
            <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center mb-24">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
                    <Users className="w-4 h-4 text-indigo-400" />
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-widest text-indigo-400">Step 05</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">AI-Synthesized Recommendations</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Three AI-driven strategic perspectives debate the best path forward — with visible
                  disagreement and trade-off analysis. You see where they agree, where they
                  don't, and why. Then you approve, reject, or refine.
                </p>
              </div>
              <ScreenshotFrame label="Council Debate" src="/screenshots/05-council-debate.png" />
            </motion.div>

            {/* Step 6 — Proof */}
            <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center">
              <div className="md:order-2">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-8 h-8 rounded-full bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center">
                    <LineChart className="w-4 h-4 text-emerald-400" />
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Step 06</span>
                </div>
                <h3 className="text-xl font-bold text-white mb-3">Proof It Worked</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  After you approve a solution, Decision Studio tracks what actually happened
                  versus what would have happened without action. Causal attribution — not
                  correlation. The first system that closes the accountability loop.
                </p>
              </div>
              <div className="md:order-1">
                <ScreenshotFrame label="Value Assurance Portfolio" src="/screenshots/06-portfolio.png" />
              </div>
            </motion.div>

          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          4. THE ACCOUNTABILITY LOOP
      ═══════════════════════════════════════════ */}
      <section className="py-28 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}>

            <motion.div variants={fadeUp} className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                The accountability loop
              </h2>
              <p className="text-slate-400 max-w-2xl mx-auto">
                Most tools stop at the recommendation. Decision Studio tracks three trajectories
                after every approved decision — so you know whether it actually worked.
              </p>
            </motion.div>

            <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">

              {/* Chart */}
              <div className="rounded-xl bg-slate-900/80 border border-slate-800/60 p-8">
                <TrajectoryMiniChart />
              </div>

              {/* Three lines explained */}
              <div className="space-y-6">
                <div className="flex items-start gap-4">
                  <div className="w-3 h-3 rounded-full bg-red-500 mt-1.5 flex-shrink-0" />
                  <div>
                    <p className="text-white font-semibold text-sm mb-1">Inaction trajectory</p>
                    <p className="text-slate-400 text-sm leading-relaxed">
                      What would have happened if you did nothing. Projected at approval, frozen — the cost of delay made visible.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-3 h-3 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                  <div>
                    <p className="text-white font-semibold text-sm mb-1">Expected recovery</p>
                    <p className="text-slate-400 text-sm leading-relaxed">
                      What the analysis predicted would happen if the solution works. Your hypothesis, tracked.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-4">
                  <div className="w-3 h-3 rounded-full bg-emerald-500 mt-1.5 flex-shrink-0" />
                  <div>
                    <p className="text-white font-semibold text-sm mb-1">Actual results</p>
                    <p className="text-slate-400 text-sm leading-relaxed">
                      What really happened — measured monthly, with causal attribution that separates your impact from market noise.
                    </p>
                  </div>
                </div>
              </div>

            </motion.div>

          </motion.div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <section className="py-16 px-6 border-y border-slate-800/40">
        <motion.div
          className="max-w-4xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-8"
          variants={stagger}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          <AnimatedStat value="5 days" suffix="" label="Onboarding to first insight" />
          <AnimatedStat value="3" suffix="×" label="Strategic perspectives" />
          <AnimatedStat value="100" suffix="%" label="Decision audit trail" />
          <AnimatedStat value="DiD" suffix="" label="Causal attribution" />
        </motion.div>
      </section>

      {/* ═══════════════════════════════════════════
          5. BUILT BY — credibility section
      ═══════════════════════════════════════════ */}
      <section className="py-20 px-6">
        <motion.div
          className="max-w-3xl mx-auto text-center"
          variants={stagger}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          <motion.p variants={fadeUp} className="text-slate-300 leading-relaxed mb-8">
            Decision Studio is built by a data &amp; analytics practitioner with 30+ years
            across enterprise IT — from ERP implementations to AI-driven decision systems.
            It exists because I saw the same pattern at every company: smart people making
            expensive decisions without structured analysis or any way to prove they worked.
          </motion.p>
          <motion.div variants={fadeUp} className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-slate-500">
            {[
              'ExxonMobil', 'Shell', 'Valvoline', 'Hess',
              'BCG', 'PwC',
              'Roche', 'McKesson', 'Teleflex',
              'Whirlpool', 'Panasonic', 'Commercial Metals',
              'Pilgrim\'s Pride', 'Cadence Design Systems',
            ].map((name) => (
              <span key={name} className="whitespace-nowrap">{name}</span>
            ))}
          </motion.div>
          <motion.p variants={fadeUp} className="text-slate-600 text-xs mt-6">
            Past client engagements in data, analytics, and enterprise systems.
          </motion.p>
        </motion.div>
      </section>

      {/* ═══════════════════════════════════════════
          6. REQUEST A CONVERSATION
      ═══════════════════════════════════════════ */}
      <section id="conversation" className="py-28 px-6">
        <div className="max-w-2xl mx-auto">
          <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true }}>

            <motion.div variants={fadeUp} className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Let's have a conversation
              </h2>
              <p className="text-slate-400 max-w-lg mx-auto mb-6">
                Not a sales call. A real conversation about the decisions your team is
                making and whether this approach could help.
              </p>
              <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
                <Shield className="w-3.5 h-3.5 text-slate-600" />
                <span>Human-in-the-loop by design. AI does the analysis — you make the decisions.</span>
              </div>
            </motion.div>

            <motion.div variants={fadeUp} className="rounded-2xl bg-slate-900/80 border border-slate-800/60 p-8">
              {submitted ? (
                <div className="text-center py-10">
                  <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
                  <h3 className="text-white font-semibold text-xl mb-2">Thank you.</h3>
                  <p className="text-slate-400 text-sm">
                    I'll reach out within a day or two to find a time that works.
                  </p>
                </div>
              ) : (
                <form onSubmit={onSubmit} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label htmlFor="name" className="block text-xs font-medium text-slate-400 mb-1.5">
                        Name <span className="text-indigo-400">*</span>
                      </label>
                      <input
                        id="name" name="name" type="text" required
                        value={form.name} onChange={onChange}
                        placeholder="Jane Smith"
                        className="w-full rounded-lg bg-slate-800 border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                      />
                    </div>
                    <div>
                      <label htmlFor="email" className="block text-xs font-medium text-slate-400 mb-1.5">
                        Email <span className="text-indigo-400">*</span>
                      </label>
                      <input
                        id="email" name="email" type="email" required
                        value={form.email} onChange={onChange}
                        placeholder="jane@company.com"
                        className="w-full rounded-lg bg-slate-800 border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="company" className="block text-xs font-medium text-slate-400 mb-1.5">
                      Company <span className="text-indigo-400">*</span>
                    </label>
                    <input
                      id="company" name="company" type="text" required
                      value={form.company} onChange={onChange}
                      placeholder="Acme Corp"
                      className="w-full rounded-lg bg-slate-800 border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                    />
                  </div>

                  <div>
                    <label htmlFor="message" className="block text-xs font-medium text-slate-400 mb-1.5">
                      What decisions are keeping you up at night?{' '}
                      <span className="text-slate-600">(optional)</span>
                    </label>
                    <textarea
                      id="message" name="message" rows={3}
                      value={form.message} onChange={onChange}
                      placeholder="e.g. We have 20+ KPIs in Snowflake views but nobody's watching them proactively..."
                      className="w-full rounded-lg bg-slate-800 border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition resize-none"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-colors"
                  >
                    Request a Conversation
                  </button>

                  <p className="text-center text-slate-500 text-xs pt-1">
                    No sales pitch. Just a conversation about whether this fits.
                  </p>
                </form>
              )}
            </motion.div>

          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          6. FOOTER
      ═══════════════════════════════════════════ */}
      <footer className="border-t border-slate-800/40 py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
          <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-6">
            <span className="font-bold text-white" style={font}>Decision Studio</span>
            <a href="mailto:info@trydecisionstudio.com" className="hover:text-slate-300 transition-colors">
              info@trydecisionstudio.com
            </a>
            <span>&copy; 2026 Decision Studio</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/how-it-works" className="text-slate-400 hover:text-white transition-colors">
              How It Works
            </Link>
            <Link to="/insights/bi-modernization" className="text-slate-400 hover:text-white transition-colors">
              Insights
            </Link>
            <Link to="/data-onboarding" className="text-slate-400 hover:text-white transition-colors">
              Data Onboarding
            </Link>
            <Link to="/login" className="text-slate-400 hover:text-white transition-colors flex items-center gap-1">
              Sign In <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </footer>

    </div>
  )
}
