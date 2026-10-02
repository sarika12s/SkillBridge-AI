/**
 * TypeScript definitions for Phase 5 Semantic Matching, Skill Gaps, and Scoring Engine.
 */

export type MatchType =
  | 'DIRECT_MATCH'
  | 'ALIAS_MATCH'
  | 'TAXONOMY_EQUIVALENT'
  | 'SEMANTIC_MATCH'
  | 'RELATED_SUPPORT'
  | 'PARTIAL_MATCH'
  | 'NO_MATCH'
  | 'UNCERTAIN';

export type MatchStatus =
  | 'MATCHED_REQUIRED'
  | 'MISSING_REQUIRED'
  | 'PARTIAL_REQUIRED'
  | 'MATCHED_PREFERRED'
  | 'MISSING_PREFERRED'
  | 'PARTIAL_PREFERRED'
  | 'RELATED_SUPPORT'
  | 'UNCERTAIN';

export type RequirementPriority = 'REQUIRED' | 'PREFERRED' | 'UNKNOWN';

export interface SkillMatch {
  id?: string;
  canonical_skill_name: string;
  canonical_skill_id?: string;
  job_skill_id?: string;
  resume_skill_id?: string;
  match_type: MatchType;
  match_status: MatchStatus;
  priority: RequirementPriority;
  confidence: number;
  similarity_score?: number;
  resume_evidence?: string;
  job_evidence?: string;
  explanation: string;
}

export interface SkillGap {
  id?: string;
  canonical_skill_name: string;
  priority: RequirementPriority;
  status: string;
  importance_weight: number;
  explanation: string;
  job_evidence?: string;
}

export interface ScoreBreakdown {
  component_name: string;
  score: number;
  max_possible: number;
  weight: number;
  weighted_score: number;
  explanation: string;
}

export interface StructuredAlignment {
  experience_status: 'MEETS' | 'BELOW_REQUIREMENT' | 'UNKNOWN';
  experience_explanation: string;
  resume_years?: number;
  required_years?: number;

  education_status: 'MEETS' | 'PARTIAL' | 'MISSING' | 'UNKNOWN';
  education_explanation: string;
  resume_degree?: string;
  required_degree?: string;

  certification_status: 'MATCHED' | 'MISSING' | 'PARTIAL' | 'UNKNOWN';
  certification_explanation: string;
  matched_certifications: string[];
  missing_certifications: string[];
}

export interface ExplainabilitySummary {
  strengths: string[];
  critical_gaps: string[];
  positive_factors: string[];
  negative_factors: string[];
  uncertainties: string[];
}

export interface MatchAnalysisResponse {
  id: string;
  user_id: string;
  resume_id: string;
  job_id: string;
  job_title: string;
  job_company?: string;
  compatibility_score: number;
  ats_readiness_score: number;
  matching_engine_version: string;
  scoring_version: string;
  embedding_model: string;
  taxonomy_versions: string;
  summary_explanation?: string;
  created_at: string;

  skill_matches: SkillMatch[];
  skill_gaps: SkillGap[];
  score_breakdowns: ScoreBreakdown[];
  alignment: StructuredAlignment;
  explainability: ExplainabilitySummary;
}

export interface MatchRequest {
  resume_id: string;
  job_id: string;
}

export interface ResumeSkillGapsResponse {
  resume_id: string;
  total_gaps: number;
  required_gaps: SkillGap[];
  preferred_gaps: SkillGap[];
}

export interface SimulatedSkillDetail {
  skill_id: string;
  canonical_skill_name: string;
  priority: RequirementPriority;
  current_status: string;
  gap_reason: string;
  estimated_learning_hours?: number;
  learning_resources_count: number;
}

export interface ProjectedGapState {
  closed_gaps: string[];
  remaining_required_gaps: string[];
  remaining_preferred_gaps: string[];
  total_initial_gaps: number;
  total_remaining_gaps: number;
}

export interface CareerRoleProjection {
  occupation_id: string;
  occupation_title: string;
  current_compatibility_score: number;
  projected_compatibility_score: number;
  compatibility_score_delta: number;
}

export interface SimulationResponse {
  match_analysis_id: string;
  job_id: string;
  job_title: string;
  resume_id: string;

  current_ats_score: number;
  projected_ats_score: number;
  ats_score_delta: number;

  current_compatibility_score: number;
  projected_compatibility_score: number;
  compatibility_score_delta: number;

  current_required_coverage: number;
  projected_required_coverage: number;
  required_coverage_delta: number;

  current_preferred_coverage: number;
  projected_preferred_coverage: number;
  preferred_coverage_delta: number;

  simulated_skills: SimulatedSkillDetail[];
  gap_state: ProjectedGapState;
  projected_score_breakdowns: ScoreBreakdown[];

  total_estimated_learning_hours?: number;
  learning_hour_roi?: number;

  explanation: string;
  target_role_projection?: CareerRoleProjection;
}

export interface SimulationRequest {
  match_analysis_id: string;
  simulated_skill_ids: string[];
}
