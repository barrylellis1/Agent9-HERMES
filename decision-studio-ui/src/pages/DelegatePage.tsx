import { useEffect, useRef, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, Loader2, UserCheck, ArrowRight } from 'lucide-react';
import { BrandLogo } from '../components/BrandLogo';

// ── Types ────────────────────────────────────────────────────────────────

interface DelegateSuggestion {
  principal_id: string;
  name: string;
  title: string;
  is_recommended: boolean;
  reason: string | null;
}

type PageState = 'loading' | 'ready' | 'submitting' | 'done' | 'error';

const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000') + '/api/v1';

// ── Component ────────────────────────────────────────────────────────────

export function DelegatePage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [pageState, setPageState] = useState<PageState>('loading');
  const [suggestions, setSuggestions] = useState<DelegateSuggestion[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [note, setNote] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [kpiName, setKpiName] = useState('');
  const calledRef = useRef(false);

  // Read from query params: ?situation=<kpi_name>&token=<delegate_token>
  const situation = searchParams.get('situation') || '';
  const token = searchParams.get('token') || '';
  const principalId = searchParams.get('principal') || '';

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    if (!situation) {
      setErrorMsg('No situation specified.');
      setPageState('error');
      return;
    }

    setKpiName(situation);

    // Fetch delegate suggestions
    const params = new URLSearchParams({
      kpi_name: situation,
      ...(principalId ? { exclude_principal_id: principalId } : {}),
    });

    fetch(`${API_BASE}/pib/delegates?${params}`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`${res.status}`);
        const data: DelegateSuggestion[] = await res.json();
        setSuggestions(data);
        // Pre-select the first recommended principal
        const recommended = data.find(d => d.is_recommended);
        if (recommended) setSelectedId(recommended.principal_id);
        setPageState('ready');
      })
      .catch(() => {
        setErrorMsg('Failed to load delegate options.');
        setPageState('error');
      });
  }, [situation, principalId]);

  const handleDelegate = async () => {
    if (!selectedId || !token) return;
    setPageState('submitting');
    try {
      const res = await fetch(`${API_BASE}/pib/delegate/${encodeURIComponent(token)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          delegate_to_principal_id: selectedId,
          note: note || null,
        }),
      });
      if (!res.ok) {
        const detail = await res.text();
        throw new Error(detail);
      }
      setPageState('done');
      setTimeout(() => navigate('/'), 3000);
    } catch {
      setErrorMsg('Failed to complete delegation.');
      setPageState('error');
    }
  };

  const selectedPrincipal = suggestions.find(s => s.principal_id === selectedId);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        {/* Brand */}
        <div className="text-center mb-6">
          <div className="flex justify-center mb-1">
            <BrandLogo size={28} scheme="dark" />
          </div>
          <p className="text-xs text-gray-500 uppercase tracking-widest mt-1">
            Delegate Situation
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-8 shadow-sm">
          {/* Loading */}
          {pageState === 'loading' && (
            <div className="text-center">
              <Loader2 className="mx-auto mb-4 h-8 w-8 text-blue-500 animate-spin" />
              <p className="text-gray-500 text-sm">Loading delegate options...</p>
            </div>
          )}

          {/* Ready — show situation + principal list */}
          {pageState === 'ready' && (
            <>
              {/* Situation summary */}
              <div className="mb-6 pb-5 border-b border-gray-100">
                <p className="text-xs font-semibold uppercase tracking-wide text-gray-400 mb-1">
                  Situation
                </p>
                <p className="text-lg font-bold text-gray-900">{kpiName}</p>
                <p className="text-sm text-gray-500 mt-1">
                  Select a principal to own the investigation of this situation.
                </p>
              </div>

              {/* Principal list */}
              <div className="space-y-2 mb-6">
                {suggestions.map((s) => (
                  <button
                    key={s.principal_id}
                    onClick={() => setSelectedId(s.principal_id)}
                    className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                      selectedId === s.principal_id
                        ? 'border-slate-900 bg-slate-50'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className={`text-sm font-semibold ${
                          selectedId === s.principal_id ? 'text-slate-900' : 'text-gray-900'
                        }`}>
                          {s.name}
                        </p>
                        <p className="text-xs text-gray-500">{s.title}</p>
                        {s.is_recommended && s.reason && (
                          <p className="text-xs text-slate-600 mt-1 flex items-center gap-1">
                            <UserCheck className="w-3 h-3" />
                            {s.reason}
                          </p>
                        )}
                      </div>
                      {s.is_recommended && (
                        <span className="text-[10px] font-bold uppercase tracking-wide text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                          Recommended
                        </span>
                      )}
                    </div>
                  </button>
                ))}
                {suggestions.length === 0 && (
                  <p className="text-sm text-gray-400 text-center py-4">
                    No other principals available for delegation.
                  </p>
                )}
              </div>

              {/* Optional note */}
              <div className="mb-6">
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Note (optional)
                </label>
                <input
                  type="text"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Any context for the delegate..."
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-400"
                />
              </div>

              {/* Submit */}
              <button
                onClick={handleDelegate}
                disabled={!selectedId}
                className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg text-sm font-semibold transition-colors ${
                  selectedId
                    ? 'bg-slate-900 text-white hover:bg-slate-700'
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }`}
              >
                {selectedPrincipal
                  ? `Delegate to ${selectedPrincipal.name}`
                  : 'Select a principal'}
                <ArrowRight className="w-4 h-4" />
              </button>
            </>
          )}

          {/* Submitting */}
          {pageState === 'submitting' && (
            <div className="text-center">
              <Loader2 className="mx-auto mb-4 h-8 w-8 text-blue-500 animate-spin" />
              <p className="text-gray-500 text-sm">Delegating...</p>
            </div>
          )}

          {/* Done */}
          {pageState === 'done' && (
            <div className="text-center">
              <CheckCircle className="mx-auto mb-4 h-10 w-10 text-emerald-500" />
              <p className="text-gray-900 font-semibold mb-1">Situation Delegated</p>
              <p className="text-gray-500 text-sm">
                {selectedPrincipal
                  ? `${kpiName} has been assigned to ${selectedPrincipal.name}.`
                  : 'Delegation complete.'}
              </p>
            </div>
          )}

          {/* Error */}
          {pageState === 'error' && (
            <div className="text-center">
              <XCircle className="mx-auto mb-4 h-10 w-10 text-red-400" />
              <p className="text-gray-900 font-semibold mb-4">{errorMsg}</p>
              <button
                onClick={() => navigate('/')}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-700 text-white text-sm font-medium transition-colors"
              >
                Open Decision Studio
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DelegatePage;
