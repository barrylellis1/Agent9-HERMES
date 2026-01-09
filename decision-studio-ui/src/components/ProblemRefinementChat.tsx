import React, { useState, useRef, useEffect, useCallback } from 'react';
import { MessageCircle, Send, SkipForward, AlertCircle, Loader2 } from 'lucide-react';
import { refineProblem, ProblemRefinementResult, ProblemRefinementRequest } from '../api/client';

interface ProblemRefinementChatProps {
  deepAnalysisOutput: any;
  principalContext: any;
  principalId: string;
  onComplete: (result: ProblemRefinementResult) => void;
  onCancel: () => void;
}

const TOPIC_LABELS: Record<string, string> = {
  hypothesis_validation: 'Validating Findings',
  scope_boundaries: 'Defining Scope',
  external_context: 'External Context',
  constraints: 'Constraints',
  success_criteria: 'Success Criteria',
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

  const progressPercentage = (topicsCompleted.length / 5) * 100;

  return (
    <div className="flex flex-col h-full bg-slate-800 rounded-lg shadow-lg">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700 bg-slate-900 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5 text-indigo-400" />
            <h3 className="font-semibold text-white">Problem Refinement</h3>
            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${styleInfo.color}`}>
              {styleInfo.label} Style
            </span>
          </div>
          <button
            onClick={onCancel}
            className="text-slate-400 hover:text-white text-sm"
          >
            Cancel
          </button>
        </div>
        
        {/* Progress bar */}
        <div className="mt-2">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span>{TOPIC_LABELS[currentTopic] || currentTopic}</span>
            <span>{topicsCompleted.length}/5 topics</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-1.5">
            <div
              className="bg-indigo-500 h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[300px] max-h-[400px]">
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

      {/* Suggested responses */}
      {suggestedResponses.length > 0 && !isLoading && (
        <div className="px-4 py-2 border-t border-slate-700">
          <div className="flex flex-wrap gap-2">
            {suggestedResponses.map((response, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestedResponse(response)}
                className="px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-full transition-colors"
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
        <div className="px-4 py-2 border-t border-slate-700 bg-slate-900">
          <div className="text-xs text-slate-400 space-y-1">
            {refinementState.exclusions && refinementState.exclusions.length > 0 && (
              <div>
                <span className="font-medium text-slate-300">Exclusions:</span>{' '}
                {refinementState.exclusions.map(e => e.value).join(', ')}
              </div>
            )}
            {refinementState.external_context && refinementState.external_context.length > 0 && (
              <div>
                <span className="font-medium text-slate-300">Context:</span>{' '}
                {refinementState.external_context.slice(0, 2).join('; ')}
              </div>
            )}
            {refinementState.constraints && refinementState.constraints.length > 0 && (
              <div>
                <span className="font-medium text-slate-300">Constraints:</span>{' '}
                {refinementState.constraints.slice(0, 2).join('; ')}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="px-4 py-3 border-t border-slate-700">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your response..."
            disabled={isLoading}
            className="flex-1 px-4 py-2 bg-slate-700 text-white border border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-slate-800 placeholder-slate-400"
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
  );
};

export default ProblemRefinementChat;
