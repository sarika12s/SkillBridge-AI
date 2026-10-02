/**
 * TypeScript type definitions for SkillBridge AI Phase 3:
 * Skill intelligence, canonical taxonomy, and extraction results.
 */

export interface SkillAlias {
  id?: string;
  alias: string;
  alias_type: string;
  source: string;
  confidence: number;
}

export interface SkillRelationship {
  id?: string;
  source_skill_id: string;
  target_skill_id: string;
  target_skill_name?: string;
  relationship_type: string; // 'PREREQUISITE_OF' | 'SUBSKILL_OF' | 'RELATED_TO' | 'USED_WITH'
  strength_weight: number;
  source: string;
  confidence: number;
}

export interface CanonicalSkill {
  id: string;
  name: string;
  normalized_name: string;
  category: string;
  taxonomy_source: string; // 'ESCO' | 'ONET' | 'CUSTOM' | 'HYBRID'
  taxonomy_code?: string;
  description?: string;
  embedding_available: boolean;
  aliases: SkillAlias[];
  relationships: SkillRelationship[];
}

export interface ExtractedSkillMatch {
  canonical_skill_id: string;
  canonical_name: string;
  original_text: string;
  source_section: string;
  evidence_sentence: string;
  normalization_method: string; // 'EXACT' | 'ALIAS' | 'SYNONYM' | 'ACRONYM' | 'SPELLING_VARIANT'
  taxonomy_sources: string[];
  embedding_available: boolean;
  confidence: number;
}

export interface ResumeSkillsResponse {
  resume_id: string;
  total_skills_extracted: number;
  skills: ExtractedSkillMatch[];
}
