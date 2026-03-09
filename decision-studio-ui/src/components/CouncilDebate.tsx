import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Loader2, MessageSquare } from 'lucide-react';

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

  // Inject kpiName into a few context-specific phrases
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
  const [feed, setFeed] = useState<Array<{ id: string, text: string, personaId: string }>>([]);
  const [activeSpeakerId, setActiveSpeakerId] = useState<string | null>(null);

  const FIRM_NAMES: Record<string, string> = {
    mckinsey: 'McKinsey & Company',
    bcg: 'BCG',
    bain: 'Bain & Company',
  };

  // Get full persona objects
  const councilMembers = useMemo(() => (
    activePersonas.map(id =>
      availablePersonas.find(p => p.id === id) || { id, label: id, color: 'text-slate-400' }
    )
  ), [activePersonas, availablePersonas]);

  // Simulate live conversation feed
  useEffect(() => {
    if (phase === 0) return;

    let timeoutId: ReturnType<typeof setTimeout>;

    const addThought = () => {
      const randomPersona = councilMembers[Math.floor(Math.random() * councilMembers.length)];
      if (!randomPersona) return;

      const thoughts = getThoughtsForPersona(randomPersona.id);
      const randomThought = thoughts.length > 0
        ? thoughts[Math.floor(Math.random() * thoughts.length)]
        : 'Analysing...';

      setActiveSpeakerId(randomPersona.id);
      
      setFeed(prev => [
        { 
          id: Math.random().toString(36).substr(2, 9), 
          text: randomThought, 
          personaId: randomPersona.id 
        }, 
        ...prev.slice(0, 4) // Keep last 5
      ]);

      // Reset active speaker after a short burst
      setTimeout(() => setActiveSpeakerId(null), 400);

      // Schedule next thought
      timeoutId = setTimeout(addThought, Math.random() * 500 + 400);
    };

    addThought();

    return () => clearTimeout(timeoutId);
  }, [phase, councilMembers]);

  return (
    <div className="bg-slate-900 border border-indigo-500/30 rounded-xl p-6 relative overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 relative z-10">
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
          <div>
            <h4 className="text-sm font-bold text-white">Council in Session</h4>
            <p className="text-xs text-slate-400">
              {phase === 1 && "Phase 1: Generative Hypotheses"}
              {phase === 2 && "Phase 2: Adversarial Review"}
              {phase === 3 && "Phase 3: Strategic Synthesis"}
            </p>
          </div>
        </div>
      </div>

      {/* Avatars Row */}
      <div className="flex justify-center gap-6 mb-8 relative z-10">
        {councilMembers.map(member => {
          const isActive = activeSpeakerId === member.id;
          return (
            <div key={member.id} className="flex flex-col items-center gap-2 transition-all duration-300">
              <div className={`relative w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${isActive ? `border-indigo-400 bg-indigo-500/20 scale-110 shadow-[0_0_15px_rgba(99,102,241,0.5)]` : 'border-slate-700 bg-slate-800'}`}>
                <User className={`w-6 h-6 ${member.color}`} />
                {isActive && (
                  <motion.div 
                    layoutId="speaking-indicator"
                    className="absolute -bottom-1 -right-1 w-4 h-4 bg-indigo-500 rounded-full border-2 border-slate-900 flex items-center justify-center"
                  >
                    <MessageSquare className="w-2 h-2 text-white" />
                  </motion.div>
                )}
              </div>
              <span className={`text-[10px] font-medium transition-colors ${isActive ? 'text-white' : 'text-slate-500'}`}>
                {member.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Live Feed Terminal — hidden when real Stage 1 data is available */}
      {(!stageOneHypotheses || phase < 2) && (
        <div className="bg-slate-950/80 rounded-lg p-4 h-48 overflow-hidden border border-slate-800 relative z-10">
          <div className="absolute top-2 right-3 text-[9px] text-slate-600 uppercase tracking-wider">Live Transcript</div>
          <div className="flex flex-col-reverse h-full gap-3">
            <AnimatePresence initial={false}>
              {feed.map((item) => {
                const persona = councilMembers.find(p => p.id === item.personaId);
                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0 }}
                    className="flex gap-3 items-start"
                  >
                    <span className={`text-[10px] font-bold uppercase min-w-[60px] text-right mt-0.5 ${persona?.color || 'text-slate-500'}`}>
                      {persona?.label || 'Unknown'}
                    </span>
                    <p className="text-xs text-slate-300 font-mono leading-relaxed">
                      {item.text}
                    </p>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Real Stage 1 Firm Hypothesis Cards */}
      {stageOneHypotheses && phase >= 2 && (
        <div className="mt-4 space-y-3">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Stage 1 Hypotheses — {phase === 2 ? 'Cross-review in progress...' : 'Synthesis in progress...'}
          </p>
          {Object.entries(stageOneHypotheses).map(([firmId, hyp]: [string, any]) => (
            <div key={firmId} className="bg-slate-800/60 border border-slate-700 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-bold text-white">
                  {FIRM_NAMES[firmId.toLowerCase()] ?? (firmId.charAt(0).toUpperCase() + firmId.slice(1))}
                </span>
                {hyp.framework && (
                  <span className="text-xs text-slate-400 italic">{hyp.framework}</span>
                )}
              </div>
              {hyp.hypothesis && (
                <p className="text-sm text-slate-300 leading-snug mb-2">{hyp.hypothesis}</p>
              )}
              {hyp.proposed_option?.title && (
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-semibold text-blue-400 uppercase tracking-wider">Proposed:</span>
                  <span className="text-xs text-blue-300 font-medium">{hyp.proposed_option.title}</span>
                </div>
              )}
              {hyp.conviction && (
                <div className="mt-1.5">
                  <span className="text-[10px] font-semibold text-slate-500 uppercase">Conviction: </span>
                  <span className={`text-xs font-semibold ${
                    hyp.conviction === 'High' ? 'text-emerald-400' :
                    hyp.conviction === 'Medium' ? 'text-amber-400' : 'text-slate-400'
                  }`}>{hyp.conviction}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Progress Stepper */}
      <div className="flex items-center gap-2 mt-6 relative z-10">
        {[1, 2, 3].map(step => (
          <div key={step} className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
            <motion.div 
              className="h-full bg-indigo-500"
              initial={{ width: "0%" }}
              animate={{ width: step < phase ? "100%" : step === phase ? "60%" : "0%" }}
              transition={{ duration: 0.5 }}
            />
          </div>
        ))}
      </div>

      {/* Background Ambience */}
      <div className="absolute inset-0 bg-gradient-to-b from-indigo-900/5 to-transparent pointer-events-none" />
    </div>
  );
};
