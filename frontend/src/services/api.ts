import {
  DataRecord,
  DataRecordCreateInput,
  HealthStatus,
  PurposeMismatchResult,
  PurposeMismatchCheckRequest,
  BatchAIAnalysisResponse,
  AIGovernanceSummary,
  PolicyRule,
  PolicyRuleCreateInput,
  PolicyRuleUpdateInput,
  PolicyEvaluationItem,
  PolicyEvaluationSummary,
  AuditLog,
  AuditFilterParams,
  LifecycleActionRequest,
  LifecycleActionResponse,
} from '../types';


const API_BASE_URL = '/api';

class ApiService {
  /**
   * Check API health status.
   */
  async getHealth(): Promise<HealthStatus> {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Healthcheck failed: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Fetch all data records with optional query filtering.
   */
  async getDataRecords(params?: {
    category?: string;
    status?: string;
    sensitivity?: string;
    limit?: number;
    offset?: number;
  }): Promise<DataRecord[]> {
    const searchParams = new URLSearchParams();
    if (params?.category) searchParams.append('category', params.category);
    if (params?.status) searchParams.append('status', params.status);
    if (params?.sensitivity) searchParams.append('sensitivity', params.sensitivity);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());

    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : '';
    const response = await fetch(`${API_BASE_URL}/data${queryString}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch records: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Fetch a single data record by record_id (e.g. CUS-1001) or internal ID.
   */
  async getDataRecord(recordId: string): Promise<DataRecord> {
    const response = await fetch(`${API_BASE_URL}/data/${encodeURIComponent(recordId)}`);
    if (!response.ok) {
      throw new Error(`Record '${recordId}' not found or error occurred.`);
    }
    return response.json();
  }

  /**
   * Create a new data record.
   */
  async createDataRecord(data: DataRecordCreateInput): Promise<DataRecord> {
    const response = await fetch(`${API_BASE_URL}/data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to create data record.`);
    }
    return response.json();
  }

  /**
   * Run batch AI purpose mismatch detection across all database records.
   */
  async runBatchAiAnalysis(): Promise<BatchAIAnalysisResponse> {
    const response = await fetch(`${API_BASE_URL}/ai/batch-analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to run batch AI analysis.`);
    }
    return response.json();
  }

  /**
   * Run AI analysis on a single record by record_id.
   */
  async analyzeRecord(recordId: string): Promise<PurposeMismatchResult> {
    const response = await fetch(`${API_BASE_URL}/data/${encodeURIComponent(recordId)}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to analyze record ${recordId}.`);
    }
    return response.json();
  }

  /**
   * Interactive sandbox evaluation for purpose vs usage without modifying DB records.
   */
  async checkPurposeMismatch(request: PurposeMismatchCheckRequest): Promise<PurposeMismatchResult> {
    const response = await fetch(`${API_BASE_URL}/ai/check-mismatch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Failed to check purpose mismatch.`);
    }
    return response.json();
  }

  /**
   * Get high-level AI governance metrics and distributions.
   */
  async getAIGovernanceSummary(): Promise<AIGovernanceSummary> {
    const response = await fetch(`${API_BASE_URL}/ai/summary`);
    if (!response.ok) {
      throw new Error(`Failed to fetch AI governance summary: ${response.statusText}`);
    }
    return response.json();
  }

  // ==============================================================================
  // Development Role / Identity Helpers (for local testing of RBAC)
  // ==============================================================================

  getDevRole(): string {
    return localStorage.getItem('dataexpiry-dev-role') || 'DATA_GOVERNANCE';
  }

  setDevRole(role: string): void {
    localStorage.setItem('dataexpiry-dev-role', role);
  }

  getDevUserId(): string {
    return localStorage.getItem('dataexpiry-dev-user-id') || 'dev_governance_user';
  }

  setDevUserId(userId: string): void {
    localStorage.setItem('dataexpiry-dev-user-id', userId);
  }

  isDevAuthHeaderEnabled(): boolean {
    const val = localStorage.getItem('dataexpiry-dev-auth-header-enabled');
    return val === null ? true : val === 'true';
  }

  setDevAuthHeaderEnabled(enabled: boolean): void {
    localStorage.setItem('dataexpiry-dev-auth-header-enabled', enabled ? 'true' : 'false');
  }

  private getAuthHeaders(includeAuth: boolean = true): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (includeAuth && this.isDevAuthHeaderEnabled()) {
      const role = this.getDevRole();
      const userId = this.getDevUserId();
      if (role) headers['X-User-Role'] = role;
      if (userId) headers['X-User-Id'] = userId;
    }
    return headers;
  }

  private async parseError(response: Response, defaultMsg: string): Promise<Error> {
    try {
      const errorData = await response.json();
      let detail = errorData.detail;
      if (Array.isArray(detail)) {
        detail = detail.map((d: any) => d.msg || JSON.stringify(d)).join('; ');
      }
      return new Error(detail || defaultMsg);
    } catch {
      return new Error(`${defaultMsg} (${response.status} ${response.statusText})`);
    }
  }

  // ==============================================================================
  // Policy Management Endpoints
  // ==============================================================================

  /**
   * List retention policies with optional active-only filter.
   */
  async listPolicies(activeOnly: boolean = false): Promise<PolicyRule[]> {
    const url = `${API_BASE_URL}/policies${activeOnly ? '?active_only=true' : ''}`;
    // Read operations work with default least-privileged VIEWER role without headers
    const response = await fetch(url, {
      headers: this.getAuthHeaders(false),
    });
    if (!response.ok) {
      throw await this.parseError(response, 'Failed to list retention policies.');
    }
    return response.json();
  }

  /**
   * Retrieve details of a specific policy by ID.
   */
  async getPolicy(id: number): Promise<PolicyRule> {
    const response = await fetch(`${API_BASE_URL}/policies/${id}`, {
      headers: this.getAuthHeaders(false),
    });
    if (!response.ok) {
      throw await this.parseError(response, `Policy rule #${id} not found.`);
    }
    return response.json();
  }

