/**
 * DecisionMakerLanding — the default view for principals whose
 * workflow_role is 'decision_maker' (2026-08-25, Wave 4 item 16, Stage 6).
 *
 * A distilled "what's awaiting my decision" queue, backed by the new
 * GET /workflows/solutions/pending endpoint (Stages 3-5) — replacing the
 * situations dashboard as the DEFAULT landing view only. This is an entry
 * point / disclosure-depth adaptation, never a permission: the "View full
 * dashboard" escape hatch is always present, matching the invariant stated
 * in docs/architecture/decision_framer_and_decision_maker_personas_design.md
 * ("role sets the default, not a permission").
 *
 * Wrapped in its own AppShell, same as DashboardView — this replaces
 * DashboardView at the /dashboard route for decision_maker principals, and
 * without its own AppShell the global nav would silently disappear here,
 * the same class of bug fixed earlier this session for CompanyProfile.tsx
 * and DataProductOnboardingNew.tsx.
 *
 * User-caught, live (2026-08-26): the first version of this component wired
 * a click straight into DeepFocusView via handleDeepAnalysis — which re-ran
 * Deep Analysis for real, against BigQuery, every time. A pending decision
 * is a completed recommendation awaiting sign-off, not an invitation to
 * redo the analysis. Clicking now navigates directly to the Executive
 * Briefing's snapshot of what synthesis already produced — the exact same
 * "review a fixed artifact" pattern value_assurance_solutions.briefing_snapshot
 * already uses for the POST-approval case (Portfolio replay); this is its
 * pre-approval counterpart, not a new pattern.
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Inbox, ArrowRight, Clock, RefreshCw } from 'lucide-react';
import { AppShell } from '../components/shared/AppShell';
import { PrincipalSelector } from '../components/shared/PrincipalSelector';
import { getPendingDecisions, getPendingDecisionSnapshot, PendingDecisionSummary } from '../api/client';
import { Principal } from '../api/types';

function timeAgo(iso?: string | null): string {
  if (!iso) return '';
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '';
  const mins = Math.floor((Date.now() - then) / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

interface DecisionMakerLandingProps {
  principalId: string;
  clientId: string;
  currentPrincipal: Principal;
  availablePrincipals: Principal[];
  onSelectPrincipal: (id: string) => void;
  onViewFullDashboard: () => void;
}

export function DecisionMakerLanding({
  principalId,
  clientId,
  currentPrincipal,
  availablePrincipals,
  onSelectPrincipal,
  onViewFullDashboard,
}: DecisionMakerLandingProps) {
  const navigate = useNavigate();
  const [pending, setPending] = useState<PendingDecisionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [openingId, setOpeningId] = useState<string | null>(null);

  useEffect(() => {
    if (!principalId || !clientId) return;
    let canceled = false;
    getPendingDecisions(principalId, clientId)
      .then((rows) => { if (!canceled) setPending(rows); })
      .catch((e: unknown) => { if (!canceled) setError(e instanceof Error ? e.message : 'Failed to load pending decisions'); });
    return () => { canceled = true; };
  }, [principalId, clientId]);

  const loading = pending === null && !error;

  // Opens the completed recommendation's snapshot — never re-runs DA/SF.
  // Prefers this browser's own localStorage cache (written by
  // CouncilDebatePage.tsx the moment synthesis completed, same key
  // ExecutiveBriefing.tsx already reads directly); falls back to the
  // server-side snapshot (Stage 4.1) for any other session/device.
  async function openPendingDecision(item: PendingDecisionSummary) {
    if (!item.situation_id) {
      setError('This recommendation has no linked situation to open.');
      return;
    }
    const localKey = `briefing_${item.situation_id}`;
    if (localStorage.getItem(localKey)) {
      navigate(`/briefing/${item.situation_id}`);
      return;
    }
    setOpeningId(item.request_id);
    try {
      const snapshot = await getPendingDecisionSnapshot(item.request_id);
      localStorage.setItem(localKey, JSON.stringify(snapshot));
      navigate(`/briefing/${item.situation_id}`);
    } catch {
      setError(
        'No saved snapshot found for this recommendation yet — it may predate snapshot capture. ' +
        'Re-running the analysis is the only way to see it, and is not done automatically.'
      );
    } finally {
      setOpeningId(null);
    }
  }

  return (
    <AppShell>
      <div className="min-h-full bg-background text-foreground p-8 font-sans">
        <header className="mb-8 flex justify-between items-start max-w-5xl mx-auto">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Awaiting Your Decision</h1>
            <p className="text-sm text-slate-400 mt-1">
              Recommendations ready for {currentPrincipal.name}'s sign-off
            </p>
          </div>
          <div className="flex items-start gap-4">
            <PrincipalSelector
              selectedPrincipal={principalId}
              availablePrincipals={availablePrincipals}
              onSelectPrincipal={onSelectPrincipal}
            />
            <button
              onClick={onViewFullDashboard}
              className="mt-5 flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm text-slate-300 transition-colors"
            >
              View full dashboard <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </header>

        <main className="max-w-5xl mx-auto">
          {error && (
            <div className="mb-6 p-4 bg-severity-critical/10 border border-severity-critical/20 rounded-lg text-severity-critical text-sm">
              {error}
            </div>
          )}

          {loading && (
            <div className="flex items-center gap-2 text-slate-500 text-sm py-16 justify-center">
              <RefreshCw className="w-4 h-4 animate-spin" /> Loading pending decisions…
            </div>
          )}

          {!loading && pending && pending.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center border border-dashed border-slate-800 rounded-xl">
              <Inbox className="w-10 h-10 text-slate-700 mb-4" />
              <h2 className="text-lg font-semibold text-white mb-1">Nothing awaiting your decision</h2>
              <p className="text-sm text-slate-500 max-w-md">
                Recommendations from the Framer team will appear here once a situation has been
                investigated and is ready for your sign-off.
              </p>
            </div>
          )}

          {!loading && pending && pending.length > 0 && (
            <div className="space-y-3">
              {pending.map((item) => {
                const isOpening = openingId === item.request_id;
                return (
                  <div
                    key={item.request_id}
                    className="border-l-[3px] border-l-indigo-500 bg-card border border-border rounded-xl p-5 flex items-center justify-between gap-4 transition-colors hover:bg-slate-900/60 cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500/60"
                    onClick={() => { if (!isOpening) openPendingDecision(item); }}
                    role="button"
                    tabIndex={0}
                    aria-busy={isOpening}
                    onKeyDown={(e) => { if ((e.key === 'Enter' || e.key === ' ') && !isOpening) { e.preventDefault(); openPendingDecision(item); } }}
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-white truncate">
                        {item.summary || 'Recommendation pending review'}
                      </p>
                      <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                        {item.kpi_id && <span className="font-mono">{item.kpi_id}</span>}
                        {item.created_at && (
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" /> {timeAgo(item.created_at)}
                          </span>
                        )}
                      </div>
                    </div>
                    <span className="flex items-center gap-1 text-xs font-semibold uppercase tracking-widest text-indigo-400 shrink-0">
                      {isOpening ? (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <>Review <ArrowRight className="w-3.5 h-3.5" /></>
                      )}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </main>
      </div>
    </AppShell>
  );
}
