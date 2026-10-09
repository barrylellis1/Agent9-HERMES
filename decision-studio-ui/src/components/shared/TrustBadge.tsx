import { CheckCircle2, HelpCircle, Calculator, XCircle } from 'lucide-react';
import type { TrustState } from '../../utils/trustState';

/**
 * Tested is the only state with a colour accent. Assumed is the normal state
 * for most items, so it stays neutral rather than reading as a warning.
 */
export function TrustBadge({ state, held }: { state: TrustState; held?: boolean }) {
  if (state === 'tested' && held === false) {
    return (
      <span data-testid="trust-badge" data-state="tested" className="inline-flex flex-shrink-0 items-center gap-1 rounded border border-severity-critical px-1.5 py-0.5 text-[10px] font-medium text-severity-critical">
        <XCircle className="h-3 w-3" /> Tested · did not hold
      </span>
    );
  }
  if (state === 'tested') {
    return (
      <span data-testid="trust-badge" data-state="tested" className="inline-flex flex-shrink-0 items-center gap-1 rounded border border-severity-opportunity px-1.5 py-0.5 text-[10px] font-medium text-severity-opportunity print:text-emerald-700">
        <CheckCircle2 className="h-3 w-3" /> Tested
      </span>
    );
  }
  if (state === 'calculated') {
    return (
      <span data-testid="trust-badge" data-state="calculated" className="inline-flex flex-shrink-0 items-center gap-1 rounded border border-slate-600 px-1.5 py-0.5 text-[10px] font-medium text-slate-300 print:text-slate-700">
        <Calculator className="h-3 w-3" /> Calculated
      </span>
    );
  }
  return (
    <span data-testid="trust-badge" data-state="assumed" className="inline-flex flex-shrink-0 items-center gap-1 rounded border border-slate-600 px-1.5 py-0.5 text-[10px] font-medium text-slate-400 print:text-slate-600">
      <HelpCircle className="h-3 w-3" /> Assumed
    </span>
  );
}

export default TrustBadge;
