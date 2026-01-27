# Agent9 API Integration Guide

## Overview

This guide establishes the standards and best practices for integrating the Agent9 frontend (React) with the backend (FastAPI) APIs.

## API Endpoint Structure

### Backend API Organization

The Agent9 backend uses a versioned API structure with the following prefixes:

```
/api/v1/workflows/*          - Multi-step orchestrated workflows
/api/v1/registry/*           - Metadata registry operations
/api/kpi-assistant/*         - KPI Assistant AI services
/api/connection-profiles/*   - Data source connection management
/api/v1/upload/*             - File upload services
```

### Version Prefix Strategy

- **Versioned endpoints** (`/api/v1/*`): Core platform APIs that may evolve
- **Unversioned endpoints** (`/api/*`): Stable service APIs with backward compatibility

## Frontend Integration Pattern

### ✅ DO: Use the API Endpoints Constants File

**Always import from the centralized constants file:**

```typescript
import { API_ENDPOINTS, buildUrl } from '../config/api-endpoints'

// Example: Call the query validation endpoint
const response = await fetch(buildUrl(API_ENDPOINTS.workflows.dataProductOnboarding.validateQueries), {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
})
```

### ❌ DON'T: Hardcode API URLs

**Never hardcode URLs in components:**

```typescript
// ❌ WRONG - Hardcoded URL
const response = await fetch('http://localhost:8000/api/v1/workflows/...', {
  method: 'POST',
  ...
})

// ❌ WRONG - String concatenation
const response = await fetch(`${API_BASE_URL}/api/workflows/...`, {
  method: 'POST',
  ...
})
```

## API Endpoints Constants File

### Location

```
decision-studio-ui/src/config/api-endpoints.ts
```

### Structure

The constants file provides:

1. **Base URL configuration** - Environment-aware base URL
2. **Organized endpoint groups** - Logical grouping by feature area
3. **Type-safe builders** - TypeScript types for autocomplete
4. **Helper functions** - `buildUrl()` for constructing full URLs

### Example Structure

```typescript
export const API_ENDPOINTS = {
  workflows: {
    base: '/api/v1/workflows',
    dataProductOnboarding: {
      run: '/api/v1/workflows/data-product-onboarding/run',
      status: (requestId: string) => `/api/v1/workflows/data-product-onboarding/${requestId}/status`,
      validateQueries: '/api/v1/workflows/data-product-onboarding/validate-kpi-queries',
    },
  },
  kpiAssistant: {
    base: '/api/kpi-assistant',
    suggestKpis: '/api/kpi-assistant/suggest-kpis',
    finalizeKpis: '/api/kpi-assistant/finalize-kpis',
  },
  // ... more endpoints
} as const
```

## Adding New Endpoints

### Backend (FastAPI)

1. **Define the route in the appropriate router:**

```python
# src/api/routes/workflows.py
@router.post("/data-product-onboarding/validate-kpi-queries", response_model=Envelope)
async def validate_kpi_queries(
    request: ValidateKPIQueriesRequest,
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> Envelope:
    # Implementation
    pass
```

2. **Ensure the router is registered in `src/api/main.py`:**

```python
from src.api.routes.workflows import router as workflows_router

app.include_router(workflows_router, prefix="/api/v1")
```

### Frontend (React/TypeScript)

1. **Add the endpoint to `api-endpoints.ts`:**

```typescript
export const API_ENDPOINTS = {
  workflows: {
    dataProductOnboarding: {
      validateQueries: '/api/v1/workflows/data-product-onboarding/validate-kpi-queries',
    },
  },
}
```

2. **Use the endpoint in your component:**

```typescript
import { API_ENDPOINTS, buildUrl } from '../config/api-endpoints'

const response = await fetch(buildUrl(API_ENDPOINTS.workflows.dataProductOnboarding.validateQueries), {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
})
```

## Common Patterns

### Polling for Async Results

Many Agent9 workflows are asynchronous. Use this pattern:

```typescript
// 1. Start the workflow
const response = await fetch(buildUrl(API_ENDPOINTS.workflows.dataProductOnboarding.run), {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
})

const result = await response.json()
const requestId = result.data.request_id

// 2. Poll for status
const pollInterval = setInterval(async () => {
  const statusResponse = await fetch(
    buildUrl(API_ENDPOINTS.workflows.dataProductOnboarding.status(requestId))
  )
  const statusData = await statusResponse.json()
  
  if (statusData.data.state === 'completed' || statusData.data.state === 'failed') {
    clearInterval(pollInterval)
    // Handle completion
  }
}, 2000)
```

### Error Handling

Always handle errors gracefully:

```typescript
try {
  const response = await fetch(buildUrl(API_ENDPOINTS.workflows.dataProductOnboarding.validateQueries), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })

  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.detail || 'Request failed')
  }

  const data = await response.json()
  // Handle success
  
} catch (err: any) {
  console.error('Validation failed:', err.message)
  setError(`Validation failed: ${err.message}`)
}
```

## Benefits of This Pattern

1. **Single Source of Truth** - All endpoints defined in one place
2. **Type Safety** - TypeScript ensures correct usage with autocomplete
3. **Maintainability** - Change once, update everywhere
4. **Discoverability** - Developers can easily find available endpoints
5. **Prevents Mismatches** - No more `/api` vs `/api/v1` issues
6. **Environment Flexibility** - Easy to switch between dev/staging/prod

## Troubleshooting

### 404 Not Found Errors

If you get a 404 error:

1. **Check the endpoint path** - Verify it matches the backend route exactly
2. **Check the version prefix** - Ensure `/api/v1` is included if required
3. **Check the router registration** - Verify the router is registered in `main.py`
4. **Check the constants file** - Ensure the endpoint is correctly defined

### CORS Errors

If you get CORS errors in development:

1. **Verify the backend CORS settings** in `src/api/main.py`
2. **Check the API_BASE_URL** in `api-endpoints.ts`
3. **Ensure the frontend is running on the expected port** (default: 5173)

## Migration Checklist

When migrating existing code to use the constants file:

- [ ] Import `API_ENDPOINTS` and `buildUrl` from `../config/api-endpoints`
- [ ] Replace all hardcoded URLs with constant references
- [ ] Remove any `API_BASE_URL` string concatenation
- [ ] Test all API calls to ensure they still work
- [ ] Remove unused `API_BASE_URL` imports if no longer needed

## Related Documentation

- [Agent9 Architecture Blueprint](../architecture/agent9_architecture_blueprint.md)
- [API Endpoint Registry](../api/endpoint_registry.md)
- [FastAPI Backend Documentation](http://localhost:8000/docs)

## Questions or Issues?

If you encounter issues with API integration or need to add new endpoints, please:

1. Review this guide
2. Check the `api-endpoints.ts` file for existing patterns
3. Consult the backend API documentation at `/docs`
4. Update this guide if you discover new patterns or best practices
