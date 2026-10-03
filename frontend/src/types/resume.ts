export interface PersonalInformation {
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
}

export interface ResumeSection {
  id?: string;
  section_type: string;
  section_title: string;
  content_text: string;
  order_index: number;
  confidence_score: number;
}

export interface ResumeExperience {
  id?: string;
  company_name: string;
  job_title: string;
  location?: string | null;
  description?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
}

export interface ResumeProject {
  id?: string;
  project_name: string;
  role?: string | null;
  description?: string | null;
  technologies_used?: string[] | null;
  url?: string | null;
  start_date?: string | null;
  end_date?: string | null;
}

export interface ResumeCertification {
  id?: string;
  name: string;
  issuing_organization?: string | null;
  issue_date?: string | null;
  expiration_date?: string | null;
  credential_id?: string | null;
  credential_url?: string | null;
}

export interface ResumeSummary {
  id: string;
  user_id: string;
  title: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  parsing_status: string;
  extraction_method: 'TEXT' | 'OCR';
  page_count: number;
  character_count: number;
  version?: number;
  parsed_at: string | null;
  created_at: string;
  sections_count: number;
}

export interface StructuredResume {
  id: string;
  user_id: string;
  title: string;
  file_name: string;
  file_type: string;
  file_size_bytes: number;
  parsing_status: string;
  extraction_method: 'TEXT' | 'OCR';
  page_count: number;
  character_count: number;
  version?: number;
  parsed_at: string | null;
  created_at: string;
  personal_information: PersonalInformation;
  sections: ResumeSection[];
  experience: ResumeExperience[];
  projects: ResumeProject[];
  certifications: ResumeCertification[];
  raw_text?: string | null;
}

export interface STARComponentDetail {
  detected: boolean;
  evidence_text: string | null;
  signals_detected: string[];
  explanation: string;
}

export interface BulletSTARAnalysis {
  bullet_id: string;
  section_type: string;
  parent_entry_title: string;
  raw_text: string;
  situation: STARComponentDetail;
  task: STARComponentDetail;
  action: STARComponentDetail;
  result: STARComponentDetail;
  completeness_score: number;
  missing_components: string[];
  improvement_guidance: string[];
}

export interface STARSummaryMetrics {
  total_bullets_analyzed: number;
  bullets_with_action: number;
  bullets_with_result: number;
  bullets_with_situation: number;
  bullets_with_task: number;
  overall_completeness_percentage: number;
  strong_bullets_count: number;
  needs_improvement_count: number;
}

export interface ResumeSTARGuidanceResponse {
  resume_id: string;
  resume_version: number;
  resume_title: string;
  summary: STARSummaryMetrics;
  bullets: BulletSTARAnalysis[];
  methodology: string;
}
