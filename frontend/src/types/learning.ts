export interface LearningResource {
  id?: string;
  skill_id: string;
  skill_name?: string;
  title: string;
  provider: string;
  url: string;
  resource_type: string;
  cost_type: string;
  difficulty_level: string;
  estimated_hours: number;
  description?: string;
  rating: number;
}

export interface LearningPathItem {
  id: string;
  learning_path_id: string;
  skill_id: string;
  skill_name: string;
  skill_category?: string;
  stage_order: number;
  sequence_in_stage: number;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
  estimated_hours: number;
  completed_at?: string;
  notes?: string;
  prerequisites_summary?: string;
  verified_by_resume_id?: string;
  verified_by_resume_version?: number;
  verified_at?: string;
  verification_method?: string;
  resource?: LearningResource;
}

export interface LearningStage {
  stage_number: number;
  stage_title: string;
  stage_description: string;
  stage_estimated_hours: number;
  items: LearningPathItem[];
}

export interface LearningPathGraphNode {
  id: string;
  label: string;
  status: 'ACQUIRED' | 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
  category?: string;
  stage: number;
}

export interface LearningPathGraphEdge {
  source: string;
  target: string;
  relationship_type: string;
}

export interface LearningPathGraph {
  nodes: LearningPathGraphNode[];
  edges: LearningPathGraphEdge[];
}

export interface LearningPath {
  id: string;
  user_id: string;
  resume_id: string;
  target_type: 'CAREER' | 'JOB';
  target_occupation_id?: string;
  target_job_id?: string;
  target_title?: string;
  title: string;
  description?: string;
  total_estimated_hours_min: number;
  total_estimated_hours_max: number;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'ARCHIVED';
  overall_progress_percentage: number;
  stages: LearningStage[];
  graph?: LearningPathGraph;
  created_at: string;
  updated_at: string;
}

export interface LearningPathCreateRequest {
  resume_id: string;
  target_type: 'CAREER' | 'JOB';
  target_occupation_id?: string;
  target_job_id?: string;
}

export interface ItemProgressUpdateRequest {
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
  notes?: string;
}

export interface ReconciliationRequest {
  resume_id?: string;
}

export interface VerifiedItemDetail {
  item_id: string;
  skill_id: string;
  skill_name: string;
  stage_order: number;
  match_method: string;
  confidence: number;
  evidence_sentence: string;
  verified_at: string;
}

export interface ReconciliationResponse {
  learning_path_id: string;
  baseline_resume_id: string;
  verifying_resume_id: string;
  verifying_resume_version: number;
  items_evaluated: number;
  newly_verified_count: number;
  already_completed_count: number;
  remaining_unverified_count: number;
  previous_progress_percentage: number;
  new_progress_percentage: number;
  previous_remaining_hours: number;
  new_remaining_hours: number;
  path_status: string;
  verified_items: VerifiedItemDetail[];
  message: string;
}

export interface PrioritizedSkill {
  skill_id: string;
  skill_name: string;
  category: string;
  priority_score: number;
  role_criticality: number;
  dependency_leverage: number;
  gap_impact: number;
  learning_efficiency: number;
  readiness_status: 'READY' | 'BLOCKED' | 'COMPLETED';
  unsatisfied_prerequisites: string[];
  satisfied_prerequisites: string[];
  downstream_unlocked_skills: string[];
  downstream_unlocked_count: number;
  estimated_hours: number;
  delta_compatibility: number;
  is_implicit_prerequisite: boolean;
  explanation: string;
  item_id?: string | null;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
  stage_order?: number | null;
}

export interface NextBestSkill {
  skill_id: string;
  skill_name: string;
  category: string;
  priority_score: number;
  estimated_hours: number;
  delta_compatibility: number;
  downstream_unlocked_count: number;
  downstream_unlocked_skills: string[];
  explanation: string;
  is_implicit_prerequisite: boolean;
  item_id?: string | null;
}

export interface DiagnosticCycle {
  has_cycle: boolean;
  cycle_paths: string[][];
}

export interface PrioritizedRoadmapResponse {
  learning_path_id: string;
  target_type: 'CAREER' | 'JOB';
  target_title?: string | null;
  overall_progress_percentage: number;
  total_skills_count: number;
  ready_skills_count: number;
  blocked_skills_count: number;
  completed_skills_count: number;
  next_best_skill?: NextBestSkill | null;
  prioritized_skills: PrioritizedSkill[];
  diagnostics: DiagnosticCycle;
}
