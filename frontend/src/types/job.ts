/**
 * TypeScript type definitions for SkillBridge AI Phase 4:
 * Job Description ingestion, structured requirements, and job skills.
 */

export interface JobSection {
  id?: string;
  section_type: string;
  section_title: string;
  content_text: string;
  order_index: number;
}

export interface JobRequirement {
  id?: string;
  original_text: string;
  normalized_text: string;
  requirement_category: string; // 'SKILL' | 'EXPERIENCE' | 'EDUCATION' | 'CERTIFICATION' | 'RESPONSIBILITY' | 'DOMAIN_KNOWLEDGE' | 'SOFT_SKILL' | 'OTHER'
  priority: string; // 'REQUIRED' | 'PREFERRED' | 'UNKNOWN'
  source_section: string;
  evidence_text: string;
  confidence: number;
}

export interface JobSkill {
  id?: string;
  skill_id: string; // References canonical skill in DB
  raw_skill_text: string;
  canonical_skill_name: string;
  requirement_type: string; // 'REQUIRED' | 'PREFERRED' | 'UNKNOWN'
  source_section: string;
  evidence_text: string;
  confidence: number;
  taxonomy_sources: string[];
}

export interface JobExperienceRequirement {
  id?: string;
  minimum_years?: number | null;
  maximum_years?: number | null;
  experience_text: string;
  classification: string;
}

export interface JobEducationRequirement {
  id?: string;
  degree_level: string;
  field?: string | null;
  original_text: string;
  requirement_type: string;
}

export interface JobCertification {
  id?: string;
  name: string;
  requirement_type: string;
}

export interface JobSummary {
  id: string;
  title: string;
  normalized_role: string;
  company?: string | null;
  location?: string | null;
  ingestion_type: string;
  total_skills: number;
  required_skills_count: number;
  preferred_skills_count: number;
  min_years_experience?: number | null;
  created_at: string;
}

export interface StructuredJob {
  id: string;
  user_id: string;
  title: string;
  normalized_role: string;
  role_confidence: number;
  role_classification_method: string;
  company?: string | null;
  location?: string | null;
  source_url?: string | null;
  ingestion_type: string;
  raw_text: string;
  summary?: string | null;
  sections: JobSection[];
  requirements: JobRequirement[];
  required_skills: JobSkill[];
  preferred_skills: JobSkill[];
  all_skills: JobSkill[];
  experience_requirements: JobExperienceRequirement[];
  education_requirements: JobEducationRequirement[];
  certifications: JobCertification[];
  created_at: string;
  updated_at: string;
}

export interface JobCreatePastedPayload {
  title: string;
  raw_text: string;
  company?: string;
  location?: string;
  source_url?: string;
}
