import { useState, useEffect } from 'react';
import { X, Save, Plus, Trash2 } from 'lucide-react';
import { replaceKpi } from '../api/client';

interface Threshold {
  comparison_type: string;
  green_threshold: number | null;
  yellow_threshold: number | null;
  red_threshold: number | null;
}

interface ThresholdEditorModalProps {
  kpi: any; // raw KPI definition from registry
  clientId?: string;
  onClose: () => void;
  onSaved: () => void;
}

export function ThresholdEditorModal({ kpi, clientId, onClose, onSaved }: ThresholdEditorModalProps) {
  const [thresholds, setThresholds] = useState<Threshold[]>(
    (kpi.thresholds || []).length > 0
      ? kpi.thresholds
      : [{ comparison_type: 'yoy', green_threshold: null, yellow_threshold: null, red_threshold: null }]
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // The close button was the ONLY way to dismiss this modal — no backdrop
  // click, no Escape. Found during the 2026-08-29 harden pass fixing that
  // button's missing aria-label; Escape belongs with it, not a separate fix,
  // since both are "can a keyboard/screen-reader user get out of this modal."
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const COMPARISON_TYPES = ['yoy', 'qoq', 'mom', 'target', 'budget', 'greater_than', 'less_than'];

  const updateThreshold = (i: number, field: keyof Threshold, value: any) => {
    setThresholds(prev => prev.map((t, idx) => idx === i ? { ...t, [field]: value } : t));
  };

  const addThreshold = () => {
    setThresholds(prev => [
      ...prev,
      { comparison_type: 'yoy', green_threshold: null, yellow_threshold: null, red_threshold: null },
    ]);
  };

  const removeThreshold = (i: number) => {
    setThresholds(prev => prev.filter((_, idx) => idx !== i));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = { ...kpi, thresholds, client_id: clientId || kpi.client_id };
      await replaceKpi(kpi.id, payload);
      onSaved();
      onClose();
    } catch (e: any) {
      setError(e.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-xl shadow-2xl">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-semibold text-white">{kpi.name}</h2>
            <p className="text-xs text-slate-400 mt-0.5">Configure monitoring thresholds</p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close"
            className="p-1.5 text-slate-500 hover:text-white rounded-lg hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/60"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
          <div className="text-xs text-slate-500 mb-2">
            Green = healthy, Yellow = watch, Red = breach. Values are % change unless comparison_type is{' '}
            <code className="text-slate-400">target</code> or <code className="text-slate-400">budget</code>.
          </div>

          {thresholds.map((t, i) => (
            <div
              key={i}
              className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50 space-y-3"
            >
              <div className="flex items-center gap-2">
                <select
                  value={t.comparison_type}
                  onChange={e => updateThreshold(i, 'comparison_type', e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                >
                  {COMPARISON_TYPES.map(ct => (
                    <option key={ct} value={ct}>{ct}</option>
                  ))}
                </select>
                <button
                  onClick={() => removeThreshold(i)}
                  className="p-1.5 text-slate-600 hover:text-severity-critical ml-auto transition-colors"
                  title="Remove threshold"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="grid grid-cols-3 gap-3">
                {(['green_threshold', 'yellow_threshold', 'red_threshold'] as const).map(field => (
                  <div key={field}>
                    <label
                      className={`block text-[10px] font-semibold uppercase tracking-wider mb-1 ${
                        field === 'green_threshold'
                          ? 'text-severity-opportunity'
                          : field === 'yellow_threshold'
                          ? 'text-severity-warning'
                          : 'text-severity-critical'
                      }`}
                    >
                      {field.split('_')[0]}
                    </label>
                    <input
                      type="number"
                      value={t[field] ?? ''}
                      onChange={e =>
                        updateThreshold(i, field, e.target.value === '' ? null : Number(e.target.value))
                      }
                      placeholder="—"
                      className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                    />
                  </div>
                ))}
              </div>
            </div>
          ))}

          <button
            onClick={addThreshold}
            className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" /> Add threshold rule
          </button>

          {error && <p className="text-xs text-severity-critical">{error}</p>}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white text-sm font-medium transition-colors"
          >
            <Save className="w-4 h-4" />
            {saving ? 'Saving…' : 'Save Thresholds'}
          </button>
        </div>
      </div>
    </div>
  );
}
