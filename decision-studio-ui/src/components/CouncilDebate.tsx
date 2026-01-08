import React, { useState, useEffect } from 'react';
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
}

// Mock "thoughts" for the live feed effect
const MOCK_THOUGHTS = {
  1: [
    "Analyzing historical variance patterns...",
    "Correlating with external market indices...",
    "Checking inventory turnover rates...",
    "Flagging pricing inconsistencies in Q3...",
    "Reviewing supplier contracts for force majeure..."
  ],
  2: [
    "Challenging the pricing hypothesis - demand was stable.",
    "The inventory data contradicts the supply chain argument.",
    "Have we considered the currency fluctuation impact?",
    "Risk assessment: Proposed solution ignores compliance mandates.",
    "Validating financial feasibility of Option A..."
  ],
  3: [
    "Synthesizing findings into coherent options...",
    "Ranking solutions by ROI and Time-to-Value...",
    "Drafting the executive summary...",
    "Finalizing implementation roadmap...",
    "Generating risk mitigation strategies..."
  ]
};

export const CouncilDebate: React.FC<CouncilDebateProps> = ({ 
  phase, 
  activePersonas, 
  availablePersonas 
}) => {
  const [feed, setFeed] = useState<Array<{ id: string, text: string, personaId: string }>>([]);
  const [activeSpeakerId, setActiveSpeakerId] = useState<string | null>(null);

  // Get full persona objects
  const councilMembers = activePersonas.map(id => 
    availablePersonas.find(p => p.id === id) || { id, label: id, color: 'text-slate-400' }
  );

  // Simulate live conversation feed
  useEffect(() => {
    if (phase === 0) return;

    const thoughts = MOCK_THOUGHTS[phase as keyof typeof MOCK_THOUGHTS] || [];
    let timeoutId: ReturnType<typeof setTimeout>;

    const addThought = () => {
      const randomPersona = councilMembers[Math.floor(Math.random() * councilMembers.length)];
      const randomThought = thoughts[Math.floor(Math.random() * thoughts.length)];
      
      if (!randomPersona) return;

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
      setTimeout(() => setActiveSpeakerId(null), 800);

      // Schedule next thought
      timeoutId = setTimeout(addThought, Math.random() * 1500 + 1000);
    };

    addThought();

    return () => clearTimeout(timeoutId);
  }, [phase, activePersonas]); // Re-run when phase changes

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

      {/* Live Feed Terminal */}
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
