import { Circle, Clock, User } from 'lucide-react'
import type { ImmediateAction } from '../../api/types'

/**
 * The first tasks, as a checklist with an owner and a deadline on each.
 *
 * Phase 13 Cat 3 / M5. Renders `List[ImmediateAction]` — the typed replacement
 * for the prose `next_steps` list, which had no owner field at all and so could
 * (and did) produce steps nobody was accountable for.
 *
 * WHAT THIS DOES NOT DO
 * ---------------------
 * It does not invent an owner. M5's rule is that inconsistent action counts or
 * missing owners are fixed in the PROMPT, not papered over in the component —
 * a UI that fills "Finance team" into every blank owner makes the prompt defect
 * invisible and hands the reader an accountability that was never assigned.
 * A missing owner therefore renders as "unassigned", visibly.
 *
 * Checkboxes are deliberately non-interactive: nothing persists this state, and
 * a tick that silently vanishes on reload is worse than no tick.
 */

interface ImmediateActionsChecklistProps {
  actions: ImmediateAction[]
  /** Legacy prose steps, shown only when the typed list is empty. */
  fallbackSteps?: string[]
}

function dueLabel(days: number | null | undefined): string | null {
  if (days == null || !Number.isFinite(days)) return null
  if (days <= 0) return 'Immediately'
  if (days === 1) return 'Within 1 day'
  if (days <= 7) return `Within ${days} days`
  if (days <= 14) return 'Within 2 weeks'
  if (days <= 31) return `Within ${Math.round(days / 7)} weeks`
  return `Within ${Math.round(days / 30)} months`
}

/** Urgency band drives the badge colour only — never the order, which is the model's. */
function dueTone(days: number | null | undefined): string {
  if (days == null) return 'text-slate-400 border-slate-600'
  if (days <= 7) return 'text-severity-critical border-severity-critical print:text-red-700'
  if (days <= 30) return 'text-severity-warning border-severity-warning print:text-amber-700'
  return 'text-slate-400 border-slate-600'
}

export function ImmediateActionsChecklist({ actions, fallbackSteps = [] }: ImmediateActionsChecklistProps) {
  if (!actions.length) {
    if (!fallbackSteps.length) return null
    return (
      <div>
        <h4 className="mb-2 text-sm font-semibold text-slate-200 print:text-slate-800">Immediate Actions</h4>
        {/* Said plainly rather than styled to look equivalent. These steps have no
            owner field behind them — the reader is entitled to know which of the
            two shapes they are looking at. */}
        <p className="mb-3 text-xs text-slate-500 print:text-slate-600">
          This run produced prose steps rather than assigned actions, so no owners or deadlines are attached.
        </p>
        <ol className="space-y-1.5">
          {fallbackSteps.map((s, i) => (
            <li key={i} className="flex items-start gap-2.5">
              <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-slate-700 text-xs font-bold text-white print:bg-slate-800">
                {i + 1}
              </span>
              <span className="text-sm text-slate-300 print:text-slate-700">{s}</span>
            </li>
          ))}
        </ol>
      </div>
    )
  }

  return (
    <div>
      <h4 className="mb-3 text-sm font-semibold text-slate-200 print:text-slate-800">
        Immediate Actions
        <span className="ml-2 text-xs font-normal text-slate-500">{actions.length} assigned</span>
      </h4>
      <ul data-testid="immediate-actions" className="space-y-2">
        {actions.map((a, i) => {
          const due = dueLabel(a.due_by_days)
          return (
            <li
              key={i}
              data-testid="immediate-action"
              className="rounded-lg border border-slate-700 bg-slate-800/40 p-3 print:border-slate-200 print:bg-white"
            >
              <div className="flex items-start gap-2.5">
                <Circle className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-600 print:text-slate-400" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium leading-snug text-slate-200 print:text-slate-900">
                    {a.action_text}
                  </p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] ${
                        a.owner
                          ? 'border-slate-600 text-slate-300 print:text-slate-700'
                          : 'border-severity-warning text-severity-warning print:text-amber-700'
                      }`}
                    >
                      <User className="h-2.5 w-2.5" />
                      {a.owner || 'unassigned'}
                    </span>
                    {due && (
                      <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] ${dueTone(a.due_by_days)}`}>
                        <Clock className="h-2.5 w-2.5" />
                        {due}
                      </span>
                    )}
                  </div>
                  {a.why_it_matters && (
                    <p className="mt-1.5 text-xs leading-snug text-slate-500 print:text-slate-600">
                      {a.why_it_matters}
                    </p>
                  )}
                </div>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default ImmediateActionsChecklist
