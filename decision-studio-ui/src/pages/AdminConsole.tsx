import { Link } from 'react-router-dom'
import { ArrowLeft, Database, FileUp, CheckCircle2 } from 'lucide-react'

export function AdminConsole() {
  return (
    <div className="min-h-screen bg-background text-foreground p-8 font-sans">
      <header className="mb-8 flex justify-between items-center">
        <div className="flex items-center gap-4">
            <Link to="/" className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors">
                <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
                <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Admin Console</h1>
                <p className="text-slate-400">Data Product Management</p>
            </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Onboarding Card */}
            <Link to="/admin/onboarding" className="group block p-6 bg-card border border-border rounded-xl hover:border-slate-500 transition-colors">
                <div className="flex items-center justify-between mb-4">
                    <div className="p-3 bg-blue-500/10 text-blue-400 rounded-lg">
                        <FileUp className="w-6 h-6" />
                    </div>
                    <ArrowLeft className="w-4 h-4 text-slate-500 opacity-0 group-hover:opacity-100 rotate-180 transition-all" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Onboard Data Product</h3>
                <p className="text-sm text-slate-400">Upload CSV/Parquet files, inspect schema, and register new data products.</p>
            </Link>

            {/* Registry Card (Future) */}
            <div className="p-6 bg-card/50 border border-border/50 rounded-xl opacity-50 cursor-not-allowed">
                <div className="flex items-center justify-between mb-4">
                    <div className="p-3 bg-purple-500/10 text-purple-400 rounded-lg">
                        <Database className="w-6 h-6" />
                    </div>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Registry Explorer</h3>
                <p className="text-sm text-slate-400">View registered data products, KPIs, and entities.</p>
            </div>
        </div>
      </main>
    </div>
  )
}
