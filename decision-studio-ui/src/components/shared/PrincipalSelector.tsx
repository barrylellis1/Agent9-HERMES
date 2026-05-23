import { ChevronRight } from 'lucide-react';
import { Principal } from '../../api/types';

interface PrincipalSelectorProps {
  selectedPrincipal: string;
  availablePrincipals: Principal[];
  onSelectPrincipal: (id: string) => void;
}

export function PrincipalSelector({
  selectedPrincipal,
  availablePrincipals,
  onSelectPrincipal,
}: PrincipalSelectorProps) {
  const current = availablePrincipals.find(p => p.id === selectedPrincipal);

  return (
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
              {p.name} ({p.title.split(' ').map((w: string) => w[0]).join('')})
            </option>
          ))}
        </select>
        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
          <ChevronRight className="w-4 h-4 text-slate-400 rotate-90" />
        </div>
      </div>
      {current && (
        <span className="text-[10px] text-slate-500 tracking-wide">
          Viewing as: {current.title}
        </span>
      )}
    </div>
  );
}
