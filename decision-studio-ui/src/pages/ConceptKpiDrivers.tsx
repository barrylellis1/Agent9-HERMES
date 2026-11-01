/**
 * Concept illustration of the KPI Drivers screen, for the public site.
 * Renders the real exhibit with illustrative data, inside a frame that says
 * it is a concept. Used to produce the image on the landing page.
 */
import { TheoryLayerView } from '../components/theory/TheoryLayerExhibit';
import { conceptKpiDrivers } from '../components/theory/theoryLayerConcept';

export function ConceptKpiDrivers() {
  return (
    <div className="min-h-screen bg-slate-950 flex items-start justify-center p-6">
      <figure id="concept-frame" className="w-full max-w-4xl m-0">
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-t-xl border border-b-0 border-indigo-500/40 bg-indigo-950/60 px-5 py-3">
          <div className="flex items-center gap-3">
            <span className="rounded-full border border-indigo-400/50 bg-indigo-500/20 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-widest text-indigo-200">
              Concept
            </span>
            <span className="text-sm font-semibold text-white">How your KPIs connect</span>
          </div>
          <span className="text-xs text-slate-400">Illustrative data. Not built as shown.</span>
        </div>
        <div className="rounded-b-xl border border-indigo-500/40 bg-slate-950 [&>div]:max-w-none [&>div]:rounded-none [&>div]:border-0">
          <TheoryLayerView data={conceptKpiDrivers} />
        </div>
      </figure>
    </div>
  );
}
