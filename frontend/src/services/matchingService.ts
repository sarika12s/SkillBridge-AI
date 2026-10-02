import { apiClient } from './api';
import type {
  MatchAnalysisResponse,
  ResumeSkillGapsResponse,
  SimulationRequest,
  SimulationResponse,
} from '../types/matching';

export const analyzeResumeJobMatch = async (
  resumeId: string,
  jobId: string
): Promise<MatchAnalysisResponse> => {
  const response = await apiClient.post<MatchAnalysisResponse>('/matching/analyze', {
    resume_id: resumeId,
    job_id: jobId,
  });
  return response.data;
};

export const getMatchAnalysisById = async (
  analysisId: string
): Promise<MatchAnalysisResponse> => {
  const response = await apiClient.get<MatchAnalysisResponse>(`/matching/${analysisId}`);
  return response.data;
};

export const getResumeJobMatch = async (
  resumeId: string,
  jobId: string
): Promise<MatchAnalysisResponse> => {
  const response = await apiClient.get<MatchAnalysisResponse>(
    `/resumes/${resumeId}/jobs/${jobId}/match`
  );
  return response.data;
};

export const getResumeSkillGaps = async (
  resumeId: string
): Promise<ResumeSkillGapsResponse> => {
  const response = await apiClient.get<ResumeSkillGapsResponse>(
    `/resumes/${resumeId}/skill-gaps`
  );
  return response.data;
};

export const simulateMatch = async (
  request: SimulationRequest
): Promise<SimulationResponse> => {
  const response = await apiClient.post<SimulationResponse>(
    '/matching/simulate',
    request
  );
  return response.data;
};
