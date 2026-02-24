import { 
  ProblemRefinementRequest, 
  ProblemRefinementResult, 
  Situation 
} from './types';

// Re-export types for backward compatibility
export type { ProblemRefinementRequest, ProblemRefinementResult, Situation };
export * from './types';

const API_BASE = 'http://localhost:8000/api/v1';

export type Envelope<T> = {
  status: string;
  data: T;
};

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export interface SituationRequest {
  principalId: string;
  timeframe?: string;
  comparisonType?: string;
}

export type BusinessTerm = {
  name: string;
  synonyms: string[];
  description?: string | null;
  technical_mappings?: Record<string, unknown>;
};

export async function listGlossaryTerms(): Promise<BusinessTerm[]> {
  const envelope = await requestJson<Envelope<BusinessTerm[]>>(`/registry/glossary`);
  return envelope.data || [];
}

export async function createGlossaryTerm(payload: BusinessTerm): Promise<BusinessTerm> {
  const envelope = await requestJson<Envelope<BusinessTerm>>(`/registry/glossary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function updateGlossaryTerm(termName: string, payload: BusinessTerm): Promise<BusinessTerm> {
  const envelope = await requestJson<Envelope<BusinessTerm>>(`/registry/glossary/${encodeURIComponent(termName)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function deleteGlossaryTerm(termName: string): Promise<void> {
  await requestJson<void>(`/registry/glossary/${encodeURIComponent(termName)}`, {
    method: 'DELETE',
  });
}

// ------------------------------------------------------------------
// KPI Registry API
// ------------------------------------------------------------------

export async function listKpis(): Promise<any[]> {
  const envelope = await requestJson<Envelope<any[]>>(`/registry/kpis`);
  return envelope.data || [];
}

export async function getKpi(id: string): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/kpis/${encodeURIComponent(id)}`);
  return envelope.data;
}

export async function createKpi(payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/kpis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function updateKpi(id: string, payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/kpis/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function replaceKpi(id: string, payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/kpis/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function deleteKpi(id: string): Promise<void> {
  await requestJson<void>(`/registry/kpis/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
}

// ------------------------------------------------------------------
// Principal Registry API
// ------------------------------------------------------------------

export async function listPrincipals(clientId?: string): Promise<any[]> {
  const qs = clientId ? `?client_id=${encodeURIComponent(clientId)}` : '';
  const envelope = await requestJson<Envelope<any[]>>(`/registry/principals${qs}`);
  return envelope.data || [];
}

export async function listClients(): Promise<any[]> {
  const envelope = await requestJson<Envelope<any[]>>(`/registry/clients`);
  return envelope.data || [];
}

export async function getPrincipal(id: string): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/principals/${encodeURIComponent(id)}`);
  return envelope.data;
}

export async function createPrincipal(payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/principals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function updatePrincipal(principalId: string, payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/principals/${encodeURIComponent(principalId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return envelope.data;
}

export async function replacePrincipal(principalId: string, payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/principals/${encodeURIComponent(principalId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return envelope.data;
}

export async function deletePrincipal(id: string): Promise<void> {
  await requestJson<void>(`/registry/principals/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
}

// ------------------------------------------------------------------
// Data Product Registry API
// ------------------------------------------------------------------

export async function listDataProducts(): Promise<any[]> {
  const envelope = await requestJson<Envelope<any[]>>(`/registry/data-products`);
  return envelope.data || [];
}

export async function getDataProduct(id: string): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/data-products/${encodeURIComponent(id)}`);
  return envelope.data;
}

export async function createDataProduct(payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/data-products`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function updateDataProduct(id: string, payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/data-products/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function replaceDataProduct(id: string, payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/data-products/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function deleteDataProduct(id: string): Promise<void> {
  await requestJson<void>(`/registry/data-products/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
}

// ------------------------------------------------------------------
// Business Process Registry API
// ------------------------------------------------------------------

export async function listBusinessProcesses(): Promise<any[]> {
  const envelope = await requestJson<Envelope<any[]>>(`/registry/business-processes`);
  return envelope.data || [];
}

export async function getBusinessProcess(id: string): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/business-processes/${encodeURIComponent(id)}`);
  return envelope.data;
}

export async function createBusinessProcess(payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/business-processes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function updateBusinessProcess(id: string, payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/business-processes/${encodeURIComponent(id)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function replaceBusinessProcess(id: string, payload: any): Promise<any> {
  const envelope = await requestJson<Envelope<any>>(`/registry/business-processes/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return envelope.data;
}

export async function deleteBusinessProcess(id: string): Promise<void> {
  await requestJson<void>(`/registry/business-processes/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
}

export interface UploadResponse {
  filename: string;
  filepath: string;
  size: number;
  content_type: string;
}

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/registry/upload`, {
    method: 'POST',
    body: formData, // fetch automatically sets Content-Type to multipart/form-data
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Upload failed: ${errorText}`);
  }

  return response.json();
}

export async function onboardDataProduct(payload: any) {
    // 1. Trigger the workflow
    const runResponse = await fetch(`${API_BASE}/workflows/data-product-onboarding/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (!runResponse.ok) {
      const errorText = await runResponse.text();
      throw new Error(`Failed to start onboarding: ${errorText}`);
    }
    
    const { data: { request_id } } = await runResponse.json();
  
    // 2. Poll for completion
    let attempts = 0;
    while (attempts < 60) { // Timeout after 60s
      const statusResponse = await fetch(`${API_BASE}/workflows/data-product-onboarding/${request_id}/status`);
      const { data } = await statusResponse.json();
      
      if (data.state === 'completed') {
        return data.result; 
      }
      if (data.state === 'failed') {
        throw new Error(data.error || 'Workflow failed');
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1s
      attempts++;
    }
    throw new Error('Workflow timed out');
  }

export async function detectSituations(
  principalId: string = 'cfo_001',
  timeframe: string = 'year_to_date',
  comparisonType: string = 'year_over_year',
  clientId?: string
): Promise<Situation[]> {
  // 1. Trigger the workflow
  const body: Record<string, any> = {
    principal_id: principalId,
    timeframe: timeframe,
    comparison_type: comparisonType,
  };
  if (clientId) body.client_id = clientId;

  const runResponse = await fetch(`${API_BASE}/workflows/situations/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  
  if (!runResponse.ok) {
    const errorText = await runResponse.text();
    throw new Error(`Failed to start detection: ${errorText}`);
  }
  
  const { data: { request_id } } = await runResponse.json();

  // 2. Poll for completion
  let attempts = 0;
  while (attempts < 30) { // Timeout after 30s
    const statusResponse = await fetch(`${API_BASE}/workflows/situations/${request_id}/status`);
    const { data } = await statusResponse.json();
    
    if (data.state === 'completed') {
      // The result structure is: result: { situations: { status: "success", situations: [...], ... } }
      // We want to return the normalized list
      const output = data.result.situations;
      return output.situations || []; 
    }
    if (data.state === 'failed') {
      throw new Error(data.error || 'Workflow failed');
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1s
    attempts++;
  }
  throw new Error('Workflow timed out');
}

export async function refineProblem(
  request: ProblemRefinementRequest
): Promise<ProblemRefinementResult> {
  const response = await fetch(`${API_BASE}/workflows/deep-analysis/refine`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to refine problem: ${errorText}`);
  }

  const { data } = await response.json();
  return data as ProblemRefinementResult;
}

export async function runDeepAnalysis(situationId: string, kpiName: string, principalId: string = 'cfo_001') {
    // 1. Trigger the workflow
    const runResponse = await fetch(`${API_BASE}/workflows/deep-analysis/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        principal_id: principalId,
        situation_id: situationId,
        scope: {
            kpi_id: kpiName
        },
        include_supporting_evidence: true
      })
    });
    
    if (!runResponse.ok) {
      const errorText = await runResponse.text();
      throw new Error(`Failed to start deep analysis: ${errorText}`);
    }
    
    const { data: { request_id } } = await runResponse.json();
  
    // 2. Poll for completion
    let attempts = 0;
    while (attempts < 45) { // Timeout after 45s (analysis can be slow)
      const statusResponse = await fetch(`${API_BASE}/workflows/deep-analysis/${request_id}/status`);
      const { data } = await statusResponse.json();
      
      if (data.state === 'completed') {
        return data.result; 
      }
      if (data.state === 'failed') {
        throw new Error(data.error || 'Workflow failed');
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1s
      attempts++;
    }
    throw new Error('Workflow timed out');
  }

export async function runSolutionFinder(
  deepAnalysisOutput: any,
  personas: string[] = ["CFO", "Supply Chain Expert", "Data Scientist"], 
  principalInput: any = null,
  principalId: string = 'cfo_001',
  preferencesOverride: any = null,
  principalContext: any = null  // NEW: Principal context with decision_style
) {
    // 1. Trigger the workflow - pass full Deep Analysis result for agent-to-agent data exchange
    const body: any = {
        principal_id: principalId,
        deep_analysis_output: deepAnalysisOutput,
        preferences: preferencesOverride || {
            personas: personas,
            principal_input: principalInput
        }
    };
    
    // Add principal_context if provided (for Principal-driven approach)
    if (principalContext) {
        body.principal_context = principalContext;
    }

    const runResponse = await fetch(`${API_BASE}/workflows/solutions/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    if (!runResponse.ok) {
      const errorText = await runResponse.text();
      throw new Error(`Failed to start solution finder: ${errorText}`);
    }
    
    const { data: { request_id } } = await runResponse.json();
  
    // 2. Poll for completion
    let attempts = 0;
    while (attempts < 60) {
      const statusResponse = await fetch(`${API_BASE}/workflows/solutions/${request_id}/status`);
      const { data } = await statusResponse.json();
      
      if (data.state === 'completed') {
        // Return full result envelope to access audit log (transcript) and solutions
        return data.result; 
      }
      if (data.state === 'failed') {
        throw new Error(data.error || 'Workflow failed');
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      attempts++;
    }
    throw new Error('Workflow timed out');
  }
