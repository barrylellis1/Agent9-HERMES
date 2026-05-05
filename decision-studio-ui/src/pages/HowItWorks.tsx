import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowRight,
  ChevronRight,
  ChevronLeft,
  Eye,
  Globe,
  LineChart,
  Search,
  UserCircle,
  Users,
} from 'lucide-react'
import {
  KPIGridAnimation,
  IsIsNotAnimation,
  MarketContextAnimation,
  CouncilDebateAnimation,
  TrajectoryMiniChart,
} from '../components/animations/AgentAnimations'

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
// Pipeline node type
// ─────────────────────────────────────────────────
interface PipelineNode {
  id: string
  label: string
  sublabel: string
  icon: React.ReactNode
  color: 'indigo' | 'emerald'
}

const pipelineNodes: PipelineNode[] = [
  {
    id: 'PC',
    label: 'PC',
    sublabel: 'Principal Context',
    icon: <UserCircle className="w-4 h-4" />,
    color: 'indigo',
  },
  {
    id: 'SA',
    label: 'SA',
    sublabel: 'Situation Awareness',
    icon: <Eye className="w-4 h-4" />,
    color: 'indigo',
  },
  {
    id: 'DA',
    label: 'DA',
    sublabel: 'Deep Analysis',
    icon: <Search className="w-4 h-4" />,
    color: 'indigo',
  },
  {
    id: 'MA',
    label: 'MA',
    sublabel: 'Market Analysis',
    icon: <Globe className="w-4 h-4" />,
    color: 'indigo',
  },
  {
    id: 'SF',
    label: 'SF',
    sublabel: 'Solution Finder',
    icon: <Users className="w-4 h-4" />,
    color: 'indigo',
  },
  {
    id: 'VA',
    label: 'VA',
    sublabel: 'Value Assurance',
    icon: <LineChart className="w-4 h-4" />,
    color: 'emerald',
  },
]

