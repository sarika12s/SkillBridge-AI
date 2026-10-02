"""Unit and integration tests for SkillBridge AI Phase 5:
Semantic Matching, Skill Gap Analysis & Explainable Scoring Engine.
"""

import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.resume import Resume
from app.models.skill import Skill, SkillRelationship, ResumeSkill
from app.models.job import (
    Job,
    JobSkill,
    JobExperienceRequirement,
    JobEducationRequirement,
    JobCertification,
)
from app.ai.matching.config import matching_config
from app.ai.matching.matcher import SkillMatchingEngine
from app.ai.matching.evaluators import AlignmentEvaluator
from app.ai.matching.gap_analyzer import SkillGapAnalyzer
from app.ai.matching.scoring_engine import ScoringEngine, clamp_score
from app.ai.matching.explainability import ExplainabilityEngine
from app.ai.matching.vector_embedder import VectorEmbedder


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers(db_session):
    """Provides a registered test user and JWT authorization header."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    reg_payload = {
        "email": "matching_tester@skillbridge.ai",
        "password": "Password123!",
        "full_name": "Matching Analyst",
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    token = res.json()["access_token"]
    user_id = uuid.UUID(res.json()["user"]["id"])
    return client, {"Authorization": f"Bearer {token}"}, user_id


def test_exact_canonical_match():
    """Case A: Verifies exact canonical skill ID match takes highest precedence."""
    canon_id = uuid.uuid4()
    job_sk = JobSkill(
        id=uuid.uuid4(),
        skill_id=canon_id,
        canonical_skill_name="Python",
        requirement_type="REQUIRED",
        evidence_text="Strong Python required.",
    )
    res_sk = ResumeSkill(
        id=uuid.uuid4(),
        skill_id=canon_id,
        canonical_skill_name="Python",
        source_section="TECHNICAL_SKILLS",
        evidence_sentence="5 years developing backends in Python.",
    )

    matcher = SkillMatchingEngine()
    result = matcher.match_job_skill_to_resume_skills(
        job_skill=job_sk,
        resume_skills=[res_sk],
        canonical_skills_map={},
        relationships=[],
    )

    assert result["match_type"] == "DIRECT_MATCH"
    assert result["match_status"] == "MATCHED_REQUIRED"
    assert result["confidence"] == 1.0
    assert result["canonical_skill_id"] == canon_id
    assert "Python" in result["explanation"]


def test_alias_match():
    """Case B: Verifies alias mapping resolves terms cleanly."""
    job_canon_id = uuid.uuid4()
    res_canon_id = uuid.uuid4()

    job_sk = JobSkill(
        id=uuid.uuid4(),
        skill_id=job_canon_id,
        canonical_skill_name="JavaScript",
        requirement_type="REQUIRED",
        evidence_text="JavaScript proficiency needed.",
    )
    res_sk = ResumeSkill(
        id=uuid.uuid4(),
        skill_id=res_canon_id,
        raw_skill_text="JS",
        canonical_skill_name="JavaScript",
        source_section="EXPERIENCE",
        evidence_sentence="Front-end development with JS and React.",
    )

    matcher = SkillMatchingEngine()
    result = matcher.match_job_skill_to_resume_skills(
        job_skill=job_sk,
        resume_skills=[res_sk],
        canonical_skills_map={},
        relationships=[],
    )

    assert result["match_type"] == "ALIAS_MATCH"
    assert result["match_status"] == "MATCHED_REQUIRED"
    assert result["confidence"] >= 0.95


def test_critical_false_positives_prevented():
    """
    Case I & Critical Gate: Tests that distinct technical families NEVER match:
    Java != JavaScript, React != React Native, AWS != Azure, SQL != PostgreSQL, TensorFlow != PyTorch.
    """
    matcher = SkillMatchingEngine()

    prohibited_checks = [
        ("Java", "JavaScript"),
        ("React", "React Native"),
        ("Amazon Web Services", "Microsoft Azure"),
        ("SQL", "PostgreSQL"),
        ("TensorFlow", "PyTorch"),
        ("C", "C++"),
        ("C++", "C#"),
    ]

    for cand_name, req_name in prohibited_checks:
        job_sk = JobSkill(
            id=uuid.uuid4(),
            skill_id=uuid.uuid4(),
            canonical_skill_name=req_name,
            requirement_type="REQUIRED",
            evidence_text=f"Must have {req_name}.",
        )
        res_sk = ResumeSkill(
            id=uuid.uuid4(),
            skill_id=uuid.uuid4(),
            canonical_skill_name=cand_name,
            raw_skill_text=cand_name,
            source_section="SKILLS",
            evidence_sentence=f"Expert in {cand_name}.",
        )

        result = matcher.match_job_skill_to_resume_skills(
            job_skill=job_sk,
            resume_skills=[res_sk],
            canonical_skills_map={},
            relationships=[],
        )

        # Must NOT be classified as DIRECT_MATCH, ALIAS_MATCH, or SEMANTIC_MATCH
        assert result["match_type"] == "NO_MATCH", f"False positive occurred: {cand_name} matched {req_name}!"
        assert result["match_status"] == "MISSING_REQUIRED"


def test_taxonomy_related_is_supporting_only_not_full_match():
    """
    Case D & Rule: A RELATED skill does NOT automatically satisfy a REQUIRED skill.
    Must be classified as RELATED_SUPPORT rather than DIRECT_MATCH.
    """
    req_id = uuid.uuid4()
    rel_id = uuid.uuid4()

    job_sk = JobSkill(
        id=uuid.uuid4(),
        skill_id=req_id,
        canonical_skill_name="Kubernetes",
        requirement_type="REQUIRED",
        evidence_text="Required Kubernetes container orchestration.",
    )
    res_sk = ResumeSkill(
        id=uuid.uuid4(),
        skill_id=rel_id,
        canonical_skill_name="Docker",
        source_section="EXPERIENCE",
        evidence_sentence="Containerized microservices using Docker.",
    )

    relationship = SkillRelationship(
        source_skill_id=rel_id,
        target_skill_id=req_id,
        relationship_type="RELATED_TO",
        confidence=0.85,
    )

    matcher = SkillMatchingEngine()
    result = matcher.match_job_skill_to_resume_skills(
        job_skill=job_sk,
        resume_skills=[res_sk],
        canonical_skills_map={},
        relationships=[relationship],
    )

    assert result["match_type"] == "RELATED_SUPPORT"
    assert result["match_status"] == "RELATED_SUPPORT"
    assert "does not automatically fulfill" in result["explanation"]


def test_required_vs_preferred_priority_scoring():
    """Case D vs E: Missing REQUIRED skill incurs heavier penalty than missing PREFERRED."""
    # Scenario 1: Missing 1 REQUIRED skill
    matches_missing_req = [
        {"match_type": "NO_MATCH", "match_status": "MISSING_REQUIRED", "priority": "REQUIRED"},
        {"match_type": "DIRECT_MATCH", "match_status": "MATCHED_PREFERRED", "priority": "PREFERRED"},
    ]
    # Scenario 2: Missing 1 PREFERRED skill
    matches_missing_pref = [
        {"match_type": "DIRECT_MATCH", "match_status": "MATCHED_REQUIRED", "priority": "REQUIRED"},
        {"match_type": "NO_MATCH", "match_status": "MISSING_PREFERRED", "priority": "PREFERRED"},
    ]

    neutral_align = {
        "experience_status": "MEETS",
        "education_status": "MEETS",
        "certification_status": "MATCHED",
    }

    score_req = ScoringEngine.calculate_scores(matches_missing_req, neutral_align)
    score_pref = ScoringEngine.calculate_scores(matches_missing_pref, neutral_align)

    # Missing REQUIRED skill must produce lower compatibility than missing PREFERRED skill
    assert score_req["compatibility_score"] < score_pref["compatibility_score"]
    assert score_pref["compatibility_score"] - score_req["compatibility_score"] >= 20.0


def test_experience_alignment_evaluation():
    """Case F: Partial experience and unstated experience evaluations."""
    resume_with_exp = Resume(
        id=uuid.uuid4(),
        raw_text="Over 2 years of professional backend software development experience.",
    )
    req_senior = [JobExperienceRequirement(minimum_years=5.0, classification="SENIOR_LEVEL")]
    req_mid = [JobExperienceRequirement(minimum_years=2.0, classification="MID_LEVEL")]

    # 1. 2 years vs 5 years -> BELOW_REQUIREMENT
    res_below = AlignmentEvaluator.evaluate_experience(resume_with_exp, req_senior)
    assert res_below["experience_status"] == "BELOW_REQUIREMENT"
    assert res_below["resume_years"] == 2.0
    assert res_below["required_years"] == 5.0

    # 2. 2 years vs 2 years -> MEETS
    res_meets = AlignmentEvaluator.evaluate_experience(resume_with_exp, req_mid)
    assert res_meets["experience_status"] == "MEETS"

    # 3. Unstated experience -> UNKNOWN (never fabricated)
    resume_empty = Resume(id=uuid.uuid4(), raw_text="Enthusiastic programmer with Python knowledge.")
    res_unk = AlignmentEvaluator.evaluate_experience(resume_empty, req_mid)
    assert res_unk["experience_status"] == "UNKNOWN"
    assert res_unk["resume_years"] is None


def test_education_and_certification_alignment():
    """Case G & H: Education degrees and certifications."""
    resume = Resume(
        id=uuid.uuid4(),
        raw_text="Bachelor of Science in Computer Science. AWS Certified Solutions Architect Associate.",
    )

    # Education: Bachelors required, candidate holds Bachelors in CS -> MEETS
    edu_reqs = [JobEducationRequirement(degree_level="BACHELORS", field="Computer Science")]
    edu_res = AlignmentEvaluator.evaluate_education(resume, edu_reqs)
    assert edu_res["education_status"] == "MEETS"
    assert edu_res["resume_degree"] == "BACHELORS"

    # Education: Doctorate required, candidate holds Bachelors -> PARTIAL
    phd_reqs = [JobEducationRequirement(degree_level="DOCTORATE", field="Artificial Intelligence")]
    phd_res = AlignmentEvaluator.evaluate_education(resume, phd_reqs)
    assert phd_res["education_status"] == "PARTIAL"

    # Certification: AWS Certified present -> MATCHED
    cert_reqs = [JobCertification(name="AWS Certified Solutions Architect")]
    cert_res = AlignmentEvaluator.evaluate_certifications(resume, cert_reqs)
    assert cert_res["certification_status"] == "MATCHED"

    # Certification: CKA absent -> MISSING
    cka_reqs = [JobCertification(name="Certified Kubernetes Administrator (CKA)")]
    cka_res = AlignmentEvaluator.evaluate_certifications(resume, cka_reqs)
    assert cka_res["certification_status"] == "MISSING"


def test_score_normalization_and_boundaries():
    """Ensures clamp_score prevents negative, >100, NaN, and Inf."""
    assert clamp_score(-15.5) == 0.0
    assert clamp_score(125.8) == 100.0
    assert clamp_score(float("nan")) == 0.0
    assert clamp_score(float("inf")) == 0.0
    assert clamp_score(88.456) == 88.46


def test_skill_gap_analyzer_prioritization():
    """Verifies skill gap prioritization separates required from preferred."""
    matches = [
        {
            "canonical_skill_name": "Docker",
            "match_status": "MISSING_REQUIRED",
            "priority": "REQUIRED",
            "job_evidence": "Docker required for packaging.",
        },
        {
            "canonical_skill_name": "Kubernetes",
            "match_status": "MISSING_PREFERRED",
            "priority": "PREFERRED",
            "job_evidence": "Kubernetes is a plus.",
        },
    ]

    gaps = SkillGapAnalyzer.identify_gaps(matches)
    assert len(gaps) == 2
    # First gap must be the REQUIRED one due to higher weight (2.0 vs 1.0)
    assert gaps[0]["canonical_skill_name"] == "Docker"
    assert gaps[0]["priority"] == "REQUIRED"
    assert gaps[0]["importance_weight"] == 2.0
    assert gaps[1]["canonical_skill_name"] == "Kubernetes"
    assert gaps[1]["priority"] == "PREFERRED"


def test_matching_api_flow(auth_headers, db_session):
    """Integration Test: End-to-end API analysis execution and retrieval."""
    client, headers, user_id = auth_headers

    # 1. Seed canonical skills
    py_skill = Skill(id=uuid.uuid4(), name="Python", normalized_name="python")
    sql_skill = Skill(id=uuid.uuid4(), name="SQL", normalized_name="sql")
    docker_skill = Skill(id=uuid.uuid4(), name="Docker", normalized_name="docker")
    db_session.add_all([py_skill, sql_skill, docker_skill])
    db_session.commit()

    # 2. Create Resume with Python and SQL
    res_id = uuid.uuid4()
    resume = Resume(
        id=res_id,
        user_id=user_id,
        title="Senior Backend Resume",
        file_name="resume_backend.pdf",
        stored_path="uploads/resume_backend.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        raw_text="Senior Developer with 4 years experience in Python and SQL databases. Bachelor of Science in Computer Science.",
    )
    db_session.add(resume)
    db_session.flush()

    r_sk1 = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=res_id,
        skill_id=py_skill.id,
        raw_skill_text="Python",
        canonical_skill_name="Python",
        source_section="SKILLS",
        evidence_sentence="4 years experience in Python.",
    )
    r_sk2 = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=res_id,
        skill_id=sql_skill.id,
        raw_skill_text="SQL",
        canonical_skill_name="SQL",
        source_section="SKILLS",
        evidence_sentence="SQL database query optimization.",
    )
    db_session.add_all([r_sk1, r_sk2])

    # 3. Create Job requiring Python (REQUIRED) and Docker (REQUIRED)
    job_id = uuid.uuid4()
    job = Job(
        id=job_id,
        user_id=user_id,
        title="Backend Software Engineer",
        raw_text="Seeking Backend Software Engineer. Must know Python and Docker.",
    )
    db_session.add(job)
    db_session.flush()

    j_sk1 = JobSkill(
        id=uuid.uuid4(),
        job_id=job_id,
        skill_id=py_skill.id,
        raw_skill_text="Python",
        canonical_skill_name="Python",
        requirement_type="REQUIRED",
        evidence_text="Must know Python.",
    )
    j_sk2 = JobSkill(
        id=uuid.uuid4(),
        job_id=job_id,
        skill_id=docker_skill.id,
        raw_skill_text="Docker",
        canonical_skill_name="Docker",
        requirement_type="REQUIRED",
        evidence_text="Docker deployment required.",
    )
    db_session.add_all([j_sk1, j_sk2])
    db_session.commit()

    # 4. Invoke POST /api/v1/matching/analyze
    match_req = {"resume_id": str(res_id), "job_id": str(job_id)}
    post_res = client.post("/api/v1/matching/analyze", json=match_req, headers=headers)
    assert post_res.status_code == 201, post_res.text
    data = post_res.json()

    assert data["job_title"] == "Backend Software Engineer"
    assert data["compatibility_score"] > 0.0
    assert data["ats_readiness_score"] > 0.0
    assert len(data["skill_matches"]) == 2
    assert len(data["skill_gaps"]) >= 1

    # Python should be DIRECT_MATCH, Docker should be MISSING_REQUIRED
    match_map = {m["canonical_skill_name"]: m for m in data["skill_matches"]}
    assert match_map["Python"]["match_type"] == "DIRECT_MATCH"
    assert match_map["Docker"]["match_type"] == "NO_MATCH"
    assert match_map["Docker"]["match_status"] == "MISSING_REQUIRED"

    analysis_id = data["id"]

    # 5. Invoke GET /api/v1/matching/{analysis_id}
    get_res = client.get(f"/api/v1/matching/{analysis_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == analysis_id

    # 6. Invoke GET /api/v1/resumes/{resume_id}/skill-gaps
    gap_res = client.get(f"/api/v1/resumes/{res_id}/skill-gaps", headers=headers)
    assert gap_res.status_code == 200
    assert gap_res.json()["total_gaps"] >= 1
