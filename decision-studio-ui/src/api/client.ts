import {
  ProblemRefinementRequest,
  ProblemRefinementResult,
  Situation,
  OpportunitySignal,
  SituationDetectionResult,
  AssessmentSummary,
  AssessmentRun,
  KPIAssessment,
  PrincipalActionSummary,
} from './types';
import type {
  AcceptedSolution as VAAcceptedSolution,
  SolutionPhase,
  StrategyAwarePortfolio,
  RecordKPIMeasurementResponse,
  InactionCostProjection,
} from '../types/valueAssurance';

// Re-export types for backward compatibility
export type { ProblemRefinementRequest, ProblemRefinementResult, Situation, OpportunitySignal, SituationDetectionResult };
export * from './types';

const API_BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000') + '/api/v1';

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
): Promise<SituationDetectionResult> {
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

  // 2. Poll for completion (90s — monthly series adds ~15s to detection)
  let attempts = 0;
  while (attempts < 90) {
    const statusResponse = await fetch(`${API_BASE}/workflows/situations/${request_id}/status`);
    const { data } = await statusResponse.json();

    if (data.state === 'completed') {
      // The result structure is: result: { situations: { status: "success", situations: [...], opportunities: [...], ... } }
      const output = data.result.situations;
      return {
        situations: (output.situations || []) as Situation[],
        opportunities: (output.opportunities || []) as OpportunitySignal[],
      };
    }
    if (data.state === 'failed') {
      throw new Error(data.error || 'Workflow failed');
    }

    await new Promise(resolve => setTimeout(resolve, 1000));
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

export async function runDeepAnalysis(
  situationId: string,
  kpiName: string,
  principalId: string = 'cfo_001',
  timeframe?: string,
  analysisMode?: 'problem' | 'opportunity'
) {
    // 1. Trigger the workflow
    const body: Record<string, any> = {
      principal_id: principalId,
      situation_id: situationId,
      scope: { kpi_id: kpiName, timeframe: timeframe },
      include_supporting_evidence: true,
    };
    if (analysisMode) body.analysis_mode = analysisMode;
    const runResponse = await fetch(`${API_BASE}/workflows/deep-analysis/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
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
  principalContext: any = null,  // NEW: Principal context with decision_style
  situationId?: string
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

    if (situationId) {
        body.situation_id = situationId;
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
    while (attempts < 120) {  // 2 min — synthesis (Sonnet) + 529 retries can exceed 60s
      const statusResponse = await fetch(`${API_BASE}/workflows/solutions/${request_id}/status`);
      const { data } = await statusResponse.json();

      if (data.state === 'completed') {
        // Return result + request_id so callers can use request_id for HITL actions
        return { result: data.result, request_id };
      }
      if (data.state === 'failed') {
        throw new Error(data.error || 'Workflow failed');
      }

      await new Promise(resolve => setTimeout(resolve, 1000));
      attempts++;
    }
    throw new Error('Workflow timed out');
  }

export async function approveSolution(
  requestId: string,
  solutionOptionId: string,
  comment?: string
) {
  const response = await fetch(`${API_BASE}/workflows/solutions/${requestId}/actions/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action: 'approve',
      comment: comment || 'Approved via Decision Studio',
      payload: { solution_option_id: solutionOptionId },
    }),
  });
  if (!response.ok) {
    throw new Error(`Approve failed: ${await response.text()}`);
  }
  const { data } = await response.json();
  return data;
}

export interface BriefingQAResponse {
  answer: string;
  transparency_tier: number;
  tier_label: string;
  sources: string[];
  suggested_followups: string[];
}

