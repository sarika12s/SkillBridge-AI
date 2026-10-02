import { apiClient } from './api';
import type { ResumeVersionSummary, ResumeVersionComparison } from '../types/dashboard';

export const versionService = {
  async listVersions(): Promise<ResumeVersionSummary[]> {
    const response = await apiClient.get<ResumeVersionSummary[]>('/resumes/versions');
    return response.data;
  },

  async compareVersions(
    resumeId1: string,
    resumeId2: string
  ): Promise<ResumeVersionComparison> {
    const response = await apiClient.get<ResumeVersionComparison>('/resumes/compare', {
      params: {
        resume_id_1: resumeId1,
        resume_id_2: resumeId2,
      },
    });
    return response.data;
  },
};
