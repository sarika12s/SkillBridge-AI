import { apiClient } from './api';

export interface HealthCheckResponse {
  status: string;
  project: string;
  official_title: string;
  environment: string;
  api_version: string;
  database: {
    status: string;
    engine: string;
    pgvector: string;
  };
}

export const fetchHealthCheck = async (): Promise<HealthCheckResponse> => {
  const response = await apiClient.get<HealthCheckResponse>('/health');
  return response.data;
};
