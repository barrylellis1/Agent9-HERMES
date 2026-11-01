import { useState, useRef, useEffect } from 'react'
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
  ChevronRight,
  Eye,
  Globe,
  MessageCircle,
  Search,
  Shield,
  Users,
  LineChart,
} from 'lucide-react'
import { usePageMeta } from '../utils/pageMeta'

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

const closedLoopProofPoints = [
  {
    label: 'Consultants recommend action',
    title: 'Decision Studio measures whether it worked.',
    copy: 'Each approved action is tracked against what inaction would have cost, what was expected, and what actually happened, compared with the parts of the business it did not touch.',
    icon: <LineChart className="w-5 h-5 text-emerald-400" />,
  },
  {
    label: 'Decisions go unrecorded',
    title: 'Decision Studio keeps the decision record.',
    copy: 'What was decided, by whom, on what evidence, and what it was betting on. The record is written at approval, before the result is known.',
    icon: <Shield className="w-5 h-5 text-indigo-400" />,
  },
  {
    label: 'Decision ownership drifts',
    title: 'Decision Studio names the accountable owner.',
    copy: 'Every KPI has a named owner before monitoring begins, so each situation reaches the person responsible for it.',
    icon: <Users className="w-5 h-5 text-emerald-400" />,
  },
  {
    label: 'A KPI moves',
    title: 'Decision Studio finds where the change came from.',
    copy: 'Dimensional IS/IS NOT analysis isolates where, when, and what changed in the underlying data.',
    icon: <Search className="w-5 h-5 text-indigo-400" />,
  },
]

