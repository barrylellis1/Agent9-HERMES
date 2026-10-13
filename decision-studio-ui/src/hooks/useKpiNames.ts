import { useEffect, useState } from 'react';
import { listKpis } from '../api/client';

/**
 * KPI display names from the registry, keyed by id, for screens that only
 * hold a kpi_id (the Portfolio list, the trajectory chart).
 *
 * The fallback keeps the WHOLE id. An earlier helper stripped a leading
 * 2-5 letter word, which turned `net_revenue` into "Revenue" and
 * `gross_margin_pct` into "Margin Pct" — a different KPI's name.
 */

interface KpiMeta { names: Record<string, string>; units: Record<string, string> }

const cache = new Map<string, Promise<KpiMeta>>();

function loadMeta(clientId: string): Promise<KpiMeta> {
  let p = cache.get(clientId);
  if (!p) {
    p = listKpis(clientId).then(kpis => ({
      names: Object.fromEntries(kpis.map((k: any) => [k.id, k.name || k.id])),
      units: Object.fromEntries(kpis.filter((k: any) => k.unit).map((k: any) => [k.id, k.unit])),
    }));
    p.catch(() => cache.delete(clientId));
    cache.set(clientId, p);
  }
  return p;
}

export function fallbackKpiName(id: string): string {
  return id
    .split('_')
    .filter(Boolean)
    .map(w => (w === 'pct' ? '%' : w.charAt(0).toUpperCase() + w.slice(1)))
    .join(' ');
}

export function useKpiNames(clientId?: string): (kpiId?: string | null) => string {
  const [names, setNames] = useState<Record<string, string>>({});
  const client = clientId ?? (() => {
    try { return localStorage.getItem('a9_active_client_id') ?? ''; } catch { return ''; }
  })();

  useEffect(() => {
    if (!client) return;
    let cancelled = false;
    loadMeta(client).then(m => { if (!cancelled) setNames(m.names); }).catch(() => {});
    return () => { cancelled = true; };
  }, [client]);

  return (kpiId) => (kpiId ? names[kpiId] ?? fallbackKpiName(kpiId) : '');
}

/**
 * A change in a KPI, written with the KPI's registered unit: "+$575K",
 * "+1.7pp", "+1.2K units". With no unit known, the number is abbreviated and
 * no symbol is added. A guessed "$" or "%" on the wrong kind of figure has
 * shipped before (a $575K revenue change rendered as "+575000.0%").
 */
export function formatKpiChange(value: number, unit?: string | null): string {
  if (value === 0) return unit === '%' ? '0.0pp' : unit === '$' ? '$0' : unit ? `0 ${unit}` : '0';
  const sign = value >= 0 ? '+' : '-';
  const abs = Math.abs(value);
  if (unit === '%') return `${sign}${abs.toFixed(1)}pp`;
  const short =
    abs >= 1e9 ? `${(abs / 1e9).toFixed(1)}B`
    : abs >= 1e6 ? `${(abs / 1e6).toFixed(1)}M`
    : abs >= 1e3 ? `${(abs / 1e3).toFixed(0)}K`
    : abs.toFixed(abs < 10 ? 1 : 0);
  if (unit === '$') return `${sign}$${short}`;
  return unit ? `${sign}${short} ${unit}` : `${sign}${short}`;
}

/** Registry unit lookup by KPI id; undefined until loaded or when none is registered. */
export function useKpiUnits(clientId?: string): (kpiId?: string | null) => string | undefined {
  const [units, setUnits] = useState<Record<string, string>>({});
  const client = clientId ?? (() => {
    try { return localStorage.getItem('a9_active_client_id') ?? ''; } catch { return ''; }
  })();

  useEffect(() => {
    if (!client) return;
    let cancelled = false;
    loadMeta(client).then(m => { if (!cancelled) setUnits(m.units); }).catch(() => {});
    return () => { cancelled = true; };
  }, [client]);

  return (kpiId) => (kpiId ? units[kpiId] : undefined);
}