// ─────────────────────────────────────────────────
// Pipeline diagram (flex divs, no SVG)
// ─────────────────────────────────────────────────
function PipelineDiagram() {
  return (
    <div className="overflow-x-auto pb-4">
      <div className="flex items-center gap-0 min-w-max mx-auto w-fit">
        {pipelineNodes.map((node, i) => (
          <div key={node.id} className="flex items-center">
            {/* Node box */}
            <div
              className={`flex flex-col items-center gap-2 px-5 py-4 rounded-xl border ${
                node.color === 'emerald'
                  ? 'bg-emerald-950/60 border-emerald-600/40'
                  : 'bg-indigo-950/60 border-indigo-600/30'
              }`}
              style={{ minWidth: '96px' }}
            >
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center ${
                  node.color === 'emerald'
                    ? 'bg-emerald-600/20 text-emerald-400'
                    : 'bg-indigo-600/20 text-indigo-400'
                }`}
              >
                {node.icon}
              </div>
              <span
                className={`text-sm font-bold tracking-wide ${
                  node.color === 'emerald' ? 'text-emerald-300' : 'text-indigo-300'
                }`}
              >
                {node.label}
              </span>
              <span className="text-[10px] text-slate-400 text-center leading-tight whitespace-nowrap">
                {node.sublabel}
              </span>
            </div>

            {/* Arrow connector */}
            {i < pipelineNodes.length - 1 && (
              <div className="flex items-center px-1">
                <div className="w-6 h-px bg-slate-700" />
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 -ml-1" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Agent detail section
// ─────────────────────────────────────────────────
interface AgentSectionProps {
  id: string
  label: string
  icon: React.ReactNode
  color: 'indigo' | 'emerald'
  title: string
  whatItDoes: string
  methodology: React.ReactNode
  whatItProduces: string
  note?: string
  differentiator?: React.ReactNode
  hitlNote?: string
  index: number
  animation?: React.ReactNode
}

function AgentSection({
  label,
  icon,
  color,
  title,
  whatItDoes,
  methodology,
  whatItProduces,
  note,
  differentiator,
  hitlNote,
  index,
  animation,
}: AgentSectionProps) {
  const isEven = index % 2 === 0
  const accentText = color === 'emerald' ? 'text-emerald-400' : 'text-indigo-400'
  const accentBg = color === 'emerald' ? 'bg-emerald-600/20' : 'bg-indigo-600/20'
  const accentBorder = color === 'emerald' ? 'border-emerald-500/30' : 'border-indigo-500/30'
  const accentLabel = color === 'emerald' ? 'text-emerald-400' : 'text-indigo-400'

  const content = (
    <div>
      {/* Agent badge */}
      <div className="flex items-center gap-3 mb-5">
        <div className={`w-10 h-10 rounded-full ${accentBg} border ${accentBorder} flex items-center justify-center ${accentText}`}>
          {icon}
        </div>
        <span className={`text-xs font-semibold uppercase tracking-widest ${accentLabel}`}>
          {label}
        </span>
      </div>

      <h3 className="text-2xl font-bold text-white mb-6">{title}</h3>

      <div className="space-y-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-2">What it does</p>
          <p className="text-slate-300 text-sm leading-relaxed">{whatItDoes}</p>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-2">Methodology</p>
          <div className="text-slate-300 text-sm leading-relaxed">{methodology}</div>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-2">What it produces</p>
          <p className="text-slate-300 text-sm leading-relaxed">{whatItProduces}</p>
        </div>

        {differentiator && (
          <div className={`rounded-lg border ${accentBorder} bg-slate-900/60 px-4 py-3`}>
            <p className={`text-xs font-semibold uppercase tracking-widest ${accentLabel} mb-1.5`}>Key differentiator</p>
            <div className="text-slate-300 text-sm leading-relaxed">{differentiator}</div>
          </div>
        )}

        {note && (
          <p className="text-slate-500 text-xs leading-relaxed italic">{note}</p>
        )}

        {hitlNote && (
          <div className="flex items-start gap-3 rounded-lg border border-emerald-600/20 bg-emerald-950/30 px-4 py-3">
            <div className="w-1 h-full min-h-[1rem] rounded-full bg-emerald-500/40 flex-shrink-0 mt-0.5" />
            <p className="text-emerald-300 text-sm leading-relaxed">{hitlNote}</p>
          </div>
        )}
      </div>
    </div>
  )

  const visual = animation ? (
    <div>{animation}</div>
  ) : (
    <div className={`rounded-xl border ${accentBorder} bg-slate-900/60 flex flex-col items-center justify-center p-8 gap-4 min-h-[200px]`}>
      <div className={`w-16 h-16 rounded-2xl ${accentBg} ${accentText} flex items-center justify-center`}>
        <span className="scale-150">{icon}</span>
      </div>
      <span className={`text-3xl font-black tracking-tight ${accentText}`}>{label}</span>
    </div>
  )

  return (
    <motion.div
      variants={fadeUp}
      className="grid grid-cols-1 md:grid-cols-2 gap-10 items-center py-16 border-b border-slate-800/40 last:border-b-0"
    >
      <div className={isEven ? '' : 'md:order-2'}>{content}</div>
      <div className={isEven ? '' : 'md:order-1'}>{visual}</div>
    </motion.div>
  )
}

// ═══════════════════════════════════════════════════
// HOW IT WORKS PAGE
// ═══════════════════════════════════════════════════
export function HowItWorks() {
  useSatoshiFont()

  const [navSolid, setNavSolid] = useState(false)
  useEffect(() => {
    const onScroll = () => setNavSolid(window.scrollY > 60)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const font = { fontFamily: 'Satoshi, sans-serif' }

  return (
    <div className="min-h-screen bg-slate-950 text-white" style={{ ...font, scrollBehavior: 'smooth' }}>

      {/* ── NAVIGATION ── */}
      <nav
        className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
          navSolid
            ? 'bg-slate-950/95 backdrop-blur border-b border-slate-800/60'
            : 'bg-transparent'
        }`}
      >
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/landing" className="text-lg font-bold tracking-tight text-white" style={font}>
            Decision Studio
          </Link>
          <div className="flex items-center gap-6">
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

      {/* ── BREADCRUMB ── */}
      <div className="pt-24 pb-0 px-6">
        <div className="max-w-4xl mx-auto">
          <Link
            to="/landing"
            className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Back to Decision Studio
          </Link>
        </div>
      </div>

      {/* ═══════════════════════════════════════════
          1. HERO
      ═══════════════════════════════════════════ */}
      <section className="relative py-20 px-6 overflow-hidden">
        {/* Subtle gradient */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              'radial-gradient(ellipse 60% 40% at 50% 30%, rgba(99,102,241,0.07) 0%, transparent 70%)',
          }}
        />

        <motion.div
          className="relative max-w-4xl mx-auto"
          variants={stagger}
          initial="hidden"
          animate="visible"
        >
          <motion.p
            variants={fadeUp}
            className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-4"
          >
            Architecture
          </motion.p>
          <motion.h1
            variants={fadeUp}
            className="text-4xl sm:text-5xl font-bold leading-[1.1] tracking-tight text-white mb-6"
          >
            How Decision Studio works
          </motion.h1>
          <motion.p
            variants={fadeUp}
            className="text-lg text-slate-300 max-w-2xl leading-relaxed"
          >
            Six specialized AI agents, two proven methodologies, and a human in the loop
            at every decision point.
          </motion.p>
        </motion.div>
      </section>

      {/* ═══════════════════════════════════════════
          2. THE PIPELINE
      ═══════════════════════════════════════════ */}
      <section className="py-20 px-6 bg-slate-900/30">
        <div className="max-w-5xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <motion.div variants={fadeUp} className="mb-10">
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">The pipeline</h2>
              <p className="text-slate-400 max-w-2xl text-sm leading-relaxed">
                From detection to proof — six purpose-built agents in sequence.
              </p>
            </motion.div>

            <motion.div variants={fadeUp}>
              <PipelineDiagram />
            </motion.div>

            <motion.div
              variants={fadeUp}
              className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4"
            >
              <div className="flex items-start gap-3 rounded-lg bg-indigo-950/40 border border-indigo-600/20 px-5 py-4">
                <div className="w-3 h-3 rounded-sm bg-indigo-600/60 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-slate-300 leading-relaxed">
                  <span className="text-indigo-300 font-medium">Indigo nodes</span> — AI-driven steps.
                  Each agent has a single, well-defined job.
                </p>
              </div>
              <div className="flex items-start gap-3 rounded-lg bg-emerald-950/40 border border-emerald-600/20 px-5 py-4">
                <div className="w-3 h-3 rounded-sm bg-emerald-600/60 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-slate-300 leading-relaxed">
                  <span className="text-emerald-300 font-medium">Emerald node</span> — the accountability
                  layer. Tracks whether decisions actually worked.
                </p>
              </div>
            </motion.div>

            <motion.div
              variants={fadeUp}
              className="mt-6 rounded-lg bg-slate-900/80 border border-slate-800/60 px-5 py-4"
            >
              <p className="text-sm text-slate-400 leading-relaxed">
                Each agent is purpose-built for one job. No single monolithic model attempting
                to do everything. Structured inputs, structured outputs, full audit trail at
                every step.
              </p>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          3. AGENT DETAILS
      ═══════════════════════════════════════════ */}
      <section className="py-16 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
          >
            <motion.div variants={fadeUp} className="mb-12">
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">Agent details</h2>
              <p className="text-slate-400 max-w-2xl text-sm leading-relaxed">
                What each agent does, how it works, and what it produces.
              </p>
            </motion.div>
          </motion.div>

          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            {/* PC */}
            <AgentSection
              id="PC"
              index={0}
              label="Principal Context Agent"
              icon={<UserCircle className="w-4 h-4" />}
              color="indigo"
              title="Context before analysis"
              whatItDoes="Maps each executive's role, responsibilities, and business context. The same data gets framed differently for a CFO vs. a COO — because they care about different things."
              methodology={
                <span>
                  Principal profiles define KPI ownership, business process mapping, and contextual
                  priorities. The system personalizes every output to the decision-maker — not by
                  changing the underlying data, but by surfacing what's relevant to their remit
                  and filtering out noise that doesn't belong in their view.
                </span>
              }
              whatItProduces="Contextualized views — the same situation card looks different depending on who's reading it. A margin problem surfaces differently for Finance than for Operations."
            />

            {/* SA */}
            <AgentSection
              id="SA"
              index={1}
              label="Situation Awareness Agent"
              icon={<Eye className="w-4 h-4" />}
              color="indigo"
              title="Continuous, automatic monitoring"
              animation={<KPIGridAnimation />}
              whatItDoes="Monitors KPIs against thresholds and historical patterns — and surfaces situation cards automatically, without anyone asking."
              methodology={
                <span>
                  Threshold monitoring with contextual filtering — not just a simple "value &lt;
                  target" alert, but pattern detection that distinguishes one-off blips from
                  developing trends. KPI definitions, ownership mappings, and severity thresholds
                  all live in the registry and inform every detection pass.
                </span>
              }
              whatItProduces="Situation cards — each with severity level, affected KPIs, business process context, and enough initial framing to kick off deep analysis without starting from zero."
              note="This runs automatically. No one needs to ask a question. When something meaningful changes, a situation is surfaced."
            />

            {/* DA */}
            <AgentSection
              id="DA"
              index={2}
              label="Deep Analysis Agent"
              icon={<Search className="w-4 h-4" />}
              color="indigo"
              title="Structured root cause, not narrative guessing"
              animation={<IsIsNotAnimation />}
              whatItDoes="Isolates exactly where, when, and what changed — using structured IS/IS NOT analysis against your actual data, not a plausible-sounding guess."
              methodology={
                <span>
                  <span className="text-white font-medium">Kepner-Tregoe IS/IS NOT analysis</span>
                  {' '}— a structured problem-analysis framework that separates what IS true from
                  what IS NOT true across multiple dimensions (product, region, channel, time
                  period). Automated against your data, this produces a dimensional isolation matrix
                  rather than a guess. Results are then framed using{' '}
                  <span className="text-white font-medium">SCQA narrative structure</span>
                  {' '}(Situation — what's the context; Complication — what changed; Question —
                  what should we do; Answer — the recommended path), which is the standard
                  McKinsey uses for executive communication because it leads with impact rather
                  than background.
                  <br /><br />
                  This analysis is <span className="text-white font-medium">deterministic</span>,
                  not generative. The same data always produces the same diagnosis.
                </span>
              }
              whatItProduces="Diverging bar charts showing which dimensions are affected vs. unaffected, change-point detection pinpointing when the shift began, and a structured diagnostic narrative ready for executive review."
              differentiator={
                <span>
                  The IS NOT segments — the dimensions that are <em>not</em> affected — become
                  natural control groups for Value Assurance measurement later. The same analysis
                  that finds the problem creates the measurement framework for proving the fix worked.
                  This connection is designed in, not bolted on after the fact.
                </span>
              }
            />

            {/* MA */}
            <AgentSection
              id="MA"
              index={3}
              label="Market Analysis Agent"
              icon={<Globe className="w-4 h-4" />}
              color="indigo"
              title="Is this internal or systemic?"
              animation={<MarketContextAnimation />}
              whatItDoes="Scans external sources for competitor moves, industry trends, and regulatory changes — answering whether the situation is your problem or everyone's problem."
              methodology={
                <span>
                  Web search synthesis via{' '}
                  <span className="text-white font-medium">Perplexity</span>
                  {' '}(real-time web retrieval) combined with Claude synthesis — external context
                  generated at analysis time, not pulled from a static database that went stale
                  six months ago. The agent identifies signals relevant to the specific situation
                  being analyzed, not a generic industry overview.
                </span>
              }
              whatItProduces="Market signals woven directly into the analysis — competitor pricing moves, category volume trends, regulatory developments. If the same problem is happening industry-wide, that changes the strategic response."
            />

            {/* SF */}
            <AgentSection
              id="SF"
              index={4}
              label="Solution Finder Agent"
              icon={<Users className="w-4 h-4" />}
              color="indigo"
              title="Three perspectives, visible disagreement"
              animation={<CouncilDebateAnimation />}
              whatItDoes="Generates recommendations from three independent analytical perspectives — then synthesizes them with the disagreements left visible, not smoothed over."
              methodology={
                <span>
                  <span className="text-white font-medium">MBB-inspired multi-persona architecture</span>
                  {' '}— three parallel AI calls, each using a different strategic framework modeled
                  on McKinsey, BCG, and Bain analytical traditions (growth orientation, portfolio
                  logic, operational rigor). These run in parallel, then a fourth synthesis call
                  reads all three outputs and produces a unified briefing that explicitly calls out
                  consensus, dissent, and the trade-offs involved in choosing between approaches.
                  <br /><br />
                  This is not consensus-by-averaging. The synthesis preserves real disagreement
                  because strategic ambiguity is information, not noise.
                </span>
              }
              whatItProduces="Three independent solution proposals, a trade-off matrix comparing them on impact, cost, risk, and time-to-result, quantified impact estimates with confidence ranges, and a synthesized executive briefing. The decision-maker sees where the perspectives agree, where they diverge, and the reasoning behind each position."
              hitlNote="This is where you step in. Approve a solution, reject it, or ask follow-up questions to challenge assumptions. The system adapts to your input — your domain expertise shapes the final recommendation."
            />

            {/* VA */}
            <AgentSection
              id="VA"
              index={5}
              label="Value Assurance Agent"
              icon={<LineChart className="w-4 h-4" />}
              color="emerald"
              title="Did it actually work?"
              animation={
                <div className="rounded-xl border border-emerald-500/30 bg-slate-900/60 p-6 flex flex-col items-center justify-center gap-4">
                  <TrajectoryMiniChart />
                  <p className="text-xs text-slate-500 text-center">Inaction vs. expected vs. actual — from approval date forward</p>
                </div>
              }
              whatItDoes="Tracks whether approved decisions produced the expected results, and separates your impact from market noise. This is the part most systems skip entirely."
              methodology={
                <span>
                  <span className="text-white font-medium">Difference-in-Differences (DiD) causal attribution</span>
                  {' '}— an econometric method for measuring the effect of an intervention by
                  comparing changes in the affected group against changes in a control group over
                  the same period. The control groups come directly from the IS NOT segments
                  identified during Deep Analysis — this is why that connection matters.
                  <br /><br />
                  Three trajectories are tracked from the approval date forward:{' '}
                  <span className="text-white font-medium">inaction</span> (what would have happened
                  without the intervention, projected at approval and frozen),{' '}
                  <span className="text-white font-medium">expected</span> (what the analysis predicted
                  with the approved solution), and{' '}
                  <span className="text-white font-medium">actual</span> (what the data shows really
                  happened). The gap between inaction and actual — adjusted for market movement via
                  the control group — is the attributed impact.
                </span>
              }
              whatItProduces="Composite verdict (Validated / Partial / Failed / Measuring), attribution breakdown separating your impact from external factors, strategy alignment assessment comparing actual outcomes to original intent, and a portfolio-level ROI view across all tracked decisions."
              differentiator="No other system connects diagnosis → recommendation → proof in a single pipeline. The audit trail runs from the original situation card through the approved solution to the measured outcome — so you can answer 'did that work?' with data, not instinct."
            />
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          4. AI vs DETERMINISTIC
      ═══════════════════════════════════════════ */}
      <section className="py-20 px-6 bg-slate-900/30">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <motion.div variants={fadeUp} className="mb-12">
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">
                Where AI is used — and where it isn't
              </h2>
              <p className="text-slate-400 max-w-2xl text-sm leading-relaxed">
                AI generates insight. Structure ensures rigor. The combination is what makes this work.
              </p>
            </motion.div>

            <motion.div variants={fadeUp} className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* AI-driven */}
              <div className="rounded-xl bg-indigo-950/40 border border-indigo-600/20 p-6">
                <div className="flex items-center gap-2 mb-5">
                  <div className="w-2 h-2 rounded-full bg-indigo-500" />
                  <h3 className="text-sm font-semibold text-indigo-300 uppercase tracking-widest">
                    AI-driven
                  </h3>
                </div>
                <ul className="space-y-3">
                  {[
                    'Situation context interpretation and framing',
                    'SCQA narrative construction from dimensional data',
                    'Market signal synthesis from live web search',
                    'Multi-perspective strategic recommendations',
                    'Synthesis across three independent viewpoints',
                    'Impact estimation with confidence ranges',
                  ].map((item) => (
                    <li key={item} className="flex items-start gap-2.5 text-sm text-slate-300 leading-relaxed">
                      <span className="w-1 h-1 rounded-full bg-indigo-500/60 mt-2 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Deterministic */}
              <div className="rounded-xl bg-slate-900/80 border border-slate-700/40 p-6">
                <div className="flex items-center gap-2 mb-5">
                  <div className="w-2 h-2 rounded-full bg-slate-400" />
                  <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-widest">
                    Deterministic / structured
                  </h3>
                </div>
                <ul className="space-y-3">
                  {[
                    'KPI threshold monitoring against historical baselines',
                    'IS/IS NOT dimensional isolation against real data',
                    'SQL execution — actual numbers, not approximations',
                    'Change-point detection (statistical, not generative)',
                    'Trajectory projection math (inaction / expected / actual)',
                    'DiD attribution calculation against control groups',
                  ].map((item) => (
                    <li key={item} className="flex items-start gap-2.5 text-sm text-slate-300 leading-relaxed">
                      <span className="w-1 h-1 rounded-full bg-slate-500/60 mt-2 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>

            <motion.div
              variants={fadeUp}
              className="mt-6 rounded-lg border border-slate-700/40 bg-slate-900/60 px-5 py-4"
            >
              <p className="text-sm text-slate-400 leading-relaxed">
                When an AI component generates a narrative or recommendation, there is always
                structured data underneath it that can be audited. You can challenge the diagnosis
                by looking at the dimensional table. You can verify the attribution by examining
                the trajectory math. Nothing is a black box.
              </p>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          5. WHAT DECISION STUDIO DOES NOT REPLACE
      ═══════════════════════════════════════════ */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <motion.div variants={fadeUp} className="mb-10">
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">
                What Decision Studio does not replace
              </h2>
              <p className="text-slate-400 max-w-2xl text-sm leading-relaxed">
                Transparency about scope is part of the product. A system that claims to replace
                human judgment is one you shouldn't trust.
              </p>
            </motion.div>

            <motion.div variants={fadeUp}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
                {[
                  {
                    title: 'Board-level strategic planning',
                    desc: 'Long-horizon competitive positioning, M&A strategy, and portfolio-level capital allocation require human judgment at a level of abstraction this system is not designed for.',
                  },
                  {
                    title: 'Unprecedented situations',
                    desc: 'When the situation has no historical precedent — a category that has never existed before, a regulatory change with no comparable prior — structured analysis has limited leverage.',
                  },
                  {
                    title: 'Relationship-driven insights',
                    desc: 'The VP of Sales is about to quit. A key customer is quietly sourcing alternatives. A competitor is about to poach your team. No data pipeline surfaces this.',
                  },
                  {
                    title: 'Deep industry pattern recognition',
                    desc: '20 years of watching a specific market develop an intuition for what matters. That contextual expertise shapes which insights are actually important.',
                  },
                  {
                    title: 'Organizational change management',
                    desc: 'Knowing the right move and getting an organization to execute it are different problems. Decision Studio addresses the former, not the latter.',
                  },
                  {
                    title: 'Ethical and political judgment',
                    desc: 'Some decisions involve trade-offs that are fundamentally about values, not data. Those remain yours.',
                  },
                ].map(({ title, desc }) => (
                  <div
                    key={title}
                    className="rounded-lg border border-slate-800/60 bg-slate-900/40 px-5 py-4"
                  >
                    <p className="text-white text-sm font-semibold mb-1.5">{title}</p>
                    <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
                  </div>
                ))}
              </div>

              <div className="rounded-lg bg-indigo-950/30 border border-indigo-600/20 px-5 py-4">
                <p className="text-indigo-200 text-sm leading-relaxed">
                  Decision Studio handles the analytical heavy lifting so your team can focus on
                  the decisions that require human judgment. The goal is not to automate decision-making
                  — it's to make structured analysis fast enough that executives can use it on every
                  significant decision, not just the ones that justify a consulting engagement.
                </p>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          6. THE REGISTRY
      ═══════════════════════════════════════════ */}
      <section className="py-20 px-6 bg-slate-900/30">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <motion.div variants={fadeUp} className="mb-10">
              <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">
                The registry — why it gets smarter over time
              </h2>
              <p className="text-slate-400 max-w-2xl text-sm leading-relaxed">
                Most knowledge management systems are passive storage. The registry is an operational layer.
              </p>
            </motion.div>

            <motion.div variants={fadeUp} className="space-y-5">
              <div className="rounded-xl border border-slate-700/40 bg-slate-900/60 px-6 py-5">
                <p className="text-slate-300 leading-relaxed text-sm">
                  Every KPI definition, business process mapping, principal profile, decision
                  rationale, and outcome measurement is stored in a living registry. This isn't a
                  wiki — it actively informs every future analysis. When the system monitors KPIs,
                  it reads the registry. When it frames a situation for a specific executive, it
                  reads their principal profile. When it measures outcomes, it reads the original
                  approved solution.
                </p>
              </div>

              <div className="rounded-xl border border-slate-700/40 bg-slate-900/60 px-6 py-5">
                <p className="text-slate-300 leading-relaxed text-sm">
                  Unlike a consultant's deck that sits on a shared drive or a wiki that goes stale
                  three months after it's written, the registry is used every time the system runs.
                  That usage keeps it current and creates pressure to keep it accurate — because
                  inaccurate registry entries produce visibly wrong outputs.
                </p>
              </div>

              <div className="rounded-xl border border-indigo-600/20 bg-indigo-950/30 px-6 py-5">
                <p className="text-indigo-200 leading-relaxed text-sm">
                  When key people leave, the knowledge stays. The institutional context that usually
                  walks out the door with a departing CFO or VP of Strategy is encoded in the
                  registry — which KPIs they owned, how they weighted different business processes,
                  what decisions were made and why. That context informs the next person in the role
                  from day one.
                </p>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          7. PIPELINE VISUAL SUMMARY
      ═══════════════════════════════════════════ */}
      <section className="py-20 px-6 border-t border-slate-800/40">
        <div className="max-w-4xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
          >
            <motion.p variants={fadeUp} className="text-xs font-semibold uppercase tracking-widest text-slate-500 text-center mb-12">
              The full pipeline
            </motion.p>
            <motion.div variants={fadeUp} className="flex items-center justify-center gap-0">
              {[
                { label: 'Monitor',   color: 'bg-blue-500' },
                { label: 'Detect',    color: 'bg-red-500' },
                { label: 'Diagnose',  color: 'bg-amber-500' },
                { label: 'Recommend', color: 'bg-violet-400' },
                { label: 'Decide',    color: 'bg-indigo-500' },
                { label: 'Prove',     color: 'bg-emerald-500' },
              ].map((step, i, arr) => (
                <div key={step.label} className="flex items-center">
                  <div className="flex flex-col items-center gap-3">
                    <div className={`w-14 h-14 rounded-full ${step.color} shadow-lg`} />
                    <span className="text-xs text-slate-400 font-medium tracking-wide">{step.label}</span>
                  </div>
                  {i < arr.length - 1 && (
                    <div className="w-10 sm:w-16 border-t-2 border-dashed border-slate-700 mb-5 mx-1" />
                  )}
                </div>
              ))}
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          8. CTA
      ═══════════════════════════════════════════ */}
      <section className="py-28 px-6">
        <div className="max-w-3xl mx-auto">
          <motion.div
            variants={stagger}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            <motion.div variants={fadeUp} className="text-center mb-12">
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
                Want to see it in action?
              </h2>
              <p className="text-slate-400 max-w-lg mx-auto">
                The walkthrough on the landing page runs through the full pipeline
                with a real scenario — from situation detection to outcome tracking.
              </p>
            </motion.div>

            <motion.div variants={fadeUp} className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/landing#walkthrough"
                className="w-full sm:w-auto px-8 py-3.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-semibold transition-colors text-sm border border-slate-700/60 flex items-center justify-center gap-2"
              >
                See the walkthrough <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/landing#conversation"
                className="w-full sm:w-auto px-8 py-3.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors text-sm flex items-center justify-center gap-2"
              >
                Ready to talk? <ArrowRight className="w-4 h-4" />
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          FOOTER
      ═══════════════════════════════════════════ */}
      <footer className="border-t border-slate-800/40 py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500" style={font}>
          <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-6">
            <span className="font-bold text-white">Decision Studio</span>
            <a href="mailto:info@trydecisionstudio.com" className="hover:text-slate-300 transition-colors">
              info@trydecisionstudio.com
            </a>
            <span>&copy; 2026 Decision Studio</span>
          </div>
          <div className="flex items-center gap-6">
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
