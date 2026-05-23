import { Situation } from '../../api/types';

interface SummaryStripProps {
  kpisScanned: number;
  breachCount: number;
  impactLevel: string;
  impactColor: string;
  situations: Situation[];
}

export function SummaryStrip({ kpisScanned, breachCount, situations }: SummaryStripProps) {
  const criticalCount = situations.filter(
    s => s.card_type !== 'opportunity' && (s.severity === 'critical' || s.severity === 'high')
  ).length;
  const warningCount = situations.filter(
    s => s.card_type !== 'opportunity' && s.severity === 'medium'
  ).length;
  const opportunityCount = situations.filter(
    s => s.card_type === 'opportunity' || s.direction === 'up'
  ).length;
  const leadFinding = [...situations].sort(
    (a, b) => Math.abs(b.kpi_value?.percent_change ?? 0) - Math.abs(a.kpi_value?.percent_change ?? 0)
  )[0];

  return (
    <div className="mb-6 animate-in slide-in-from-top-4 fade-in duration-500">
      <div className="bg-slate-900/40 border border-slate-800 rounded-lg px-5 py-3 flex flex-wrap items-center gap-0 text-xs divide-x divide-slate-800">
        <span className="pr-4 text-white font-semibold">{kpisScanned} KPIs evaluated</span>
        <span className="px-4 text-slate-400">
          <span className="text-white font-medium">{breachCount}</span>{' '}
          {breachCount === 1 ? 'finding' : 'findings'}
        </span>
        {criticalCount > 0 && (
          <span className="px-4" style={{ color: 'rgb(248 113 113)' }}>
            {criticalCount} critical
          </span>
        )}
        {warningCount > 0 && (
          <span className="px-4" style={{ color: 'rgb(251 191 36)' }}>
            {warningCount} warning
          </span>
        )}
        {opportunityCount > 0 && (
          <span className="px-4" style={{ color: 'rgb(52 211 153)' }}>
            {opportunityCount} {opportunityCount === 1 ? 'opportunity' : 'opportunities'}
          </span>
        )}
        {leadFinding && (
          <span className="px-4 text-slate-400">
            Lead: <span className="text-white">{leadFinding.kpi_name}</span>
          </span>
        )}
        <span className="px-4 text-slate-600">Just now</span>
      </div>
    </div>
  );
}
