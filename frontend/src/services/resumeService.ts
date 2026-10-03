import { apiClient } from './api';
import type { StructuredResume, ResumeSummary, ResumeSTARGuidanceResponse } from '../types/resume';

export const uploadResume = async (
  file: File,
  title?: string,
  onProgress?: (percent: number) => void
): Promise<StructuredResume> => {
  const formData = new FormData();
  formData.append('file', file);
  if (title && title.trim()) {
    formData.append('title', title.trim());
  }

  const response = await apiClient.post<StructuredResume>('/resumes/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (progressEvent.total && onProgress) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });

  return response.data;
};

export const listResumes = async (): Promise<ResumeSummary[]> => {
  const response = await apiClient.get<ResumeSummary[]>('/resumes');
  return response.data;
};

export const getResumeById = async (id: string): Promise<StructuredResume> => {
  const response = await apiClient.get<StructuredResume>(`/resumes/${id}`);
  return response.data;
};

export const deleteResume = async (id: string): Promise<void> => {
  await apiClient.delete(`/resumes/${id}`);
};

export const getSTARGuidance = async (resumeId: string): Promise<ResumeSTARGuidanceResponse> => {
  const response = await apiClient.get<ResumeSTARGuidanceResponse>(`/resumes/${resumeId}/star-guidance`);
  return response.data;
};
