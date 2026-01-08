import { 
  ProblemRefinementRequest, 
  ProblemRefinementResult, 
  Situation 
} from './types';

// Re-export types for backward compatibility
export type { ProblemRefinementRequest, ProblemRefinementResult, Situation };
export * from './types';

const API_BASE = 'http://localhost:8000/api/v1';

export interface SituationRequest {
  principalId: string;
  timeframe?: string;
  comparisonType?: string;
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

export async function detectSituations(principalId: string = 'cfo_001'): Promise<Situation[]> {
  // 1. Trigger the workflow
  const runResponse = await fetch(`${API_BASE}/workflows/situations/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      principal_id: principalId,
      timeframe: 'year_to_date',
      comparison_type: 'year_over_year'
    })
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
