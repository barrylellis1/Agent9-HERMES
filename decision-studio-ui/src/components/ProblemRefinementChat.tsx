import React, { useState, useRef, useEffect, useCallback } from 'react';
import { MessageCircle, Send, SkipForward, AlertCircle, Loader2 } from 'lucide-react';
import { refineProblem, ProblemRefinementResult, ProblemRefinementRequest, MarketSignal, FramingDecision, FramingPrompt } from '../api/client';
import { FramingGateCard } from './FramingGateCard';

/**
 * Phase 19 — the progress-lifting plumbing that didn't exist before this:
 * `currentTopic`/`topicsCompleted` were component-local, surfaced to the
 * parent only via the all-or-nothing `onComplete`/`onCancel`. DeepFocusView
 * (Slice 6) needs `framingRequired` on EVERY turn, live, to grey out
 * "Generate Solutions" and the other two bypass paths while the gate is
 * pending — not just once, at the end.
 */
export interface RefinementProgress {
  currentTopic: string;
  topicsCompleted: string[];
  framingRequired: boolean;
  scqaSummary?: string | null;
  /**
   * Present only on the turn that submitted it — later turns' results don't
   * re-echo it. The parent must remember this itself (it does — see
   * useDecisionStudio.ts's `framingDecision` state) since by the time the
   * interview finishes, the LAST turn's own framing_decision field is back
   * to undefined.
   */
  framingDecision?: FramingDecision | null;
  /**
   * Phase 20 — lifted so DeepFocusView's LEFT-panel "Causal Neighbourhood"
   * evidence section can render the same alternatives/snapshots the compact
   * right-panel FramingGateCard shows, off the SAME turn-0 response (§14
   * decision 9: evidence and the question arrive atomically, never a
   * separate lazy fetch). Present on the presentation turn; undefined once
   * framing is answered (matches framingDecision's own only-that-turn shape).
   */
  framingPrompt?: FramingPrompt | null;
}

interface ProblemRefinementChatProps {
  deepAnalysisOutput: any;
  principalContext: any;
  principalId: string;
  onComplete: (result: ProblemRefinementResult) => void;
  onCancel: () => void;
  initialMarketSignals?: MarketSignal[];
  onTopicProgress?: (progress: RefinementProgress) => void;
}

const TOPIC_LABELS: Record<string, string> = {
  hypothesis_validation: 'Validating Findings',
  scope_boundaries: 'Defining Scope',
  external_context: 'External Context',
  constraints: 'Constraints',
  success_criteria: 'Success Criteria',
  replication_potential: 'Replication Targets',
  // Problem-shape-routed topics (Stage I B-1) — asked only when the analysis's
  // measured structure makes them the question worth spending a turn on.
  tradeoff_tolerance: 'Trade-off Tolerance',
  segment_specific_causation: 'Why This Segment',
  comparison_baseline: 'Comparison Baseline',
};

/**
 * The principal's decision style, labelled as the decision style.
 *
 * De-branded 2026-08-16 (Phase 18 Category C; `ProblemRefinementChat.tsx:29` in
 * that inventory). This previously read `analytical -> "McKinsey"`, `visionary ->
 * "BCG"`, `pragmatic -> "Bain"`, each with an approximation of that firm's brand
 * colour — so a PERSON's decision style rendered as a consulting firm's identity,
 * with no persona involved anywhere in the mapping.
 *
 * That is a stranger claim than the briefing's firm attribution was. The briefing
 * at least named firms whose frameworks the council prompt genuinely invokes;
 * this badge asserted that Sarah Chen, who is analytical, *is* McKinsey.
 *
 * The label now states the attribute it was always derived from, which is also
 * more useful to the reader: it tells them which style the interview is adapting
 * to. Colours are neutral and chosen only to keep the three distinguishable.
 *
 * NOTE: `decision_style` currently resolves to "analytical" for effectively every
 * principal in production — nothing seeds `metadata.decision_style`, per the
 * A9_Principal_Context_Agent audit. So this badge is near-constant today. It is
 * at least now near-constantly TRUE.
 */
const STYLE_LABELS: Record<string, { label: string; color: string }> = {
  analytical: { label: 'Analytical', color: 'bg-blue-100 text-blue-800' },
  visionary: { label: 'Visionary', color: 'bg-purple-100 text-purple-800' },
  pragmatic: { label: 'Pragmatic', color: 'bg-green-100 text-green-800' },
};

