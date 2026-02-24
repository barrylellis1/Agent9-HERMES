import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Sparkles, CheckCircle, AlertCircle, Edit3, Trash2 } from 'lucide-react'
import { API_ENDPOINTS, buildUrl } from '../config/api-endpoints'

interface KPIDefinition {
    id: string
    name: string
    domain: string
    description: string
    unit?: string
    data_product_id: string
    sql_query?: string
    dimensions?: Array<{
        name: string
        field: string
        description?: string
    }>
    thresholds?: Array<{
        comparison_type: string
        green_threshold?: number
        yellow_threshold?: number
        red_threshold?: number
    }>
    metadata?: {
        line?: string
        altitude?: string
        profit_driver_type?: string
        lens_affinity?: string
    }
    tags?: string[]
    owner_role?: string
    stakeholder_roles?: string[]
}

interface Message {
    role: 'user' | 'assistant' | 'system'
    content: string
    kpis?: KPIDefinition[]
    actions?: Array<{
        label: string
        action: string
    }>
}

interface KPIAssistantChatProps {
    dataProductId: string
    domain: string
    sourceSystem: string
    tables: string[]
    database?: string
    schema?: string
    schemaMetadata: {
        measures: Array<{ name: string; data_type: string }>
        dimensions: Array<{ name: string; data_type: string }>
        time_columns: Array<{ name: string; data_type: string }>
        identifiers: Array<{ name: string; data_type: string }>
    }
    onKPIsFinalized: (kpis: KPIDefinition[]) => void
    onClose?: () => void
}

