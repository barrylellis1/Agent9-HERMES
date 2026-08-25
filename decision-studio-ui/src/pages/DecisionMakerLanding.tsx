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
 */
import { useEffect, useState } from 'react';
import { Inbox, ArrowRight, Clock, RefreshCw } from 'lucide-react';
import { AppShell } from '../components/shared/AppShell';
import { PrincipalSelector } from '../components/shared/PrincipalSelector';
import { getPendingDecisions, PendingDecisionSummary } from '../api/client';
import { Principal, Situation } from '../api/types';

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
  /** Situations from the SA scan already in flight for this session — a
   *  pending decision's situation_id is matched against these to jump
   *  straight into DeepFocusView; a scan that hasn't completed yet (or
   *  never surfaced this situation) degrades to an informational row,
   *  never a broken link. */
  situations: Situation[];
  scanComplete: boolean;
  onOpenSituation: (situation: Situation) => void;
  onViewFullDashboard: () => void;
}

export function DecisionMakerLanding({
  principalId,
  clientId,
  currentPrincipal,
  availablePrincipals,
  onSelectPrincipal,
  situations,
  scanComplete,
  onOpenSituation,
  onViewFullDashboard,
}: DecisionMakerLandingProps) {
  const [pending, setPending] = useState<PendingDecisionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!principalId || !clientId) return;
    let canceled = false;
    getPendingDecisions(principalId, clientId)
      .then((rows) => { if (!canceled) setPending(rows); })
      .catch((e: unknown) => { if (!canceled) setError(e instanceof Error ? e.message : 'Failed to load pending decisions'); });
    return () => { canceled = true; };
  }, [principalId, clientId]);

  const loading = pending === null && !error;

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
                const matchedSituation = situations.find(
                  (s) => s.situation_id === item.situation_id
                );
                const openable = Boolean(matchedSituation);
                return (
                  <div
                    key={item.request_id}
                    className={`border-l-[3px] border-l-indigo-500 bg-card border border-border rounded-xl p-5 flex items-center justify-between gap-4 transition-colors ${
                      openable ? 'hover:bg-slate-900/60 cursor-pointer' : 'opacity-70'
                    }`}
                    onClick={() => { if (matchedSituation) onOpenSituation(matchedSituation); }}
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
                    {openable ? (
                      <span className="flex items-center gap-1 text-xs font-semibold uppercase tracking-widest text-indigo-400 shrink-0">
                        Review <ArrowRight className="w-3.5 h-3.5" />
                      </span>
                    ) : (
                      <span className="text-xs text-slate-600 shrink-0">
                        {scanComplete ? 'Not in current scan' : 'Scanning…'}
                      </span>
                    )}
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
