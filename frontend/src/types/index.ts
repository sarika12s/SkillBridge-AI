export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export * from './resume';
export * from './skill';
export * from './job';
export * from './matching';
export * from './career';
export * from './learning';
export * from './dashboard';

