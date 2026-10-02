import type { ResumeSummary } from './resume';

export type DashboardLifecycleState =
  | 'NEW_USER'
  | 'NO_RESUME'
  | 'RESUME_ONLY'
  | 'RESUME_ANALYZED'
  | 'JOB_ANALYZED'
  | 'CAREER_ANALYZED'
  | 'LEARNING_PATH_CREATED'
  | 'ACTIVE_LEARNING'
  | 'COMPLETED_LEARNING';

export interface ResumeVersionSummary {
  id: string;
  version: number;
  title: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  parsing_status: string;
  skills_count: number;
  created_at: string;
  last_analysis_at?: string | null;
}

export interface SkillEvidenceChange {
  skill_name: string;
  previous_section: string;
  new_section: string;
  previous_evidence: string;
  new_evidence: string;
  strengthened: boolean;
}

export interface SectionChanges {
  v1_section_count: number;
  v2_section_count: number;
  new_sections: string[];
  removed_sections: string[];
  character_delta: number;
}

export interface ResumeVersionComparison {
  resume_v1_id: string;
  resume_v1_version: number;
  resume_v1_title: string;
  resume_v1_created_at: string;

  resume_v2_id: string;
  resume_v2_version: number;
  resume_v2_title: string;
  resume_v2_created_at: string;

  new_skills: string[];
  retained_skills: string[];
  removed_skills: string[];

  skill_evidence_changes: SkillEvidenceChange[];
  section_changes: SectionChanges;

  ats_score_v1?: number | null;
  ats_score_v2?: number | null;
  ats_score_delta?: number | null;

  job_compatibility_v1?: number | null;
  job_compatibility_v2?: number | null;
  job_compatibility_delta?: number | null;

  is_same_job_comparison: boolean;
  target_job_title?: string | null;
  comparability_notes: string;
}

export interface SkillHistoryItem {
  resume_id: string;
  resume_version: number;
  detected_at: string;
  status: 'FIRST_DETECTED' | 'RETAINED' | 'NEW' | 'REMOVED' | 'STRENGTHENED' | 'WEAKENED' | 'UNKNOWN';
  evidence_sentence?: string | null;
  source_section?: string | null;
  confidence: number;
}

export interface SkillHistoryResponse {
  skill_name: string;
  category: string;
  current_status: string;
  history: SkillHistoryItem[];
}

export interface ScoreHistoryItem {
  analysis_id: string;
  analysis_type: 'JOB_MATCH' | 'CAREER_COMPATIBILITY';
  resume_id: string;
  resume_version: number;
  target_id: string;
  target_title: string;
  company_name?: string | null;
  ats_readiness_score?: number | null;
  compatibility_score: number;
  required_skill_coverage?: number | null;
  preferred_skill_coverage?: number | null;
  scoring_version: string;
  engine_version: string;
  created_at: string;
}

export interface LearningProgressOverview {
  total_paths: number;
  completed_paths: number;
  in_progress_paths: number;
  active_path_id?: string | null;
  active_path_title?: string | null;
  active_path_target?: string | null;
  total_items: number;
  completed_items: number;
  in_progress_items: number;
  not_started_items: number;
  overall_completion_percentage: number;
  total_estimated_hours: number;
  remaining_estimated_hours: number;
  current_stage: number;
}

export interface DashboardJobAnalysis {
  id: string;
  job_id: string;
  job_title: string;
  company_name?: string | null;
  compatibility_score: number;
  ats_readiness_score: number;
  scoring_version: string;
  created_at: string;
}

export interface TopCareerRole {
  id: string;
  occupation_id: string;
  title: string;
  code: string;
  category: string;
  compatibility_score: number;
  created_at: string;
}

export interface SkillGapTrendItem {
  id: string;
  skill_name: string;
  priority: string;
  importance_weight: number;
  difficulty_level: string;
  reason: string;
}

export interface DashboardOverviewResponse {
  state: DashboardLifecycleState;
  latest_resume?: ResumeSummary | null;
  resume_versions_count: number;
  latest_job_analysis?: DashboardJobAnalysis | null;

  latest_ats_readiness_score?: number | null;
  latest_job_compatibility_score?: number | null;
  required_skill_coverage?: number | null;
  preferred_skill_coverage?: number | null;

  matched_skills_count: number;
  missing_required_skills_count: number;
  missing_preferred_skills_count: number;

  top_career_roles: TopCareerRole[];
  learning_overview?: LearningProgressOverview | null;
  score_trends: ScoreHistoryItem[];
  skill_gap_trends: SkillGapTrendItem[];
  insights: string[];
}
