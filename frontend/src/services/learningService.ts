import { apiClient } from './api';
import type { LearningPath, LearningPathCreateRequest } from '../types/learning';

export const learningService = {
  async createLearningPath(request: LearningPathCreateRequest): Promise<LearningPath> {
    const response = await apiClient.post<LearningPath>('/learning-paths', request);
    return response.data;
  },

  async getLearningPath(pathId: string): Promise<LearningPath> {
    const response = await apiClient.get<LearningPath>(`/learning-paths/${pathId}`);
    return response.data;
  },

  async listLearningPaths(): Promise<any[]> {
    const response = await apiClient.get<any[]>('/learning-paths');
    return response.data;
  },

  async updateItemProgress(
    itemId: string,
    status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED',
    notes?: string
  ): Promise<any> {
    const response = await apiClient.patch<any>(`/learning-paths/items/${itemId}/progress`, {
      status,
      notes,
    });
    return response.data;
  },
};
