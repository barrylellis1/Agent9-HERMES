import React from 'react';
import { KPITile } from '../dashboard/KPITile';
import { RefreshCw, Settings, ChevronRight, Scan, Activity, Clock } from 'lucide-react';
import { Situation } from '../../api/types';
import { Principal } from '../../api/types';

interface DashboardViewProps {
  scanComplete: boolean;
  loading: boolean;
  situations: Situation[];
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
  timeframe,
  onSelectTimeframe,
  onRefresh,
  onSelectSituation,
  statusMsg,
  error
}) => {
  return (
    <div className="min-h-screen bg-background text-foreground p-8 font-sans relative overflow-x-hidden">
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Decision Studio</h1>
          <p className="text-slate-400">Situation Awareness Console</p>
        </div>
        <div className="flex items-center gap-4">
            {/* Timeframe Selector */}
            <div className="flex flex-col items-end gap-1">
                <label className="text-xs text-slate-500 uppercase tracking-wider">Timeframe</label>
                <div className="relative">
                    <select
                        value={timeframe}
                        onChange={(e) => onSelectTimeframe(e.target.value)}
                        className="appearance-none bg-slate-800/80 border border-slate-700 rounded-lg px-3 py-2 pr-8 text-sm text-white cursor-pointer hover:bg-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/50 min-w-[160px]"
                    >
                        <option value="year_to_date">Year to Date</option>
                        <option value="current_month">Current Month</option>
                    </select>
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                        <ChevronRight className="w-4 h-4 text-slate-400 rotate-90" />
                    </div>
                </div>
            </div>

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
                <div className="flex items-center gap-1.5">
                    <div className={`w-5 h-5 rounded-full ${currentPrincipal.color} flex items-center justify-center font-bold text-[9px]`}>
                        {currentPrincipal.initials}
                    </div>
                    <span className="text-xs text-slate-400">
                        <span className="capitalize">{currentPrincipal.decision_style}</span> style
                    </span>
                </div>
            </div>

            <div className="flex flex-col items-end gap-2">
            <button 
                onClick={onRefresh}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                {loading ? 'Scanning...' : 'Scan Now'}
            </button>
            {statusMsg && (
                <span className="text-xs text-emerald-400 font-medium animate-in fade-in slide-in-from-right-4">
                {statusMsg}
                </span>
            )}
            </div>
            
            <a href="/admin" className="p-2 text-slate-400 hover:text-white transition-colors" title="Admin Console">
                <Settings className="w-5 h-5" />
            </a>
        </div>
      </header>

      {/* KPI Evaluation Summary */}
      {scanComplete && (
        <section className="mb-8 animate-in slide-in-from-top-4 fade-in duration-500">
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                <div className="col-span-1 border-r border-slate-800 pr-6">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Scan Coverage</h3>
                    <div className="text-2xl font-light text-white">{kpisScanned} <span className="text-sm text-slate-500 font-normal">KPIs Evaluated</span></div>
                    <div className="text-xs text-slate-400 mt-1">Across 1 Data Product (FI Star Schema)</div>
                </div>

                <div className="col-span-1 border-r border-slate-800 pr-6">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Results</h3>
                    <div className="flex items-baseline gap-2">
                        <span className={`text-2xl font-bold ${breachCount > 0 ? 'text-red-400' : 'text-green-400'}`}>{breachCount}</span>
                        <span className="text-sm text-slate-400">Situations Detected</span>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">{kpisScanned - breachCount} KPIs within normal range</div>
                </div>

                <div className="col-span-1">
                    <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Impact Category</h3>
                    <div className={`text-lg font-medium ${impactColor} flex items-center gap-2`}>
                        {impactLevel.toUpperCase()} IMPACT
                        <div className={`w-2 h-2 rounded-full ${breachCount > 3 ? 'bg-red-500' : 'bg-amber-500'}`}></div>
                    </div>
                    {situations.length > 0 && (
                        <div className="text-xs text-slate-400 mt-1 truncate">
                            Top: {situations[0].kpi_name || 'Gross Revenue'}
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
                <h2 className="text-lg font-semibold text-white mb-4">Priority Briefings</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {situations.map((sit, idx) => (
                        <div key={idx} className="h-48">
                            <KPITile 
                                situation={sit}
                                onClick={() => onSelectSituation(sit)}
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
