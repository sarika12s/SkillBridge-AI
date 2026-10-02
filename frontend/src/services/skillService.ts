import { apiClient } from './api';
import type {
  ResumeSkillsResponse,
  CanonicalSkill,
  SkillRelationship,
} from '../types/skill';

export const extractResumeSkills = async (resumeId: string): Promise<ResumeSkillsResponse> => {
  const response = await apiClient.post<ResumeSkillsResponse>(`/skills/extract/${resumeId}`);
  return response.data;
};

export const getResumeSkills = async (resumeId: string): Promise<ResumeSkillsResponse> => {
  const response = await apiClient.get<ResumeSkillsResponse>(`/resumes/${resumeId}/skills`);
  return response.data;
};

export const getSkillById = async (skillId: string): Promise<CanonicalSkill> => {
  const response = await apiClient.get<CanonicalSkill>(`/skills/${skillId}`);
  return response.data;
};

export const getSkillRelationships = async (
  skillId: string
): Promise<SkillRelationship[]> => {
  const response = await apiClient.get<SkillRelationship[]>(`/skills/${skillId}/relationships`);
  return response.data;
};