export function KPIAssistantChat({
    dataProductId,
    domain,
    sourceSystem,
    tables,
    database,
    schema,
    schemaMetadata,
    onKPIsFinalized,
    onClose
}: KPIAssistantChatProps) {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [conversationId, setConversationId] = useState<string | null>(null)
    const [currentKPIs, setCurrentKPIs] = useState<KPIDefinition[]>([])
    const [suggestionsGenerated, setSuggestionsGenerated] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    // Auto-generate suggestions on mount
    useEffect(() => {
        if (!suggestionsGenerated) {
            generateInitialSuggestions()
        }
    }, [])

    const generateInitialSuggestions = async () => {
        setLoading(true)
        try {
            const response = await fetch(buildUrl(API_ENDPOINTS.kpiAssistant.suggest), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    data_product_id: dataProductId,
                    domain: domain,
                    source_system: sourceSystem,
                    tables: tables,
                    database: database,
                    schema: schema,
                    measures: schemaMetadata.measures,
                    dimensions: schemaMetadata.dimensions,
                    time_columns: schemaMetadata.time_columns,
                    identifiers: schemaMetadata.identifiers,
                    num_suggestions: 5
                })
            })

            if (!response.ok) throw new Error('Failed to generate suggestions')

            const data = await response.json()
            
            setConversationId(data.conversation_id)
            setCurrentKPIs(data.suggested_kpis)
            setSuggestionsGenerated(true)

            setMessages([
                {
                    role: 'assistant',
                    content: `I've analyzed your ${sourceSystem} schema and suggested ${data.suggested_kpis.length} KPIs based on the available measures and dimensions.\n\n${data.rationale}\n\nYou can review these suggestions below, ask me to modify them, or add new KPIs.`,
                    kpis: data.suggested_kpis,
                    actions: [
                        { label: 'Accept All', action: 'accept' },
                        { label: 'Customize', action: 'edit' }
                    ]
                }
            ])
        } catch (error) {
            console.error('Error generating suggestions:', error)
            setMessages([
                {
                    role: 'assistant',
                    content: 'I encountered an error generating KPI suggestions. Please try again or define KPIs manually.',
                }
            ])
        } finally {
            setLoading(false)
        }
    }

    const sendMessage = async () => {
        if (!input.trim() || !conversationId) return

        const userMessage: Message = { role: 'user', content: input }
        setMessages(prev => [...prev, userMessage])
        setInput('')
        setLoading(true)

        try {
            const response = await fetch(buildUrl(API_ENDPOINTS.kpiAssistant.chat), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conversation_id: conversationId,
                    message: input,
                    current_kpis: currentKPIs
                })
            })

            if (!response.ok) throw new Error('Chat request failed')

            const data = await response.json()

            // Update KPIs if the assistant provided updates
            if (data.updated_kpis && data.updated_kpis.length > 0) {
                setCurrentKPIs(data.updated_kpis)
            }

            const assistantMessage: Message = {
                role: 'assistant',
                content: data.response,
                kpis: data.updated_kpis,
                actions: data.actions
            }

            setMessages(prev => [...prev, assistantMessage])
        } catch (error) {
            console.error('Error sending message:', error)
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Sorry, I encountered an error processing your request. Please try again.'
            }])
        } finally {
            setLoading(false)
        }
    }

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    const handleAcceptAll = () => {
        onKPIsFinalized(currentKPIs)
    }

    const handleRemoveKPI = (kpiId: string) => {
        setCurrentKPIs(prev => prev.filter(kpi => kpi.id !== kpiId))
    }

    const getMetadataBadgeColor = (type: string, value: string) => {
        if (type === 'line') {
            return value === 'top_line' ? 'bg-green-500/20 text-green-400' :
                   value === 'middle_line' ? 'bg-blue-500/20 text-blue-400' :
                   'bg-purple-500/20 text-purple-400'
        }
        if (type === 'altitude') {
            return value === 'strategic' ? 'bg-red-500/20 text-red-400' :
                   value === 'tactical' ? 'bg-amber-500/20 text-amber-400' :
                   'bg-slate-500/20 text-slate-400'
        }
        return 'bg-slate-700/50 text-slate-300'
    }

    return (
        <div className="flex flex-col h-full bg-slate-950 rounded-xl border border-slate-800">
            {/* Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-blue-400" />
                    <h3 className="font-semibold text-white">KPI Assistant</h3>
                    <span className="text-xs text-slate-500">Powered by LLM</span>
                </div>
                {onClose && (
                    <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors">
                        ✕
                    </button>
                )}
            </div>

            {/* Current KPIs Panel */}
            {currentKPIs.length > 0 && (
                <div className="p-4 border-b border-slate-800 bg-slate-900/50 max-h-64 overflow-y-auto">
                    <div className="flex items-center justify-between mb-3">
                        <h4 className="text-sm font-semibold text-slate-400">Current KPIs ({currentKPIs.length})</h4>
                        <button
                            onClick={handleAcceptAll}
                            className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white text-xs rounded-md transition-colors flex items-center gap-1"
                        >
                            <CheckCircle className="w-3 h-3" />
                            Accept All
                        </button>
                    </div>
                    <div className="space-y-2">
                        {currentKPIs.map((kpi) => (
                            <div key={kpi.id} className="p-3 bg-slate-950 rounded-lg border border-slate-800 group">
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex-1">
                                        <h5 className="text-sm font-medium text-white">{kpi.name}</h5>
                                        <p className="text-xs text-slate-400 mt-1">{kpi.description}</p>
                                    </div>
                                    <button
                                        onClick={() => handleRemoveKPI(kpi.id)}
                                        className="opacity-0 group-hover:opacity-100 p-1 text-red-400 hover:text-red-300 transition-all"
                                    >
                                        <Trash2 className="w-3 h-3" />
                                    </button>
                                </div>
                                {kpi.metadata && (
                                    <div className="flex flex-wrap gap-1 mt-2">
                                        {kpi.metadata.line && (
                                            <span className={`px-2 py-0.5 rounded text-xs ${getMetadataBadgeColor('line', kpi.metadata.line)}`}>
                                                {kpi.metadata.line}
                                            </span>
                                        )}
                                        {kpi.metadata.altitude && (
                                            <span className={`px-2 py-0.5 rounded text-xs ${getMetadataBadgeColor('altitude', kpi.metadata.altitude)}`}>
                                                {kpi.metadata.altitude}
                                            </span>
                                        )}
                                        {kpi.metadata.profit_driver_type && (
                                            <span className="px-2 py-0.5 rounded text-xs bg-indigo-500/20 text-indigo-400">
                                                {kpi.metadata.profit_driver_type}
                                            </span>
                                        )}
                                        {kpi.unit && (
                                            <span className="px-2 py-0.5 rounded text-xs bg-slate-700 text-slate-300">
                                                {kpi.unit}
                                            </span>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message, idx) => (
                    <div key={idx} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-lg p-3 ${
                            message.role === 'user' 
                                ? 'bg-blue-600 text-white' 
                                : 'bg-slate-800 text-slate-100'
                        }`}>
                            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                            
                            {message.actions && message.actions.length > 0 && (
                                <div className="flex gap-2 mt-3">
                                    {message.actions.map((action, actionIdx) => (
                                        <button
                                            key={actionIdx}
                                            onClick={() => {
                                                if (action.action === 'accept') {
                                                    handleAcceptAll()
                                                }
                                            }}
                                            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                                                action.action === 'accept' 
                                                    ? 'bg-green-600 hover:bg-green-500 text-white'
                                                    : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
                                            }`}
                                        >
                                            {action.label}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-slate-800 rounded-lg p-3 flex items-center gap-2">
                            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                            <span className="text-sm text-slate-300">Thinking...</span>
                        </div>
                    </div>
                )}
                
                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-slate-800">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask me to modify KPIs, add thresholds, or explain strategic metadata..."
                        className="flex-1 p-3 bg-slate-900 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 focus:outline-none text-sm"
                        disabled={loading || !conversationId}
                    />
                    <button
                        onClick={sendMessage}
                        disabled={loading || !input.trim() || !conversationId}
                        className="px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                    Example: "Add a threshold for revenue growth" or "Change the altitude to tactical"
                </p>
            </div>
        </div>
    )
}
