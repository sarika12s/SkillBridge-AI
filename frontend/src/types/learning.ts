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