  /**
   * Create a new retention policy. Requires MANAGE_POLICY_ROLES (ADMIN or DATA_GOVERNANCE).
   */
  async createPolicy(policy: PolicyRuleCreateInput): Promise<PolicyRule> {
    const response = await fetch(`${API_BASE_URL}/policies`, {
      method: 'POST',
      headers: this.getAuthHeaders(true),
      body: JSON.stringify(policy),
    });
    if (!response.ok) {
      throw await this.parseError(response, 'Failed to create retention policy.');
    }
    return response.json();
  }

  /**
   * Update an existing retention policy. Requires MANAGE_POLICY_ROLES (ADMIN or DATA_GOVERNANCE).
   */
  async updatePolicy(id: number, policy: PolicyRuleUpdateInput): Promise<PolicyRule> {
    const response = await fetch(`${API_BASE_URL}/policies/${id}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(true),
      body: JSON.stringify(policy),
    });
    if (!response.ok) {
      throw await this.parseError(response, `Failed to update policy rule #${id}.`);
    }
    return response.json();
  }

  /**
   * Soft-deactivates a retention policy rule (sets is_active=False).
   * Requires MANAGE_POLICY_ROLES (ADMIN or DATA_GOVERNANCE).
   */
  async deactivatePolicy(id: number): Promise<PolicyRule> {
    const response = await fetch(`${API_BASE_URL}/policies/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(true),
    });
    if (!response.ok) {
      throw await this.parseError(response, `Failed to deactivate policy rule #${id}.`);
    }
    return response.json();
  }

  /**
   * Batch evaluate records against active retention policies.
   * Requires EVALUATE_POLICY_ROLES (ADMIN, DATA_GOVERNANCE, PRIVACY_OFFICER, AUDITOR).
   */
  async evaluatePolicies(params?: {
    as_of_date?: string;
    expiring_soon_days?: number;
    category?: string;
  }): Promise<PolicyEvaluationSummary> {
    const searchParams = new URLSearchParams();
    if (params?.as_of_date) searchParams.append('as_of_date', params.as_of_date);
    if (params?.expiring_soon_days !== undefined) {
      searchParams.append('expiring_soon_days', params.expiring_soon_days.toString());
    }
    if (params?.category) searchParams.append('category', params.category);

    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : '';
    const response = await fetch(`${API_BASE_URL}/policies/evaluate${queryString}`, {
      method: 'POST',
      headers: this.getAuthHeaders(true),
    });
    if (!response.ok) {
      throw await this.parseError(response, 'Batch policy evaluation failed.');
    }
    return response.json();
  }

