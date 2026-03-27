import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  ArrowRight,
  ChevronRight,
  AlertTriangle,
  BarChart2,
  Clock,
  BellOff,
  Bot,
  CheckCircle2,
  TrendingUp,
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
// Divider line
// ─────────────────────────────────────────────────
function SectionDivider() {
  return <div className="border-t border-slate-800/50 my-2" />
}

// ─────────────────────────────────────────────────
// Attribution note
// ─────────────────────────────────────────────────
function Attribution({ text }: { text: string }) {
  return (
    <p className="mt-4 text-xs text-slate-600 flex items-center gap-1.5">
      <span className="inline-block w-1 h-1 rounded-full bg-slate-700 flex-shrink-0" />
      {text}
    </p>
  )
}

// ─────────────────────────────────────────────────
// Problem narrative block (text-heavy, no card border)
// ─────────────────────────────────────────────────
function ProblemBlock({
  icon,
  heading,
  body,
}: {
  icon: React.ReactNode
  heading: string
  body: string
}) {
  return (
    <motion.div variants={fadeUp} className="flex gap-5">
      <div className="flex-shrink-0 mt-1">
        <div className="w-9 h-9 rounded-lg bg-slate-800/80 border border-slate-700/50 flex items-center justify-center">
          {icon}
        </div>
      </div>
      <div>
        <h3 className="text-white font-semibold text-base mb-2 leading-snug">{heading}</h3>
        <p className="text-slate-400 text-sm leading-relaxed">{body}</p>
      </div>
    </motion.div>
  )
}

