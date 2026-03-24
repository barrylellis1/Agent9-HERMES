import { useState, useEffect, useRef, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  AlertTriangle,
  MessageSquare,
  TrendingDown,
  Database,
  Radar,
  Target,
  Shield,
  Brain,
  Archive,
  TrendingUp,
  LineChart,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ChevronRight,
} from 'lucide-react'

// ─────────────────────────────────────────────────
// Animation variants
// ─────────────────────────────────────────────────
const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.55, ease: 'easeOut' } },
}

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12 } },
}

// ─────────────────────────────────────────────────
// Smooth-scroll helper
// ─────────────────────────────────────────────────
function scrollTo(id: string) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// ─────────────────────────────────────────────────
// Comparison cell helpers
// ─────────────────────────────────────────────────
function Yes() {
  return <CheckCircle2 className="w-5 h-5 text-emerald-400 mx-auto" />
}
function No() {
  return <XCircle className="w-5 h-5 text-slate-600 mx-auto" />
}
function Partial({ label }: { label?: string }) {
  return (
    <span className="flex items-center justify-center gap-1">
      <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
      {label && <span className="text-amber-400 text-xs">{label}</span>}
    </span>
  )
}

// ─────────────────────────────────────────────────
// LandingPage
// ─────────────────────────────────────────────────
export function LandingPage() {
  // Nav transparency on scroll
  const [navSolid, setNavSolid] = useState(false)

  useEffect(() => {
    function handleScroll() {
      setNavSolid(window.scrollY > 60)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Demo form state
  const [form, setForm] = useState({
    name: '',
    company: '',
    role: '',
    email: '',
    problem: '',
  })
  const [submitted, setSubmitted] = useState(false)

  function handleFormChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitted(true)
  }

  // Ref for form section (for scrolling)
  const demoRef = useRef<HTMLDivElement>(null)

  return (
    <div className="min-h-screen bg-slate-950 text-white" style={{ scrollBehavior: 'smooth' }}>

      {/* ── Navigation ── */}
      <nav
        className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
          navSolid ? 'bg-slate-950/95 backdrop-blur border-b border-slate-800' : 'bg-transparent'
        }`}
      >
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-lg font-bold tracking-tight text-white">
            Decision Studio
          </span>
          <Link
            to="/login"
            className="text-sm text-slate-400 hover:text-white transition-colors flex items-center gap-1"
          >
            Sign In <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </nav>

      {/* ══════════════════════════════════════════
          1. HERO
      ══════════════════════════════════════════ */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-6 pt-24 pb-20 overflow-hidden">
        {/* Background radial glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 50% 30%, rgba(99,102,241,0.12) 0%, transparent 70%)',
          }}
        />

        <motion.div
          className="relative max-w-4xl text-center"
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={fadeUp}>
            <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/25 text-indigo-300 text-xs font-medium mb-8">
              AI-Powered Decision Intelligence
            </span>
          </motion.div>

          <motion.h1
            variants={fadeUp}
            className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight tracking-tight text-white mb-6"
          >
            Your executives deserve a{' '}
            <span className="text-indigo-400">decision intelligence team.</span>
            <br className="hidden sm:block" /> Not another dashboard.
          </motion.h1>

          <motion.p
            variants={fadeUp}
            className="text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Continuous KPI monitoring, structured root cause analysis, and
            multi-perspective recommendations — with a full audit trail. Any
            domain. In hours, not weeks.
          </motion.p>

          <motion.div
            variants={fadeUp}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <button
              onClick={() => scrollTo('request-demo')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors text-sm shadow-lg shadow-indigo-900/40"
            >
              Request a Demo
            </button>
            <button
              onClick={() => scrollTo('how-it-works')}
              className="w-full sm:w-auto px-8 py-3.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold transition-colors text-sm border border-slate-700"
            >
              See How It Works
            </button>
          </motion.div>
        </motion.div>
      </section>

      {/* ══════════════════════════════════════════
          2. THE PROBLEM
      ══════════════════════════════════════════ */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <motion.div variants={fadeUp} className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                The world changed. Decision-making didn't.
              </h2>
              <p className="text-slate-400 max-w-xl mx-auto">
                Three forces are converging — and most companies aren't ready.
              </p>
            </motion.div>

            <motion.div
              variants={staggerContainer}
              className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-14"
            >
              {[
                {
                  icon: <AlertTriangle className="w-6 h-6 text-amber-400" />,
                  title: 'Consulting-quality analysis — in hours, not weeks',
                  desc: 'MBB-grade structured analysis (root cause, multi-perspective debate, trade-off matrix) was either too expensive or took months. AI makes it actionable in hours — for every decision, not just the ones worth a $2M engagement.',
                },
                {
                  icon: <TrendingDown className="w-6 h-6 text-amber-400" />,
                  title: 'AI adoption is accelerating market change',
                  desc: 'Your competitors are adopting AI to ship faster, reprice faster, restructure faster. The quarterly review cycle is already obsolete. Companies that still decide on monthly cadences are playing chess by mail.',
                },
                {
                  icon: <MessageSquare className="w-6 h-6 text-amber-400" />,
                  title: '"Data-driven" is unproven — until now',
                  desc: 'Every company claims to be data-driven. None can prove their data-informed decisions actually worked. No baseline, no tracking, no attribution. Decision Studio is the first system that closes the loop.',
                },
              ].map((card) => (
                <motion.div
                  key={card.title}
                  variants={fadeUp}
                  className="rounded-xl bg-slate-900 border border-slate-800 p-6"
                >
                  <div className="mb-4">{card.icon}</div>
                  <h3 className="text-white font-semibold text-lg mb-2">{card.title}</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">{card.desc}</p>
                </motion.div>
              ))}
            </motion.div>

            <motion.p
              variants={fadeUp}
              className="text-slate-400 italic text-base max-w-2xl mx-auto border-l-2 border-indigo-600 pl-5 text-left"
            >
              "Stop claiming you're data-driven. Start proving it."
            </motion.p>
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          3. HOW IT WORKS
      ══════════════════════════════════════════ */}
      <section id="how-it-works" className="py-24 px-6 bg-slate-900/50">
        <div className="max-w-6xl mx-auto">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <motion.div variants={fadeUp} className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                How it works
              </h2>
              <p className="text-slate-400 max-w-xl mx-auto">
                Three steps from raw data to a tracked, approved decision.
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  step: '01',
                  icon: <Database className="w-7 h-7 text-indigo-400" />,
                  title: 'Connect Your Data',
                  desc: 'SAP, Oracle, Snowflake, or a CSV extract. 5-day onboarding.',
                },
                {
                  step: '02',
                  icon: <Radar className="w-7 h-7 text-indigo-400" />,
                  title: 'Continuous Monitoring',
                  desc: 'KPI breaches and opportunities detected automatically. Situation cards appear on your dashboard.',
                },
                {
                  step: '03',
                  icon: <Target className="w-7 h-7 text-indigo-400" />,
                  title: 'Structured Decisions, Tracked Outcomes',
                  desc: 'Root cause analysis, multi-perspective solution debate, approval workflow. Then trajectory tracking proves whether it worked.',
                },
              ].map((item, i) => (
                <motion.div
                  key={item.step}
                  variants={fadeUp}
                  className="relative"
                >
                  {/* Connector line — visible between steps on desktop */}
                  {i < 2 && (
                    <div className="hidden md:block absolute top-8 left-[calc(100%+1px)] w-8 border-t border-dashed border-slate-700" />
                  )}
                  <div className="rounded-xl bg-slate-900 border border-slate-800 p-7 h-full">
                    <div className="text-xs font-bold text-indigo-500 mb-4 tracking-widest">
                      STEP {item.step}
                    </div>
                    <div className="mb-4">{item.icon}</div>
                    <h3 className="text-white font-semibold text-lg mb-3">{item.title}</h3>
                    <p className="text-slate-400 text-sm leading-relaxed">{item.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          4. FIVE PILLARS
      ══════════════════════════════════════════ */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <motion.div variants={fadeUp} className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Five pillars of decision intelligence
              </h2>
            </motion.div>

            <motion.div
              variants={staggerContainer}
              className="grid grid-cols-1 sm:grid-cols-2 gap-5"
            >
              {[
                {
                  icon: <Shield className="w-5 h-5 text-emerald-400" />,
                  title: 'Always-On Monitoring',
                  desc: 'Problems and opportunities detected before you ask the question.',
                },
                {
                  icon: <Brain className="w-5 h-5 text-indigo-400" />,
                  title: 'Consulting-Quality Insight',
                  desc: 'SCQA analysis + multi-perspective debate in hours, not weeks.',
                },
                {
                  icon: <Archive className="w-5 h-5 text-indigo-400" />,
                  title: 'Institutional Memory',
                  desc: 'KPI definitions and decision rationale that survive executive turnover.',
                },
                {
                  icon: <TrendingUp className="w-5 h-5 text-emerald-400" />,
                  title: 'Opportunity Detection',
                  desc: 'Outperformance spotted and captured, not just problems fixed.',
                },
                {
                  icon: <LineChart className="w-5 h-5 text-indigo-400" />,
                  title: 'Proven ROI',
                  desc: 'Trajectory tracking shows whether each decision actually worked.',
                },
              ].map((pillar) => (
                <motion.div
                  key={pillar.title}
                  variants={fadeUp}
                  className="flex items-start gap-4 rounded-xl bg-slate-900 border border-slate-800 px-6 py-5"
                >
                  <div className="mt-0.5 flex-shrink-0">{pillar.icon}</div>
                  <div>
                    <p className="text-white font-semibold text-sm mb-1">{pillar.title}</p>
                    <p className="text-slate-400 text-sm leading-relaxed">{pillar.desc}</p>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          5. COMPARISON TABLE
      ══════════════════════════════════════════ */}
      <section className="py-24 px-6 bg-slate-900/50">
        <div className="max-w-5xl mx-auto">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <motion.div variants={fadeUp} className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                How we compare
              </h2>
              <p className="text-slate-400 max-w-xl mx-auto">
                Traditional consulting is too slow. Generic AI lacks structure and accountability.
                Decision Studio closes the gap.
              </p>
            </motion.div>

            <motion.div variants={fadeUp} className="overflow-x-auto rounded-xl border border-slate-800">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-900 border-b border-slate-800">
                    <th className="text-left px-5 py-4 text-slate-400 font-medium w-48">
                      Capability
                    </th>
                    <th className="px-5 py-4 text-center text-indigo-300 font-semibold">
                      Decision Studio
                    </th>
                    <th className="px-5 py-4 text-center text-slate-400 font-medium">
                      Traditional Consulting
                    </th>
                    <th className="px-5 py-4 text-center text-slate-400 font-medium">
                      Generic AI
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    {
                      cap: 'Multi-perspective debate',
                      ds: <Yes />,
                      tc: <No />,
                      ga: <No />,
                      tcNote: 'One firm',
                    },
                    {
                      cap: 'Full audit trail',
                      ds: <Yes />,
                      tc: <No />,
                      ga: <No />,
                    },
                    {
                      cap: 'On-demand, 24/7',
                      ds: <Yes />,
                      tc: <No />,
                      ga: <Yes />,
                    },
                    {
                      cap: 'Human-in-the-loop',
                      ds: <Yes />,
                      tc: <Yes />,
                      ga: <Partial />,
                    },
                    {
                      cap: 'Post-decision ROI tracking',
                      ds: <Yes />,
                      tc: <No />,
                      ga: <No />,
                    },
                    {
                      cap: 'Opportunity detection',
                      ds: <Yes />,
                      tc: <Partial label="Ad hoc" />,
                      ga: <No />,
                    },
                    {
                      cap: 'Time to first insight',
                      ds: <span className="text-emerald-400 font-medium block text-center">Hours</span>,
                      tc: <span className="text-slate-400 block text-center">4–8 weeks</span>,
                      ga: <span className="text-slate-400 block text-center">Hours</span>,
                    },
                    {
                      cap: 'Annual cost',
                      ds: <span className="text-emerald-400 font-medium block text-center">$44K–$100K</span>,
                      tc: <span className="text-slate-400 block text-center">$500K–$3M</span>,
                      ga: <span className="text-slate-400 block text-center">$20K–$50K</span>,
                    },
                  ].map((row, i) => (
                    <tr
                      key={row.cap}
                      className={`border-b border-slate-800 last:border-0 ${
                        i % 2 === 0 ? 'bg-slate-950' : 'bg-slate-900/40'
                      }`}
                    >
                      <td className="px-5 py-3.5 text-slate-300">{row.cap}</td>
                      <td className="px-5 py-3.5">{row.ds}</td>
                      <td className="px-5 py-3.5">{row.tc}</td>
                      <td className="px-5 py-3.5">{row.ga}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          6. PRICING
      ══════════════════════════════════════════ */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <motion.div variants={fadeUp} className="text-center mb-14">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Simple, transparent pricing
              </h2>
              <p className="text-slate-400 max-w-xl mx-auto">
                Two engagement models. Both include dedicated setup and onboarding.
              </p>
            </motion.div>

            <motion.div
              variants={staggerContainer}
              className="grid grid-cols-1 md:grid-cols-2 gap-6"
            >
              {/* Fast Start Pilot */}
              <motion.div
                variants={fadeUp}
                className="rounded-xl bg-slate-900 border border-slate-800 p-8 flex flex-col"
              >
                <div className="mb-6">
                  <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-3">
                    Fast Start Pilot
                  </p>
                  <div className="flex items-end gap-2 mb-1">
                    <span className="text-4xl font-bold text-white">$15K</span>
                    <span className="text-slate-400 text-sm mb-1">/ 3 months</span>
                  </div>
                  <p className="text-slate-500 text-xs">
                    Best for: VP-level functional leaders evaluating the platform.
                  </p>
                </div>

                <ul className="space-y-3 mb-8 flex-1">
                  {[
                    '5-day onboarding',
                    'First insight in week one',
                    'Full SA → DA → Solutions pipeline',
                    'Dedicated implementation support',
                  ].map((item) => (
                    <li key={item} className="flex items-center gap-2.5 text-sm text-slate-300">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => scrollTo('request-demo')}
                  className="w-full py-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-sm border border-slate-700 transition-colors"
                >
                  Request a Demo
                </button>
              </motion.div>

              {/* Full Platform */}
              <motion.div
                variants={fadeUp}
                className="rounded-xl bg-indigo-950/60 border border-indigo-700/50 p-8 flex flex-col relative overflow-hidden"
              >
                <div
                  className="absolute inset-0 pointer-events-none"
                  style={{
                    background:
                      'radial-gradient(ellipse 80% 60% at 50% 0%, rgba(99,102,241,0.10) 0%, transparent 70%)',
                  }}
                />
                <div className="relative">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-indigo-300 text-xs font-semibold uppercase tracking-widest">
                      Full Platform
                    </p>
                    <span className="px-2.5 py-0.5 rounded-full bg-indigo-600/30 border border-indigo-500/30 text-indigo-300 text-[10px] font-semibold uppercase tracking-wide">
                      Most Popular
                    </span>
                  </div>
                  <div className="flex items-end gap-2 mb-1">
                    <span className="text-4xl font-bold text-white">$25–30K</span>
                    <span className="text-slate-400 text-sm mb-1">/ 6 months</span>
                  </div>
                  <p className="text-slate-400 text-xs">
                    Best for: C-suite executives wanting continuous decision intelligence.
                  </p>
                </div>

                <ul className="space-y-3 my-8 flex-1 relative">
                  {[
                    'Full pipeline: monitoring → analysis → solutions → tracking',
                    'Multi-persona debate council',
                    'Executive Briefing reports',
                    'ROI trajectory tracking',
                    'Institutional knowledge registry',
                  ].map((item) => (
                    <li key={item} className="flex items-center gap-2.5 text-sm text-slate-200">
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => scrollTo('request-demo')}
                  className="relative w-full py-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-colors shadow-lg shadow-indigo-900/40"
                >
                  Request a Demo
                </button>
              </motion.div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          7. REQUEST A DEMO
      ══════════════════════════════════════════ */}
      <section id="request-demo" ref={demoRef} className="py-24 px-6 bg-slate-900/50">
        <div className="max-w-2xl mx-auto">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <motion.div variants={fadeUp} className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Request a demo
              </h2>
              <p className="text-slate-400">
                Tell us a little about your context and we'll put together a
                personalised walkthrough.
              </p>
            </motion.div>

            <motion.div
              variants={fadeUp}
              className="rounded-2xl bg-slate-900 border border-slate-800 p-8"
            >
              {submitted ? (
                <div className="text-center py-10">
                  <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
                  <h3 className="text-white font-semibold text-xl mb-2">
                    Thanks — we'll be in touch.
                  </h3>
                  <p className="text-slate-400 text-sm">
                    We'll reach out within 24 hours to schedule a personalised walkthrough.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label
                        htmlFor="name"
                        className="block text-xs font-medium text-slate-400 mb-1.5"
                      >
                        Name <span className="text-indigo-400">*</span>
                      </label>
                      <input
                        id="name"
                        name="name"
                        type="text"
                        required
                        value={form.name}
                        onChange={handleFormChange}
                        placeholder="Jane Smith"
                        className="w-full rounded-lg bg-slate-800 border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                      />
                    </div>
                    <div>
                      <label
                        htmlFor="company"
                        className="block text-xs font-medium text-slate-400 mb-1.5"
                      >
                        Company <span className="text-indigo-400">*</span>
                      </label>
                      <input
                        id="company"
                        name="company"
                        type="text"
                        required
                        value={form.company}
                        onChange={handleFormChange}
                        placeholder="Acme Corp"
                        className="w-full rounded-lg bg-slate-800 border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label
                        htmlFor="role"
                        className="block text-xs font-medium text-slate-400 mb-1.5"
                      >
                        Role / Title <span className="text-indigo-400">*</span>
                      </label>
                      <input
                        id="role"
                        name="role"
                        type="text"
                        required
                        value={form.role}
                        onChange={handleFormChange}
                        placeholder="Chief Financial Officer"
                        className="w-full rounded-lg bg-slate-800 border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                      />
                    </div>
                    <div>
                      <label
                        htmlFor="email"
                        className="block text-xs font-medium text-slate-400 mb-1.5"
                      >
                        Work Email <span className="text-indigo-400">*</span>
                      </label>
                      <input
                        id="email"
                        name="email"
                        type="email"
                        required
                        value={form.email}
                        onChange={handleFormChange}
                        placeholder="jane@acme.com"
                        className="w-full rounded-lg bg-slate-800 border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                      />
                    </div>
                  </div>

                  <div>
                    <label
                      htmlFor="problem"
                      className="block text-xs font-medium text-slate-400 mb-1.5"
                    >
                      What decision keeps you up at night?{' '}
                      <span className="text-slate-600">(optional)</span>
                    </label>
                    <textarea
                      id="problem"
                      name="problem"
                      rows={4}
                      value={form.problem}
                      onChange={handleFormChange}
                      placeholder="e.g. Gross margin has declined 3 points over 6 months and we don't know why..."
                      className="w-full rounded-lg bg-slate-800 border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition resize-none"
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-colors shadow-lg shadow-indigo-900/40"
                  >
                    Request a Demo
                  </button>

                  <p className="text-center text-slate-500 text-xs pt-1">
                    We'll reach out within 24 hours to schedule a personalised walkthrough.
                  </p>
                </form>
              )}
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════════════════════
          8. FOOTER
      ══════════════════════════════════════════ */}
      <footer className="border-t border-slate-800 py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500">
          <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-6">
            <span className="font-bold text-white">Decision Studio</span>
            <a
              href="mailto:info@trydecisionstudio.com"
              className="hover:text-slate-300 transition-colors"
            >
              info@trydecisionstudio.com
            </a>
            <span>© 2026 Decision Studio</span>
          </div>
          <Link
            to="/login"
            className="text-slate-400 hover:text-white transition-colors flex items-center gap-1"
          >
            Sign In <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </footer>

    </div>
  )
}
