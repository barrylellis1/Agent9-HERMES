import { useState, useRef, useEffect, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { motion, useScroll, useTransform } from 'framer-motion'
import {
  TrajectoryMiniChart,
  KPIGridAnimation,
  IsIsNotAnimation,
  MarketContextAnimation,
  RefinementChatAnimation,
  CouncilDebateAnimation,
} from '../components/animations/AgentAnimations'
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

// LANDING PAGE ALTERNATE (Redesign)
// ═══════════════════════════════════════════════════
export function LandingPageAlternate() {
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
            The data is there. The pressure is on.{' '}
            <span className="text-indigo-400">So why are decisions still made the same way?</span>
          </motion.h1>

          <motion.p
            variants={fadeUp}
            className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto mb-12 leading-relaxed"
          >
            Regardless of your data maturity, executives must act now. Decision Studio is the 
            only platform focused on end-to-end decision making — delivering regimented analysis, 
            market context, and provable outcomes that reinforce your strategy over time.
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
          1b. THE GAPS (bridge)
      ═══════════════════════════════════════════ */}
      <section className="py-24 px-6 border-t border-slate-800/40">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
            <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}>
              <motion.p variants={fadeUp} className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-4">
                The decision execution gap
              </motion.p>
              <motion.h2 variants={fadeUp} className="text-2xl font-bold text-white mb-4 leading-snug">
                Your board wants AI that moves the P&amp;L. Not another chatbot.
              </motion.h2>
              <motion.p variants={fadeUp} className="text-slate-300 text-sm leading-relaxed mb-4">
                Every executive team is under pressure to show AI investment. But most options —
                copilots, assistants, prompt playgrounds — just generate text and can't tie their 
                output to a financial outcome. Decision Studio is different. It delivers an unbroken 
                chain of accountability from anomaly detection to root-cause diagnosis to proven ROI.
              </motion.p>
            </motion.div>

            <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}>
              <motion.p variants={fadeUp} className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-4">
                The speed of instinct
              </motion.p>
              <motion.h2 variants={fadeUp} className="text-2xl font-bold text-white mb-4 leading-snug">
                Rigorous analysis at the speed of human reaction.
              </motion.h2>
              <motion.p variants={fadeUp} className="text-slate-300 text-sm leading-relaxed mb-4">
                When executives don't have time for a twelve-week consulting engagement, they revert to instinct. 
                Decision Studio changes the economics. It orchestrates structured root-cause isolation and 
                causal attribution — with you guiding every step — in the time it takes to finish a cup of coffee.
              </motion.p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          2. THE THREE PROBLEMS (Redesigned Grid)
      ═══════════════════════════════════════════ */}
      <section className="py-28 px-6 bg-slate-900/30 border-t border-slate-800/40">
        <div className="max-w-6xl mx-auto">
          <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}>
            
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">The mid-market reality</h2>
              <p className="text-slate-400 max-w-2xl mx-auto text-lg">
                You have governed data, but you don't have an army of analysts. That creates three critical gaps in how decisions get made.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {/* Problem 1 */}
              <motion.div variants={fadeUp} className="p-8 rounded-2xl bg-slate-950 border border-slate-800/60 relative overflow-hidden group flex flex-col">
                <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-6">
                  <Eye className="w-5 h-5 text-indigo-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">The monitoring gap</h3>
                <p className="text-slate-300 text-sm leading-relaxed mb-6">
                  You're always reacting, never anticipating. Your KPIs get reviewed monthly. Dashboards show you what happened, but nobody is proactively watching them. By the time someone spots a margin drop, it's already expensive.
                </p>
                <div className="mt-auto pt-5 border-t border-slate-800/50 flex items-center gap-2 text-xs text-slate-500">
                  <span className="w-1 h-1 rounded-full bg-slate-600" />
                  87% of organizations have low BI maturity
                </div>
              </motion.div>

              {/* Problem 2 */}
              <motion.div variants={fadeUp} className="p-8 rounded-2xl bg-slate-950 border border-slate-800/60 relative overflow-hidden group flex flex-col">
                <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-6">
                  <Search className="w-5 h-5 text-indigo-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">The analysis gap</h3>
                <p className="text-slate-300 text-sm leading-relaxed mb-6">
                  Deep analysis requires resources you don't have. It traditionally requires an army of analysts or a $500K consulting engagement. You're forced to choose between expensive rigor and cheap guessing.
                </p>
                <div className="mt-auto pt-5 border-t border-slate-800/50 flex items-center gap-2 text-xs text-slate-500">
                  <span className="w-1 h-1 rounded-full bg-slate-600" />
                  Enterprise rigor for lean teams
                </div>
              </motion.div>

              {/* Problem 3 */}
              <motion.div variants={fadeUp} className="p-8 rounded-2xl bg-slate-950 border border-slate-800/60 relative overflow-hidden group flex flex-col">
                <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-6">
                  <LineChart className="w-5 h-5 text-emerald-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">The proof gap</h3>
                <p className="text-slate-300 text-sm leading-relaxed mb-6">
                  Nobody can prove their decisions worked. Attribution requires tracking the Cost of Inaction versus recovery. Even advanced analytics teams rarely set up control groups before acting to separate impact from market noise.
                </p>
                <div className="mt-auto pt-5 border-t border-slate-800/50 flex items-center gap-2 text-xs text-slate-500">
                  <span className="w-1 h-1 rounded-full bg-emerald-600" />
                  Only 15% can tie AI to P&L changes
                </div>
              </motion.div>
            </div>

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
      <section id="walkthrough" className="py-28 px-6 bg-slate-900/30 border-t border-slate-800/40">
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
              <KPIGridAnimation />
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
                <IsIsNotAnimation />
              </div>
            </motion.div>

            {/* Step 3 */}
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
              <MarketContextAnimation />
            </motion.div>

            {/* Step 4 */}
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
                <RefinementChatAnimation />
              </div>
            </motion.div>

            {/* Step 5 */}
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
              <CouncilDebateAnimation />
            </motion.div>

          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          4. STEP 06 — PROOF IT WORKED
      ═══════════════════════════════════════════ */}
      <section className="py-28 px-6 border-t border-slate-800/40">
        <div className="max-w-5xl mx-auto">
          <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}>

            <motion.div variants={fadeUp} className="mb-16">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-8 h-8 rounded-full bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center">
                  <LineChart className="w-4 h-4 text-emerald-400" />
                </div>
                <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Step 06</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Proof it worked.
              </h2>
              <p className="text-slate-300 max-w-2xl leading-relaxed">
                After you approve a solution, Decision Studio tracks three trajectories — so you
                know whether your decision actually moved the KPI, or whether the market recovered
                on its own. Most tools stop at the recommendation. This closes the loop.
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
                      What really happened — measured monthly, with causal attribution that separates your decision's impact from market noise.
                    </p>
                  </div>
                </div>
              </div>

              <motion.div variants={fadeUp} className="md:col-span-2 mt-6 pt-8 border-t border-slate-800/40">
                <p className="text-xs font-semibold uppercase tracking-widest text-emerald-400 mb-3">
                  The compounding effect
                </p>
                <p className="text-slate-300 text-sm leading-relaxed max-w-2xl">
                  Over time, this feedback loop does something more powerful than attribution.
                  Every approved solution, tracked outcome, and verified ROI becomes part of the
                  Registry — a compounding institutional memory. Executive intuition, trained on
                  verified outcomes rather than market noise, becomes progressively more accurate.
                  When leadership changes, the organization doesn't reset. It inherits a verified
                  playbook of what actually worked, and the causal evidence to distinguish strategy
                  from luck. Decision quality compounds.
                </p>
              </motion.div>

            </motion.div>

          </motion.div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <section className="py-16 px-6 border-y border-slate-800/40 bg-slate-900/30">
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
          5. BUILT BY — Enterprise Pedigree section
      ═══════════════════════════════════════════ */}
      <section className="py-24 px-6 border-b border-slate-800/40">
        <motion.div
          className="max-w-4xl mx-auto text-center"
          variants={stagger}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
        >
          <motion.p variants={fadeUp} className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-6">
            Enterprise Pedigree
          </motion.p>
          <motion.h2 variants={fadeUp} className="text-2xl sm:text-3xl font-bold text-white mb-6 leading-snug">
            Architected for scale. Informed by the Fortune 500.
          </motion.h2>
          <motion.p variants={fadeUp} className="text-slate-300 leading-relaxed mb-10 max-w-2xl mx-auto text-lg">
            Decision Studio's intelligence engine is informed by 30+ years of enterprise engagements 
            designing data platforms, ERP implementations, and decision support systems for the world's most complex organizations.
          </motion.p>
          <motion.div variants={fadeUp} className="flex flex-wrap items-center justify-center gap-x-8 gap-y-4 text-sm font-semibold tracking-wide text-slate-500">
            {[
              'EXXONMOBIL', 'SHELL', 'VALVOLINE', 'HESS',
              'BCG', 'PWC',
              'ROCHE', 'MCKESSON', 'TELEFLEX',
              'WHIRLPOOL', 'PANASONIC', 'COMMERCIAL METALS',
              'PILGRIM\'S PRIDE', 'CADENCE',
            ].map((name) => (
              <span key={name} className="whitespace-nowrap">{name}</span>
            ))}
          </motion.div>
          <motion.p variants={fadeUp} className="text-slate-600 text-xs mt-8 font-medium uppercase tracking-wider">
            Past client engagements informing platform architecture
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