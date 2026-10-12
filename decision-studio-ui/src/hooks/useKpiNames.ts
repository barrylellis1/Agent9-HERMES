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

const cache = new Map<string, Promise<Record<string, string>>>();

function loadNames(clientId: string): Promise<Record<string, string>> {
  let p = cache.get(clientId);
  if (!p) {
    p = listKpis(clientId).then(kpis =>
      Object.fromEntries(kpis.map((k: any) => [k.id, k.name || k.id])),
    );
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
    loadNames(client).then(n => { if (!cancelled) setNames(n); }).catch(() => {});
    return () => { cancelled = true; };
  }, [client]);

  return (kpiId) => (kpiId ? names[kpiId] ?? fallbackKpiName(kpiId) : '');
}
