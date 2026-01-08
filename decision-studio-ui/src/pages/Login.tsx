import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AVAILABLE_PRINCIPALS } from '../config/uiConstants';
import { ShieldCheck, ArrowRight } from 'lucide-react';

export function Login() {
  const navigate = useNavigate();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = () => {
    if (!selectedId) return;
    setLoading(true);
    // Simulate SSO delay
    setTimeout(() => {
      navigate('/dashboard', { state: { principalId: selectedId } });
    }, 800);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-slate-900 border-b border-slate-800 p-8 text-center">
          <div className="mx-auto w-16 h-16 bg-indigo-500/10 rounded-full flex items-center justify-center mb-4">
            <ShieldCheck className="w-8 h-8 text-indigo-400" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Agent9 Decision Studio</h1>
          <p className="text-slate-400 text-sm">Secure Single Sign-On</p>
        </div>

        {/* User Selection */}
        <div className="p-8 space-y-6">
          <div className="space-y-3">
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
              Select Identity
            </label>
            <div className="space-y-2">
              {AVAILABLE_PRINCIPALS.map((principal) => (
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
                        : `${principal.color.replace('text-', 'bg-').split(' ')[0]} text-white`
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
              ))}
            </div>
          </div>

          <button
            onClick={handleLogin}
            disabled={!selectedId || loading}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all flex items-center justify-center gap-2 group"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                Authenticating...
              </span>
            ) : (
              <>
                Sign In via SSO
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </button>
          
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
