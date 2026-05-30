import { useEffect, useRef, useState } from 'react';
import { AlertTriangle, CheckCircle2, Loader2, Send, UserCheck } from 'lucide-react';
import {
  type AccountabilityInterviewResponse,
  chatAccountabilityInterview,
  confirmAccountabilityInterview,
  startAccountabilityInterview,
} from '../api/client';

interface Props {
  clientId: string;
}

const STATUS_ICON: Record<string, string> = {
  confirmed: '✓',
  modified:  '~',
  rejected:  '✗',
  proposed:  '·',
};

const STATUS_COLOR: Record<string, string> = {
  confirmed: 'text-emerald-400',
  modified:  'text-amber-400',
  rejected:  'text-red-400',
  proposed:  'text-slate-500',
};

const PHASE_LABEL: Record<string, string> = {
  process_suggestion: 'Phase 1 — Process Suggestion',
  gap_resolution:     'Phase 2 — Gap Resolution',
  review:             'Phase 3 — Review',
};

export function AccountabilityInterviewPanel({ clientId }: Props) {
  const [interviewState, setInterviewState] = useState<AccountabilityInterviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [inputText, setInputText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmed, setConfirmed] = useState<{ rows_written: number } | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Chat history for display: flat list of {role, text}
  const [displayMessages, setDisplayMessages] = useState<{ role: 'agent' | 'user'; text: string }[]>([]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [displayMessages]);

  const startInterview = async () => {
    setLoading(true);
    setError(null);
    setConfirmed(null);
    try {
      const resp = await startAccountabilityInterview(clientId);
      setInterviewState(resp);
      setDisplayMessages([{ role: 'agent', text: resp.agent_message }]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to start interview');
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (text: string) => {
    if (!interviewState || !text.trim()) return;
    setLoading(true);
    setError(null);
    setInputText('');

    setDisplayMessages((prev) => [...prev, { role: 'user', text }]);

    try {
      const resp = await chatAccountabilityInterview(interviewState.session_id, clientId, text);
      setInterviewState(resp);
      setDisplayMessages((prev) => [...prev, { role: 'agent', text: resp.agent_message }]);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => sendMessage(inputText);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const approveAll = async () => {
    if (!interviewState) return;
    const approved = interviewState.proposed_assignments.filter(
      (a) => a.status === 'confirmed' || a.status === 'modified',
    );
    if (approved.length === 0) {
      setError('No confirmed or modified assignments to approve.');
      return;
    }
    setConfirming(true);
    setError(null);
    try {
      const result = await confirmAccountabilityInterview(clientId, approved);
      setConfirmed(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to confirm assignments');
    } finally {
      setConfirming(false);
    }
  };

  // ── Not started ────────────────────────────────────────────────────────────
  if (!interviewState && !loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16 gap-6">
        <UserCheck className="w-12 h-12 text-indigo-400 opacity-70" />
        <div className="text-center">
          <h3 className="text-lg font-semibold text-white mb-1">Assign KPI Ownership</h3>
          <p className="text-sm text-slate-400 max-w-sm">
            Start an AI-guided interview to assign accountable principals to each KPI.
            The agent will use your process registry to batch-suggest assignments.
          </p>
        </div>
        <button
          onClick={startInterview}
          className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors"
        >
          Start Interview
        </button>
      </div>
    );
  }

  if (loading && !interviewState) {
    return (
      <div className="flex items-center gap-3 py-16 justify-center text-slate-400 text-sm">
        <Loader2 className="w-5 h-5 animate-spin" />
        Starting interview…
      </div>
    );
  }

  const coverage = interviewState ? Math.round(interviewState.coverage_pct * 100) : 0;
  const unassignedCount = interviewState?.unassigned_kpis.length ?? 0;
  const confirmedRows = interviewState?.proposed_assignments.filter(
    (a) => a.status === 'confirmed' || a.status === 'modified',
  ) ?? [];

  // ── Two-panel layout ───────────────────────────────────────────────────────
  return (
    <div className="flex flex-col gap-4">
      {/* Phase header */}
      {interviewState && (
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
            {PHASE_LABEL[interviewState.phase] ?? interviewState.phase}
          </span>
          {interviewState.interview_complete && (
            <span className="flex items-center gap-1 text-xs text-emerald-400 font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Interview complete
            </span>
          )}
        </div>
      )}

      <div className="grid grid-cols-[1fr_1.2fr] gap-4 min-h-[480px]">
        {/* ── Left: chat ── */}
        <div className="flex flex-col bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Interview</span>
          </div>

          {/* Message list */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
            {displayMessages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={
                    'max-w-[85%] rounded-xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ' +
                    (msg.role === 'user'
                      ? 'bg-indigo-600/80 text-white'
                      : 'bg-slate-800 text-slate-200')
                  }
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-slate-800 rounded-xl px-4 py-2.5">
                  <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Suggested responses */}
          {!interviewState?.interview_complete &&
            (interviewState?.suggested_responses ?? []).length > 0 && (
              <div className="px-4 py-2 border-t border-slate-800 flex flex-wrap gap-2">
                {interviewState!.suggested_responses.map((s, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(s)}
                    disabled={loading}
                    className="px-3 py-1 rounded-full border border-slate-700 text-xs text-slate-300 hover:border-indigo-500 hover:text-indigo-300 transition-colors disabled:opacity-50"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

          {/* Input */}
          {!interviewState?.interview_complete && (
            <div className="px-4 py-3 border-t border-slate-800 flex items-end gap-2">
              <textarea
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Reply to the agent…"
                rows={2}
                disabled={loading}
                className="flex-1 resize-none rounded-lg bg-slate-800 border border-slate-700 text-sm text-white placeholder-slate-500 px-3 py-2 focus:outline-none focus:border-indigo-500 disabled:opacity-50"
              />
              <button
                onClick={handleSend}
                disabled={loading || !inputText.trim()}
                className="p-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white transition-colors"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* ── Right: proposed assignments ── */}
        <div className="flex flex-col bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Proposed Assignments
            </span>
            {interviewState && (
              <span className="text-xs text-slate-400">
                Coverage:{' '}
                <span className={coverage >= 80 ? 'text-emerald-400 font-semibold' : 'text-amber-400 font-semibold'}>
                  {coverage}%
                </span>{' '}
                ({(interviewState.proposed_assignments.filter(a => a.status !== 'rejected').length)} /{' '}
                {interviewState.proposed_assignments.length + unassignedCount} KPIs)
              </span>
            )}
          </div>

          {/* Conflict warnings */}
          {(interviewState?.conflict_warnings ?? []).length > 0 && (
            <div className="mx-4 mt-3 space-y-1">
              {interviewState!.conflict_warnings.map((w, i) => (
                <div key={i} className="flex items-start gap-2 p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
                  <span className="text-xs text-amber-300">{w}</span>
                </div>
              ))}
            </div>
          )}

          {/* Unassigned KPIs */}
          {unassignedCount > 0 && (
            <div className="mx-4 mt-3 px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700">
              <span className="text-xs text-slate-400">
                {unassignedCount} KPI{unassignedCount !== 1 ? 's' : ''} unassigned:{' '}
                {interviewState!.unassigned_kpis.slice(0, 3).map((k) => k.name).join(', ')}
                {unassignedCount > 3 ? `… +${unassignedCount - 3}` : ''}
              </span>
            </div>
          )}

          {/* Assignments table */}
          <div className="flex-1 overflow-y-auto px-4 mt-3 min-h-0">
            {(interviewState?.proposed_assignments ?? []).length === 0 ? (
              <p className="text-xs text-slate-500 italic py-2">
                No assignments proposed yet. Start the interview to begin.
              </p>
            ) : (
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="pb-1.5 pr-3 text-left text-slate-500 font-semibold uppercase tracking-wide w-5"></th>
                    <th className="pb-1.5 pr-3 text-left text-slate-500 font-semibold uppercase tracking-wide">Principal</th>
                    <th className="pb-1.5 pr-3 text-left text-slate-500 font-semibold uppercase tracking-wide">KPI</th>
                    <th className="pb-1.5 pr-3 text-left text-slate-500 font-semibold uppercase tracking-wide">Scope</th>
                    <th className="pb-1.5 text-left text-slate-500 font-semibold uppercase tracking-wide">Role</th>
                  </tr>
                </thead>
                <tbody>
                  {interviewState!.proposed_assignments.map((a, i) => (
                    <tr key={i} className="border-b border-slate-800/50">
                      <td className={`py-2 pr-3 font-bold ${STATUS_COLOR[a.status] ?? 'text-slate-500'}`}>
                        {STATUS_ICON[a.status] ?? '·'}
                      </td>
                      <td className="py-2 pr-3 text-slate-300 truncate max-w-[100px]">{a.principal_name}</td>
                      <td className="py-2 pr-3 text-white font-medium truncate max-w-[120px]">{a.kpi_name}</td>
                      <td className="py-2 pr-3 text-slate-400">
                        {a.scope_dimension
                          ? <span className="font-mono">{a.scope_dimension}={a.scope_value}</span>
                          : <span className="text-slate-600 italic">Global</span>}
                      </td>
                      <td className="py-2">
                        {a.role === 'accountable' ? (
                          <span className="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">Acct</span>
                        ) : (
                          <span className="px-1.5 py-0.5 rounded bg-slate-700 text-slate-400 border border-slate-600">Resp</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Footer: approve button */}
          <div className="px-4 py-3 border-t border-slate-800 flex items-center justify-between gap-3">
            {confirmed ? (
              <span className="flex items-center gap-1.5 text-sm text-emerald-400 font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                {confirmed.rows_written} row{confirmed.rows_written !== 1 ? 's' : ''} written to registry
              </span>
            ) : (
              <>
                <span className="text-xs text-slate-500">
                  {confirmedRows.length} assignment{confirmedRows.length !== 1 ? 's' : ''} ready to approve
                </span>
                <button
                  onClick={approveAll}
                  disabled={confirming || confirmedRows.length === 0}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold transition-colors"
                >
                  {confirming ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                  Approve All Confirmed
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-200 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
