import { useEffect, useRef, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';

// ── Types ─────────────────────────────────────────────────────────────────────

interface TokenActionResponse {
  token_type: string;
  situation_id: string;
  action_taken: string;
  redirect_url?: string | null;
  principal_id?: string | null;
  kpi_name?: string | null;
  message: string;
}

type PageState = 'loading' | 'success' | 'error';

// ── Helpers ───────────────────────────────────────────────────────────────────

const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000') + '/api/v1';

async function resolveToken(token: string): Promise<TokenActionResponse> {
  const response = await fetch(`${API_BASE}/pib/token/${encodeURIComponent(token)}`);
  if (!response.ok) {
    // 410 expired/used, 404 not found — both treated as "invalid link"
    throw new Error(`${response.status}`);
  }
  return response.json() as Promise<TokenActionResponse>;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function ActionHandler() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [pageState, setPageState] = useState<PageState>('loading');
  const [message, setMessage] = useState('');

  // Guard against React StrictMode double-invoke in dev
  const calledRef = useRef(false);

  useEffect(() => {
    if (calledRef.current) return;
    calledRef.current = true;

    const token = searchParams.get('token');

    if (!token) {
      setMessage('No action token was provided in this link.');
      setPageState('error');
      return;
    }

    resolveToken(token)
      .then((data) => {
        setMessage(data.message);
        setPageState('success');

        const principalId = data.principal_id || undefined;
        const kpiName = data.kpi_name || undefined;

        // After a brief confirmation pause, navigate appropriately
        setTimeout(() => {
          if (data.token_type === 'deep_link') {
            navigate('/dashboard', {
              state: { principalId, kpiName },
            });
          } else if (data.token_type === 'delegate') {
            // Redirect to delegate page with context
            const params = new URLSearchParams();
            params.set('situation', data.situation_id || '');
            params.set('token', token!);
            if (principalId) params.set('principal', principalId);
            navigate(`/delegate?${params.toString()}`);
          } else {
            navigate('/dashboard', {
              state: { principalId },
            });
          }
        }, 1500);
      })
      .catch(() => {
        setMessage('This link has expired or has already been used.');
        setPageState('error');
      });
  }, [searchParams, navigate]);

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Brand header */}
        <div className="text-center mb-8">
          <span className="text-xl font-semibold tracking-tight text-white">
            Decision Studio
          </span>
        </div>

        <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8 text-center shadow-xl">
          {pageState === 'loading' && (
            <>
              <Loader2 className="mx-auto mb-4 h-10 w-10 text-blue-400 animate-spin" />
              <p className="text-slate-300 text-sm">Verifying your action...</p>
            </>
          )}

          {pageState === 'success' && (
            <>
              <CheckCircle className="mx-auto mb-4 h-10 w-10 text-emerald-400" />
              <p className="text-white font-medium mb-1">{message}</p>
              <p className="text-slate-400 text-sm">Redirecting you to Decision Studio...</p>
            </>
          )}

          {pageState === 'error' && (
            <>
              <XCircle className="mx-auto mb-4 h-10 w-10 text-red-400" />
              <p className="text-white font-medium mb-4">{message}</p>
              <button
                onClick={() => navigate('/')}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors"
              >
                Open Decision Studio
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ActionHandler;
