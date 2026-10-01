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
