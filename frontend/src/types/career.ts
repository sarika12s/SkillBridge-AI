export interface OccupationSkill {
  id?: string;
  skill_id: string;
  skill_name?: string;
  requirement_type: 'REQUIRED' | 'PREFERRED';
  importance_weight: number;
}

export interface Occupation {
  id: string;
  code: string;
  title: string;
  normalized_title: string;
  description: string;
  category: string;
  source: string;
  source_version: string;
  created_at?: string;
  skills: OccupationSkill[];
}

export interface CareerCompatibilityComponent {
  component_name: string;
  score: number;
  weight: number;
  weighted_score: number;
  explanation: string;
}

export interface CareerRoleMatch {
  occupation_id: string;
  occupation_title: string;
  occupation_code: string;
  category: string;
  compatibility_score: number;
  summary_explanation: string;
  components: CareerCompatibilityComponent[];
  strengths: string[];
  skill_gaps: string[];
  matched_skills_count: number;
  total_skills_count: number;
}

export interface CareerCompatibilityResponse {
  resume_id: string;
  roles: CareerRoleMatch[];
  matching_engine_version: string;
  scoring_version: string;
}