  /**
   * Evaluate a single record against active retention policies.
   */
  async evaluateSingleRecord(
    recordId: string,
    params?: { as_of_date?: string; expiring_soon_days?: number }
  ): Promise<PolicyEvaluationItem> {
    const searchParams = new URLSearchParams();
    if (params?.as_of_date) searchParams.append('as_of_date', params.as_of_date);
    if (params?.expiring_soon_days !== undefined) {
      searchParams.append('expiring_soon_days', params.expiring_soon_days.toString());
    }

    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : '';
    const response = await fetch(
      `${API_BASE_URL}/policies/evaluate/${encodeURIComponent(recordId)}${queryString}`,
      {
        method: 'POST',
        headers: this.getAuthHeaders(true),
      }
    );
    if (!response.ok) {
      throw await this.parseError(response, `Evaluation failed for record '${recordId}'.`);
    }
    return response.json();
  }

  // ==============================================================================
  // Audit Trail Endpoints
  // ==============================================================================

  /**
   * Retrieve immutable audit log records with optional filtering and pagination.
   * Requires AUDIT_READ_ROLES (ADMIN, AUDITOR, DATA_GOVERNANCE, PRIVACY_OFFICER).
   */
  async getAuditLogs(params?: AuditFilterParams): Promise<AuditLog[]> {
    const searchParams = new URLSearchParams();
    if (params?.record_id) searchParams.append('record_id', params.record_id);
    if (params?.action) searchParams.append('action', params.action);
    if (params?.user) searchParams.append('user', params.user);
    if (params?.limit !== undefined) searchParams.append('limit', params.limit.toString());
    if (params?.offset !== undefined) searchParams.append('offset', params.offset.toString());

    const queryString = searchParams.toString() ? `?${searchParams.toString()}` : '';
    const response = await fetch(`${API_BASE_URL}/audit${queryString}`, {
      headers: this.getAuthHeaders(true),
    });
    if (!response.ok) {
      throw await this.parseError(response, 'Failed to fetch audit log trail.');
    }
    return response.json();
  }

  /**
   * Retrieve full chronological audit history for a specific data record.
   * Requires AUDIT_READ_ROLES (ADMIN, AUDITOR, DATA_GOVERNANCE, PRIVACY_OFFICER).
   */
  async getRecordAuditLogs(recordId: string): Promise<AuditLog[]> {
    const response = await fetch(`${API_BASE_URL}/audit/${encodeURIComponent(recordId)}`, {
      headers: this.getAuthHeaders(true),
    });
    if (!response.ok) {
      throw await this.parseError(response, `Failed to fetch audit logs for record '${recordId}'.`);
    }
    return response.json();
  }

  // ==============================================================================
  // Lifecycle Actions Endpoints
  // ==============================================================================

  /**
   * Execute a deterministic lifecycle action on a record.
   * Endpoint: POST /api/data/{record_id}/execute-action
   * Supported actions: KEEP, REVIEW, ANONYMIZE, DELETE (simulated).
   * Requires ACTION_PERMITTED_ROLES (ADMIN, DATA_GOVERNANCE, PRIVACY_OFFICER).
   * Note: DELETE is strictly restricted to ADMIN and DATA_GOVERNANCE.
   */
  async executeLifecycleAction(
    recordId: string,
    action: string,
    reason?: string | null
  ): Promise<LifecycleActionResponse> {
    const payload: LifecycleActionRequest = {
      action: action.toUpperCase(),
      reason: reason ? reason.trim() : undefined,
    };
    const response = await fetch(`${API_BASE_URL}/data/${encodeURIComponent(recordId)}/execute-action`, {
      method: 'POST',
      headers: this.getAuthHeaders(true),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw await this.parseError(response, `Failed to execute action '${action}' on record '${recordId}'.`);
    }
    return response.json();
  }
}




export const apiService = new ApiService();
export default apiService;
