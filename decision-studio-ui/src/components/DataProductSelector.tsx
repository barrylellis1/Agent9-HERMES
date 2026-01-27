/**
 * Data Product Selector Component
 * 
 * Allows users to select an existing registered data product to extend
 * with additional KPIs, rather than creating a new data product from scratch.
 */

import { useState, useEffect } from 'react'
import { Database, Search, ChevronRight, Loader2, Package, Calendar, Tag } from 'lucide-react'

interface DataProductSummary {
  id: string
  name: string
  domain: string
  description?: string
  source_system: string
  tags: string[]
  last_updated?: string
  table_count?: number
  kpi_count?: number
  yaml_contract_path?: string
}

interface DataProductSelectorProps {
  onSelect: (product: DataProductSummary) => void
  onCancel: () => void
}

export function DataProductSelector({ onSelect, onCancel }: DataProductSelectorProps) {
  const [products, setProducts] = useState<DataProductSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedDomain, setSelectedDomain] = useState<string>('all')
  const [selectedSystem, setSelectedSystem] = useState<string>('all')

  useEffect(() => {
    loadDataProducts()
  }, [])

  const loadDataProducts = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:8000/api/v1/registry/data-products')
      
      if (!response.ok) {
        throw new Error(`Failed to load data products: ${response.statusText}`)
      }

      const data = await response.json()
      // Registry API returns {status: "ok", data: [...]}
      setProducts(data.data || [])
    } catch (err) {
      console.error('Error loading data products:', err)
      setError(err instanceof Error ? err.message : 'Failed to load data products')
    } finally {
      setLoading(false)
    }
  }

  // Get unique domains and source systems for filters
  const domains = ['all', ...new Set(products.map(p => p.domain))]
  const sourceSystems = ['all', ...new Set(products.map(p => p.source_system))]

  // Filter products based on search and filters
  const filteredProducts = products.filter(product => {
    const matchesSearch = searchTerm === '' || 
      product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.id.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesDomain = selectedDomain === 'all' || product.domain === selectedDomain
    const matchesSystem = selectedSystem === 'all' || product.source_system === selectedSystem

    return matchesSearch && matchesDomain && matchesSystem
  })

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Unknown'
    try {
      return new Date(dateStr).toLocaleDateString()
    } catch {
      return dateStr
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 rounded-xl border border-slate-700 w-full max-w-4xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Package className="w-6 h-6 text-blue-400" />
              <h2 className="text-xl font-semibold text-white">Select Data Product to Extend</h2>
            </div>
            <button
              onClick={onCancel}
              className="text-slate-400 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>
          <p className="text-sm text-slate-400">
            Choose an existing data product to add new KPIs. You'll skip to KPI definition with the product's context pre-loaded.
          </p>
        </div>

        {/* Filters */}
        <div className="p-6 border-b border-slate-800 space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name, description, or ID..."
              className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Filters */}
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-400 mb-1">Domain</label>
              <select
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
              >
                {domains.map(domain => (
                  <option key={domain} value={domain}>
                    {domain === 'all' ? 'All Domains' : domain}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-xs font-medium text-slate-400 mb-1">Source System</label>
              <select
                value={selectedSystem}
                onChange={(e) => setSelectedSystem(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
              >
                {sourceSystems.map(system => (
                  <option key={system} value={system}>
                    {system === 'all' ? 'All Systems' : system}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Product List */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-400 mb-4">{error}</p>
              <button
                onClick={loadDataProducts}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
              >
                Retry
              </button>
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="text-center py-12">
              <Database className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400">No data products found</p>
              {searchTerm && (
                <p className="text-sm text-slate-500 mt-2">
                  Try adjusting your search or filters
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              {filteredProducts.map((product) => (
                <button
                  key={product.id}
                  onClick={() => onSelect(product)}
                  className="w-full p-4 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-blue-500 rounded-lg transition-all text-left group"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-white group-hover:text-blue-400 transition-colors">
                          {product.name}
                        </h3>
                        <span className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs rounded">
                          {product.domain}
                        </span>
                      </div>
                      {product.description && (
                        <p className="text-sm text-slate-400 mb-3 line-clamp-2">
                          {product.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-xs text-slate-500">
                        <div className="flex items-center gap-1">
                          <Database className="w-3 h-3" />
                          {product.source_system}
                        </div>
                        {product.table_count !== undefined && (
                          <div>
                            {product.table_count} table{product.table_count !== 1 ? 's' : ''}
                          </div>
                        )}
                        {product.kpi_count !== undefined && (
                          <div>
                            {product.kpi_count} KPI{product.kpi_count !== 1 ? 's' : ''}
                          </div>
                        )}
                        {product.last_updated && (
                          <div className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {formatDate(product.last_updated)}
                          </div>
                        )}
                      </div>
                      {product.tags && product.tags.length > 0 && (
                        <div className="flex items-center gap-2 mt-2">
                          <Tag className="w-3 h-3 text-slate-500" />
                          <div className="flex gap-1 flex-wrap">
                            {product.tags.slice(0, 3).map((tag, idx) => (
                              <span key={idx} className="px-1.5 py-0.5 bg-slate-700/50 text-slate-400 text-xs rounded">
                                {tag}
                              </span>
                            ))}
                            {product.tags.length > 3 && (
                              <span className="px-1.5 py-0.5 text-slate-500 text-xs">
                                +{product.tags.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                    <ChevronRight className="w-5 h-5 text-slate-600 group-hover:text-blue-400 transition-colors flex-shrink-0 ml-4" />
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-slate-800">
          <div className="flex items-center justify-between text-sm text-slate-400">
            <span>
              {filteredProducts.length} product{filteredProducts.length !== 1 ? 's' : ''} available
            </span>
            <button
              onClick={onCancel}
              className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
