"""Pydantic v2 schemas for skills, aliases, relationships, and extraction results."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class SkillAliasSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    alias: str
    alias_type: str
    source: str
    confidence: float = 1.0


class SkillRelationshipSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    source_skill_id: UUID
    target_skill_id: UUID
    target_skill_name: Optional[str] = None
    relationship_type: str
    strength_weight: float = 1.0
    source: str
    confidence: float = 1.0


class SkillSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    normalized_name: str
    category: str
    taxonomy_source: str
    taxonomy_code: Optional[str] = None
    description: Optional[str] = None
    embedding_available: bool = False
    aliases: List[SkillAliasSchema] = []
    relationships: List[SkillRelationshipSchema] = []


class ExtractedSkillMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    canonical_skill_id: UUID
    canonical_name: str
    original_text: str
    source_section: str
    evidence_sentence: str
    normalization_method: str  # 'EXACT', 'ALIAS', 'LEXICON_MATCH', 'SEMANTIC_EMBEDDING'
    taxonomy_sources: List[str] = []
    embedding_available: bool = True
    confidence: float = Field(..., ge=0.0, le=1.0)


class ResumeSkillsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resume_id: UUID
    total_skills_extracted: int
    skills: List[ExtractedSkillMatch]
