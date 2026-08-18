import { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckCircle, AlertTriangle, Users, ChevronRight, Zap } from 'lucide-react'
import { AssumptionsPanel } from './AssumptionsPanel'

/**
 * Full narrative for ONE option, in a side drawer.
 *
 * Phase 13 Cat 3: the options section previously rendered every option's
 * complete narrative expanded inline — arguments for and against, stakeholder
 * perspectives, prerequisites, triggers — for all three options at once. That is
 * three full analyses stacked above the risk section, which is what pushed the
 * briefing past a 2-minute read. The comparison stays on the page; the narrative
 * moves behind a click.
 *
 * Print is unaffected: the drawer is screen-only, and the print path keeps
 * rendering the expanded narrative inline (a drawer cannot be opened on paper).
 */

interface OptionDetailDrawerProps {
  option: any | null
  optionLabel: string
  onClose: () => void
}

export function OptionDetailDrawer({ option, optionLabel, onClose }: OptionDetailDrawerProps) {
  // Escape closes. A drawer that can only be dismissed by hitting a small target
  // is a trap on the page an executive is skimming.
  useEffect(() => {
    if (!option) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [option, onClose])

  return (
    <AnimatePresence>
      {option && (
        <>
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/60 print:hidden"
          />
          <motion.aside
            initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
            transition={{ type: 'tween', duration: 0.2 }}
            className="fixed right-0 top-0 z-50 flex h-full w-full max-w-lg flex-col border-l border-slate-700 bg-slate-900 shadow-2xl print:hidden"
          >
            <header className="flex flex-shrink-0 items-start justify-between gap-3 border-b border-slate-800 px-5 py-4">
              <div className="min-w-0">
                <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500">{optionLabel}</p>
                <h3 className="text-base font-bold leading-snug text-white">{option.title}</h3>
                {option.subtitle && <p className="mt-0.5 text-xs text-slate-400">{option.subtitle}</p>}
              </div>
              <button
                onClick={onClose}
                aria-label="Close option detail"
                className="flex-shrink-0 rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-800 hover:text-white"
              >
                <X className="h-4 w-4" />
              </button>
            </header>

            <div className="flex-1 overflow-y-auto px-5 py-4">
              {option.description && (
                <p className="mb-4 text-sm leading-relaxed text-slate-300">{option.description}</p>
              )}

              <div className="mb-4 grid grid-cols-2 gap-2">
                {[
                  { label: 'Est. Impact', val: option.roi },
                  { label: 'Investment', val: option.investment },
                  { label: 'Timeline', val: option.timeline },
                  { label: 'Risk', val: option.riskLevel },
                ].map(({ label, val }) => (
                  <div key={label} className="rounded-lg bg-slate-800/60 p-2.5">
                    <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
                    <p className="text-xs font-semibold text-slate-200">{val || '—'}</p>
                  </div>
                ))}
              </div>

              {option.impactBasis && (
                <p className="mb-4 text-xs leading-snug text-slate-500">Basis: {option.impactBasis}</p>
              )}

              {/* Critic-pass findings sit HIGH, not in an appendix. Stage E traces
                  each lever through the causal graph specifically to surface a
                  downstream cost the option's own narrative will not mention. */}
              {option.flagged_side_effects?.length > 0 && (
                <div className="mb-4 rounded-lg border border-amber-700/50 bg-amber-950/20 p-3">
                  <h4 className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-amber-300">
                    <Zap className="h-3.5 w-3.5" /> Side effects flagged against the causal model
                  </h4>
                  <ul className="space-y-1">
                    {option.flagged_side_effects.map((s: string, i: number) => (
                      <li key={i} className="text-xs leading-snug text-amber-200/80">• {s}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="space-y-4">
                {option.prosDetailed?.length > 0 && (
                  <div>
                    <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-slate-300">
                      <CheckCircle className="h-3.5 w-3.5 text-slate-500" /> Arguments For
                    </h4>
                    <ul className="space-y-1.5">
                      {option.prosDetailed.map((p: any, i: number) => (
                        <li key={i} className="flex items-start gap-1.5 text-xs text-slate-400">
                          <ChevronRight className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-slate-600" />
                          <span>{p.point?.replace(/[:]+$/, '')}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {option.consDetailed?.length > 0 && (
                  <div>
                    <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-slate-300">
                      <AlertTriangle className="h-3.5 w-3.5 text-slate-500" /> Arguments Against
                    </h4>
                    <ul className="space-y-1.5">
                      {option.consDetailed.map((c: any, i: number) => (
                        <li key={i} className="flex items-start gap-1.5 text-xs text-slate-400">
                          <ChevronRight className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-slate-600" />
                          <span>{c.point?.replace(/[:]+$/, '')}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {option.lens_views?.length > 0 && (
                  <div>
                    <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-slate-200">
                      {/* "Council Lenses", not "Stakeholder Perspectives" — these are
                          the council's analytical readings, not the views of real
                          stakeholders, and the old heading claimed the latter. */}
                      <Users className="h-3.5 w-3.5" /> Council Lenses
                    </h4>
                    <div data-testid="council-lenses" className="space-y-2">
                      {option.lens_views.map((p: any, i: number) => (
                        <div key={i} data-testid="council-lens-item" className="rounded-lg bg-slate-800/60 p-2.5">
                          <p className="text-xs font-medium text-slate-200">{p.role}</p>
                          <p className="mt-0.5 text-xs text-slate-400">{p.view}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {option.prerequisites?.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-sm font-semibold text-slate-300">Prerequisites</h4>
                    <ul className="space-y-1">
                      {option.prerequisites.map((p: string, i: number) => (
                        <li key={i} className="text-xs text-slate-400">• {p}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {option.implementation_triggers?.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-sm font-semibold text-slate-300">Implementation Triggers</h4>
                    <ul className="space-y-1">
                      {option.implementation_triggers.map((t: string, i: number) => (
                        <li key={i} className="text-xs text-slate-400">• {t}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <AssumptionsPanel
                assumptions={option.key_assumptions || []}
                impactLabel={option.roi}
                defaultOpen
              />
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}

export default OptionDetailDrawer
