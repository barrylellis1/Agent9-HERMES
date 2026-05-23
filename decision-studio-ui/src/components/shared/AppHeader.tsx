import { RefreshCw, Settings, LayoutGrid } from 'lucide-react';
import { Principal } from '../../api/types';
import { BrandLogo } from '../BrandLogo';
import { PrincipalSelector } from './PrincipalSelector';

interface AppHeaderProps {
  selectedPrincipal: string;
  availablePrincipals: Principal[];
  onSelectPrincipal: (id: string) => void;
  loading: boolean;
  onRefresh: () => void;
  statusMsg?: string | null;
  lastScannedAt?: Date | null;
}

function timeAgo(date: Date): string {
  const mins = Math.floor((Date.now() - date.getTime()) / 60000);
  if (mins < 1) return 'just now';
  if (mins === 1) return '1 min ago';
  return `${mins} min ago`;
}

export function AppHeader({
  selectedPrincipal,
  availablePrincipals,
  onSelectPrincipal,
  loading,
  onRefresh,
  statusMsg,
  lastScannedAt,
}: AppHeaderProps) {
  return (
    <header className="mb-8 flex justify-between items-center">
      <BrandLogo size={36} />

      <div className="flex items-center gap-4">
        <PrincipalSelector
          selectedPrincipal={selectedPrincipal}
          availablePrincipals={availablePrincipals}
          onSelectPrincipal={onSelectPrincipal}
        />

        <div className="flex flex-col items-end gap-1">
          {/* #12: Last scanned timestamp above the button */}
          {lastScannedAt ? (
            <span className="text-[10px] text-slate-600 uppercase tracking-wider">
              Last scanned: {timeAgo(lastScannedAt)}
            </span>
          ) : (
            <div className="h-[15px]" />
          )}
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
              <span className="text-xs text-severity-opportunity font-medium animate-in fade-in slide-in-from-right-4 whitespace-nowrap">
                {statusMsg}
              </span>
            )}
          </div>
        </div>

        {/* #14: LayoutGrid is recognizable as "registry / data explorer" */}
        <a href="/context" className="p-2 text-slate-400 hover:text-white transition-colors" title="Context Explorer — View KPIs, Principals & Data Products">
          <LayoutGrid className="w-5 h-5" />
        </a>
        <a href="/settings" className="p-2 text-slate-400 hover:text-white transition-colors" title="Settings">
          <Settings className="w-5 h-5" />
        </a>
      </div>
    </header>
  );
}
