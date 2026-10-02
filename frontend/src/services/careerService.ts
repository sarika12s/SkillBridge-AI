import { apiClient } from './api';
import type { Occupation, CareerCompatibilityResponse } from '../types/career';

export const careerService = {
  async listOccupations(): Promise<Occupation[]> {
    const response = await apiClient.get<Occupation[]>('/careers/occupations');
    return response.data;
  },

  async getOccupation(occupationId: string): Promise<Occupation> {
    const response = await apiClient.get<Occupation>(`/careers/occupations/${occupationId}`);
    return response.data;
  },

  async getCareerCompatibility(resumeId: string): Promise<CareerCompatibilityResponse> {
    const response = await apiClient.get<CareerCompatibilityResponse>(`/careers/compatibility/${resumeId}`);
    return response.data;
  },
};
