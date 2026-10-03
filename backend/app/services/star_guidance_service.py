"""Service layer for Phase 8.3 STAR Resume Guidance.

Provides compute-on-read, deterministic structural analysis of resume
experience and project achievement bullets using the STAR framework.

Guarantees:
- Read-only: zero database writes or mutations.
- Strict tenant isolation and ownership validation.
- Stable derived bullet identifiers.
- Fixed-order deterministic guidance generation.
- Exact version matching.
"""

import re
from typing import List, Optional, Dict
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.resume import Resume, ResumeExperience, ResumeProject
from app.ai.guidance.star_analyzer import (
    STARAnalyzer,
    ComponentAnalysis,
    BulletAnalysisResult,
)
from app.schemas.star_guidance import (
    STARComponentDetail,
    BulletSTARAnalysis,
    STARSummaryMetrics,
    ResumeSTARGuidanceResponse,
)


class STARGuidanceOwnershipError(PermissionError, HTTPException):
    """Raised when the authenticated user does not own the requested resume."""
    def __init__(self, detail: str = "Access denied: Resume does not belong to the authenticated user."):
        HTTPException.__init__(self, status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        PermissionError.__init__(self, detail)


class STARGuidanceNotFoundError(ValueError, HTTPException):
    """Raised when the requested resume is not found in persistent storage."""
    def __init__(self, detail: str = "Resume not found."):
        HTTPException.__init__(self, status_code=status.HTTP_404_NOT_FOUND, detail=detail)
        ValueError.__init__(self, detail)


GUIDANCE_TEMPLATES: Dict[str, str] = {
    "SITUATION": "Consider adding brief context describing the environment, problem, constraint, or scale.",
    "TASK": "Consider clarifying the objective, responsibility, or scope you were expected to address.",
    "ACTION": "Consider starting with a clear action verb that describes what you personally implemented or performed.",
    "RESULT": "Consider adding a measurable outcome if one can be verified from your project.",
}

ORDERED_COMPONENTS: List[str] = ["SITUATION", "TASK", "ACTION", "RESULT"]


class STARGuidanceService:
    """
    Read-only service that evaluates persisted resume experiences and projects
    against the deterministic STAR analysis framework.
    """

    def __init__(self, analyzer: Optional[STARAnalyzer] = None) -> None:
        self.analyzer = analyzer or STARAnalyzer()

    # ---------------------------------------------------------------------
    # Bullet Segmentation
    # ---------------------------------------------------------------------

    def segment_bullets(self, text: Optional[str]) -> List[str]:
        """
        Deterministically segments experience/project descriptions into bullets.

        Note on why skill_extractor._split_into_sentences is not reused as-is:
        _split_into_sentences aggressively splits on periods followed by capital
        letters (r'\\.\\s+(?=[A-Z])'), which fractures coherent multi-sentence STAR
        achievement statements into disconnected single-sentence fragments.
        This segmenter isolates bullets along linebreaks and explicit bullet glyphs
        while keeping multi-sentence bullet statements intact.
        """
        if not text or not text.strip():
            return []

        # Split on line breaks
        raw_lines = re.split(r"[\r\n]+", text.strip())
        bullets: List[str] = []

        for line in raw_lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Within each line, split on inline bullet glyphs if multiple exist
            # e.g. "• Bullet 1 • Bullet 2"
            inline_splits = re.split(r"(?<=\s)[•\*\-\–\—]\s+", line_str)
            for sub in inline_splits:
                cleaned = sub.strip()
                # Clean leading bullet symbols, numbers, and list markers
                cleaned = re.sub(r"^[\s•\*\-\–\—\>#]+\s*", "", cleaned)
                cleaned = re.sub(r"^\d+[\.\)]\s+", "", cleaned).strip()
                if cleaned and len(cleaned) >= 3:
                    bullets.append(cleaned)

        return bullets

    # ---------------------------------------------------------------------
    # Stable Derived Bullet Identifiers
    # ---------------------------------------------------------------------

    def _generate_bullet_id(
        self,
        resume_id: UUID,
        section_type: str,
        parent_title: str,
        entry_index: int,
        bullet_index: int,
    ) -> str:
        """Constructs a deterministic, human-readable bullet identifier."""
        clean_title = re.sub(r"[^a-zA-Z0-9_-]", "_", parent_title.strip()).strip("_") or "entry"
        return f"{resume_id}:{section_type}:{entry_index}:{clean_title}:{bullet_index}"

    # ---------------------------------------------------------------------
    # Deterministic Guidance Generation
    # ---------------------------------------------------------------------

    def _generate_guidance(self, missing_components: List[str]) -> List[str]:
        """
        Generates deterministic structural guidance for missing STAR pillars
        in strict fixed order: SITUATION, TASK, ACTION, RESULT.
        """
        if not missing_components:
            return [
                "Comprehensive STAR evidence detected: statement demonstrates operational context, objective, active implementation, and measurable impact."
            ]

        guidance: List[str] = []
        for component in ORDERED_COMPONENTS:
            if component in missing_components:
                guidance.append(GUIDANCE_TEMPLATES[component])
        return guidance

    # ---------------------------------------------------------------------
    # Metric Aggregation
    # ---------------------------------------------------------------------

    def _compute_summary(self, bullets: List[BulletSTARAnalysis]) -> STARSummaryMetrics:
        """Computes aggregate summary metrics across all analyzed bullets."""
        total_bullets = len(bullets)
        if total_bullets == 0:
            return STARSummaryMetrics(
                total_bullets_analyzed=0,
                bullets_with_action=0,
                bullets_with_result=0,
                bullets_with_situation=0,
                bullets_with_task=0,
                overall_completeness_percentage=0.0,
                strong_bullets_count=0,
                needs_improvement_count=0,
            )

        bullets_with_action = sum(1 for b in bullets if b.action.detected)
        bullets_with_result = sum(1 for b in bullets if b.result.detected)
        bullets_with_situation = sum(1 for b in bullets if b.situation.detected)
        bullets_with_task = sum(1 for b in bullets if b.task.detected)

        # Strong bullet definition: Action detected + Result detected + score >= 65.0
        strong_bullets_count = sum(
            1 for b in bullets
            if b.action.detected and b.result.detected and b.completeness_score >= 65.0
        )
        needs_improvement_count = total_bullets - strong_bullets_count

        mean_score = sum(b.completeness_score for b in bullets) / total_bullets
        overall_percentage = round(mean_score, 1)

        return STARSummaryMetrics(
            total_bullets_analyzed=total_bullets,
            bullets_with_action=bullets_with_action,
            bullets_with_result=bullets_with_result,
            bullets_with_situation=bullets_with_situation,
            bullets_with_task=bullets_with_task,
            overall_completeness_percentage=overall_percentage,
            strong_bullets_count=strong_bullets_count,
            needs_improvement_count=needs_improvement_count,
        )

    # ---------------------------------------------------------------------
    # Primary Service Entry Point (Read-Only)
    # ---------------------------------------------------------------------

    def get_resume_star_guidance(
        self,
        db: Session,
        resume_id: UUID,
        user_id: UUID,
    ) -> ResumeSTARGuidanceResponse:
        """
        Evaluates the specified resume for STAR completeness across experience and projects.

        - Verifies existence and strict tenant ownership.
        - Analyzes the exact resume version requested.
        - Returns a complete read-only guidance response without mutating database state.
        """
        # 1. Load exact Resume record
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            raise STARGuidanceNotFoundError(f"Resume with ID '{resume_id}' not found.")

        # 2. Strict Tenant Authorization
        if resume.user_id != user_id:
            raise STARGuidanceOwnershipError(
                "Access denied: Resume does not belong to the authenticated user."
            )

        analyzed_bullets: List[BulletSTARAnalysis] = []

        # 3. Analyze Experience Bullets
        experiences: List[ResumeExperience] = resume.experience or []
        for exp_idx, exp in enumerate(experiences):
            parent_title = (
                f"{exp.job_title} at {exp.company_name}"
                if exp.job_title and exp.company_name
                else (exp.company_name or exp.job_title or "Professional Experience")
            )
            raw_bullets = self.segment_bullets(exp.description)
            for bullet_idx, raw_bullet in enumerate(raw_bullets):
                analysis_res = self.analyzer.analyze_bullet(raw_bullet)

                # Order missing components in fixed order
                ordered_missing = [
                    c for c in ORDERED_COMPONENTS if c in analysis_res.missing_components
                ]
                bullet_guidance = self._generate_guidance(ordered_missing)

                bullet_id = self._generate_bullet_id(
                    resume.id, "EXPERIENCE", parent_title, exp_idx, bullet_idx
                )

                bullet_entry = BulletSTARAnalysis(
                    bullet_id=bullet_id,
                    section_type="EXPERIENCE",
                    parent_entry_title=parent_title,
                    raw_text=raw_bullet,
                    situation=STARComponentDetail(
                        detected=analysis_res.situation.detected,
                        evidence_text=analysis_res.situation.evidence_text,
                        signals_detected=analysis_res.situation.signals_detected,
                        explanation=analysis_res.situation.explanation,
                    ),
                    task=STARComponentDetail(
                        detected=analysis_res.task.detected,
                        evidence_text=analysis_res.task.evidence_text,
                        signals_detected=analysis_res.task.signals_detected,
                        explanation=analysis_res.task.explanation,
                    ),
                    action=STARComponentDetail(
                        detected=analysis_res.action.detected,
                        evidence_text=analysis_res.action.evidence_text,
                        signals_detected=analysis_res.action.signals_detected,
                        explanation=analysis_res.action.explanation,
                    ),
                    result=STARComponentDetail(
                        detected=analysis_res.result.detected,
                        evidence_text=analysis_res.result.evidence_text,
                        signals_detected=analysis_res.result.signals_detected,
                        explanation=analysis_res.result.explanation,
                    ),
                    completeness_score=analysis_res.completeness_score,
                    missing_components=ordered_missing,
                    improvement_guidance=bullet_guidance,
                )
                analyzed_bullets.append(bullet_entry)

        # 4. Analyze Project Bullets
        projects: List[ResumeProject] = resume.projects or []
        for proj_idx, proj in enumerate(projects):
            parent_title = proj.project_name or "Technical Project"
            raw_bullets = self.segment_bullets(proj.description)
            for bullet_idx, raw_bullet in enumerate(raw_bullets):
                analysis_res = self.analyzer.analyze_bullet(raw_bullet)

                ordered_missing = [
                    c for c in ORDERED_COMPONENTS if c in analysis_res.missing_components
                ]
                bullet_guidance = self._generate_guidance(ordered_missing)

                bullet_id = self._generate_bullet_id(
                    resume.id, "PROJECTS", parent_title, proj_idx, bullet_idx
                )

                bullet_entry = BulletSTARAnalysis(
                    bullet_id=bullet_id,
                    section_type="PROJECTS",
                    parent_entry_title=parent_title,
                    raw_text=raw_bullet,
                    situation=STARComponentDetail(
                        detected=analysis_res.situation.detected,
                        evidence_text=analysis_res.situation.evidence_text,
                        signals_detected=analysis_res.situation.signals_detected,
                        explanation=analysis_res.situation.explanation,
                    ),
                    task=STARComponentDetail(
                        detected=analysis_res.task.detected,
                        evidence_text=analysis_res.task.evidence_text,
                        signals_detected=analysis_res.task.signals_detected,
                        explanation=analysis_res.task.explanation,
                    ),
                    action=STARComponentDetail(
                        detected=analysis_res.action.detected,
                        evidence_text=analysis_res.action.evidence_text,
                        signals_detected=analysis_res.action.signals_detected,
                        explanation=analysis_res.action.explanation,
                    ),
                    result=STARComponentDetail(
                        detected=analysis_res.result.detected,
                        evidence_text=analysis_res.result.evidence_text,
                        signals_detected=analysis_res.result.signals_detected,
                        explanation=analysis_res.result.explanation,
                    ),
                    completeness_score=analysis_res.completeness_score,
                    missing_components=ordered_missing,
                    improvement_guidance=bullet_guidance,
                )
                analyzed_bullets.append(bullet_entry)

        # 5. Compute Aggregate Summary
        summary = self._compute_summary(analyzed_bullets)

        # 6. Return Structured Read-Only Response
        return ResumeSTARGuidanceResponse(
            resume_id=resume.id,
            resume_version=resume.version,
            resume_title=resume.title,
            summary=summary,
            bullets=analyzed_bullets,
            methodology="Deterministic Rule-Based STAR Structural Analysis",
        )


star_guidance_service = STARGuidanceService()
