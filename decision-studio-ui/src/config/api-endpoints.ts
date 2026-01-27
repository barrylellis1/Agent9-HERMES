/**
 * Agent9 API Endpoint Registry
 * 
 * Single source of truth for all backend API endpoints.
 * Import and use these constants instead of hardcoding URLs.
 * 
 * Backend API Structure:
 * - Workflows: /api/v1/workflows/*
 * - Registry: /api/v1/registry/*
 * - KPI Assistant: /api/kpi-assistant/*
 * - Connection Profiles: /api/connection-profiles/*
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const API_ENDPOINTS = {
  /**
   * Workflow endpoints for orchestrated multi-step processes
   */
  workflows: {
    base: '/api/v1/workflows',
    
    situations: {
      run: '/api/v1/workflows/situations/run',
      status: (requestId: string) => `/api/v1/workflows/situations/${requestId}/status`,
      annotate: (requestId: string) => `/api/v1/workflows/situations/${requestId}/annotations`,
    },
    
    deepAnalysis: {
      run: '/api/v1/workflows/deep-analysis/run',
      status: (requestId: string) => `/api/v1/workflows/deep-analysis/${requestId}/status`,
      refine: '/api/v1/workflows/deep-analysis/refine',
      requestRevision: (requestId: string) => `/api/v1/workflows/deep-analysis/${requestId}/actions/request-revision`,
    },
    
    solutions: {
      run: '/api/v1/workflows/solutions/run',
      status: (requestId: string) => `/api/v1/workflows/solutions/${requestId}/status`,
      approve: (requestId: string) => `/api/v1/workflows/solutions/${requestId}/actions/approve`,
      requestChanges: (requestId: string) => `/api/v1/workflows/solutions/${requestId}/actions/request-changes`,
      iterate: (requestId: string) => `/api/v1/workflows/solutions/${requestId}/actions/iterate`,
    },
    
    dataProductOnboarding: {
      run: '/api/v1/workflows/data-product-onboarding/run',
      status: (requestId: string) => `/api/v1/workflows/data-product-onboarding/${requestId}/status`,
      validateQueries: '/api/v1/workflows/data-product-onboarding/validate-kpi-queries',
    },
  },

  /**
   * KPI Assistant endpoints for AI-powered KPI generation
   */
  kpiAssistant: {
    base: '/api/v1/data-product-onboarding/kpi-assistant',
    suggest: '/api/v1/data-product-onboarding/kpi-assistant/suggest',
    finalize: '/api/v1/data-product-onboarding/kpi-assistant/finalize',
  },

  /**
   * Registry endpoints for metadata management
   */
  registry: {
    base: '/api/v1/registry',
    kpis: '/api/v1/registry/kpis',
    dataProducts: '/api/v1/registry/data-products',
    businessProcesses: '/api/v1/registry/business-processes',
    principals: '/api/v1/registry/principals',
    businessGlossary: '/api/v1/registry/business-glossary',
  },

  /**
   * Connection profile endpoints for data source management
   */
  connectionProfiles: {
    base: '/api/connection-profiles',
    list: '/api/connection-profiles',
    get: (profileId: string) => `/api/connection-profiles/${profileId}`,
    create: '/api/connection-profiles',
    update: (profileId: string) => `/api/connection-profiles/${profileId}`,
    delete: (profileId: string) => `/api/connection-profiles/${profileId}`,
    setActive: (profileId: string) => `/api/connection-profiles/${profileId}/set-active`,
  },

  /**
   * Upload endpoints for file management
   */
  upload: {
    base: '/api/v1/upload',
    file: '/api/v1/upload',
  },
} as const

/**
 * Helper function to build full URL
 */
export function buildUrl(endpoint: string): string {
  return `${API_BASE_URL}${endpoint}`
}

/**
 * Type-safe endpoint builder
 */
export type ApiEndpoint = typeof API_ENDPOINTS
