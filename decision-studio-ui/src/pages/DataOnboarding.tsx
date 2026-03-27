import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowLeft,
  ArrowRight,
  ChevronRight,
  CheckCircle2,
  Database,
  Search,
  Layers,
  Bot,
  FlaskConical,
  BookOpen,
  Zap,
  AlertTriangle,
  Clock,
  Code2,
  Users,
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
// Section divider
// ─────────────────────────────────────────────────
function SectionDivider() {
  return <div className="border-t border-slate-800/50 my-2" />
}

// ─────────────────────────────────────────────────
// Problem block (icon + heading + body)
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

// ─────────────────────────────────────────────────
// Workflow step
// ─────────────────────────────────────────────────
function WorkflowStep({
  number,
  title,
  body,
  icon,
}: {
  number: string
  title: string
  body: string
  icon: React.ReactNode
}) {
  return (
    <motion.div variants={fadeUp} className="flex gap-5">
      <div className="flex-shrink-0 flex flex-col items-center">
        <div className="w-10 h-10 rounded-full bg-indigo-600/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
          {icon}
        </div>
        <div className="w-px flex-1 bg-slate-800/60 mt-2 mb-0 min-h-[1.5rem]" />
      </div>
      <div className="pb-8">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-xs font-bold text-indigo-500 uppercase tracking-widest">
            Step {number}
          </span>
        </div>
        <h3 className="text-white font-semibold text-base mb-2 leading-snug">{title}</h3>
        <p className="text-slate-400 text-sm leading-relaxed">{body}</p>
      </div>
    </motion.div>
  )
}

// ─────────────────────────────────────────────────
// Differentiator card
// ─────────────────────────────────────────────────
function DifferentiatorCard({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode
  title: string
  body: string
}) {
  return (
    <motion.div
      variants={fadeUp}
      className="rounded-xl bg-slate-900/60 border border-slate-800/60 px-6 py-5"
    >
      <div className="w-9 h-9 rounded-lg bg-indigo-600/15 border border-indigo-500/25 flex items-center justify-center text-indigo-400 mb-4">
        {icon}
      </div>
      <h3 className="text-white font-semibold text-sm mb-2 leading-snug">{title}</h3>
      <p className="text-slate-400 text-sm leading-relaxed">{body}</p>
    </motion.div>
  )
}

// ─────────────────────────────────────────────────
// Platform badge
// ─────────────────────────────────────────────────
function PlatformBadge({
  name,
  status,
}: {
  name: string
  status: 'production' | 'supported' | 'local'
}) {
  const statusStyles = {
    production: 'text-emerald-400 bg-emerald-950/60 border-emerald-600/30',
    supported: 'text-indigo-400 bg-indigo-950/60 border-indigo-600/30',
    local: 'text-slate-400 bg-slate-800/60 border-slate-700/40',
  }
  const statusLabel = {
    production: 'Production ready',
    supported: 'Supported',
    local: 'Local dev',
  }
  return (
    <div
      className={`rounded-xl border px-5 py-4 flex flex-col gap-2 ${statusStyles[status]}`}
    >
      <span className="font-semibold text-white text-sm">{name}</span>
      <span className={`text-xs font-medium ${statusStyles[status].split(' ')[0]}`}>
        {statusLabel[status]}
      </span>
    </div>
  )
}

