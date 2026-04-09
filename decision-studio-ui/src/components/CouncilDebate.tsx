import React, { useState, useEffect, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface Persona {
  id: string;
  label: string;
  color: string;
  icon?: any;
}

interface CouncilDebateProps {
  phase: number; // 1=Hypothesis, 2=Cross-Review, 3=Synthesis
  activePersonas: string[]; // IDs of active personas
  availablePersonas: Persona[];
  stageOneHypotheses?: Record<string, any> | null;
  kpiName?: string;
}

// Phase label shown in the terminal header
const PHASE_LABELS: Record<number, string> = {
  1: 'STAGE 1 — HYPOTHESIS GENERATION',
  2: 'STAGE 2 — CROSS-REVIEW',
  3: 'STAGE 3 — SYNTHESIS',
};

export const CouncilDebate: React.FC<CouncilDebateProps> = ({
  phase,
  activePersonas,
  availablePersonas,
  stageOneHypotheses,
  kpiName = 'KPI',
}) => {
  // Phase 1: Independent hypothesis formation — persona-specific framework language
  const PHASE1_THOUGHTS: Record<string, string[]> = {
    mckinsey: [
      'Applying MECE decomposition to isolate primary cost drivers...',
      'Three Horizons profit pool mapping in progress...',
      'Hypothesis-driven analysis: identifying the critical lever...',
      'Structuring the problem using pyramid principle...',
      'Separating structural shift from cyclical variance...',
      'Where-else analysis: which segments are NOT affected?',
      'Quantifying the addressable opportunity within the variance...',
      'Stress-testing the leading hypothesis against contrary evidence...',
    ],
    bcg: [
      'Growth-Share Matrix positioning across business units...',
      'Experience curve analysis on unit economics...',
      'Mapping competitive cost position vs. industry benchmark...',
      'Deconstruction: fixed vs. variable cost absorption at current volume...',
      'Identifying advantage segments vs. disadvantage segments...',
      'Portfolio view: where is value being created vs. destroyed?',
      'Relative market share implications for pricing power...',
      'Advantage Matrix: assessing scale vs. differentiation trade-off...',
    ],
    bain: [
      'Full Potential assessment: where is performance falling short?',
      'Rapid diagnostic: which levers have the fastest payback?',
      'Net value identification — separating noise from signal...',
      "Founder's Mentality lens: is this a complexity tax?",
      'Implementation risk calibration for each intervention...',
      "Owner's economics: what would the best operator do here?",
      'Prioritising interventions by effort-to-impact ratio...',
      'Decision effectiveness check: who owns this outcome?',
    ],
    default: [
      'Forming independent hypothesis from first principles...',
      'Reviewing dimensional analysis for primary driver...',
      'Calibrating confidence against available evidence...',
      'Structuring intervention options by time horizon...',
    ],
  };

  // Phase 2: Cross-review — adversarial critique language
  const PHASE2_THOUGHTS: Record<string, string[]> = {
    mckinsey: [
      'Reviewing BCG proposal: does the experience curve logic hold at this volume?',
      "Stress-testing Bain's implementation timeline against resource constraints...",
      'MECE check: are the proposed options mutually exclusive?',
      'Flagging overlap between option mechanisms — are these truly distinct?',
      'Identifying the assumption most likely to break under execution...',
      'Which proposal has the weakest evidence base? Flagging now...',
    ],
    bcg: [
      "Pressure-testing McKinsey's structural hypothesis against market data...",
      'Reviewing Bain proposal: is the quick-win sustainable or one-time?',
      'Portfolio coherence check: do these options conflict at the margin?',
      'Growth-Share lens: does the recommended option protect the core?',
      'Flagging pricing assumptions — are competitor responses modelled?',
      'Experience curve: does option A accelerate or delay cost improvement?',
    ],
    bain: [
      'McKinsey option: strong diagnosis, but who owns the execution?',
      'Reviewing BCG proposal: robust analysis, implementation plan is thin...',
      'Sequencing risk: can option B be executed before option A is resolved?',
      'NPS implication: how does each option affect customer relationships?',
      'Flagging missing BATNA — what if the primary option stalls?',
      'Results delivery check: are 90-day milestones achievable as stated?',
    ],
    default: [
      'Cross-reviewing peer proposals for logical consistency...',
      'Flagging contradictions between recommended approaches...',
      'Adversarial stress-test in progress...',
      'Identifying blind spots in alternative hypotheses...',
    ],
  };

  // Phase 3: Synthesis — council convergence language
  const PHASE3_THOUGHTS: Record<string, string[]> = {
    mckinsey: [
      'Synthesising three frameworks into MECE option set...',
      'Pyramid principle: structuring the recommendation narrative...',
      'Ensuring options span full time-horizon spectrum...',
      'Quantifying recovery range anchored to observed variance...',
    ],
    bcg: [
      'Portfolio view: ranking options by risk-adjusted impact...',
      'Mapping option trade-offs on the Advantage Matrix...',
      'Calibrating investment-to-return ratio across all three options...',
      'Ensuring structural option addresses root cause, not symptom...',
    ],
    bain: [
      'Translating analysis into actionable next steps...',
      'Owner assignment: every action needs a name and a date...',
      'Implementation sequencing: what must happen in Week 1?',
      'Results framework: defining what success looks like in 90 days...',
    ],
    default: [
      'Council converging on ranked options...',
      'Synthesising three analytical frameworks...',
      'Building implementation roadmap from debate output...',
      'Calibrating confidence scores across option set...',
    ],
  };

  if (kpiName && kpiName !== 'KPI') {
    PHASE1_THOUGHTS.mckinsey.unshift(`Isolating root drivers of ${kpiName} variance using MECE...`);
    PHASE1_THOUGHTS.bcg.unshift(`Experience curve analysis on ${kpiName} cost structure...`);
    PHASE1_THOUGHTS.bain.unshift(`Full Potential gap: what is the ${kpiName} recovery opportunity?`);
    PHASE2_THOUGHTS.default.unshift(`Cross-reviewing all proposals against ${kpiName} data signals...`);
  }

  const getThoughtsForPersona = (personaId: string): string[] => {
    const dict = phase === 1 ? PHASE1_THOUGHTS
               : phase === 2 ? PHASE2_THOUGHTS
               : PHASE3_THOUGHTS;
    const lower = personaId.toLowerCase();
    return dict[lower] ?? dict['default'] ?? [];
  };

  // Terminal log entries: each has a timestamp string (captured once at creation), persona label, and text
  const [feed, setFeed] = useState<Array<{ id: string; ts: string; personaLabel: string; personaColor: string; text: string }>>([]);

  const FIRM_NAMES: Record<string, string> = {
    mckinsey: 'McKinsey & Company',
    bcg: 'BCG',
    bain: 'Bain & Company',
  };

  const councilMembers = useMemo(() => (
    activePersonas.map(id =>
      availablePersonas.find(p => p.id === id) || { id, label: id, color: 'text-slate-400' }
    )
  ), [activePersonas, availablePersonas]);

  // Stable ref for councilMembers/phase so the interval closure stays fresh
  const councilRef = useRef(councilMembers);
  const phaseRef = useRef(phase);
  useEffect(() => { councilRef.current = councilMembers; }, [councilMembers]);
  useEffect(() => { phaseRef.current = phase; }, [phase]);

  useEffect(() => {
    if (phase === 0) return;

    let timeoutId: ReturnType<typeof setTimeout>;

    const addThought = () => {
      const members = councilRef.current;
      const randomPersona = members[Math.floor(Math.random() * members.length)];
      if (!randomPersona) return;

      const thoughts = getThoughtsForPersona(randomPersona.id);
      const randomThought = thoughts.length > 0
        ? thoughts[Math.floor(Math.random() * thoughts.length)]
        : 'Analysing...';

      const ts = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

      setFeed(prev => [
        {
          id: Math.random().toString(36).substr(2, 9),
          ts,
          personaLabel: randomPersona.label,
          personaColor: randomPersona.color,
          text: randomThought,
        },
        ...prev.slice(0, 7),
      ]);

      timeoutId = setTimeout(addThought, Math.random() * 600 + 500);
    };

    addThought();
    return () => clearTimeout(timeoutId);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  // Progress bar width per phase segment
  const progressPct = (step: number) => {
    if (step < phase) return 100;
    if (step === phase) return 60;
    return 0;
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      {/* Terminal header */}
      <div className="px-4 py-3 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
        <div>
          <div className="text-[10px] font-mono text-slate-500 mb-0.5">
            [{new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}]
          </div>
          <div className="text-xs font-mono font-semibold text-slate-300 uppercase tracking-wider">
            {PHASE_LABELS[phase] ?? 'COUNCIL IN SESSION'}
          </div>
        </div>
        {/* Phase progress bars */}
        <div className="flex items-center gap-1.5">
          {[1, 2, 3].map(step => (
            <div key={step} className="w-12 h-1 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-slate-400 rounded-full"
                initial={{ width: '0%' }}
                animate={{ width: `${progressPct(step)}%` }}
                transition={{ duration: 0.4 }}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Terminal log — hidden when real Stage 1 data is available */}
      {(!stageOneHypotheses || phase < 2) && (
        <div className="bg-slate-950 px-4 py-3 h-44 overflow-hidden font-mono">
          <div className="flex flex-col-reverse h-full gap-2">
            <AnimatePresence initial={false}>
              {feed.map(item => (
                <motion.div
                  key={item.id}
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                  className="flex gap-2 items-start leading-snug"
                >
                  <span className="text-[9px] text-slate-600 flex-shrink-0 mt-0.5 tabular-nums">
                    [{item.ts}]
                  </span>
                  <span className={`text-[10px] font-semibold uppercase flex-shrink-0 w-16 truncate ${item.personaColor}`}>
                    {item.personaLabel}
                  </span>
                  <span className="text-[10px] text-slate-400 leading-relaxed">
                    {item.text}
                  </span>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Real Stage 1 Firm Hypothesis Cards */}
      {stageOneHypotheses && phase >= 2 && (
        <div className="px-4 py-4 space-y-3">
          <p className="text-[10px] font-mono font-semibold text-slate-500 uppercase tracking-wider">
            {phase === 2 ? 'CROSS-REVIEW IN PROGRESS' : 'SYNTHESIS IN PROGRESS'} — STAGE 1 HYPOTHESES
          </p>
          {Object.entries(stageOneHypotheses).map(([firmId, hyp]: [string, any]) => (
            <div key={firmId} className="bg-slate-800/50 border border-slate-700 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-white font-mono">
                  {FIRM_NAMES[firmId.toLowerCase()] ?? (firmId.charAt(0).toUpperCase() + firmId.slice(1))}
                </span>
                {hyp.framework && (
                  <span className="text-[10px] text-slate-500 italic font-mono">{hyp.framework}</span>
                )}
              </div>
              {hyp.hypothesis && (
                <p className="text-xs text-slate-300 leading-snug mb-2">{hyp.hypothesis}</p>
              )}
              {hyp.proposed_option?.title && (
                <div className="flex items-center gap-1.5">
                  <span className="text-[9px] font-mono font-semibold text-slate-500 uppercase tracking-wider">Proposed:</span>
                  <span className="text-[10px] text-slate-300 font-medium">{hyp.proposed_option.title}</span>
                </div>
              )}
              {hyp.conviction && (
                <div className="mt-1.5">
                  <span className="text-[9px] font-mono font-semibold text-slate-600 uppercase">Conviction: </span>
                  <span className={`text-[10px] font-mono font-semibold ${
                    hyp.conviction === 'High' ? 'text-emerald-400' :
                    hyp.conviction === 'Medium' ? 'text-amber-400' : 'text-slate-400'
                  }`}>{hyp.conviction}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