export const ProblemRefinementChat: React.FC<ProblemRefinementChatProps> = ({
  deepAnalysisOutput,
  principalContext,
  principalId,
  onComplete,
  onCancel,
  initialMarketSignals: _initialMarketSignals,
  onTopicProgress,
}) => {
  const [messages, setMessages] = useState<Array<{ role: string; content: string; transparency_tier?: number; tier_label?: string }>>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentTopic, setCurrentTopic] = useState<string>('hypothesis_validation');
  const [topicsCompleted, setTopicsCompleted] = useState<string[]>([]);
  const [turnCount, setTurnCount] = useState(0);
  // Phase 19 — the framing gate's own submit state, separate from the normal
  // chat input row (which is hidden entirely while this is truthy).
  const [isSubmittingFraming, setIsSubmittingFraming] = useState(false);
  // Turns spent on the CURRENT topic, reset whenever the topic changes. The
  // server judges topic completion per topic; it used to count every assistant
  // message in the conversation, so from turn 3 onward each topic completed the
  // moment it was reached.
  const [turnsOnCurrentTopic, setTurnsOnCurrentTopic] = useState(0);
  const [refinementState, setRefinementState] = useState<Partial<ProblemRefinementResult>>({});
  const [suggestedResponses, setSuggestedResponses] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const prevTopicRef = useRef<string>('hypothesis_validation');

  const decisionStyle = principalContext?.decision_style || 'analytical';
  const styleInfo = STYLE_LABELS[decisionStyle] || STYLE_LABELS.analytical;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  const handleRefinementResult = useCallback((result: ProblemRefinementResult) => {
    // Add agent message to chat, carrying tier metadata if present
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: result.agent_message,
      transparency_tier: (result as any).transparency_tier,
      tier_label: (result as any).tier_label,
    }]);
    
    // Reset the per-topic counter on a topic change, otherwise advance it.
    // Tracked via a ref, not derived inside a state updater: React invokes
    // updaters twice under StrictMode, which would double-count the turns and
    // trip the auto-complete threshold a turn early.
    if (prevTopicRef.current === result.current_topic) {
      setTurnsOnCurrentTopic(c => c + 1);
    } else {
      setTurnsOnCurrentTopic(0);
      prevTopicRef.current = result.current_topic;
    }

    // Update state
    setCurrentTopic(result.current_topic);
    setTopicsCompleted(result.topics_completed);
    setTurnCount(result.turn_count);
    setSuggestedResponses(result.suggested_responses || []);
    setRefinementState(result);
    setIsSubmittingFraming(false);

    // Phase 19 — lift progress to the parent on EVERY turn, not just at
    // completion. DeepFocusView needs framingRequired live to keep
    // "Generate Solutions" (and the other two bypass paths) blocked for as
    // long as the gate is pending, not just retroactively once the whole
    // interview finishes.
    onTopicProgress?.({
      currentTopic: result.current_topic,
      topicsCompleted: result.topics_completed,
      framingRequired: !!result.framing_required,
      scqaSummary: result.scqa_summary,
      framingDecision: result.framing_decision,
      framingPrompt: result.framing_prompt,
    });

    // Check if refinement is complete
    if (result.ready_for_solutions) {
      onComplete(result);
    }
  }, [onComplete]);

  const startConversation = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const request: ProblemRefinementRequest = {
        principal_id: principalId,
        deep_analysis_output: deepAnalysisOutput,
        principal_context: principalContext,
        conversation_history: [],
        turn_count: 0,
        topics_completed: [],
        turns_on_current_topic: 0,
      };

      const result = await refineProblem(request);
      handleRefinementResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start refinement chat');
    } finally {
      setIsLoading(false);
    }
  }, [principalId, deepAnalysisOutput, principalContext, handleRefinementResult]);

  // Start the conversation on mount (with guard against double-call in StrictMode)
  const hasStarted = useRef(false);
  useEffect(() => {
    if (!hasStarted.current) {
      hasStarted.current = true;
      startConversation();
    }
  }, [startConversation]);

  const sendMessage = async (message: string) => {
    if (!message.trim() || isLoading) return;

    // Add user message to chat
    const newMessages = [...messages, { role: 'user', content: message }];
    setMessages(newMessages);
    setInputValue('');
    setSuggestedResponses([]);
    setIsLoading(true);
    setError(null);

    try {
      const request: ProblemRefinementRequest = {
        principal_id: principalId,
        deep_analysis_output: deepAnalysisOutput,
        principal_context: principalContext,
        conversation_history: newMessages,
        user_message: message,
        current_topic: currentTopic,
        turn_count: turnCount,
        topics_completed: topicsCompleted,
        turns_on_current_topic: turnsOnCurrentTopic,
        // Echo prior typed state back. The server is stateless; without this it
        // re-derives earlier turns heuristically and loses exclusions entirely.
        prior_constraint_items: refinementState.constraint_items || [],
        prior_exclusions: refinementState.exclusions || [],
      };

      const result = await refineProblem(request);
      handleRefinementResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Phase 19 — parallel to sendMessage, but a structured submit: no
   * user_message (a framing decision is not free text), framing_decision
   * carries the whole submission. Deliberately does NOT add a "user"
   * message bubble to the chat — the FramingGateCard IS the record of what
   * was submitted; a duplicated text bubble would be redundant with it.
   */
  const submitFraming = async (decision: FramingDecision) => {
    if (isSubmittingFraming) return;
    setIsSubmittingFraming(true);
    setError(null);

    try {
      const request: ProblemRefinementRequest = {
        principal_id: principalId,
        deep_analysis_output: deepAnalysisOutput,
        principal_context: principalContext,
        conversation_history: messages,
        current_topic: currentTopic,
        turn_count: turnCount,
        topics_completed: topicsCompleted,
        turns_on_current_topic: turnsOnCurrentTopic,
        prior_constraint_items: refinementState.constraint_items || [],
        prior_exclusions: refinementState.exclusions || [],
        framing_decision: decision,
      };

      const result = await refineProblem(request);
      handleRefinementResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record the framing decision');
      setIsSubmittingFraming(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  const handleSuggestedResponse = (response: string) => {
    sendMessage(response);
  };

  const handleSkipToSolutions = () => {
    sendMessage('Proceed to solutions');
  };

  // The one signal every UI gate should read (Phase 19) — supersedes
  // topic_complete, which nothing here ever actually consumed for gating.
  const framingRequired = !!refinementState.framing_required;

  const hasBenchmarks = (
    deepAnalysisOutput?.execution?.kt_is_is_not?.benchmark_segments?.some(
      (s: any) => s.benchmark_type === 'internal_benchmark'
    ) ??
    deepAnalysisOutput?.kt_is_is_not?.benchmark_segments?.some(
      (s: any) => s.benchmark_type === 'internal_benchmark'
    ) ??
    false
  );
  // The sequence is routed off the problem's structure (Stage I B-1), so its
  // length is no longer a function of benchmarks alone — the server reports it.
  // The benchmark heuristic remains only as the pre-first-response fallback.
  const totalTopics = refinementState.topic_sequence?.length || (hasBenchmarks ? 6 : 5);
  const progressPercentage = Math.min(100, (topicsCompleted.length / totalTopics) * 100);

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-slate-800 rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex-shrink-0 px-3 py-2 border-b border-slate-700 bg-slate-900 rounded-t-lg">
        <div className="flex items-center justify-between gap-1">
          <div className="flex items-center gap-1.5 min-w-0">
            <MessageCircle className="w-4 h-4 text-indigo-400 flex-shrink-0" />
            <h3 className="text-sm font-semibold text-white truncate">Refinement</h3>
            <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded-full flex-shrink-0 ${styleInfo.color}`}>
              {styleInfo.label}
            </span>
          </div>
          <button
            onClick={onCancel}
            className="text-slate-400 hover:text-white text-xs flex-shrink-0"
          >
            Cancel
          </button>
        </div>

        {/* Progress bar */}
        <div className="mt-1">
          <div className="flex items-center justify-between text-[10px] text-slate-400 mb-0.5">
            <span>{TOPIC_LABELS[currentTopic] || currentTopic}</span>
            <span>{topicsCompleted.length}/{totalTopics}</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-1">
            <div
              className="bg-indigo-500 h-1 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Market Intelligence signals moved to left panel (DeepFocusView) */}

      {/* Messages — capped, not flex-1, while the framing gate is showing.
          Two flex-1 min-h-0 siblings in the same column (this + the footer
          below) split the remaining space 50/50 regardless of content, so
          the framing gate — which routinely needs most of the panel — was
          still being squeezed into half of it even after making it properly
          scrollable. During framing there's typically only the one
          intro message here; capping it frees the rest for the gate. */}
      <div className={refinementState.framing_prompt
        ? 'flex-shrink-0 max-h-28 overflow-y-auto p-4 space-y-4'
        : 'flex-1 min-h-0 overflow-y-auto p-4 space-y-4'}>
        {messages.map((msg, idx) => {
          // Tier badge color map
          const tierColor =
            msg.transparency_tier === 3 ? 'text-amber-600' :
            msg.transparency_tier === 4 ? 'text-red-500' :
            'text-slate-400';

          return (
            <div
              key={idx}
              className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-700 text-slate-100'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
              {msg.role === 'assistant' && msg.transparency_tier != null && msg.tier_label && (
                <span className={`mt-0.5 text-[9px] uppercase tracking-wide px-1.5 py-0.5 rounded font-medium bg-slate-800 ${tierColor}`}>
                  {msg.tier_label}
                </span>
              )}
            </div>
          );
        })}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-700 rounded-lg px-4 py-2">
              <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
            </div>
          </div>
        )}
        
        {error && (
          <div className="flex justify-center">
            <div className="bg-red-900/50 text-red-300 rounded-lg px-4 py-2 flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Sticky footer — EXCEPT while the framing gate is showing: that card's
          content (up to 6+ alternatives, prior-frame box, constraints,
          falsifier field, submit button) routinely exceeds the space below
          the messages area. flex-shrink-0 here means this wrapper takes
          whatever height its content wants, uncapped by the panel — so with
          FramingGateCard's own overflow-y-auto never actually receiving a
          bounded height to scroll within, the excess just overflows past this
          wrapper and gets hard-clipped by DeepFocusView's overflow-hidden
          ancestor. The submit button (and often the falsifier textarea above
          it) landed below that clip line — genuinely unreachable, not just
          hard to find, however far the page scrolled elsewhere. Found live,
          Aug 2026. flex-1 min-h-0 here instead lets the footer take exactly
          the remaining panel space and hands FramingGateCard's own
          overflow-y-auto a real height to scroll inside. */}
      <div className={refinementState.framing_prompt ? 'flex-1 min-h-0 flex flex-col overflow-hidden' : 'flex-shrink-0'}>
      {/* Suggested responses — NEVER shown while the framing gate is pending
          (framingRequired implies suggested_responses=[] server-side too,
          this is belt-and-suspenders: a chip is a click, and the whole
          point of the structured submit is that a click can't stand in for
          a considered choice). */}
      {suggestedResponses.length > 0 && !isLoading && !framingRequired && (
        <div className="px-3 py-1.5 border-t border-slate-700">
          <div className="flex flex-col gap-1">
            {suggestedResponses.map((response, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestedResponse(response)}
                className="px-2.5 py-1 text-xs text-left bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors line-clamp-2"
              >
                {response}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Accumulated refinements summary */}
      {(refinementState.exclusions?.length || refinementState.external_context?.length ||
        refinementState.constraints?.length || refinementState.validated_hypotheses?.length) && (
        <div className="px-3 py-1.5 border-t border-slate-700 bg-slate-900 max-h-16 overflow-y-auto">
          <div className="text-[10px] text-slate-400 space-y-0.5">
            {refinementState.exclusions && refinementState.exclusions.length > 0 && (
              <div className="truncate">
                <span className="font-medium text-slate-300">Exclusions:</span>{' '}
                {refinementState.exclusions.map(e => e.value).join(', ')}
              </div>
            )}
            {refinementState.external_context && refinementState.external_context.length > 0 && (
              <div className="line-clamp-2">
                <span className="font-medium text-slate-300">Context:</span>{' '}
                {refinementState.external_context.slice(0, 2).map(c => c.length > 80 ? c.substring(0, 80) + '…' : c).join('; ')}
              </div>
            )}
            {refinementState.constraints && refinementState.constraints.length > 0 && (
              <div className="truncate">
                <span className="font-medium text-slate-300">Constraints:</span>{' '}
                {refinementState.constraints.slice(0, 2).join('; ')}
              </div>
            )}
            {refinementState.replication_constraints && refinementState.replication_constraints.length > 0 && (
              <div className="truncate">
                <span className="font-medium text-slate-300">Replication barriers:</span>{' '}
                {refinementState.replication_constraints.slice(0, 2).join('; ')}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Phase 19 — the framing gate replaces the input row entirely while
          pending. No free-text path around it: this is the ONLY thing
          rendered here in that state, not an addition alongside the normal
          input. */}
      {refinementState.framing_prompt ? (
        <div className="border-t border-slate-700 flex-1 min-h-0 flex flex-col overflow-hidden">
          <FramingGateCard
            prompt={refinementState.framing_prompt}
            onSubmit={submitFraming}
            isSubmitting={isSubmittingFraming}
          />
        </div>
      ) : (
        <div className="px-3 py-2 border-t border-slate-700">
          {/* framingRequired but no framing_prompt to show is the rare
              _build_framing_prompt failure case (registry/provider down) —
              the backend still blocks regardless of what's typed here, but
              disabling the row too avoids a confusing "it looks like I can
              type, but nothing I say matters" moment. */}
          <div className="flex items-center gap-1.5">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={framingRequired ? 'Waiting on the framing step to become available...' : 'Type your response...'}
              disabled={isLoading || framingRequired}
              className="flex-1 px-3 py-1.5 text-sm bg-slate-700 text-white border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-slate-800 placeholder-slate-400"
            />
            <button
              onClick={() => sendMessage(inputValue)}
              disabled={!inputValue.trim() || isLoading || framingRequired}
              className="p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-slate-600 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
            <button
              onClick={handleSkipToSolutions}
              disabled={isLoading || framingRequired}
              className="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-30 disabled:pointer-events-none"
              title={framingRequired ? 'Confirm the objective first' : 'Skip to Solutions'}
            >
              <SkipForward className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default ProblemRefinementChat;
