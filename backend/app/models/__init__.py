"""Models package exposing all SQLAlchemy declarative models."""

from app.core.database import Base
from app.models.user import User, UserProfile
from app.models.resume import (
    Resume,
    ResumeSection,
    ResumeProject,
    ResumeExperience,
    ResumeCertification,
)
from app.models.skill import (
    Skill,
    SkillAlias,
    SkillRelationship,
    ResumeSkill,
)
from app.models.job import (
    Job,
    JobSection,
    JobRequirement,
    JobSkill,
    JobExperienceRequirement,
    JobEducationRequirement,
    JobCertification,
)
from app.models.matching import (
    MatchAnalysis,
    SkillMatch,
    SkillGap,
    ScoreBreakdown,
)
from app.models.career import (
    Occupation,
    OccupationSkill,
    CareerCompatibility,
    CareerCompatibilityComponent,
)
from app.models.learning import (
    LearningResource,
    LearningPath,
    LearningPathItem,
)

__all__ = [
    "Base",
    "User",
    "UserProfile",
    "Resume",
    "ResumeSection",
    "ResumeProject",
    "ResumeExperience",
    "ResumeCertification",
    "Skill",
    "SkillAlias",
    "SkillRelationship",
    "ResumeSkill",
    "Job",
    "JobSection",
    "JobRequirement",
    "JobSkill",
    "JobExperienceRequirement",
    "JobEducationRequirement",
    "JobCertification",
    "MatchAnalysis",
    "SkillMatch",
    "SkillGap",
    "ScoreBreakdown",
    "Occupation",
    "OccupationSkill",
    "CareerCompatibility",
    "CareerCompatibilityComponent",
    "LearningResource",
    "LearningPath",
    "LearningPathItem",
]
