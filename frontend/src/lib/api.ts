const API_BASE = '/api/v1';

export class ApiError extends Error {
  status: number;
  detail: any;
  constructor(status: number, detail: any) {
    super(typeof detail === 'string' ? detail : JSON.stringify(detail));
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('reqripple_token');
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorJson.error || errorDetail;
    } catch {
      // fallback to statusText
    }
    throw new ApiError(response.status, errorDetail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  // Check content type for csv export
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('text/csv')) {
    const text = await response.text();
    return text as unknown as T;
  }

  return response.json();
}

export const api = {
  // Auth
  login: (data: any) => request<any>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  register: (data: any) => request<any>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => request<any>('/auth/me'),

  // Projects
  getProjects: () => request<any[]>('/projects'),
  getProject: (id: string) => request<any>(`/projects/${id}`),
  createProject: (data: any) => request<any>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  getProjectMembers: (id: string) => request<any[]>(`/projects/${id}/members`),

  // Requirements
  getRequirements: (projectId: string, params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request<any>(`/projects/${projectId}/requirements${qs ? `?${qs}` : ''}`);
  },
  getRequirement: (id: string) => request<any>(`/requirements/${id}`),
  createRequirement: (projectId: string, data: any) =>
    request<any>(`/projects/${projectId}/requirements`, { method: 'POST', body: JSON.stringify(data) }),
  getRequirementVersions: (id: string) => request<any[]>(`/requirements/${id}/versions`),

  // Artifacts
  getArtifacts: (projectId: string, params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request<any>(`/projects/${projectId}/artifacts${qs ? `?${qs}` : ''}`);
  },
  getArtifact: (id: string) => request<any>(`/artifacts/${id}`),
  createArtifact: (projectId: string, data: any) =>
    request<any>(`/projects/${projectId}/artifacts`, { method: 'POST', body: JSON.stringify(data) }),

  // Traceability Graph
  getGraph: (projectId: string) => request<any>(`/projects/${projectId}/graph`),
  createEdge: (projectId: string, data: any) =>
    request<any>(`/projects/${projectId}/edges`, { method: 'POST', body: JSON.stringify(data) }),
  deactivateEdge: (edgeId: string) => request<any>(`/edges/${edgeId}`, { method: 'DELETE' }),
  getTraceabilityHealth: (projectId: string) => request<any>(`/projects/${projectId}/traceability-health`),

  // Change Requests
  getChangeRequests: (projectId: string, params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request<any>(`/projects/${projectId}/change-requests${qs ? `?${qs}` : ''}`);
  },
  getChangeRequest: (id: string) => request<any>(`/change-requests/${id}`),
  createChangeRequest: (projectId: string, data: any) =>
    request<any>(`/projects/${projectId}/change-requests`, { method: 'POST', body: JSON.stringify(data) }),
  getChangeDiff: (id: string) => request<any[]>(`/change-requests/${id}/diff`),
  analyseChange: (id: string) => request<any>(`/change-requests/${id}/analyse`, { method: 'POST' }),
  simulateChange: (id: string) => request<any>(`/change-requests/${id}/simulate`, { method: 'POST' }),
  approveChange: (id: string, data: any) => request<any>(`/change-requests/${id}/approve`, { method: 'POST', body: JSON.stringify(data) }),
  rejectChange: (id: string, data: any) => request<any>(`/change-requests/${id}/reject`, { method: 'POST', body: JSON.stringify(data) }),
  deferChange: (id: string, data: any) => request<any>(`/change-requests/${id}/defer`, { method: 'POST', body: JSON.stringify(data) }),
  checkClosure: (id: string) => request<any>(`/change-requests/${id}/closure-check`),
  closeChange: (id: string) => request<any>(`/change-requests/${id}/close`, { method: 'POST' }),

  // Impact & Remediation
  getImpactAnalysis: (analysisId: string) => request<any>(`/impact-analyses/${analysisId}`),
  updateDisposition: (resultId: string, data: any) =>
    request<any>(`/impact-results/${resultId}/disposition`, { method: 'POST', body: JSON.stringify(data) }),
  createRemediationAction: (resultId: string, data: any) =>
    request<any>(`/impact-results/${resultId}/actions`, { method: 'POST', body: JSON.stringify(data) }),
  updateRemediationAction: (actionId: string, data: any) =>
    request<any>(`/remediation-actions/${actionId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  recordTestExecution: (artifactId: string, data: any) =>
    request<any>(`/artifacts/${artifactId}/test-executions`, { method: 'POST', body: JSON.stringify(data) }),

  // Dashboard & Reports
  getDashboard: (projectId: string) => request<any>(`/projects/${projectId}/dashboard`),
  getChangeDebt: (projectId: string) => request<any>(`/projects/${projectId}/change-debt`),
  getVolatility: (projectId: string) => request<any[]>(`/projects/${projectId}/volatility`),
  exportCsv: async (analysisId: string) => {
    const token = localStorage.getItem('reqripple_token');
    const res = await fetch(`${API_BASE}/impact-analyses/${analysisId}/export.csv`, {
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    });
    return res.blob();
  },
};