// ═══════════════════════════════════════════════════
// INSIGHTS: BI MODERNIZATION PAGE
// ═══════════════════════════════════════════════════
export function InsightsBIModernization() {
  useSatoshiFont()

  const font = { fontFamily: 'Satoshi, sans-serif' }

  // Nav opacity on scroll
  const [navSolid, setNavSolid] = useState(false)
  useEffect(() => {
    const onScroll = () => setNavSolid(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-white" style={{ ...font, scrollBehavior: 'smooth' }}>

      {/* ── NAVIGATION ── */}
      <nav
        className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
          navSolid ? 'bg-slate-950/95 backdrop-blur border-b border-slate-800/60' : 'bg-transparent'
        }`}
      >
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/landing" className="text-lg font-bold tracking-tight text-white hover:text-slate-200 transition-colors" style={font}>
            Decision Studio
          </Link>
          <div className="flex items-center gap-6">
            <Link
              to="/how-it-works"
              className="text-sm text-slate-400 hover:text-white transition-colors hidden sm:block"
            >
              How It Works
            </Link>
            <Link
              to="/data-onboarding"
              className="text-sm text-slate-400 hover:text-white transition-colors hidden sm:block"
            >
              Data Onboarding
            </Link>
            <Link
              to="/login"
              className="text-sm text-slate-400 hover:text-white transition-colors hidden sm:block"
            >
              Sign In
            </Link>
            <Link
              to="/landing#conversation"
              className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
            >
              Request a Conversation
            </Link>
          </div>
        </div>
      </nav>

      {/* ═══════════════════════════════════════════
          1. HERO
      ═══════════════════════════════════════════ */}
      <section className="relative pt-36 pb-24 px-6 overflow-hidden">
        {/* Background glow */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: 'radial-gradient(ellipse 60% 40% at 50% 20%, rgba(99,102,241,0.07) 0%, transparent 70%)',
          }}
        />

        <div className="relative max-w-4xl mx-auto">
          {/* Breadcrumb */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="flex items-center gap-2 text-xs text-slate-500 mb-8"
          >
            <Link to="/landing" className="hover:text-slate-300 transition-colors flex items-center gap-1.5">
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to Decision Studio
            </Link>
            <ChevronRight className="w-3 h-3" />
            <span className="text-slate-600">Insights</span>
          </motion.div>

          <motion.div
            variants={stagger}
            initial="hidden"
            animate="visible"
          >
            <motion.p
              variants={fadeUp}
              className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-5"
            >
              Insights
            </motion.p>

            <motion.h1
              variants={fadeUp}
              className="text-4xl sm:text-5xl lg:text-[3.25rem] font-bold leading-[1.1] tracking-tight text-white mb-6"
            >
              The BI modernization trap
            </motion.h1>

            <motion.p
              variants={fadeUp}
              className="text-lg sm:text-xl text-slate-300 max-w-2xl leading-relaxed"
            >
              You've invested in dashboards, hired analysts, and built a "data culture."
              So why does every decision still feel like a guess?
            </motion.p>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          2. THE PROMISE
      ═══════════════════════════════════════════ */}
      <section className="py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <motion.p
              variants={fadeUp}
              className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-5"
            >
              The promise
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-200 text-lg leading-relaxed mb-5"
            >
              The pitch was compelling: connect your data, build dashboards, empower everyone
              with self-service analytics. Data-driven culture would follow.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-400 leading-relaxed"
            >
              Most organizations bought in. They migrated to cloud warehouses, deployed Tableau
              or Power BI, hired data teams, and declared themselves "data-driven." The investment
              was real. The intention was genuine. The expectation — that better access to data
              would produce better decisions — was reasonable.
            </motion.p>
          </motion.div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-6">
        <SectionDivider />
      </div>

      {/* ═══════════════════════════════════════════
          3. THE REALITY
      ═══════════════════════════════════════════ */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <motion.p
              variants={fadeUp}
              className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-5"
            >
              The reality
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-200 text-lg leading-relaxed mb-4"
            >
              87% of organizations still have low BI/analytics maturity. 70–80% of BI
              initiatives fail to deliver expected business value. Only 30% of employees
              actively use the analytics tools their company paid for.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-400 leading-relaxed mb-12"
            >
              The dashboards exist. Nobody trusts them enough to make a real decision based
              on what they show. Or if they do, they can't explain why they trusted them —
              which amounts to the same thing.
            </motion.p>

            <Attribution text="Gartner BI and Analytics Maturity Survey; Gartner BI failure rate research; Dresner Advisory Services" />

            {/* Three sub-problems */}
            <motion.div variants={fadeUp} className="mt-16 space-y-12">

              <ProblemBlock
                icon={<BarChart2 className="w-4 h-4 text-amber-400" />}
                heading="Dashboards answer the wrong question"
                body="They show what happened. Executives need to know why it happened and what to do about it. The gap between a chart and a decision is still filled by meetings, gut feel, and whoever argues loudest. A beautiful visualization of a margin decline doesn't tell you whether it's a pricing problem, a mix problem, or a regional anomaly — and it certainly doesn't tell you what to do Monday morning."
              />

              <ProblemBlock
                icon={<Clock className="w-4 h-4 text-amber-400" />}
                heading="The analyst bottleneck"
                body="Every insight requires a human analyst to pull data, build context, and tell the story. With 3 analysts serving 50 stakeholders, the queue is weeks long. By the time the analysis lands, the moment has passed — the quarter has closed, the competitor has moved, the window to act has narrowed. The bottleneck isn't laziness or lack of skill. It's structural: there are not enough hours in the day."
              />

              <ProblemBlock
                icon={<BellOff className="w-4 h-4 text-amber-400" />}
                heading="Alert fatigue killed monitoring"
                body="You set up threshold alerts. Now you get 200 a week. Research suggests 62% get ignored — not because people are careless, but because alerts without context are indistinguishable from noise. Is this a blip or a trend? Is it one product line or systemic? Is it seasonal or structural? The alert doesn't know. Neither do you, without an analyst."
              />

            </motion.div>

            <Attribution text="Alert fatigue statistic: Gartner IT Operations research; analyst-to-stakeholder ratios: industry surveys across enterprise analytics teams" />

          </motion.div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-6">
        <SectionDivider />
      </div>

      {/* ═══════════════════════════════════════════
          4. WHY AI COPILOTS HAVEN'T FIXED IT
      ═══════════════════════════════════════════ */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <motion.p
              variants={fadeUp}
              className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-5"
            >
              Why AI copilots haven't fixed it
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-200 text-lg leading-relaxed mb-5"
            >
              AI chatbots arrived promising to democratize analysis. But asking a language model
              "why did margin decline?" gets you a plausible-sounding story — not a diagnosis.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-400 leading-relaxed mb-5"
            >
              47% of enterprises have made major decisions based on hallucinated AI content.
              The industry lost $67.4 billion to AI errors in 2024. These aren't edge cases —
              they're the predictable consequence of deploying a pattern-matching system to do
              causal reasoning without guardrails or structured methodology.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-400 leading-relaxed"
            >
              The problem isn't access to answers. It's access to structured, auditable,
              repeatable analysis that connects cause to effect — the kind of work that
              actually holds up when a CFO asks "how do you know?"
            </motion.p>

            <motion.div
              variants={fadeUp}
              className="mt-10 rounded-xl bg-slate-900/60 border border-slate-800/60 px-7 py-6"
            >
              <div className="flex items-start gap-4">
                <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <p className="text-slate-300 text-sm leading-relaxed">
                  <span className="text-white font-semibold">The confabulation problem.</span>{' '}
                  Large language models are built to produce coherent, confident text. They will
                  construct a plausible explanation for margin decline whether or not that
                  explanation is grounded in your actual data. Without dimensional isolation
                  running against real numbers, you cannot tell the difference between a
                  diagnosis and a hallucination.
                </p>
              </div>
            </motion.div>

            <Attribution text="AI hallucination enterprise impact: Gartner AI Trust research; $67.4B figure: AI errors cost analysis, 2024; 47% figure: enterprise AI adoption survey" />

          </motion.div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-6">
        <SectionDivider />
      </div>

      {/* ═══════════════════════════════════════════
          5. WHAT ACTUALLY WORKS
      ═══════════════════════════════════════════ */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <motion.p
              variants={fadeUp}
              className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-5"
            >
              What actually works
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-200 text-lg leading-relaxed mb-12"
            >
              The organizations that break through share three things. Not a different tool.
              A different architecture for how decisions get made.
            </motion.p>

            <motion.div variants={stagger} className="space-y-10">

              <motion.div variants={fadeUp} className="flex gap-5">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-indigo-600/15 border border-indigo-500/25 flex items-center justify-center">
                    <span className="text-indigo-400 text-xs font-bold">1</span>
                  </div>
                </div>
                <div>
                  <h3 className="text-white font-semibold mb-2">
                    Automated detection that distinguishes signal from noise
                  </h3>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    Not more alerts — contextualized situations that arrive with the analysis
                    already started. The system watches your KPIs continuously, filters out
                    the seasonal and statistical noise, and surfaces only the changes that
                    warrant a decision. When something meaningful happens, you hear about it
                    with context, not just a number.
                  </p>
                </div>
              </motion.div>

              <motion.div variants={fadeUp} className="flex gap-5">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-indigo-600/15 border border-indigo-500/25 flex items-center justify-center">
                    <span className="text-indigo-400 text-xs font-bold">2</span>
                  </div>
                </div>
                <div>
                  <h3 className="text-white font-semibold mb-2">
                    Structured diagnosis, not narrative generation
                  </h3>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    Deterministic root cause isolation against real data — not language model
                    guessing. Dimensional IS/IS NOT analysis that identifies exactly where,
                    when, and what changed. The kind of work that, historically, required a
                    consulting engagement. Auditable. Repeatable. Explainable when someone
                    challenges the conclusion.
                  </p>
                </div>
              </motion.div>

              <motion.div variants={fadeUp} className="flex gap-5">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 rounded-full bg-indigo-600/15 border border-indigo-500/25 flex items-center justify-center">
                    <span className="text-indigo-400 text-xs font-bold">3</span>
                  </div>
                </div>
                <div>
                  <h3 className="text-white font-semibold mb-2">
                    Proof that decisions worked
                  </h3>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    Trajectory tracking and causal attribution that closes the accountability
                    loop. Not a lagging dashboard — a forward-looking comparison of what
                    actually happened versus what would have happened without action.
                    The discipline to ask "did it work?" forces better decisions at the
                    start, because the team knows they'll be measured.
                  </p>
                </div>
              </motion.div>

            </motion.div>

            {/* Soft link to Decision Studio */}
            <motion.div variants={fadeUp} className="mt-12">
              <Link
                to="/landing#walkthrough"
                className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 text-sm font-medium transition-colors group"
              >
                This is what we built.
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </motion.div>

          </motion.div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-6">
        <SectionDivider />
      </div>

      {/* ═══════════════════════════════════════════
          6. THE FORRESTER WARNING
      ═══════════════════════════════════════════ */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <motion.p
              variants={fadeUp}
              className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-5"
            >
              The accountability reckoning
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-200 text-lg leading-relaxed mb-5"
            >
              Only 15% of AI decision-makers reported EBITDA uplift in the past 12 months.
              25% of AI spend has been delayed into 2027 as CFOs demand proof.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-400 leading-relaxed mb-5"
            >
              The honeymoon period for enterprise AI is ending. Boards that approved
              AI transformation budgets in 2023 and 2024 are now asking for the evidence.
              The tools that survive this reckoning won't be the most capable ones —
              they'll be the ones that can show a direct line from AI output to business outcome.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-400 leading-relaxed"
            >
              The companies that survive this reckoning won't be the ones with the best
              dashboards. They'll be the ones that can prove their decisions worked.
            </motion.p>

            <motion.div
              variants={fadeUp}
              className="mt-10 rounded-xl bg-slate-900/60 border border-slate-800/60 px-7 py-6"
            >
              <div className="flex items-start gap-4">
                <TrendingUp className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-white text-sm font-semibold mb-1">The 15% problem</p>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    When only 15% of AI decision-makers can demonstrate P&amp;L impact, the
                    other 85% are operating on faith. That was acceptable during a bull market
                    for technology investment. It is no longer acceptable when CFOs are delaying
                    renewals and demanding ROI evidence before 2027 budget commitments.
                  </p>
                </div>
              </div>
            </motion.div>

            <Attribution text="Forrester AI Decision Intelligence Pulse Survey, 2026; Gartner CFO AI spending survey, Q1 2026" />

          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          7. CTA — READY TO TALK ABOUT IT?
      ═══════════════════════════════════════════ */}
      <section className="py-28 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            className="rounded-2xl bg-slate-900/60 border border-slate-800/60 px-10 py-14 text-center"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            <div className="flex justify-center mb-6">
              <div className="w-12 h-12 rounded-full bg-indigo-600/15 border border-indigo-500/25 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-indigo-400" />
              </div>
            </div>

            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4">
              Ready to talk about it?
            </h2>

            <p className="text-slate-400 max-w-lg mx-auto mb-8 leading-relaxed">
              Not a sales call. A real conversation about the decisions your team is making,
              the gaps you're feeling, and whether this approach could help — whether or not
              you're ready to act on it.
            </p>

            <Link
              to="/landing#conversation"
              className="inline-flex items-center gap-2 px-8 py-3.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-colors"
            >
              Request a Conversation
              <ArrowRight className="w-4 h-4" />
            </Link>

            <p className="mt-5 text-xs text-slate-600">
              No pitch. No obligation. We've seen this problem many times — sometimes that's
              enough to make the conversation worthwhile.
            </p>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          FOOTER
      ═══════════════════════════════════════════ */}
      <footer className="border-t border-slate-800/40 py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500" style={font}>
          <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-6">
            <Link to="/landing" className="font-bold text-white hover:text-slate-200 transition-colors" style={font}>
              Decision Studio
            </Link>
            <a href="mailto:info@trydecisionstudio.com" className="hover:text-slate-300 transition-colors">
              info@trydecisionstudio.com
            </a>
            <span>&copy; 2026 Decision Studio</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/how-it-works" className="text-slate-400 hover:text-white transition-colors">
              How It Works
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
