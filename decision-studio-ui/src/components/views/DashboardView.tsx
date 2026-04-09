import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { KPITile } from '../dashboard/KPITile';
import { RefreshCw, Settings, GitBranch, ChevronRight, Scan, Activity, Clock, TrendingUp, BarChart3 } from 'lucide-react';
import { Situation, Client, OpportunitySignal } from '../../api/types';
import { Principal } from '../../api/types';
import { OpportunityCard } from '../OpportunityCard';
import { getVAPortfolio } from '../../api/client';
import type { StrategyAwarePortfolio } from '../../types/valueAssurance';
import { BrandLogo } from '../BrandLogo';

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
  opportunities = [],
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

  useEffect(() => {
    if (!selectedPrincipal) return;
    getVAPortfolio(selectedPrincipal)
      .then(setPortfolio)
      .catch(() => setPortfolio(null));
  }, [selectedPrincipal]);

  return (
    <div className="min-h-screen bg-background text-foreground p-8 font-sans relative overflow-x-hidden">
      <header className="mb-8 flex justify-between items-center">
        <BrandLogo size={36} />
        <div className="flex items-center gap-4">
            {/* Principal Selector */}
            <div className="flex flex-col items-end gap-1">
                <label className="text-xs text-slate-500 uppercase tracking-wider">Principal</label>
                <div className="relative">
                    <select
                        value={selectedPrincipal}
                        onChange={(e) => onSelectPrincipal(e.target.value)}
                        className="appearance-none bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-2 pr-8 text-sm text-white cursor-pointer hover:bg-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/50 min-w-[200px]"
                    >
                        {availablePrincipals.map(p => (
                            <option key={p.id} value={p.id}>
                                {p.name} ({p.title.split(' ').map(w => w[0]).join('')})
                            </option>
                        ))}
                    </select>
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                        <ChevronRight className="w-4 h-4 text-slate-400 rotate-90" />
                    </div>
                </div>
            </div>

            <div className="flex flex-col items-end gap-1">
            <div className="h-[18px]" />{/* spacer matches the label height above the dropdown */}
            <div className="flex items-center gap-2">
            <button
                onClick={onRefresh}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                {loading ? 'Scanning...' : 'Scan Now'}
            </button>
            {statusMsg && (
                <span className="text-xs text-emerald-400 font-medium animate-in fade-in slide-in-from-right-4 whitespace-nowrap">
                {statusMsg}
                </span>
            )}
            </div>
            </div>
            
            <a href="/context" className="p-2 text-slate-400 hover:text-white transition-colors" title="Context Explorer">
                <GitBranch className="w-5 h-5" />
            </a>
            <a href="/settings" className="p-2 text-slate-400 hover:text-white transition-colors" title="Settings">
                <Settings className="w-5 h-5" />
            </a>
        </div>
      </header>

      {/* KPI Evaluation Summary */}
      {scanComplete && (
        <section className="mb-8 animate-in slide-in-from-top-4 fade-in duration-500">
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                <div className="col-span-1 border-r border-slate-800 pr-6">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Coverage</h3>
                    <div className="text-2xl font-light text-white">{kpisScanned} <span className="text-sm text-slate-500 font-normal">KPIs evaluated.</span></div>
                    <div className="text-xs text-slate-400 mt-1">{breachCount > 0 ? `${breachCount} finding${breachCount === 1 ? '' : 's'} require attention.` : 'No findings require attention.'}</div>
                </div>

                <div className="col-span-1 border-r border-slate-800 pr-6">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Findings</h3>
                    <div className="flex items-baseline gap-2">
                        <span className={`text-2xl font-bold ${breachCount > 0 ? 'text-red-400' : 'text-slate-400'}`}>{breachCount}</span>
                        <span className="text-sm text-slate-400">{breachCount === 1 ? 'situation detected' : 'situations detected'}</span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">{kpisScanned - breachCount} within normal range</div>
                </div>

                <div className="col-span-1">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Impact level</h3>
                    <div className={`text-lg font-medium ${impactColor}`}>
                        {impactLevel.charAt(0).toUpperCase() + impactLevel.slice(1).toLowerCase()}
                    </div>
                    {situations.length > 0 && (
                        <div className="text-xs text-slate-400 mt-1 truncate">
                            Lead finding: {situations[0].kpi_name || 'Gross Revenue'}
                        </div>
                    )}
                </div>
            </div>
        </section>
      )}

      {error && (
        <div className="mb-8 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
          Error: {error}. Is the Agent9 backend running on port 8000?
        </div>
      )}

      <main className="max-w-7xl mx-auto space-y-8 pb-20">

        {/* Solutions in Progress — Phase 7C */}
        {portfolio && portfolio.total_solutions > 0 && (
          <section className="animate-in slide-in-from-top-4 fade-in duration-500">
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-slate-800 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-slate-400" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Solutions in Progress</h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {portfolio.measuring_count} measuring
                    {portfolio.validated_count > 0 && <> · <span className="text-emerald-400">{portfolio.validated_count} validated</span></>}
                    {portfolio.partial_count > 0 && <> · <span className="text-amber-400">{portfolio.partial_count} partial</span></>}
                    {portfolio.failed_count > 0 && <> · <span className="text-red-400">{portfolio.failed_count} failed</span></>}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {portfolio.executive_attention_required.length > 0 && (
                  <span className="text-xs text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded-full">
                    {portfolio.executive_attention_required.length} need attention
                  </span>
                )}
                <Link
                  to={`/portfolio?principal=${encodeURIComponent(selectedPrincipal)}`}
                  className="flex items-center gap-1.5 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  View All <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </section>
        )}

        {/* State 1: Scanner View (Initial) */}
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
                            Agent9 is sampling the latest KPI telemetry for {currentPrincipal.name}. We’ll surface the highest-impact situations as soon as the scan completes.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div className="bg-slate-900/40 border border-slate-800 rounded-lg p-4 flex items-center gap-3">
                            <Activity className="w-5 h-5 text-emerald-400" />
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

        {/* State 2: Situation Grid (Post-Scan) */}
        {scanComplete && (
            <div className="space-y-4">
                {/* Opportunities section — shown only when the backend returns opportunities */}
                {opportunities.length > 0 && (
                    <div className="mb-6">
                        <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                            <TrendingUp className="w-3.5 h-3.5" />
                            Opportunities Detected ({opportunities.length})
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {opportunities.map((signal, i) => (
                                <OpportunityCard
                                    key={`${signal.kpi_name}-${i}`}
                                    signal={signal}
                                />
                            ))}
                        </div>
                    </div>
                )}

                <h2 className="text-lg font-semibold text-white mb-4">Priority Briefings</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {situations.map((sit, idx) => (
                        <div key={idx} className="h-48">
                            <KPITile
                                situation={sit}
                                onClick={() => onSelectSituation(sit)}
                                isDelegated={delegatedKpiNames.has(sit.kpi_name)}
                            />
                        </div>
                    ))}
                </div>
            </div>
        )}
      </main>
    </div>
  );
};
