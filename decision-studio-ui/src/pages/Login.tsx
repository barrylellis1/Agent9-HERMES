/**
 * Login — Infra B dual-mode authentication.
 *
 * /login              → Production path: email + password via Supabase Auth.
 *                       After sign-in, infers client_id from email domain and
 *                       navigates to the dashboard.
 *
 * /login?mode=demo    → Demo/sandbox path: the original identity-selector flow.
 *                       Used for sales demos and internal testing.
 *
 * /login?token=<JWT>  → Magic-link path: handled by Supabase Auth detectSessionInUrl.
 *                       Falls through to the production path once the session is set.
 */

import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { listClients, listPrincipals } from '../api/client';
import { Client, Principal } from '../api/types';
import { AVAILABLE_PRINCIPALS } from '../config/uiConstants';
import { ArrowRight, ChevronRight, Mail, Lock, AlertCircle } from 'lucide-react';
import { BrandLogo } from '../components/BrandLogo';
import { supabase, inferClientIdFromEmail } from '../lib/supabase';

// ── Principal mapping helpers ──────────────────────────────────────────────

const STYLE_COLORS: Record<string, string> = {
  analytical: 'bg-blue-500/20 text-blue-400',
  visionary:  'bg-purple-500/20 text-purple-400',
  pragmatic:  'bg-emerald-500/20 text-emerald-400',
  decisive:   'bg-amber-500/20 text-amber-400',
};

function inferDecisionStyle(raw: any): Principal['decision_style'] {
  if (raw.decision_style && STYLE_COLORS[raw.decision_style]) return raw.decision_style;
  const title = (raw.title || raw.role || '').toLowerCase();
  if (title.includes('ceo') || title.includes('executive')) return 'visionary';
  if (title.includes('coo') || title.includes('operat')) return 'pragmatic';
  if (title.includes('cto') || title.includes('technology')) return 'decisive';
  return 'analytical';
}

