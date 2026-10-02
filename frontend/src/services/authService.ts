import { apiClient } from './api';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

const TOKEN_KEY = 'skillbridge_token';

export const getStoredToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

export const saveToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const clearToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

export const loginUser = async (email: string, password: string): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/auth/login', {
    email: email.trim(),
    password,
  });
  if (response.data.access_token) {
    saveToken(response.data.access_token);
  }
  return response.data;
};

export const registerUser = async (
  email: string,
  password: string,
  full_name: string
): Promise<{ user: UserProfile; access_token: string }> => {
  const response = await apiClient.post<{ user: UserProfile; access_token: string }>(
    '/auth/register',
    {
      email: email.trim(),
      password,
      full_name: full_name.trim(),
    }
  );
  if (response.data.access_token) {
    saveToken(response.data.access_token);
  }
  return response.data;
};

export const getCurrentUser = async (): Promise<UserProfile> => {
  const response = await apiClient.get<UserProfile>('/auth/me');
  return response.data;
};
