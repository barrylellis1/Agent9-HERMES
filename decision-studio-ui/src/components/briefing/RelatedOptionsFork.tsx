import { ArrowRight } from 'lucide-react';

/**
 * RelatedOptionsFork — shows which real proposals a stated open question
 * touches, per the 2026-08-28 compact-brief restructure.
 *
 * The reference mockup shows two hand-authored interpretive cards ("If it's
 * pricing" / "If it's cost"). No structured data backs that — only the long
 * free-prose `tension` string and `options_affected` (an array of option
 * ids) exist on the backend payload. Synthesizing short interpretive labels
 * from nothing would be exactly the fabrication this session has repeatedly
 * declined to do elsewhere (option-title rewording, D/F work). This
 * component is the honest substitute: it resolves `options_affected`
 * against the real options and shows THEIR OWN real titles and impact
 * ranges side by side — real content a reader can act on, not invented
 * framing.
 *
 * Deliberately tied to the SAME tension `ContradictionBanner` renders right
 * beside it (both sit just above the options list as of 2026-08-29 — see
 * ExecutiveBriefing.tsx's fold-order comment) — not a search across all
 * tensions for one with more affected options, which would show a fork
 * about a different open question than the one the reader was just told
 * about.
 */
interface RelatedOptionsForkProps {
  optionsAffected?: string[] | null;
  options: Array<{ id: string | null; title: string; roi: string | null; recommended?: boolean }>;
}

export function RelatedOptionsFork({ optionsAffected, options }: RelatedOptionsForkProps) {
  const resolved = (optionsAffected || [])
    .map((id) => {
      const idx = options.findIndex((o) => o.id === id);
      return idx >= 0 ? { ...options[idx], letter: String.fromCharCode(65 + idx) } : null;
    })
    .filter((o): o is NonNullable<typeof o> => o !== null);

  if (resolved.length === 0) return null;

  // Single-option degrade: no fork to show with one side, just a pointer.
  if (resolved.length === 1) {
    const o = resolved[0];
    return (
      <p className="mb-6 text-xs text-slate-400">
        Affects: <span className="text-slate-200 font-medium">Option {o.letter} — {o.title}</span>
      </p>
    );
  }

  // Two or more: the mockup's card-pair-with-divider layout. A 3rd (rare —
  // not present in the fixture this was verified against) stacks below the
  // pair rather than squeezing into a 3-column grid, keeping the two-sided
  // framing intact for the common case.
  const [first, second, ...rest] = resolved;

  const Card = ({ o }: { o: (typeof resolved)[number] }) => (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-3.5 print:border-slate-300 print:bg-white">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[10px] font-bold text-severity-warning border border-severity-warning/50 rounded w-4 h-4 flex items-center justify-center flex-shrink-0 print:text-amber-700 print:border-amber-600">
          {o.letter}
        </span>
        <p className="text-xs font-semibold text-slate-200 leading-snug print:text-slate-900">{o.title}</p>
      </div>
      {o.roi && <p className="text-[11px] text-severity-opportunity print:text-emerald-700">{o.roi}</p>}
    </div>
  );

  return (
    <div className="mb-6" data-testid="related-options-fork">
      <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] gap-2 sm:items-center">
        <Card o={first} />
        <span className="text-[10px] font-mono uppercase tracking-widest text-severity-warning text-center print:text-amber-700">
          Either / or
        </span>
        <Card o={second} />
      </div>
      {rest.length > 0 && (
        <div className="mt-2 space-y-2">
          {rest.map((o) => (
            <div key={o.id ?? o.letter} className="flex items-center gap-1.5 text-[11px] text-slate-500">
              <ArrowRight className="w-3 h-3 flex-shrink-0" />
              <span>Also affects Option {o.letter} — {o.title}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