function toInitials(name: string): string {
  return name.split(/\s+/).filter(Boolean).map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function mapApiPrincipal(raw: any): Principal {
  const style = inferDecisionStyle(raw);
  return {
    id: raw.id,
    name: raw.name || raw.id,
    title: raw.title || raw.role || '',
    initials: toInitials(raw.name || raw.id),
    decision_style: style,
    color: STYLE_COLORS[style] || 'bg-slate-500/20 text-slate-400',
  };
}

// ──────────────────────────────────────────────────────────────────────────

export function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isDemoMode = searchParams.get('mode') === 'demo';

  // ── Production auth state ──
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);

  // ── Demo mode state ──
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [demoLoading, setDemoLoading] = useState(false);
  const [selectedClientId, setSelectedClientId] = useState('lubricants');
  const [availableClients, setAvailableClients] = useState<Client[]>([]);
  const [principals, setPrincipals] = useState<Principal[]>(AVAILABLE_PRINCIPALS);
  const [principalsLoading, setPrincipalsLoading] = useState(false);

  // On mount: check if a Supabase session already exists (magic-link callback)
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user?.email) {
        _finishProductionLogin(session.user.email);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Demo mode: load clients + principals
  useEffect(() => {
    if (!isDemoMode) return;
    listClients()
      .then(data => { if (data && data.length > 0) setAvailableClients(data as Client[]); })
      .catch(() => { /* silently use fallback */ });
  }, [isDemoMode]);

  useEffect(() => {
    if (!isDemoMode) return;
    setPrincipalsLoading(true);
    setSelectedId(null);
    listPrincipals(selectedClientId)
      .then(data => {
        setPrincipals(data && data.length > 0 ? data.map(mapApiPrincipal) : AVAILABLE_PRINCIPALS);
      })
      .catch(() => setPrincipals(AVAILABLE_PRINCIPALS))
      .finally(() => setPrincipalsLoading(false));
  }, [isDemoMode, selectedClientId]);

  // ── Handlers ──────────────────────────────────────────────────────────

  function _finishProductionLogin(userEmail: string) {
    const inferred = inferClientIdFromEmail(userEmail);
    const clientId = inferred ?? 'lubricants';  // fallback for unmapped domains
    localStorage.setItem('a9_active_client_id', clientId);
    localStorage.setItem('a9_auth_email', userEmail);
    // Pick first principal in that client; real principal selection happens in-app
    navigate('/dashboard', { state: { clientId, principalId: null } });
  }

  async function handleProductionLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !password.trim()) return;
    setAuthLoading(true);
    setAuthError(null);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        setAuthError(error.message);
        return;
      }
      if (data.user?.email) {
        _finishProductionLogin(data.user.email);
      }
    } catch (err: unknown) {
      setAuthError(err instanceof Error ? err.message : 'Sign-in failed. Please try again.');
    } finally {
      setAuthLoading(false);
    }
  }

  function handleDemoLogin() {
    if (!selectedId) return;
    setDemoLoading(true);
    localStorage.setItem('a9_active_client_id', selectedClientId);
    localStorage.removeItem('a9_auth_email');
    setTimeout(() => {
      navigate('/dashboard', { state: { principalId: selectedId, clientId: selectedClientId } });
    }, 600);
  }

  const selectedClient = availableClients.find(c => c.id === selectedClientId);

  // ── Render ─────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">

        {/* Header */}
        <div className="bg-slate-900 border-b border-slate-800 p-8 text-center">
          <div className="flex items-center justify-center mb-4">
            <BrandLogo size={40} />
          </div>
          <p className="text-slate-400 text-sm">
            {isDemoMode ? 'Select your identity to continue' : 'Sign in to Decision Studio'}
          </p>
        </div>

        <div className="p-8 space-y-6">

          {isDemoMode ? (
            /* ── Demo mode ─────────────────────────────────────────────── */
            <>
              {/* Client Selector */}
              {availableClients.length > 0 && (
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                    Client
                  </label>
                  <div className="relative">
                    <select
                      value={selectedClientId}
                      onChange={(e) => setSelectedClientId(e.target.value)}
                      className="w-full appearance-none bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 pr-8 text-sm text-white cursor-pointer hover:bg-slate-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                    >
                      {availableClients.map(c => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none">
                      <ChevronRight className="w-4 h-4 text-slate-400 rotate-90" />
                    </div>
                  </div>
                  {selectedClient?.industry && (
                    <p className="text-[11px] text-slate-600 pl-1">{selectedClient.industry}</p>
                  )}
                </div>
              )}

              {/* Identity Selector */}
              <div className="space-y-3">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Select Identity
                </label>
                <div className="space-y-2">
                  {principalsLoading ? (
                    <div className="flex items-center justify-center py-6 text-slate-500 text-sm gap-2">
                      <span className="w-4 h-4 border-2 border-slate-600 border-t-slate-400 rounded-full animate-spin" />
                      Loading identities...
                    </div>
                  ) : (
                    principals.map((principal) => (
                      <button
                        key={principal.id}
                        onClick={() => setSelectedId(principal.id)}
                        className={`w-full flex items-center p-3 rounded-xl border transition-all duration-200 group ${
                          selectedId === principal.id
                            ? 'bg-indigo-600/10 border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.3)]'
                            : 'bg-slate-800/50 border-slate-700 hover:border-slate-600 hover:bg-slate-800'
                        }`}
                      >
                        <div
                          className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-xs mr-4 transition-transform group-hover:scale-105 ${
                            selectedId === principal.id
                              ? 'bg-indigo-500 text-white'
                              : `${principal.color.split(' ')[0]} text-white`
                          }`}
                        >
                          {principal.initials}
                        </div>
                        <div className="text-left flex-1">
                          <div className={`text-sm font-medium ${selectedId === principal.id ? 'text-white' : 'text-slate-300'}`}>
                            {principal.name}
                          </div>
                          <div className="text-xs text-slate-500">{principal.title}</div>
                        </div>
                        {selectedId === principal.id && (
                          <div className="w-2 h-2 rounded-full bg-indigo-400 shadow-[0_0_8px_rgba(129,140,248,0.8)] animate-pulse" />
                        )}
                      </button>
                    ))
                  )}
                </div>
              </div>

              <button
                onClick={handleDemoLogin}
                disabled={!selectedId || demoLoading}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all flex items-center justify-center gap-2 group"
              >
                {demoLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                    Loading…
                  </span>
                ) : (
                  <>
                    Continue
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>

              <div className="text-center">
                <a href="/login" className="text-xs text-slate-500 hover:text-slate-400 transition-colors">
                  ← Sign in with email
                </a>
              </div>
            </>

          ) : (
            /* ── Production auth ────────────────────────────────────────── */
            <>
              <form onSubmit={handleProductionLogin} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                    Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@yourcompany.com"
                      required
                      autoComplete="email"
                      className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-transparent"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      autoComplete="current-password"
                      className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-transparent"
                    />
                  </div>
                </div>

                {authError && (
                  <div className="flex items-start gap-2 p-3 bg-red-900/30 border border-red-700/50 rounded-lg">
                    <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
                    <p className="text-xs text-red-300">{authError}</p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={authLoading || !email.trim() || !password.trim()}
                  className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all flex items-center justify-center gap-2 group"
                >
                  {authLoading ? (
                    <span className="flex items-center gap-2">
                      <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                      Signing in…
                    </span>
                  ) : (
                    <>
                      Sign In
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </button>
              </form>

              <div className="text-center">
                <a
                  href="/login?mode=demo"
                  className="text-xs text-slate-500 hover:text-slate-400 transition-colors"
                >
                  Or try the demo →
                </a>
              </div>
            </>
          )}

          <div className="text-center pt-2">
            <p className="text-[10px] text-slate-600">
              Authorized personnel only. All actions are logged and audited.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
