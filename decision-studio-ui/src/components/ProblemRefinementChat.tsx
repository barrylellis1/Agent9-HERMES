import React, { useState, useRef, useEffect, useCallback } from 'react';
import { MessageCircle, Send, SkipForward, AlertCircle, Loader2 } from 'lucide-react';
import { refineProblem, ProblemRefinementResult, ProblemRefinementRequest, MarketSignal } from '../api/client';

interface ProblemRefinementChatProps {
  deepAnalysisOutput: any;
  principalContext: any;
  principalId: string;
  onComplete: (result: ProblemRefinementResult) => void;
  onCancel: () => void;
  initialMarketSignals?: MarketSignal[];
}

const TOPIC_LABELS: Record<string, string> = {
  hypothesis_validation: 'Validating Findings',
  scope_boundaries: 'Defining Scope',
  external_context: 'External Context',
  constraints: 'Constraints',
  success_criteria: 'Success Criteria',
  replication_potential: 'Replication Targets',
};

const STYLE_LABELS: Record<string, { label: string; color: string }> = {
  analytical: { label: 'McKinsey', color: 'bg-blue-100 text-blue-800' },
  visionary: { label: 'BCG', color: 'bg-purple-100 text-purple-800' },
  pragmatic: { label: 'Bain', color: 'bg-green-100 text-green-800' },
};

export const ProblemRefinementChat: React.FC<ProblemRefinementChatProps> = ({
  deepAnalysisOutput,
  principalContext,
  principalId,
  onComplete,
  onCancel,
  initialMarketSignals: _initialMarketSignals,
}) => {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentTopic, setCurrentTopic] = useState<string>('hypothesis_validation');
  const [topicsCompleted, setTopicsCompleted] = useState<string[]>([]);
  const [turnCount, setTurnCount] = useState(0);
  const [refinementState, setRefinementState] = useState<Partial<ProblemRefinementResult>>({});
  const [suggestedResponses, setSuggestedResponses] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const decisionStyle = principalContext?.decision_style || 'analytical';
  const styleInfo = STYLE_LABELS[decisionStyle] || STYLE_LABELS.analytical;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  const handleRefinementResult = useCallback((result: ProblemRefinementResult) => {
    // Add agent message to chat
    setMessages(prev => [...prev, { role: 'assistant', content: result.agent_message }]);
    
    // Update state
    setCurrentTopic(result.current_topic);
    setTopicsCompleted(result.topics_completed);
    setTurnCount(result.turn_count);
    setSuggestedResponses(result.suggested_responses || []);
    setRefinementState(result);

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
      };

      const result = await refineProblem(request);
      handleRefinementResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setIsLoading(false);
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

  const hasBenchmarks = (
    deepAnalysisOutput?.execution?.kt_is_is_not?.benchmark_segments?.some(
      (s: any) => s.benchmark_type === 'internal_benchmark'
    ) ??
    deepAnalysisOutput?.kt_is_is_not?.benchmark_segments?.some(
      (s: any) => s.benchmark_type === 'internal_benchmark'
    ) ??
    false
  );
  const totalTopics = hasBenchmarks ? 6 : 5;
  const progressPercentage = (topicsCompleted.length / totalTopics) * 100;

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

      {/* Messages */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
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
          </div>
        ))}
        
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

      {/* Sticky footer */}
      <div className="flex-shrink-0">
      {/* Suggested responses */}
      {suggestedResponses.length > 0 && !isLoading && (
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

      {/* Input area */}
      <div className="px-3 py-2 border-t border-slate-700">
        <div className="flex items-center gap-1.5">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your response..."
            disabled={isLoading}
            className="flex-1 px-3 py-1.5 text-sm bg-slate-700 text-white border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-slate-800 placeholder-slate-400"
          />
          <button
            onClick={() => sendMessage(inputValue)}
            disabled={!inputValue.trim() || isLoading}
            className="p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-slate-600 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
          <button
            onClick={handleSkipToSolutions}
            disabled={isLoading}
            className="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-700 rounded-lg transition-colors"
            title="Skip to Solutions"
          >
            <SkipForward className="w-5 h-5" />
          </button>
        </div>
      </div>
      </div>
    </div>
  );
};

export default ProblemRefinementChat;
