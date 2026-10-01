import { DataRecord, DataRecordCreateInput, HealthStatus } from '../types';

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
}

export const apiService = new ApiService();
export default apiService;
