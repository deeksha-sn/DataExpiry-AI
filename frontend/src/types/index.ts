export interface DataRecord {
  id: number;
  record_id: string;
  data_type: string;
  category: string;
  sensitivity: 'High' | 'Medium' | 'Low' | string;
  collection_purpose: string;
  current_usage: string;
  owner: string;
  created_date: string;
  retention_period: string;
  expiry_date: string;
  status: 'Active' | 'Expired' | 'Expiring Soon' | string;
  last_accessed?: string | null;
  source: string;

  // Future-compatible fields (for Team Members 2 & 4)
  purpose_mismatch?: boolean;
  risk_level?: 'Low' | 'Medium' | 'High' | 'Critical' | string;
  ai_recommendation?: 'KEEP' | 'REVIEW' | 'ANONYMIZE' | 'DELETE' | string;
  ai_explanation?: string | null;
  policy_rule?: string | null;
  review_status?: string | null;
  anonymization_status?: string | null;
  deletion_status?: string | null;

  created_at: string;
  updated_at: string;
}

export interface DataRecordCreateInput {
  record_id: string;
  data_type: string;
  category: string;
  sensitivity: string;
  collection_purpose: string;
  current_usage: string;
  owner: string;
  created_date: string;
  retention_period: string;
  expiry_date: string;
  status: string;
  last_accessed?: string;
  source: string;
  purpose_mismatch?: boolean;
  risk_level?: string;
  ai_recommendation?: string;
  ai_explanation?: string;
  policy_rule?: string;
  review_status?: string;
  anonymization_status?: string;
  deletion_status?: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  version?: string;
}

export interface PurposeMismatchResult {
  record_id?: string | null;
  category: string;
  sensitivity: string;
  collection_purpose: string;
  current_usage: string;
  purpose_mismatch: boolean;
  risk_level: 'Low' | 'Medium' | 'High' | 'Critical' | string;
  ai_recommendation: 'KEEP' | 'REVIEW' | 'ANONYMIZE' | 'DELETE' | string;
  explanation: string;
  analysis_mode: 'rule_based' | 'ai_assisted' | string;
}

export interface PurposeMismatchCheckRequest {
  collection_purpose: string;
  current_usage: string;
  category?: string;
  sensitivity?: string;
  status?: string;
  expiry_date?: string;
}

export interface BatchAIAnalysisResponse {
  total_analyzed: number;
  potential_mismatches: number;
  records_requiring_review: number;
  recommendations: {
    KEEP: number;
    REVIEW: number;
    ANONYMIZE: number;
    DELETE: number;
  };
  risk_breakdown: {
    Critical: number;
    High: number;
    Medium: number;
    Low: number;
  };
  records: PurposeMismatchResult[];
}

export interface AIGovernanceSummary {
  total_records: number;
  potential_mismatches: number;
  records_requiring_review: number;
  high_sensitivity_count: number;
  recommendations: {
    KEEP: number;
    REVIEW: number;
    ANONYMIZE: number;
    DELETE: number;
  };
  risk_breakdown: {
    Critical: number;
    High: number;
    Medium: number;
    Low: number;
  };
  category_breakdown: Record<string, number>;
}

export interface PolicyRule {
  id: number;
  rule_code: string;
  name: string;
  category: string;
  retention_period: string;
  retention_days: number;
  action_on_expiry: 'KEEP' | 'REVIEW' | 'ANONYMIZE' | 'DELETE' | string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PolicyRuleCreateInput {
  rule_code: string;
  name: string;
  category: string;
  retention_period: string;
  retention_days?: number;
  action_on_expiry: string;
  description?: string | null;
  is_active?: boolean;
}

export interface PolicyRuleUpdateInput {
  name?: string;
  category?: string;
  retention_period?: string;
  retention_days?: number;
  action_on_expiry?: string;
  description?: string | null;
  is_active?: boolean;
}

export interface PolicyEvaluationItem {
  record_id: string;
  category: string;
  expiry_date: string;
  expiry_status: 'ACTIVE' | 'EXPIRING_SOON' | 'EXPIRED' | string;
  days_until_expiry: number;
  deterministic_recommendation: 'KEEP' | 'REVIEW' | 'ANONYMIZE' | 'DELETE' | string;
  matched_policy_rule?: string | null;
  ai_recommendation?: string | null;
  purpose_mismatch: boolean;
  evaluation_reason: string;
}

export interface PolicyEvaluationSummary {
  total_evaluated: number;
  active_count: number;
  expiring_soon_count: number;
  expired_count: number;
  recommendations: Record<string, number>;
  as_of_date: string;
  expiring_soon_days: number;
  records: PolicyEvaluationItem[];
}

export interface AuditLog {
  audit_id: number;
  record_id: string;
  action: 'KEEP' | 'REVIEW' | 'ANONYMIZE' | 'DELETE' | string;
  previous_status?: string | null;
  new_status?: string | null;
  user: string;
  reason?: string | null;
  ai_recommendation?: string | null;
  policy_rule?: string | null;
  timestamp: string;
  created_at: string;
}

export interface AuditFilterParams {
  record_id?: string;
  action?: string;
  user?: string;
  limit?: number;
  offset?: number;
}

export interface LifecycleActionRequest {
  action: 'KEEP' | 'REVIEW' | 'ANONYMIZE' | 'DELETE' | string;
  reason?: string | null;
}

export interface LifecycleActionResponse {
  record_id: string;
  action_executed: string;
  previous_status?: string | null;
  new_status?: string | null;
  audit_id: number;
  message: string;
  deletion_status?: string | null;
  anonymization_status?: string | null;
  review_status?: string | null;
}