// ═══════════════════════════════════════════════════
// DATA ONBOARDING PAGE
// ═══════════════════════════════════════════════════
export function DataOnboarding() {
  useSatoshiFont()

  const font = { fontFamily: 'Satoshi, sans-serif' }

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
          <Link
            to="/landing"
            className="text-lg font-bold tracking-tight text-white hover:text-slate-200 transition-colors"
            style={font}
          >
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
              to="/insights/bi-modernization"
              className="text-sm text-slate-400 hover:text-white transition-colors hidden sm:block"
            >
              Insights
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
            <span className="text-slate-600">Data Onboarding</span>
          </motion.div>

          <motion.div variants={stagger} initial="hidden" animate="visible">
            <motion.p
              variants={fadeUp}
              className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-5"
            >
              Data Onboarding
            </motion.p>

            <motion.h1
              variants={fadeUp}
              className="text-4xl sm:text-5xl lg:text-[3.25rem] font-bold leading-[1.1] tracking-tight text-white mb-6"
            >
              Your data, ready in hours — not quarters
            </motion.h1>

            <motion.p
              variants={fadeUp}
              className="text-lg sm:text-xl text-slate-300 max-w-2xl leading-relaxed"
            >
              Decision Studio connects to your existing data infrastructure without migration,
              ETL pipelines, or warehouse redesign. Your data stays where it is. Analysis starts
              the same day.
            </motion.p>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          2. THE ONBOARDING PROBLEM
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
              The onboarding problem
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-200 text-lg leading-relaxed mb-5"
            >
              Before any analytics tool can tell you something useful, it has to know your data.
              In most organizations, that step alone takes months.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-400 leading-relaxed mb-12"
            >
              The traditional approach treats data readiness as a prerequisite: map your schema,
              build pipelines, define KPIs, get sign-off, then repeat every time something changes.
              By the time the infrastructure is ready, the business problem it was meant to address
              has already moved on.
            </motion.p>

            <motion.div variants={stagger} className="space-y-10">
              <ProblemBlock
                icon={<Clock className="w-4 h-4 text-amber-400" />}
                heading="6-12 month implementation timelines"
                body="Enterprise data integration projects routinely take two to four quarters before anything useful comes out the other end. The vendor demo showed a live connection in minutes. The actual deployment involved data contracts, security reviews, schema mapping sessions, and a project plan that nobody has time to manage."
              />

              <ProblemBlock
                icon={<Code2 className="w-4 h-4 text-amber-400" />}
                heading="Every new KPI requires a developer"
                body="Someone on the business side identifies a metric they want to track. A ticket goes to the data engineering queue. Three sprints later, the KPI exists. By then, the initiative it was meant to support is halfway through its cycle and the measurement window has narrowed. Non-technical stakeholders can't define what matters without going through a developer."
              />

              <ProblemBlock
                icon={<AlertTriangle className="w-4 h-4 text-amber-400" />}
                heading="Schema changes break everything downstream"
                body="Warehouse tables get renamed. Columns get deprecated. A data engineering team remodels a fact table for performance reasons. Every pipeline that depended on the old structure now fails silently or loudly, and the root cause is a schema change that no downstream consumer was told about. Maintenance becomes a full-time job."
              />

              <ProblemBlock
                icon={<Users className="w-4 h-4 text-amber-400" />}
                heading="Data readiness is the perpetual blocker"
                body="Procurement signs off on the analytics platform. The rollout stalls at 'we need to finish the data prep first.' Six months later, the data prep is still in progress. The platform license is renewing and usage numbers are low. The business case erodes before the tool has had a real chance."
              />
            </motion.div>
          </motion.div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-6">
        <SectionDivider />
      </div>

      {/* ═══════════════════════════════════════════
          3. HOW DECISION STUDIO CONNECTS
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
              How it connects
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-200 text-lg leading-relaxed mb-4"
            >
              Decision Studio guides you through a structured seven-step onboarding workflow.
              Each step has a job. At the end, you have a registered data product, validated
              KPIs, and continuous monitoring — without writing a single ETL pipeline.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-400 leading-relaxed mb-12"
            >
              This isn't a wizard that asks you to fill in forms. It's an active process:
              the system inspects your schema, infers relationships, profiles column semantics,
              and validates queries against your live data before anything is registered.
            </motion.p>

            {/* Workflow steps — last step has no trailing line */}
            <div className="mt-4">
              <WorkflowStep
                number="1"
                icon={<Database className="w-4 h-4" />}
                title="Connect"
                body="Point Decision Studio at your existing data warehouse — BigQuery, Snowflake, Databricks, PostgreSQL, or local DuckDB. No data migration. No ETL. Your data stays where it is. The system stores a connection profile, not a copy."
              />
              <WorkflowStep
                number="2"
                icon={<Search className="w-4 h-4" />}
                title="Discover"
                body="The system automatically inspects your schema: tables, columns, data types, row counts, foreign key relationships. What used to require a data catalog team and several weeks of interviews happens in seconds. You see your warehouse's structure laid out before you've made a single decision."
              />
              <WorkflowStep
                number="3"
                icon={<Layers className="w-4 h-4" />}
                title="Select"
                body="Choose which tables form your data product. Group related tables — typically a fact table and its dimension tables — into a logical unit that represents a business domain: finance, operations, sales, supply chain. One data product can serve multiple KPIs and business processes."
              />
              <WorkflowStep
                number="4"
                icon={<FlaskConical className="w-4 h-4" />}
                title="Analyze"
                body="Automated metadata analysis profiles every column in your selected tables: semantic tagging (measure, dimension, time identifier, foreign key), relationship inference, and data quality signals. The system builds a working understanding of your schema's business meaning, not just its technical structure."
              />
              <WorkflowStep
                number="5"
                icon={<Bot className="w-4 h-4" />}
                title="Define KPIs"
                body="An AI assistant helps define KPIs conversationally. Describe what you want to measure in plain language — 'gross margin by product line' or 'revenue variance against prior year.' The assistant generates SQL, validates it against your actual data, and adds strategic metadata: thresholds, comparison periods, business process mappings, and ownership. Non-technical stakeholders can define what matters."
              />
              <WorkflowStep
                number="6"
                icon={<CheckCircle2 className="w-4 h-4" />}
                title="Validate"
                body="Every KPI query is tested against your live data source before it's registered. You see actual results — real numbers from your warehouse — so you know the query is correct before monitoring begins. No surprises in production. No silent failures discovered three weeks later."
              />
              <motion.div variants={fadeUp} className="flex gap-5">
                <div className="flex-shrink-0 flex flex-col items-center">
                  <div className="w-10 h-10 rounded-full bg-indigo-600/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
                    <BookOpen className="w-4 h-4" />
                  </div>
                </div>
                <div className="pb-2">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-xs font-bold text-indigo-500 uppercase tracking-widest">
                      Step 7
                    </span>
                  </div>
                  <h3 className="text-white font-semibold text-base mb-2 leading-snug">Register</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    One action registers the data product, its KPIs, and all associated metadata
                    into the Decision Studio registry. The system immediately begins monitoring.
                    Threshold breaches surface as situation cards. The same metadata that defined
                    the KPI now powers root-cause analysis and executive briefings.
                  </p>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-6">
        <SectionDivider />
      </div>

      {/* ═══════════════════════════════════════════
          4. WHAT MAKES THIS DIFFERENT
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
              What makes this different
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-200 text-lg leading-relaxed mb-12"
            >
              The workflow is different in three specific ways from how most analytics tools
              approach data onboarding.
            </motion.p>

            <motion.div variants={stagger} className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <DifferentiatorCard
                icon={<Database className="w-4 h-4" />}
                title="No data movement"
                body="Your data stays in your warehouse. Decision Studio queries it in place. No copying, no syncing, no drift between your warehouse and a secondary store. The analysis always runs against the current state of your data — not a snapshot from last Tuesday."
              />
              <DifferentiatorCard
                icon={<Bot className="w-4 h-4" />}
                title="AI-assisted KPI definition"
                body="You don't write SQL. You describe what you want to measure. The AI generates, validates, and refines queries conversationally. Non-technical stakeholders — CFOs, COOs, heads of commercial — can define what matters without going through a developer and waiting for the next sprint."
              />
              <DifferentiatorCard
                icon={<BookOpen className="w-4 h-4" />}
                title="Registry, not just a connection"
                body="Every KPI gets strategic metadata: thresholds, ownership, business process mapping, comparison period logic. This isn't a connection string — it's a knowledge asset. The same metadata that defines the KPI informs every downstream analysis, briefing, and outcome measurement."
              />
            </motion.div>
          </motion.div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-6">
        <SectionDivider />
      </div>

      {/* ═══════════════════════════════════════════
          5. PLATFORM SUPPORT
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
              Platform support
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-200 text-lg leading-relaxed mb-4"
            >
              Decision Studio adapts to your infrastructure, not the other way around.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-400 leading-relaxed mb-10"
            >
              Bring your own warehouse. The onboarding workflow works identically regardless
              of which platform your data lives on — the same seven steps, the same AI-assisted
              KPI definition, the same registry output.
            </motion.p>

            <motion.div variants={fadeUp} className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              <PlatformBadge name="Google BigQuery" status="production" />
              <PlatformBadge name="Snowflake" status="supported" />
              <PlatformBadge name="Databricks" status="supported" />
              <PlatformBadge name="PostgreSQL" status="supported" />
              <PlatformBadge name="DuckDB" status="local" />
            </motion.div>

            <motion.div
              variants={fadeUp}
              className="mt-6 rounded-lg bg-slate-900/60 border border-slate-800/60 px-5 py-4"
            >
              <p className="text-sm text-slate-400 leading-relaxed">
                Additional warehouse integrations are added based on customer need. If your
                platform isn't listed, mention it when you request a conversation.
              </p>
            </motion.div>
          </motion.div>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-6">
        <SectionDivider />
      </div>

      {/* ═══════════════════════════════════════════
          6. FROM ONBOARDING TO MONITORING
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
              What happens next
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-200 text-lg leading-relaxed mb-5"
            >
              Registration isn't the end of the process — it's the start of the analytical pipeline.
            </motion.p>

            <motion.p
              variants={fadeUp}
              className="text-slate-400 leading-relaxed mb-10"
            >
              Once a data product is registered, Decision Studio's Situation Awareness agent
              begins monitoring those KPIs immediately. The metadata you defined during onboarding —
              thresholds, comparison periods, business process mappings — drives every subsequent
              analysis. There's no separate configuration step for monitoring. The onboarding
              workflow produces everything the system needs.
            </motion.p>

            <motion.div variants={fadeUp} className="space-y-4">
              {[
                {
                  label: 'Threshold breaches',
                  desc: 'Surface automatically as situation cards — no manual alert setup required.',
                },
                {
                  label: 'Root-cause analysis',
                  desc: 'Runs against the same schema you registered. Dimensional isolation uses the column semantics profiled during onboarding.',
                },
                {
                  label: 'Executive briefings',
                  desc: 'Framed using the KPI ownership and business process mappings from the registry. The briefing is relevant to the right person because the metadata says who owns what.',
                },
                {
                  label: 'Outcome measurement',
                  desc: 'Value Assurance tracks whether approved decisions worked — using the same KPI definitions as a baseline. The onboarding data closes the accountability loop.',
                },
              ].map(({ label, desc }) => (
                <div
                  key={label}
                  className="flex items-start gap-4 rounded-lg bg-slate-900/40 border border-slate-800/40 px-5 py-4"
                >
                  <Zap className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-white text-sm font-semibold mb-0.5">{label}</p>
                    <p className="text-slate-400 text-sm leading-relaxed">{desc}</p>
                  </div>
                </div>
              ))}
            </motion.div>

            <motion.div variants={fadeUp} className="mt-8">
              <Link
                to="/how-it-works"
                className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 text-sm font-medium transition-colors group"
              >
                See the full pipeline
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          7. CTA
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
                <Database className="w-5 h-5 text-indigo-400" />
              </div>
            </div>

            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4">
              Ready to connect your data?
            </h2>

            <p className="text-slate-400 max-w-lg mx-auto mb-8 leading-relaxed">
              Tell us what your data infrastructure looks like and what you want to measure.
              We'll walk through whether Decision Studio is the right fit — no implementation
              commitment required.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/landing#conversation"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition-colors"
              >
                Request a Conversation
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/how-it-works"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 font-semibold text-sm transition-colors border border-slate-700/60"
              >
                See the Full Pipeline
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <p className="mt-5 text-xs text-slate-600">
              Questions about a specific warehouse or integration? Mention it — we'll give you
              a straight answer about what's supported and what's in progress.
            </p>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          FOOTER
      ═══════════════════════════════════════════ */}
      <footer className="border-t border-slate-800/40 py-10 px-6">
        <div
          className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-slate-500"
          style={font}
        >
          <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-6">
            <Link
              to="/landing"
              className="font-bold text-white hover:text-slate-200 transition-colors"
              style={font}
            >
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
            <Link to="/insights/bi-modernization" className="text-slate-400 hover:text-white transition-colors">
              Insights
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
