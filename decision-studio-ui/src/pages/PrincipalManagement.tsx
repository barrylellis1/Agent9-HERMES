import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, User, ChevronsUpDown, Check, PlusCircle, XCircle, Loader2, Save } from 'lucide-react';
import { listPrincipals, listBusinessProcesses, updatePrincipal } from '../api/client';

interface Principal {
    id: string;
    name: string;
    title: string;
    business_processes: string[];
}

interface BusinessProcess {
    id: string;
    name: string;
    domain: string;
    description?: string;
}

export function PrincipalManagement() {
    const [principals, setPrincipals] = useState<Principal[]>([]);
    const [businessProcesses, setBusinessProcesses] = useState<BusinessProcess[]>([]);
    const [selectedPrincipal, setSelectedPrincipal] = useState<Principal | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    useEffect(() => {
        async function fetchData() {
            try {
                const [principalsData, bpData] = await Promise.all([
                    listPrincipals(),
                    listBusinessProcesses()
                ]);
                setPrincipals(principalsData);
                setBusinessProcesses(bpData);
                if (principalsData.length > 0) {
                    setSelectedPrincipal(principalsData[0]);
                }
            } catch (err) {
                setError('Failed to load data from backend');
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    const handleAddProcess = (processId: string) => {
        if (!selectedPrincipal) return;
        
        // Don't add if already exists
        if (selectedPrincipal.business_processes?.includes(processId)) return;

        const updatedPrincipal = {
            ...selectedPrincipal,
            business_processes: [...(selectedPrincipal.business_processes || []), processId],
        };
        setSelectedPrincipal(updatedPrincipal);
        setPrincipals(principals.map(p => p.id === updatedPrincipal.id ? updatedPrincipal : p));
        setSuccessMessage(null);
    };

    const handleRemoveProcess = (processId: string) => {
        if (!selectedPrincipal) return;
        const updatedPrincipal = {
            ...selectedPrincipal,
            business_processes: (selectedPrincipal.business_processes || []).filter(bp => bp !== processId),
        };
        setSelectedPrincipal(updatedPrincipal);
        setPrincipals(principals.map(p => p.id === updatedPrincipal.id ? updatedPrincipal : p));
        setSuccessMessage(null);
    };

    const handleSave = async () => {
        if (!selectedPrincipal) return;
        setSaving(true);
        setError(null);
        setSuccessMessage(null);
        try {
            await updatePrincipal(selectedPrincipal.id, {
                business_processes: selectedPrincipal.business_processes
            });
            setSuccessMessage('Changes saved successfully!');
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err) {
            setError('Failed to save changes');
            console.error(err);
        } finally {
            setSaving(false);
        }
    };

    const getProcessDisplayName = (bpIdentifier: string) => {
        // Try to find by ID first
        const bp = businessProcesses.find(p => p.id === bpIdentifier);
        if (bp) return `${bp.domain}: ${bp.name}`;
        
        // If not found, it might be a legacy string like "Finance: Profitability Analysis"
        return bpIdentifier;
    };

    // Filter available processes
    // We only show processes that are NOT currently assigned to the selected principal
    const availableProcesses = businessProcesses.filter(
        p => !selectedPrincipal?.business_processes?.includes(p.id) && 
             !selectedPrincipal?.business_processes?.includes(`${p.domain}: ${p.name}`) // Check legacy format too just in case
    );

    if (loading) {
        return (
            <div className="min-h-screen bg-background text-foreground p-8 flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                    <p className="text-slate-400">Loading registry data...</p>
                </div>
            </div>
        );
    }

    if (!selectedPrincipal) {
        return (
             <div className="min-h-screen bg-background text-foreground p-8 font-sans">
                <Link to="/admin" className="text-blue-400 hover:text-blue-300 flex items-center gap-2 mb-4">
                    <ArrowLeft className="w-4 h-4" /> Back to Admin
                </Link>
                <div className="text-white">No principals found in registry.</div>
             </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-foreground p-8 font-sans">
            <header className="mb-8 flex justify-between items-center max-w-7xl mx-auto">
                <div className="flex items-center gap-4">
                    <Link to="/admin" className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight text-white">Principal Management</h1>
                        <p className="text-sm text-slate-400">Assign business processes to principals for Situation Analysis.</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    {successMessage && (
                        <span className="text-green-400 text-sm flex items-center gap-2 animate-fade-in">
                            <Check className="w-4 h-4" /> {successMessage}
                        </span>
                    )}
                    {error && (
                        <span className="text-red-400 text-sm flex items-center gap-2 animate-fade-in">
                            <XCircle className="w-4 h-4" /> {error}
                        </span>
                    )}
                    <button 
                        onClick={handleSave}
                        disabled={saving}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                        {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>
            </header>

            <main className="max-w-7xl mx-auto grid grid-cols-12 gap-8">
                {/* Principal List */}
                <div className="col-span-4">
                    <div className="bg-card border border-border rounded-xl p-4 space-y-2 h-[calc(100vh-200px)] overflow-y-auto">
                        {principals.map(p => (
                            <button 
                                key={p.id} 
                                onClick={() => {
                                    setSelectedPrincipal(p);
                                    setSuccessMessage(null);
                                    setError(null);
                                }}
                                className={`w-full text-left flex items-center gap-3 p-3 rounded-lg transition-colors ${selectedPrincipal.id === p.id ? 'bg-slate-800 border-l-4 border-blue-500' : 'hover:bg-slate-800/50 border-l-4 border-transparent'}`}>
                                <div className={`p-2 rounded-full ${selectedPrincipal.id === p.id ? 'bg-blue-500/20 text-blue-400' : 'bg-slate-800 text-slate-500'}`}>
                                    <User className="w-5 h-5" />
                                </div>
                                <div>
                                    <p className={`font-medium ${selectedPrincipal.id === p.id ? 'text-white' : 'text-slate-300'}`}>{p.name}</p>
                                    <p className="text-xs text-slate-500">{p.title}</p>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Process Assignment */}
                <div className="col-span-8 grid grid-cols-1 gap-6">
                    {/* Assigned Processes */}
                    <div className="bg-card border border-border rounded-xl p-6 min-h-[300px]">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center justify-between">
                            <span>Assigned Processes</span>
                            <span className="text-sm font-normal text-slate-500">{selectedPrincipal.business_processes?.length || 0} assigned</span>
                        </h3>
                        <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
                            {selectedPrincipal.business_processes?.map(bp => (
                                <div key={bp} className="flex justify-between items-center bg-slate-800/60 p-3 rounded-lg border border-slate-700/50 group hover:border-slate-600 transition-colors">
                                    <div className="flex items-center gap-3">
                                        <div className="p-1.5 bg-green-500/10 text-green-500 rounded">
                                            <Check className="w-3 h-3" />
                                        </div>
                                        <span className="text-sm text-slate-200">{getProcessDisplayName(bp)}</span>
                                    </div>
                                    <button 
                                        onClick={() => handleRemoveProcess(bp)} 
                                        className="text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-red-500/10 rounded"
                                        title="Remove assignment"
                                    >
                                        <XCircle className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                             {(!selectedPrincipal.business_processes || selectedPrincipal.business_processes.length === 0) && (
                                <div className="text-center py-12 border-2 border-dashed border-slate-800 rounded-xl">
                                    <p className="text-slate-500 mb-2">No processes assigned</p>
                                    <p className="text-xs text-slate-600">Add processes from the list below</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Available Processes */}
                    <div className="bg-card border border-border rounded-xl p-6">
                        <h3 className="text-lg font-semibold text-white mb-4 flex items-center justify-between">
                            <span>Available Processes</span>
                            <span className="text-sm font-normal text-slate-500">{availableProcesses.length} available</span>
                        </h3>
                        <div className="grid grid-cols-2 gap-3 max-h-[300px] overflow-y-auto pr-2">
                            {availableProcesses.map(bp => (
                                <div key={bp.id} className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-800 hover:border-slate-700 transition-colors group">
                                    <div className="overflow-hidden">
                                        <p className="text-sm text-slate-300 truncate">{bp.domain}: {bp.name}</p>
                                        {bp.description && <p className="text-xs text-slate-600 truncate">{bp.description}</p>}
                                    </div>
                                    <button 
                                        onClick={() => handleAddProcess(bp.id)} 
                                        className="text-slate-500 hover:text-green-400 p-1 hover:bg-green-500/10 rounded"
                                        title="Assign to principal"
                                    >
                                        <PlusCircle className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                            {availableProcesses.length === 0 && (
                                <div className="col-span-2 text-center py-8 text-slate-500">
                                    All available processes are assigned.
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
