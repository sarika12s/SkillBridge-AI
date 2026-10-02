import { apiClient } from './api';
import type {
  JobCreatePastedPayload,
  StructuredJob,
  JobSummary,
} from '../types/job';

export const createJobPasted = async (
  payload: JobCreatePastedPayload
): Promise<StructuredJob> => {
  const response = await apiClient.post<StructuredJob>('/jobs', payload);
  return response.data;
};

export const uploadJobFile = async (
  file: File,
  title?: string,
  company?: string,
  location?: string,
  sourceUrl?: string
): Promise<StructuredJob> => {
  const formData = new FormData();
  formData.append('file', file);
  if (title && title.trim()) formData.append('title', title.trim());
  if (company && company.trim()) formData.append('company', company.trim());
  if (location && location.trim()) formData.append('location', location.trim());
  if (sourceUrl && sourceUrl.trim()) formData.append('source_url', sourceUrl.trim());

  const response = await apiClient.post<StructuredJob>('/jobs/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const listJobs = async (): Promise<JobSummary[]> => {
  const response = await apiClient.get<JobSummary[]>('/jobs');
  return response.data;
};

export const getJobById = async (id: string): Promise<StructuredJob> => {
  const response = await apiClient.get<StructuredJob>(`/jobs/${id}`);
  return response.data;
};

export const deleteJob = async (id: string): Promise<void> => {
  await apiClient.delete(`/jobs/${id}`);
};