// LANDING PAGE ALTERNATE (Redesign)
// ═══════════════════════════════════════════════════
export function LandingPageAlternate() {
  useSatoshiFont()
  usePageMeta({
    title: 'Decision Studio | An Independent Record of Whether Decisions Worked',
    description: 'Decision Studio records each business decision, what it was based on and what it was betting on, then measures whether it worked.',
    path: '/',
  })
  const councilCaseStudyVideoSrc = 'https://customer-erkp1ybr2e8wokyn.cloudflarestream.com/ab19f3317eeb53efeeb3a6dd516b6ae9/iframe'

  // Nav opacity on scroll
  const [navSolid, setNavSolid] = useState(false)
  useEffect(() => {
    const onScroll = () => setNavSolid(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    const targetId = window.location.hash.replace('#', '')
    if (!targetId) return
    window.setTimeout(() => scrollTo(targetId), 0)
  }, [])

  // Parallax for hero gradient
  const heroRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ['start start', 'end start'] })
  const gradientY = useTransform(scrollYProgress, [0, 1], ['0%', '40%'])

  const [showCouncilVideo, setShowCouncilVideo] = useState(false)

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
            className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.1] tracking-tight text-white mb-6 text-balance"
          >
            An independent record of{' '}
            <span className="text-indigo-400">whether each decision worked.</span>
          </motion.h1>

          <motion.p
            variants={fadeUp}
            className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto mb-8 leading-relaxed"
          >
            When a KPI moves, Decision Studio finds where the change came from, sets out
            options, and records the decision your team approves. Then it measures the result
            against the parts of the business the decision did not touch, so you can tell your
            effect from the market&apos;s. Built for mid-market leadership teams.
          </motion.p>

          <motion.div
            variants={fadeUp}
            className="mb-10 flex flex-wrap items-center justify-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400"
          >
            {['Detect', 'Diagnose', 'Debate', 'Approve', 'Measure'].map((step, index) => (
              <div key={step} className="flex items-center gap-2">
                <span className="rounded-full border border-slate-700/70 bg-slate-900/80 px-3 py-1.5 text-slate-300">
                  {step}
                </span>
                {index < 4 && <ChevronRight className="h-3.5 w-3.5 text-slate-600" />}
              </div>
            ))}
          </motion.div>

          <motion.div
            variants={fadeUp}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <button
              onClick={() => scrollTo('walkthrough')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors text-sm flex items-center justify-center gap-2"
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
                Your board wants measurable impact. Not another AI experiment.
              </motion.h2>
              <motion.p variants={fadeUp} className="text-slate-300 text-sm leading-relaxed mb-4">
                Every executive team is under pressure to show a return on AI investment. Most AI
                tools, from copilots to assistants, produce text and stop there. Decision Studio
                links each KPI movement to its diagnosis, the action you approved, and the measured
                result.
              </motion.p>
              <motion.a
                variants={fadeUp}
                href="https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai"
                target="_blank"
                rel="noreferrer"
                className="flex items-start gap-2 text-xs leading-relaxed text-slate-500 hover:text-slate-300 transition-colors"
              >
                <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-slate-600" />
                McKinsey 2025: 88% report regular AI use, but only 39% report enterprise-level EBIT impact.
              </motion.a>
            </motion.div>

            <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}>
              <motion.p variants={fadeUp} className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-4">
                The speed of instinct
              </motion.p>
              <motion.h2 variants={fadeUp} className="text-2xl font-bold text-white mb-4 leading-snug">
                Rigorous analysis before instinct takes over.
              </motion.h2>
              <motion.p variants={fadeUp} className="text-slate-300 text-sm leading-relaxed mb-4">
                When executives don't have time for a twelve-week consulting engagement, they revert to instinct. 
                Decision Studio changes the economics. It orchestrates structured root-cause isolation and 
                weighed action options — with you guiding every step — in the time it takes to finish a cup of coffee.
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
                  You're always reacting, never anticipating. Your KPIs get reviewed monthly. Periodic reporting shows what happened, but nobody is proactively watching for the moment that needs action. By the time someone spots a margin drop, it's already expensive.
                </p>
                <div className="mt-auto pt-5 border-t border-slate-800/50 flex items-center gap-2 text-xs text-slate-500">
                  <span className="w-1 h-1 rounded-full bg-slate-600" />
                  Monitoring without ownership leaves issues late
                </div>
              </motion.div>

              {/* Problem 2 */}
              <motion.div variants={fadeUp} className="p-8 rounded-2xl bg-slate-950 border border-slate-800/60 relative overflow-hidden group flex flex-col">
                <div className="w-12 h-12 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mb-6">
                  <Search className="w-5 h-5 text-indigo-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">The analysis gap</h3>
                <p className="text-slate-300 text-sm leading-relaxed mb-6">
                  Deep analysis requires resources lean teams often don't have. It traditionally requires analyst bandwidth or an outside advisory engagement. You're forced to choose between expensive rigor and cheap guessing.
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
                  Outcome measurement is the missing layer
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
            <span className="text-indigo-400">and measure the result?</span>
          </p>
        </motion.div>
      </section>

      {/* Closed loop differentiation */}
      <section className="py-24 px-6 bg-slate-900/30 border-t border-slate-800/40">
        <div className="max-w-6xl mx-auto">
          <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}>
            <motion.div variants={fadeUp} className="mb-14 max-w-3xl">
              <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-4">
                The closed loop
              </p>
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                One record, from KPI movement to measured result.
              </h2>
              <p className="text-slate-300 leading-relaxed">
                Decision Studio leaves the judgment to your executives. It keeps the evidence,
                the decision and the outcome together: what changed, what caused it, which options
                were weighed, what you approved, and what happened next. It measures decisions it
                did not make, so the verdict is independent of the people who made them.
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {closedLoopProofPoints.map((point) => (
                <motion.div
                  key={point.label}
                  variants={fadeUp}
                  className="rounded-xl border border-slate-800/60 bg-slate-950 p-6"
                >
                  <div className="mb-5 flex h-10 w-10 items-center justify-center rounded-full border border-slate-800 bg-slate-900">
                    {point.icon}
                  </div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-slate-500">
                    {point.label}
                  </p>
                  <h3 className="mb-3 text-xl font-bold text-white">{point.title}</h3>
                  <p className="text-sm leading-relaxed text-slate-400">{point.copy}</p>
                </motion.div>
              ))}
            </div>

            <motion.div
              variants={fadeUp}
              className="mt-8 rounded-xl border border-emerald-600/20 bg-emerald-950/20 px-6 py-5"
            >
              <p className="text-sm leading-relaxed text-emerald-100">
                Trust posture: AI performs analysis and synthesis. Executives approve, reject,
                or refine. Every approved action enters outcome tracking with an audit trail.
              </p>
              <a
                href="https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027"
                target="_blank"
                rel="noreferrer"
                className="mt-3 flex items-start gap-2 text-xs leading-relaxed text-emerald-200/70 hover:text-emerald-100 transition-colors"
              >
                <span className="mt-1.5 h-1 w-1 flex-shrink-0 rounded-full bg-emerald-500/70" />
                Gartner predicts over 40% of agentic AI projects will be canceled by the end of 2027 due to cost, unclear value, or inadequate risk controls.
              </a>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Product walkthrough */}
      <section id="walkthrough" className="py-28 px-6 bg-slate-900/30 border-t border-slate-800/40">
        <div className="max-w-5xl mx-auto">
          <motion.div variants={stagger} initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }}>

            <motion.div variants={fadeUp} className="text-center mb-20">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">See it in action</h2>
              <p className="text-slate-400 max-w-xl mx-auto">
                The operating sequence from detection to measured outcome, with you in the loop at every decision point.
              </p>
            </motion.div>

            {/* Setup beat — accountability before action */}
            <motion.div
              id="council-video"
              variants={fadeUp}
              className="mb-20 rounded-2xl border border-indigo-600/20 bg-slate-950/70 p-6 sm:p-7"
            >
              <div className="max-w-3xl">
                <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-indigo-400">
                  Illustrative scenario
                </p>
                <h3 className="mb-3 text-2xl font-bold text-white">Watch the full decision loop</h3>
                <p className="text-sm leading-relaxed text-slate-300">
                  This narrated walkthrough follows a fictional 50-location coffee chain from dashboard
                  symptom to measured outcome: the drop is detected, the cause is isolated,
                  the council debates conflicting actions, a human approves the move, and
                  Value Assurance measures whether it worked.
                </p>
              </div>

              {!showCouncilVideo ? (
                <div className="mt-6">
                  <button
                    type="button"
                    onClick={() => setShowCouncilVideo(true)}
                    className="inline-flex items-center gap-2 rounded-lg border border-slate-700/60 bg-slate-900 px-4 py-2.5 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-800 hover:text-white"
                  >
                    Watch the scenario
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="mt-6 overflow-hidden rounded-xl border border-slate-800/60 bg-black">
                  <iframe
                    title="Illustrative scenario: the full decision loop"
                    src={councilCaseStudyVideoSrc}
                    className="aspect-video w-full"
                    style={{ border: 'none' }}
                    allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture;"
                    allowFullScreen
                  />
                </div>
              )}
            </motion.div>

            <motion.div variants={fadeUp} className="mb-20 max-w-3xl mx-auto">
              <div className="rounded-2xl border border-emerald-600/30 bg-emerald-950/30 p-6 sm:p-7">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 rounded-full bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center">
                    <Users className="w-4 h-4 text-emerald-400" />
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-widest text-emerald-400">
                    Setup — Before Step 01
                  </span>
                </div>
                <h3 className="text-xl font-bold text-white mb-2">
                  Every KPI gets an owner — before the first scan.
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  A guided accountability interview walks an administrator through assigning every
                  KPI to a named owner across the leadership team. Every surfaced situation card has
                  a responsible principal before analysis begins.
                </p>
              </div>
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
                <h3 className="text-xl font-bold text-white mb-3">Situation Detection</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Each assessment checks every KPI you have enabled against its thresholds and its
                  own recent history. When something meaningful changes, including a trend that
                  has not yet crossed a threshold, it raises a situation with the diagnosis
                  already started.
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
                <h3 className="text-xl font-bold text-white mb-3">Diagnostic Isolation</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Dimensional IS/IS NOT analysis isolates exactly where, when, and what
                  changed — deterministically, against your real data. Not a chatbot
                  guessing. A structured diagnostic exhibit you can audit and challenge.
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
                <h3 className="text-xl font-bold text-white mb-3">External Context</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  The analysis adds market context relevant to the KPI: industry trends, competitor
                  behavior and regulatory factors. You see whether a problem looks internal or part
                  of a broader market pattern before you decide what to do about it.
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
                <h3 className="text-xl font-bold text-white mb-3">Executive Review</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  This isn't a black box. You ask follow-up questions, challenge assumptions,
                  and steer the analysis with your domain knowledge. The briefing adapts as
                  your expertise shapes the outcome. Human-in-the-loop by design, not as an afterthought.
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
                <h3 className="text-xl font-bold text-white mb-3">Decision Options</h3>
                <p className="text-slate-300 text-sm leading-relaxed">
                  Three perspectives, each working from a different angle, propose options and
                  compare their trade-offs. You see where they agree, where they don&apos;t, and why.
                  Then you approve, reject, or refine.
                </p>
              </div>
              <CouncilDebateAnimation />
            </motion.div>

          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          4. STEP 06 — MEASURE WHETHER IT WORKED
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
                Measure whether it worked.
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
                      What really happened — measured monthly, and compared with segments the decision did not touch, to separate its effect from market noise.
                    </p>
                  </div>
                </div>
              </div>

              <motion.div variants={fadeUp} className="md:col-span-2 mt-6 pt-8 border-t border-slate-800/40">
                <h3 className="text-xl font-bold text-white mb-3">
                  Every decision leaves a record.
                </h3>
                <p className="text-slate-300 text-sm leading-relaxed max-w-2xl mb-4">
                  When you approve a recommendation, Decision Studio writes down what it is betting
                  on: which driver should move, by how much, and why. When the result comes in, each
                  bet is marked as held up or did not hold. A link between two KPIs counts as tested
                  only after a measured decision supports it.
                </p>
                <p className="text-slate-400 text-sm leading-relaxed max-w-2xl">
                  Where this is heading: those records add up to a map of what drives your
                  business, built from your own decisions and their measured outcomes. The map
                  starts nearly empty and fills with use, and it always shows which links are
                  tested and which are still assumptions.
                </p>
              </motion.div>

            </motion.div>

          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          6. FOOTER
      ═══════════════════════════════════════════ */}
      <footer className="border-t border-slate-800/40 py-10 px-6">
        <div className="max-w-6xl mx-auto">
          <p className="text-center text-xs text-slate-600 mb-6">
            Decision Studio is in development. Examples on this site use illustrative data.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
            <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-6">
              <span className="font-bold text-white" style={font}>Decision Studio</span>
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
        </div>
      </footer>

    </div>
  )
}