export async function askBriefingQuestion(
  requestId: string,
  question: string,
  principalId: string,
  conversationHistory: Array<{ role: string; content: string }> = []
): Promise<BriefingQAResponse> {
  const envelope = await requestJson<Envelope<BriefingQAResponse>>(`/workflows/solutions/${requestId}/qa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, principal_id: principalId, conversation_history: conversationHistory }),
  });
  return envelope.data;
}

// ---------------------------------------------------------------------------
// Value Assurance — Phase 7C API functions
// ---------------------------------------------------------------------------

export async function getVASolution(solutionId: string): Promise<VAAcceptedSolution> {
  return requestJson<VAAcceptedSolution>(`/value-assurance/solutions/${solutionId}`);
}

export async function getVAPortfolio(principalId: string): Promise<StrategyAwarePortfolio> {
  return requestJson<StrategyAwarePortfolio>(`/value-assurance/portfolio/${principalId}`);
}

export async function projectInactionCost(
  situationId: string,
  kpiId: string,
  currentKpiValue: number,
  historicalTrend: number[],
  principalId: string = ''
): Promise<InactionCostProjection> {
  const resp = await requestJson<{ projection: InactionCostProjection }>(`/value-assurance/inaction-cost`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      request_id: crypto.randomUUID(),
      principal_id: principalId,
      situation_id: situationId,
      kpi_id: kpiId,
      current_kpi_value: currentKpiValue,
      historical_trend: historicalTrend,
    }),
  });
  return resp.projection;
}

export async function recordKPIMeasurement(
  solutionId: string,
  kpiValue: number,
  principalId: string = ''
): Promise<RecordKPIMeasurementResponse> {
  return requestJson<RecordKPIMeasurementResponse>(
    `/value-assurance/solutions/${solutionId}/measure?kpi_value=${kpiValue}&principal_id=${encodeURIComponent(principalId)}`,
    { method: 'POST' }
  );
}

export async function updateSolutionPhase(
  solutionId: string,
  newPhase: SolutionPhase,
  notes?: string,
  principalId: string = ''
): Promise<{ solution_id: string; phase: SolutionPhase; message: string }> {
  return requestJson(`/value-assurance/solutions/${solutionId}/phase?principal_id=${encodeURIComponent(principalId)}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ new_phase: newPhase, notes }),
  });
}

export async function storeBriefingSnapshot(solutionId: string, snapshot: Record<string, unknown>): Promise<void> {
  const response = await fetch(`${API_BASE}/value-assurance/solutions/${solutionId}/briefing`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(snapshot),
  });
  if (!response.ok) {
    throw new Error(`Failed to store briefing snapshot: ${response.status}`);
  }
}

export async function getBriefingSnapshot(solutionId: string): Promise<Record<string, unknown>> {
  return requestJson<Record<string, unknown>>(`/value-assurance/solutions/${solutionId}/briefing`);
}

// ---------------------------------------------------------------------------
// Assessment Pipeline — Phase 9C
// ---------------------------------------------------------------------------

export async function getLatestAssessment(principalId?: string): Promise<AssessmentSummary> {
  const params = principalId ? `?principal_id=${encodeURIComponent(principalId)}` : '';
  return requestJson<AssessmentSummary>(`/assessments/latest${params}`);
}

export async function getAssessment(runId: string): Promise<AssessmentSummary> {
  return requestJson<AssessmentSummary>(`/assessments/${runId}`);
}

export async function listAssessmentRuns(limit = 10): Promise<AssessmentRun[]> {
  return requestJson<AssessmentRun[]>(`/assessments/runs?limit=${limit}`);
}

export async function triggerAssessment(principalId?: string, dryRun = false): Promise<AssessmentRun> {
  const params = new URLSearchParams();
  if (principalId) params.set('principal_id', principalId);
  if (dryRun) params.set('dry_run', 'true');
  return requestJson<AssessmentRun>(`/assessments/run?${params.toString()}`, { method: 'POST' });
}

// suppress unused-import warning — KPIAssessment is exported for consumer use
export type { KPIAssessment };

// PIB delegation actions — used to badge delegated KPI tiles in the dashboard
export async function getPrincipalActions(
  principalId: string,
  actionType?: string,
): Promise<PrincipalActionSummary[]> {
  const params = new URLSearchParams({ principal_id: principalId });
  if (actionType) params.set('action_type', actionType);
  return requestJson<PrincipalActionSummary[]>(`/pib/actions?${params.toString()}`);
}
export type { PrincipalActionSummary };
