import React, { useState, useEffect, useRef } from 'react';
import { RefreshCw, Scan, Activity, Clock, CheckCircle, ChevronDown } from 'lucide-react';
import { KPITile } from '../dashboard/KPITile';
import { HeroBriefing } from '../dashboard/HeroBriefing';
import { AppHeader } from '../shared/AppHeader';
import { SummaryStrip } from '../shared/SummaryStrip';
import { SolutionsProgressBar } from '../shared/SolutionsProgressBar';
import { Situation, OpportunitySignal, Principal } from '../../api/types';
import { getVAPortfolio } from '../../api/client';
import type { StrategyAwarePortfolio } from '../../types/valueAssurance';

interface DashboardViewProps {
  scanComplete: boolean;
  loading: boolean;
  situations: Situation[];
  opportunities?: OpportunitySignal[];
  kpisScanned: number;
  breachCount: number;
  impactLevel: string;
  impactColor: string;
  selectedPrincipal: string;
  availablePrincipals: Principal[];
  currentPrincipal: Principal;
  onSelectPrincipal: (id: string) => void;
  timeframe: string;
  onSelectTimeframe: (tf: string) => void;
  onRefresh: () => void;
  onSelectSituation: (sit: Situation) => void;
  statusMsg: string | null;
  error: string | null;
  delegatedKpiNames?: Set<string>;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  scanComplete,
  loading,
  situations,
  kpisScanned,
  breachCount,
  impactLevel,
  impactColor,
  selectedPrincipal,
  availablePrincipals,
  currentPrincipal,
  onSelectPrincipal,
  timeframe: _timeframe,
  onSelectTimeframe: _onSelectTimeframe,
  onRefresh,
  onSelectSituation,
  statusMsg,
  error,
  delegatedKpiNames = new Set(),
}) => {
  const [portfolio, setPortfolio] = useState<StrategyAwarePortfolio | null>(null);
  const [lastScannedAt, setLastScannedAt] = useState<Date | null>(null);
  const [healthyExpanded, setHealthyExpanded] = useState(false);
  const prevLoadingRef = useRef(loading);

  useEffect(() => {
    if (prevLoadingRef.current && !loading && scanComplete) {
      setLastScannedAt(new Date());
    }
    prevLoadingRef.current = loading;
  }, [loading, scanComplete]);

  const activeKpiIds = new Set(
    (portfolio?.solutions ?? [])
      .filter(s => s.phase !== 'COMPLETE')
      .map(s => s.kpi_id)
  );

  useEffect(() => {
    if (!selectedPrincipal) return;
    const activeClientId = localStorage.getItem('a9_active_client_id') ?? undefined;
    getVAPortfolio(selectedPrincipal, activeClientId)
      .then(setPortfolio)
      .catch(() => setPortfolio(null));
  }, [selectedPrincipal]);

  return (
    <div className="min-h-screen bg-background text-foreground p-8 font-sans relative overflow-x-hidden">

      <AppHeader
        selectedPrincipal={selectedPrincipal}
        availablePrincipals={availablePrincipals}
        onSelectPrincipal={onSelectPrincipal}
        loading={loading}
        onRefresh={onRefresh}
        statusMsg={statusMsg}
        lastScannedAt={lastScannedAt}
      />

      {scanComplete && (
        <SummaryStrip
          kpisScanned={kpisScanned}
          breachCount={breachCount}
          impactLevel={impactLevel}
          impactColor={impactColor}
          situations={situations}
        />
      )}

      {error && (
        <div className="mb-8 p-4 bg-severity-critical/10 border border-severity-critical/20 rounded-lg text-severity-critical text-sm">
          Error: {error}. Is the Agent9 backend running on port 8000?
        </div>
      )}

      <main className="max-w-7xl mx-auto space-y-8 pb-20">

        {portfolio && portfolio.total_solutions > 0 && (
          <SolutionsProgressBar
            portfolio={portfolio}
            selectedPrincipal={selectedPrincipal}
          />
        )}

        {/* Pre-scan state */}
        {!scanComplete && (
          <section className="bg-card border border-border rounded-xl p-8 shadow-2xl relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-900/60 via-slate-900/20 to-indigo-900/20 pointer-events-none" />
            <div className="relative z-10 space-y-6">
              <div className="flex items-center gap-3 text-indigo-300">
                <Scan className="w-6 h-6 animate-pulse" />
                <span className="uppercase tracking-[0.3em] text-xs font-semibold">Auto-scan in progress</span>
              </div>

              <div>
                <h2 className="text-2xl font-semibold text-white mb-2">Evaluating KPI landscape…</h2>
                <p className="text-sm text-slate-400 max-w-2xl">
                  Agent9 is sampling the latest KPI telemetry for {currentPrincipal.name}. We'll surface the highest-impact situations as soon as the scan completes.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4 flex items-center gap-3">
                  <Activity className="w-5 h-5 text-severity-opportunity" />
                  <div>
                    <div className="text-xs text-slate-500 uppercase">Signals sampled</div>
                    <div className="text-lg font-medium text-white">Analyzing…</div>
                  </div>
                </div>
                <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4 flex items-center gap-3">
                  <Clock className="w-5 h-5 text-blue-400" />
                  <div>
                    <div className="text-xs text-slate-500 uppercase">Timeframe</div>
                    <div className="text-lg font-medium text-white">Year to Date</div>
                  </div>
                </div>
                <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4 flex items-center gap-3">
                  <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin text-indigo-400' : 'text-indigo-400'}`} />
                  <div>
                    <div className="text-xs text-slate-500 uppercase">Status</div>
                    <div className="text-lg font-medium text-white">{loading ? 'Scanning' : 'Standing by'}</div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Array.from({ length: 4 }).map((_, idx) => (
                  <div key={idx} className="h-28 bg-slate-900/30 border border-slate-800 rounded-lg overflow-hidden">
                    <div className="h-full w-full animate-pulse bg-gradient-to-r from-slate-800/40 via-slate-900/40 to-slate-800/40" />
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* Post-scan situation grid */}
        {scanComplete && (() => {
          const sorted = [...situations].sort(
            (a, b) => Math.abs(b.kpi_value?.percent_change ?? 0) - Math.abs(a.kpi_value?.percent_change ?? 0)
          );
          const [hero, ...rest] = sorted;

          if (sorted.length === 0) {
            return (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <CheckCircle className="w-10 h-10 text-severity-healthy mb-4 opacity-60" />
                <h2 className="text-lg font-semibold text-white mb-1">All KPIs within normal range</h2>
                <p className="text-sm text-slate-500">No findings detected in this scan.</p>
              </div>
            );
          }

          return (
            <div className="space-y-5">
              <h2 className="text-lg font-semibold text-white">Priority Briefings</h2>

              <HeroBriefing
                situation={hero}
                onClick={() => onSelectSituation(hero)}
                isDelegated={delegatedKpiNames.has(hero.kpi_name)}
                hasActiveSolution={hero.kpi_id ? activeKpiIds.has(hero.kpi_id) : false}
              />

              {rest.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {rest.map((sit, idx) => (
                    <div key={idx} className="h-44">
                      <KPITile
                        situation={sit}
                        onClick={() => onSelectSituation(sit)}
                        isDelegated={delegatedKpiNames.has(sit.kpi_name)}
                        hasActiveSolution={sit.kpi_id ? activeKpiIds.has(sit.kpi_id) : false}
                      />
                    </div>
                  ))}
                </div>
              )}

              {/* #9: Healthy KPIs footer */}
              {kpisScanned > sorted.length && (
                <div>
                  <button
                    onClick={() => setHealthyExpanded(v => !v)}
                    className="flex items-center gap-2 text-xs text-slate-600 hover:text-slate-400 transition-colors"
                  >
                    <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-150 ${healthyExpanded ? 'rotate-180' : ''}`} />
                    {kpisScanned - sorted.length} KPI{kpisScanned - sorted.length === 1 ? '' : 's'} within normal range
                    {!healthyExpanded && <span className="text-slate-700">— expand to view</span>}
                  </button>
                  {healthyExpanded && (
                    <p className="mt-2 text-[11px] text-slate-600 pl-5">
                      These KPIs were evaluated and are performing within acceptable thresholds. No action required.
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })()}

      </main>
    </div>
  );
};
