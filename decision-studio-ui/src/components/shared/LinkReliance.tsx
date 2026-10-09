import { useEffect, useState } from 'react';
import { listKpis, listKpiRelationships } from '../../api/client';
import { linkTrust } from '../../utils/trustState';
import { TrustBadge } from './TrustBadge';

/**
 * Which recorded KPI link a recommendation relies on, in plain terms.
 *
 * The reviewer's own text arrives as prose around raw ids, e.g.
 * "cogs -> gross_margin_pct (confirmed, correlational, ~1-month lag)". This
 * shows the KPI names and the link's CURRENT trust state from the registry
 * (utils/trustState.ts) and keeps the reviewer's wording behind an expand.
 * The state is read from the registry rather than parsed out of the prose,
 * so it cannot drift from what the other screens show for the same link.
 */

interface Registry {
  names: Record<string, string>;
  links: any[];
}

const cache = new Map<string, Promise<Registry>>();

function loadRegistry(clientId: string): Promise<Registry> {
  let p = cache.get(clientId);
  if (!p) {
    p = Promise.all([listKpis(clientId), listKpiRelationships(clientId)]).then(([kpis, links]) => ({
      names: Object.fromEntries(kpis.map((k: any) => [k.id, k.name || k.id])),
      links,
    }));
    p.catch(() => cache.delete(clientId));
    cache.set(clientId, p);
  }
  return p;
}

const PAIR = /([a-z_][a-z0-9_]{2,})\s*(?:<->|->|<-|→|↔)\s*([a-z_][a-z0-9_]{2,})/g;

export function parseLinkPairs(raw: string): Array<[string, string]> {
  const seen = new Set<string>();
  const out: Array<[string, string]> = [];
  for (const m of raw.toLowerCase().matchAll(PAIR)) {
    const key = [m[1], m[2]].sort().join('|');
    if (!seen.has(key)) {
      seen.add(key);
      out.push([m[1], m[2]]);
    }
  }
  return out;
}

export function LinkReliance({ raw, clientId }: { raw?: string | null; clientId?: string }) {
  const [registry, setRegistry] = useState<Registry | null>(null);
  const client = clientId ?? (() => {
    try { return localStorage.getItem('a9_active_client_id') ?? ''; } catch { return ''; }
  })();

  useEffect(() => {
    if (!client) return;
    let cancelled = false;
    loadRegistry(client).then(r => { if (!cancelled) setRegistry(r); }).catch(() => {});
    return () => { cancelled = true; };
  }, [client]);

  const text = (raw ?? '').trim();
  const lower = text.toLowerCase();
  if (!text || lower.includes('insufficient_data') || lower.includes('insufficient data')) {
    return <span className="text-[11px] text-slate-500 print:text-slate-600">Not enough information to say.</span>;
  }
  if (lower.includes('ungrounded')) {
    return <span className="text-[11px] text-slate-500 print:text-slate-600">Not tied to a recorded link.</span>;
  }

  const pairs = parseLinkPairs(text);
  if (pairs.length === 0) {
    return <span className="text-[11px] text-slate-400 print:text-slate-600">{text}</span>;
  }

  const nameOf = (id: string) => registry?.names[id] ?? id;
  return (
    <div data-testid="link-reliance" className="space-y-1">
      {pairs.map(([a, b]) => {
        const link = registry?.links.find(
          (l: any) => (l.kpi_id === a && l.related_kpi_id === b) || (l.kpi_id === b && l.related_kpi_id === a),
        );
        const trust = link ? linkTrust(link, null) : null;
        return (
          <div key={`${a}|${b}`} className="flex flex-wrap items-center justify-end gap-2">
            <span className="text-[11px] text-slate-300 print:text-slate-700">{nameOf(a)} ↔ {nameOf(b)}</span>
            {trust ? (
              <TrustBadge state={trust.state} held={trust.held} />
            ) : registry ? (
              <span className="text-[10px] text-slate-500">not a recorded link</span>
            ) : null}
          </div>
        );
      })}
      <details className="text-right print:hidden">
        <summary className="cursor-pointer list-none text-[11px] text-slate-500 hover:text-slate-300">▸ Reviewer's wording</summary>
        <p className="mt-1 text-[11px] text-slate-500">{text}</p>
      </details>
    </div>
  );
}

export default LinkReliance;
