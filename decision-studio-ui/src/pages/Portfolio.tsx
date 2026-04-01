import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowLeft, RefreshCw, TrendingUp, AlertCircle, BarChart2, ArrowUpRight, ShieldCheck, Target, FileText } from 'lucide-react';
import { getVAPortfolio, recordKPIMeasurement, getPrincipal } from '../api/client';
import type { StrategyAwarePortfolio, AcceptedSolution, SolutionVerdict } from '../types/valueAssurance';
import { PortfolioDashboard } from '../components/PortfolioDashboard';
import { TrajectoryChart } from '../components/visualizations/TrajectoryChart';
import { ValueAssurancePanel } from '../components/ValueAssurancePanel';
import { AttributionBreakdown } from '../components/AttributionBreakdown';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
}

// ─── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: SolutionVerdict }) {
  const map: Record<SolutionVerdict, string> = {
    MEASURING: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    VALIDATED: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    PARTIAL: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    FAILED: 'bg-red-500/20 text-red-400 border-red-500/30',
  };
  const labels: Record<SolutionVerdict, string> = {
    MEASURING: 'Measuring',
    VALIDATED: 'Validated',
    PARTIAL: 'Partial',
    FAILED: 'Failed',
  };
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${map[status]}`}
    >
      {labels[status]}
    </span>
  );
}

// ─── Detail panel ─────────────────────────────────────────────────────────────

interface DetailPanelProps {
  solution: AcceptedSolution;
  principalId: string;
  onMeasurementRecorded: (updated: AcceptedSolution) => void;
}

function DetailPanel({ solution, principalId, onMeasurementRecorded }: DetailPanelProps) {
  const [measurementValue, setMeasurementValue] = useState('');
  const [recording, setRecording] = useState(false);
  const [recordError, setRecordError] = useState<string | null>(null);
  const [recordSuccess, setRecordSuccess] = useState(false);
  const [showAttribution, setShowAttribution] = useState(false);

  const hasEvaluation = !!solution.impact_evaluation;
  const attributionNote = hasEvaluation
    ? null
    : 'Attribution: preliminary (control group data collection pending)';

  const handleRecord = async () => {
    const value = parseFloat(measurementValue);
    if (isNaN(value)) {
      setRecordError('Please enter a valid number.');
      return;
    }
    setRecording(true);
    setRecordError(null);
    setRecordSuccess(false);
    try {
      const response = await recordKPIMeasurement(solution.solution_id, value, principalId);
      // Merge updated trend arrays back into the solution object so the chart refreshes
      const updated: AcceptedSolution = {
        ...solution,
        actual_trend: response.actual_trend,
        actual_trend_dates: response.actual_trend_dates,
      };
      setRecordSuccess(true);
      setMeasurementValue('');
      onMeasurementRecorded(updated);
    } catch (err: unknown) {
      setRecordError(err instanceof Error ? err.message : 'Failed to record measurement.');
    } finally {
      setRecording(false);
    }
  };

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-6">
      {/* Solution header */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-white leading-snug">
            {solution.solution_description}
          </h2>
          <p className="text-xs text-slate-500 font-mono mt-1">{solution.kpi_id}</p>
        </div>
        <StatusBadge status={solution.status} />
      </div>

      {/* Meta row */}
      <div className="flex flex-wrap gap-6 text-xs text-slate-400">
        <div>
          <span className="text-slate-600 block uppercase tracking-wider text-[10px] mb-0.5">Approved</span>
          {formatDate(solution.approved_at)}
        </div>
        <div>
          <span className="text-slate-600 block uppercase tracking-wider text-[10px] mb-0.5">Measurement window</span>
          {solution.measurement_window_days} days
        </div>
        <div>
          <span className="text-slate-600 block uppercase tracking-wider text-[10px] mb-0.5">Inaction horizon</span>
          {solution.inaction_horizon_months} months
        </div>
        <div>
          <span className="text-slate-600 block uppercase tracking-wider text-[10px] mb-0.5">Expected impact</span>
          {solution.expected_impact_lower >= 0 ? '+' : ''}{solution.expected_impact_lower.toFixed(1)}% to{' '}
          {solution.expected_impact_upper >= 0 ? '+' : ''}{solution.expected_impact_upper.toFixed(1)}%
        </div>
      </div>

      {/* Realized Benefit — computed from trend data */}
      {solution.actual_trend.length > 1 && (() => {
        const baseline = solution.actual_trend[0];
        const latestActual = solution.actual_trend[solution.actual_trend.length - 1];
        const monthsElapsed = solution.actual_trend.length - 1;
        // Inaction value at the same month index (clamped to array bounds)
        const inactionIdx = Math.min(monthsElapsed, solution.inaction_trend.length - 1);
        const inactionAtMonth = solution.inaction_trend[inactionIdx];
        // Expected value at the same month index (clamped)
        const expectedIdx = Math.min(monthsElapsed, solution.expected_trend.length - 1);
        const expectedAtMonth = solution.expected_trend[expectedIdx];

        const realizedRecovery = latestActual - baseline;
        const avoidedLoss = latestActual - inactionAtMonth;
        const vsPlan = latestActual - expectedAtMonth;

        return (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-emerald-900/15 border border-emerald-500/20 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <ArrowUpRight className="w-4 h-4 text-emerald-400" />
                <span className="text-[10px] font-bold text-emerald-400/70 uppercase tracking-wider">Realized Recovery</span>
              </div>
              <p className="text-2xl font-bold text-emerald-400">
                {realizedRecovery >= 0 ? '+' : ''}{realizedRecovery.toFixed(1)} pp
              </p>
              <p className="text-[10px] text-slate-500 mt-1">
                {baseline.toFixed(1)}% → {latestActual.toFixed(1)}% over {monthsElapsed} month{monthsElapsed !== 1 ? 's' : ''}
              </p>
            </div>
            <div className="bg-blue-900/15 border border-blue-500/20 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <ShieldCheck className="w-4 h-4 text-blue-400" />
                <span className="text-[10px] font-bold text-blue-400/70 uppercase tracking-wider">Avoided Loss</span>
              </div>
              <p className="text-2xl font-bold text-blue-400">
                {avoidedLoss >= 0 ? '+' : ''}{avoidedLoss.toFixed(1)} pp
              </p>
              <p className="text-[10px] text-slate-500 mt-1">
                vs inaction scenario ({inactionAtMonth.toFixed(1)}% at M{monthsElapsed})
              </p>
            </div>
            <div className={`${vsPlan >= 0 ? 'bg-indigo-900/15 border-indigo-500/20' : 'bg-amber-900/15 border-amber-500/20'} border rounded-xl p-4`}>
              <div className="flex items-center gap-2 mb-2">
                <Target className={`w-4 h-4 ${vsPlan >= 0 ? 'text-indigo-400' : 'text-amber-400'}`} />
                <span className={`text-[10px] font-bold uppercase tracking-wider ${vsPlan >= 0 ? 'text-indigo-400/70' : 'text-amber-400/70'}`}>vs Plan</span>
              </div>
              <p className={`text-2xl font-bold ${vsPlan >= 0 ? 'text-indigo-400' : 'text-amber-400'}`}>
                {vsPlan >= 0 ? '+' : ''}{vsPlan.toFixed(1)} pp
              </p>
              <p className="text-[10px] text-slate-500 mt-1">
                {vsPlan >= 0 ? 'Ahead of' : 'Behind'} expected ({expectedAtMonth.toFixed(1)}% target)
              </p>
            </div>
          </div>
        );
      })()}

      {/* Value Assurance Panel — evaluation details */}
      {hasEvaluation && solution.impact_evaluation && (
        <>
          <ValueAssurancePanel
            solutionId={solution.solution_id}
            solutionDescription={solution.solution_description}
            approvedAt={solution.approved_at}
            status={solution.status}
            evaluation={solution.impact_evaluation}
            compositeVerdict={solution.impact_evaluation.composite_verdict ?? undefined}
            onViewAttribution={() => setShowAttribution(!showAttribution)}
          />
          {showAttribution && (
            <AttributionBreakdown
              totalChange={solution.impact_evaluation.total_kpi_change}
              attributableImpact={solution.impact_evaluation.attributable_impact}
              marketDrivenRecovery={solution.impact_evaluation.market_driven_recovery}
              seasonalComponent={solution.impact_evaluation.seasonal_component}
              controlGroupChange={solution.impact_evaluation.control_group_change}
              expectedLower={solution.impact_evaluation.expected_impact_lower}
              expectedUpper={solution.impact_evaluation.expected_impact_upper}
              controlGroupDescription={solution.impact_evaluation.control_group_description ?? undefined}
            />
          )}
        </>
      )}

      {/* Attribution note (when no evaluation yet) */}
      {!hasEvaluation && attributionNote && (
        <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-900/10 border border-amber-500/20 rounded-lg px-4 py-2.5">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          {attributionNote}
        </div>
      )}

      {/* View Original Briefing */}
      <a
        href={`/briefing/${solution.situation_id}?solution_id=${solution.solution_id}`}
        className="flex items-center gap-2 text-sm font-medium text-indigo-400 hover:text-indigo-300 bg-indigo-900/10 border border-indigo-500/20 rounded-lg px-4 py-3 transition-colors"
      >
        <FileText className="w-4 h-4" />
        View Original Decision Briefing
      </a>

      {/* Trajectory chart */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <BarChart2 className="w-4 h-4 text-slate-500" />
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Value Trajectory
          </span>
        </div>
        <TrajectoryChart
          inactionTrend={solution.inaction_trend}
          expectedTrend={solution.expected_trend}
          actualTrend={solution.actual_trend}
          actualTrendDates={solution.actual_trend_dates}
          approvedAt={solution.approved_at}
          measurementWindowDays={solution.measurement_window_days}
          inactionHorizonMonths={solution.inaction_horizon_months}
          kpiName={solution.kpi_id}
        />
      </div>

      {/* Record measurement */}
      <div className="border-t border-slate-800 pt-5">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Record KPI Measurement
        </p>
        <div className="flex items-center gap-3">
          <input
            type="number"
            value={measurementValue}
            onChange={(e) => {
              setMeasurementValue(e.target.value);
              setRecordError(null);
              setRecordSuccess(false);
            }}
            placeholder="Enter KPI value..."
            className="flex-1 max-w-xs bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30"
          />
          <button
            onClick={handleRecord}
            disabled={recording || !measurementValue.trim()}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            {recording ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <TrendingUp className="w-3.5 h-3.5" />
            )}
            {recording ? 'Recording...' : 'Record Measurement'}
          </button>
        </div>
        {recordError && (
          <p className="mt-2 text-xs text-red-400">{recordError}</p>
        )}
        {recordSuccess && (
          <p className="mt-2 text-xs text-emerald-400">Measurement recorded successfully.</p>
        )}
      </div>
    </div>
  );
}

// ─── Portfolio page ───────────────────────────────────────────────────────────

export function Portfolio() {
  const [searchParams] = useSearchParams();
  const principalId = searchParams.get('principal') ?? '';

  const [portfolio, setPortfolio] = useState<StrategyAwarePortfolio | null>(null);
  const [selectedSolution, setSelectedSolution] = useState<AcceptedSolution | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [principalName, setPrincipalName] = useState<string | null>(null);

  const loadPortfolio = useCallback(async () => {
    if (!principalId) {
      setError('No principal ID provided. Add ?principal=cfo_001 to the URL.');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [data, principal] = await Promise.allSettled([
        getVAPortfolio(principalId),
        getPrincipal(principalId),
      ]);
      if (data.status === 'fulfilled') setPortfolio(data.value);
      else throw data.reason;
      if (principal.status === 'fulfilled' && principal.value?.name) {
        setPrincipalName(principal.value.name);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load portfolio.');
    } finally {
      setLoading(false);
    }
  }, [principalId]);

  useEffect(() => {
    loadPortfolio();
  }, [loadPortfolio]);

  // When a solution is selected from the table, find it in the portfolio
  const handleSelectSolution = (solutionId: string) => {
    const sol = portfolio?.solutions.find((s) => s.solution_id === solutionId) ?? null;
    setSelectedSolution(sol);
    // Scroll detail panel into view on smaller screens
    if (sol) {
      setTimeout(() => {
        document.getElementById('solution-detail-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  };

  // After recording a measurement, update the solution in state without a full reload
  const handleMeasurementRecorded = (updated: AcceptedSolution) => {
    setSelectedSolution(updated);
    if (portfolio) {
      setPortfolio({
        ...portfolio,
        solutions: portfolio.solutions.map((s) =>
          s.solution_id === updated.solution_id ? updated : s
        ),
      });
    }
  };

  return (
    <div className="bg-slate-950 min-h-screen text-white">
      {/* Top bar */}
      <div className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => window.history.back()}
              className="flex items-center gap-1.5 text-slate-400 hover:text-white text-sm transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <div className="w-px h-5 bg-slate-700" />
            <div>
              <h1 className="text-2xl font-bold text-white leading-none">Decision Portfolio</h1>
              {principalId && (
                <p className="text-sm text-slate-400 mt-0.5">
                  {principalName ?? principalId}
                </p>
              )}
            </div>
          </div>

          <button
            onClick={loadPortfolio}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-600 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-24">
            <RefreshCw className="w-6 h-6 text-slate-500 animate-spin mr-3" />
            <span className="text-slate-400 text-sm">Loading portfolio...</span>
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="flex items-start gap-3 bg-red-900/15 border border-red-500/30 rounded-xl px-5 py-4 max-w-lg mx-auto mt-16">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-red-400">Failed to load portfolio</p>
              <p className="text-xs text-red-400/70 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Portfolio dashboard */}
        {!loading && !error && portfolio && (
          <>
            <PortfolioDashboard
              solutions={portfolio.solutions}
              totalAttributableImpact={portfolio.total_attributable_impact}
              validatedCount={portfolio.validated_count}
              partialCount={portfolio.partial_count}
              failedCount={portfolio.failed_count}
              measuringCount={portfolio.measuring_count}
              executiveAttentionRequired={portfolio.executive_attention_required}
              onSelectSolution={handleSelectSolution}
            />

            {/* Solution detail panel */}
            {selectedSolution && (
              <div id="solution-detail-panel">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white">
                    Solution Detail
                  </h2>
                  <button
                    onClick={() => setSelectedSolution(null)}
                    className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    Close
                  </button>
                </div>
                <DetailPanel
                  solution={selectedSolution}
                  principalId={principalId}
                  onMeasurementRecorded={handleMeasurementRecorded}
                />
              </div>
            )}

            {/* Empty portfolio hint */}
            {portfolio.solutions.length === 0 && (
              <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl">
                <TrendingUp className="w-8 h-8 text-slate-700 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">No solutions tracked yet for this principal.</p>
                <p className="text-xs text-slate-600 mt-1">
                  Solutions appear here after HITL approval in the Decision Studio.
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
