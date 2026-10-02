import { apiClient } from './api';
import type {
  DashboardOverviewResponse,
  SkillHistoryResponse,
  LearningProgressOverview,
  ScoreHistoryItem,
} from '../types/dashboard';

export const dashboardService = {
  async getOverview(): Promise<DashboardOverviewResponse> {
    const response = await apiClient.get<DashboardOverviewResponse>('/dashboard/overview');
    return response.data;
  },

  async getSkillHistory(skillName?: string): Promise<SkillHistoryResponse[]> {
    const params = skillName ? { skill_name: skillName } : {};
    const response = await apiClient.get<SkillHistoryResponse[]>('/progress/skills', { params });
    return response.data;
  },

  async getLearningProgress(): Promise<LearningProgressOverview> {
    const response = await apiClient.get<LearningProgressOverview>('/progress/learning');
    return response.data;
  },

  async getScoreHistory(): Promise<ScoreHistoryItem[]> {
    const response = await apiClient.get<ScoreHistoryItem[]>('/progress/scores');
    return response.data;
  },
};
