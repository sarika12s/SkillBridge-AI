"""Unit, integration, and security tests for SkillBridge AI Phase 8.1:
Interactive 'What-If' Gap-Closure Simulator.

Tests:
A. Zero-change baseline (projected == current, deltas == 0)
B. Single-skill simulation (required gap closure, coverage gains)
C. Multi-skill simulation (required + preferred gap closure)
D. Score bounds (bounded between 0.0 and 100.0)
E. Phase 5 formula preservation (identical results to ScoringEngine)
F. No persistence / immutability (zero DB mutations or inserts)
G. Tenant authorization (user cannot simulate another user's match)
H. Nonexistent skill IDs rejection (400 Bad Request)
I. Duplicate skill IDs rejection (400 Bad Request)
J. Unrelated / non-gap skills rejection (400 Bad Request)
K. Learning-hour ROI computation via LearningResource
L. Nonexistent match analysis rejection (404 Not Found)
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
from app.models.skill import Skill, ResumeSkill
from app.models.job import Job, JobSkill
from app.models.matching import MatchAnalysis, SkillMatch, SkillGap, ScoreBreakdown
from app.models.learning import LearningResource
from app.services.matching_service import matching_service
from app.services.simulation_service import simulation_service
from app.ai.matching.scoring_engine import ScoringEngine


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
def test_setup(db_session):
    """
    Sets up a full realistic scenario:
    - User
    - Canonical Skills (Python, Docker, TypeScript, Go)
    - Learning Resources with estimated hours
    - Resume with Python
    - Job requiring Python (Required), Docker (Required), TypeScript (Preferred)
    - Initial Match Analysis with Docker and TypeScript as GAPS
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 1. Register User A
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "simulator_user_a@skillbridge.ai",
            "password": "Password123!",
            "full_name": "Simulator User A",
        },
    )
    assert reg_res.status_code == 201
    user_a_token = reg_res.json()["access_token"]
    user_a_id = uuid.UUID(reg_res.json()["user"]["id"])
    headers_a = {"Authorization": f"Bearer {user_a_token}"}

    # 2. Register User B (for tenant isolation test)
    reg_b_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "simulator_user_b@skillbridge.ai",
            "password": "Password123!",
            "full_name": "Simulator User B",
        },
    )
    assert reg_b_res.status_code == 201
    user_b_token = reg_b_res.json()["access_token"]
    user_b_id = uuid.UUID(reg_b_res.json()["user"]["id"])
    headers_b = {"Authorization": f"Bearer {user_b_token}"}

    # 3. Canonical Skills
    skill_python = Skill(
        id=uuid.uuid4(),
        name="Python",
        normalized_name="python",
        category="PROGRAMMING_LANGUAGE",
    )
    skill_docker = Skill(
        id=uuid.uuid4(),
        name="Docker",
        normalized_name="docker",
        category="CLOUD_DEVOPS",
    )
    skill_ts = Skill(
        id=uuid.uuid4(),
        name="TypeScript",
        normalized_name="typescript",
        category="PROGRAMMING_LANGUAGE",
    )
    skill_go = Skill(
        id=uuid.uuid4(),
        name="Go",
        normalized_name="go",
        category="PROGRAMMING_LANGUAGE",
    )
    db_session.add_all([skill_python, skill_docker, skill_ts, skill_go])
    db_session.commit()

    # 4. Learning Resources for Docker (effort = 10 hrs) and TypeScript (effort = 8 hrs)
    lr_docker = LearningResource(
        id=uuid.uuid4(),
        skill_id=skill_docker.id,
        title="Docker Essentials Course",
        provider="Docker",
        url="https://docs.docker.com",
        estimated_hours=10.0,
    )
    lr_ts = LearningResource(
        id=uuid.uuid4(),
        skill_id=skill_ts.id,
        title="TypeScript Handbook",
        provider="Microsoft",
        url="https://www.typescriptlang.org",
        estimated_hours=8.0,
    )
    db_session.add_all([lr_docker, lr_ts])
    db_session.commit()

    # 5. Resume (Owned by User A) with only Python
    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_a_id,
        title="Candidate Resume",
        file_name="candidate_resume.pdf",
        stored_path="/uploads/resumes/candidate_resume.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        raw_text="Experienced developer with strong proficiency in Python.",
    )
    db_session.add(resume)
    db_session.flush()

    rs_python = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume.id,
        skill_id=skill_python.id,
        raw_skill_text="Python",
        canonical_skill_name="Python",
        evidence_sentence="Experienced in developing backend services using Python.",
        confidence=1.0,
    )
    db_session.add(rs_python)
    db_session.commit()

    # 6. Job (Owned by User A) requiring Python (REQ), Docker (REQ), TypeScript (PREF)
    job = Job(
        id=uuid.uuid4(),
        user_id=user_a_id,
        title="Full Stack Software Engineer",
        normalized_role="Software Engineer",
        raw_text="Seeking an engineer proficient in Python and Docker, TypeScript preferred.",
    )
    db_session.add(job)
    db_session.flush()

    js_python = JobSkill(
        id=uuid.uuid4(),
        job_id=job.id,
        skill_id=skill_python.id,
        raw_skill_text="Python",
        canonical_skill_name="Python",
        requirement_type="REQUIRED",
        evidence_text="Must have 3+ years of Python experience.",
    )
    js_docker = JobSkill(
        id=uuid.uuid4(),
        job_id=job.id,
        skill_id=skill_docker.id,
        raw_skill_text="Docker",
        canonical_skill_name="Docker",
        requirement_type="REQUIRED",
        evidence_text="Experience with Docker containerization required.",
    )
    js_ts = JobSkill(
        id=uuid.uuid4(),
        job_id=job.id,
        skill_id=skill_ts.id,
        raw_skill_text="TypeScript",
        canonical_skill_name="TypeScript",
        requirement_type="PREFERRED",
        evidence_text="TypeScript experience is preferred.",
    )
    db_session.add_all([js_python, js_docker, js_ts])
    db_session.commit()

    # 7. Run real match analysis to generate persisted baseline MatchAnalysis
    analysis_res = matching_service.analyze_match(
        db=db_session,
        user_id=user_a_id,
        resume_id=resume.id,
        job_id=job.id,
    )

    return {
        "client": client,
        "headers_a": headers_a,
        "user_a_id": user_a_id,
        "headers_b": headers_b,
        "user_b_id": user_b_id,
        "analysis_id": analysis_res.id,
        "resume_id": resume.id,
        "job_id": job.id,
        "skill_python": skill_python,
        "skill_docker": skill_docker,
        "skill_ts": skill_ts,
        "skill_go": skill_go,
        "initial_analysis": analysis_res,
    }


def test_simulation_zero_change_baseline(db_session, test_setup):
    """Test A: Zero-change baseline produces projected scores identical to current scores."""
    client = test_setup["client"]
    analysis_id = test_setup["analysis_id"]
    user_a_id = test_setup["user_a_id"]
    init_res = test_setup["initial_analysis"]

    # When service is invoked with an empty list, it returns zero-change baseline
    res = simulation_service.simulate_gap_closure(
        db=db_session,
        user_id=user_a_id,
        match_analysis_id=analysis_id,
        simulated_skill_ids=[],
    )

    assert res.current_compatibility_score == init_res.compatibility_score
    assert res.projected_compatibility_score == init_res.compatibility_score
    assert res.compatibility_score_delta == 0.0

    assert res.current_ats_score == init_res.ats_readiness_score
    assert res.projected_ats_score == init_res.ats_readiness_score
    assert res.ats_score_delta == 0.0

    assert res.required_coverage_delta == 0.0
    assert res.preferred_coverage_delta == 0.0
    assert len(res.gap_state.closed_gaps) == 0


def test_simulation_single_skill_required_gap(test_setup):
    """Test B: Simulating a single missing required skill closes that gap and raises scores."""
    client = test_setup["client"]
    headers_a = test_setup["headers_a"]
    analysis_id = str(test_setup["analysis_id"])
    docker_id = str(test_setup["skill_docker"].id)

    payload = {
        "match_analysis_id": analysis_id,
        "simulated_skill_ids": [docker_id],
    }

    res = client.post("/api/v1/matching/simulate", json=payload, headers=headers_a)
    assert res.status_code == 200, res.text
    data = res.json()

    # Verifications
    assert data["match_analysis_id"] == analysis_id
    assert data["projected_compatibility_score"] > data["current_compatibility_score"]
    assert data["compatibility_score_delta"] > 0.0

    assert data["projected_ats_score"] > data["current_ats_score"]
    assert data["ats_score_delta"] > 0.0

    # Required coverage increases because Docker was REQUIRED
    assert data["projected_required_coverage"] > data["current_required_coverage"]
    assert data["required_coverage_delta"] > 0.0

    # Gap state
    assert "Docker" in data["gap_state"]["closed_gaps"]
    assert "Docker" not in data["gap_state"]["remaining_required_gaps"]
    # TypeScript was PREFERRED, so it remains in remaining_preferred_gaps
    assert "TypeScript" in data["gap_state"]["remaining_preferred_gaps"]

    # Simulated skill detail
    assert len(data["simulated_skills"]) == 1
    sim_detail = data["simulated_skills"][0]
    assert sim_detail["canonical_skill_name"] == "Docker"
    assert sim_detail["priority"] == "REQUIRED"
    assert sim_detail["estimated_learning_hours"] == 10.0


def test_simulation_multi_skill_gaps(test_setup):
    """Test C: Simulating multiple gaps (Docker + TypeScript) resolves both gaps."""
    client = test_setup["client"]
    headers_a = test_setup["headers_a"]
    analysis_id = str(test_setup["analysis_id"])
    docker_id = str(test_setup["skill_docker"].id)
    ts_id = str(test_setup["skill_ts"].id)

    payload = {
        "match_analysis_id": analysis_id,
        "simulated_skill_ids": [docker_id, ts_id],
    }

    res = client.post("/api/v1/matching/simulate", json=payload, headers=headers_a)
    assert res.status_code == 200, res.text
    data = res.json()

    # Both gaps closed
    assert set(data["gap_state"]["closed_gaps"]) == {"Docker", "TypeScript"}
    assert len(data["gap_state"]["remaining_required_gaps"]) == 0
    assert len(data["gap_state"]["remaining_preferred_gaps"]) == 0
    assert data["gap_state"]["total_remaining_gaps"] == 0

    # Both required and preferred coverage reach 100%
    assert data["projected_required_coverage"] == 100.0
    assert data["projected_preferred_coverage"] == 100.0


def test_simulation_score_bounds(test_setup):
    """Test D: Projected scores remain strictly clamped in [0.0, 100.0]."""
    client = test_setup["client"]
    headers_a = test_setup["headers_a"]
    analysis_id = str(test_setup["analysis_id"])
    docker_id = str(test_setup["skill_docker"].id)

    res = client.post(
        "/api/v1/matching/simulate",
        json={"match_analysis_id": analysis_id, "simulated_skill_ids": [docker_id]},
        headers=headers_a,
    )
    assert res.status_code == 200
    data = res.json()

    assert 0.0 <= data["current_compatibility_score"] <= 100.0
    assert 0.0 <= data["projected_compatibility_score"] <= 100.0
    assert 0.0 <= data["current_ats_score"] <= 100.0
    assert 0.0 <= data["projected_ats_score"] <= 100.0
    assert 0.0 <= data["current_required_coverage"] <= 100.0
    assert 0.0 <= data["projected_required_coverage"] <= 100.0
    assert 0.0 <= data["current_preferred_coverage"] <= 100.0
    assert 0.0 <= data["projected_preferred_coverage"] <= 100.0


def test_simulation_phase5_formula_preservation(db_session, test_setup):
    """Test E: Projected scores strictly match direct ScoringEngine output."""
    client = test_setup["client"]
    headers_a = test_setup["headers_a"]
    analysis_id = test_setup["analysis_id"]
    docker_id = test_setup["skill_docker"].id

    res = client.post(
        "/api/v1/matching/simulate",
        json={"match_analysis_id": str(analysis_id), "simulated_skill_ids": [str(docker_id)]},
        headers=headers_a,
    )
    assert res.status_code == 200
    data = res.json()

    # Reconstruct projected matches and evaluate via ScoringEngine directly
    analysis = db_session.query(MatchAnalysis).filter(MatchAnalysis.id == analysis_id).first()
    job = db_session.query(Job).filter(Job.id == analysis.job_id).first()
    resume = db_session.query(Resume).filter(Resume.id == analysis.resume_id).first()

    projected_matches = []
    for m in analysis.skill_matches:
        if m.canonical_skill_id == docker_id:
            projected_matches.append({
                "priority": m.priority,
                "match_type": "DIRECT_MATCH",
                "match_status": "MATCHED_REQUIRED",
                "similarity_score": 1.0,
                "resume_evidence": f"[Simulated Acquisition] Candidate hypothetically demonstrates proficiency in {m.canonical_skill_name}.",
                "job_evidence": m.job_evidence,
                "explanation": f"Simulated acquisition: Candidate hypothetically fulfills '{m.canonical_skill_name}' requirement.",
            })
        else:
            projected_matches.append({
                "priority": m.priority,
                "match_type": m.match_type,
                "match_status": m.match_status,
                "similarity_score": m.similarity_score,
                "resume_evidence": m.resume_evidence,
                "job_evidence": m.job_evidence,
                "explanation": m.explanation,
            })

    from app.ai.matching.evaluators import AlignmentEvaluator
    exp_align = AlignmentEvaluator.evaluate_experience(resume, job.experience_requirements or [])
    edu_align = AlignmentEvaluator.evaluate_education(resume, job.education_requirements or [])
    cert_align = AlignmentEvaluator.evaluate_certifications(resume, job.certifications or [])
    alignment_dict = {**exp_align, **edu_align, **cert_align}

    expected_scores = ScoringEngine.calculate_scores(projected_matches, alignment_dict)

    assert data["projected_compatibility_score"] == expected_scores["compatibility_score"]
    assert data["projected_ats_score"] == expected_scores["ats_readiness_score"]


def test_simulation_no_persistence_mutation(db_session, test_setup):
    """Test F: Verifies zero database mutation or persistence occurred after simulation."""
    client = test_setup["client"]
    headers_a = test_setup["headers_a"]
    analysis_id = str(test_setup["analysis_id"])
    docker_id = str(test_setup["skill_docker"].id)

    # Record snapshot before simulation
    count_analyses_before = db_session.query(MatchAnalysis).count()
    count_matches_before = db_session.query(SkillMatch).count()
    count_gaps_before = db_session.query(SkillGap).count()
    count_breakdowns_before = db_session.query(ScoreBreakdown).count()
    count_resumes_before = db_session.query(Resume).count()
    count_resume_skills_before = db_session.query(ResumeSkill).count()

    orig_analysis = db_session.query(MatchAnalysis).filter(MatchAnalysis.id == test_setup["analysis_id"]).first()
    orig_compat_score = orig_analysis.compatibility_score
    orig_ats_score = orig_analysis.ats_readiness_score

    # Execute simulation
    res = client.post(
        "/api/v1/matching/simulate",
        json={"match_analysis_id": analysis_id, "simulated_skill_ids": [docker_id]},
        headers=headers_a,
    )
    assert res.status_code == 200

    # Verify snapshot after simulation is completely identical
    assert db_session.query(MatchAnalysis).count() == count_analyses_before
    assert db_session.query(SkillMatch).count() == count_matches_before
    assert db_session.query(SkillGap).count() == count_gaps_before
    assert db_session.query(ScoreBreakdown).count() == count_breakdowns_before
    assert db_session.query(Resume).count() == count_resumes_before
    assert db_session.query(ResumeSkill).count() == count_resume_skills_before

    db_session.refresh(orig_analysis)
    assert orig_analysis.compatibility_score == orig_compat_score
    assert orig_analysis.ats_readiness_score == orig_ats_score


def test_simulation_authorization_tenant_isolation(test_setup):
    """Test G: User B cannot simulate User A's match analysis (403 Forbidden)."""
    client = test_setup["client"]
    headers_b = test_setup["headers_b"]
    analysis_id = str(test_setup["analysis_id"])
    docker_id = str(test_setup["skill_docker"].id)

    res = client.post(
        "/api/v1/matching/simulate",
        json={"match_analysis_id": analysis_id, "simulated_skill_ids": [docker_id]},
        headers=headers_b,
    )
    assert res.status_code == 403
    assert "permission" in res.json()["detail"].lower()


def test_simulation_invalid_nonexistent_skill_ids(test_setup):
    """Test H: Nonexistent skill IDs are rejected with 400 Bad Request."""
    client = test_setup["client"]
    headers_a = test_setup["headers_a"]
    analysis_id = str(test_setup["analysis_id"])
    fake_skill_id = str(uuid.uuid4())

    res = client.post(
        "/api/v1/matching/simulate",
        json={"match_analysis_id": analysis_id, "simulated_skill_ids": [fake_skill_id]},
        headers=headers_a,
    )
    assert res.status_code == 400
    assert "do not exist in the taxonomy" in res.json()["detail"]


def test_simulation_duplicate_skill_ids(test_setup):
    """Test I: Duplicate skill IDs are rejected with 400 Bad Request."""
    client = test_setup["client"]
    headers_a = test_setup["headers_a"]
    analysis_id = str(test_setup["analysis_id"])
    docker_id = str(test_setup["skill_docker"].id)

    res = client.post(
        "/api/v1/matching/simulate",
        json={"match_analysis_id": analysis_id, "simulated_skill_ids": [docker_id, docker_id]},
        headers=headers_a,
    )
    assert res.status_code == 400
    assert "duplicate" in res.json()["detail"].lower()


def test_simulation_unrelated_skill_rejected(test_setup):
    """Test J: A skill that exists in taxonomy but is NOT a gap for this match is rejected."""
    client = test_setup["client"]
    headers_a = test_setup["headers_a"]
    analysis_id = str(test_setup["analysis_id"])
    go_id = str(test_setup["skill_go"].id)  # Go was NOT in the job requirements!

    res = client.post(
        "/api/v1/matching/simulate",
        json={"match_analysis_id": analysis_id, "simulated_skill_ids": [go_id]},
        headers=headers_a,
    )
    assert res.status_code == 400
    assert "not an identified gap" in res.json()["detail"].lower()


def test_simulation_learning_hour_roi(test_setup):
    """Test K: Learning effort and ROI are computed correctly from LearningResource."""
    client = test_setup["client"]
    headers_a = test_setup["headers_a"]
    analysis_id = str(test_setup["analysis_id"])
    docker_id = str(test_setup["skill_docker"].id)  # Docker has 10.0 hrs

    res = client.post(
        "/api/v1/matching/simulate",
        json={"match_analysis_id": analysis_id, "simulated_skill_ids": [docker_id]},
        headers=headers_a,
    )
    assert res.status_code == 200
    data = res.json()

    assert data["total_estimated_learning_hours"] == 10.0
    assert data["learning_hour_roi"] is not None
    expected_roi = round(data["compatibility_score_delta"] / 10.0, 2)
    assert data["learning_hour_roi"] == expected_roi


def test_simulation_nonexistent_analysis_404(test_setup):
    """Test L: Requesting simulation for unknown analysis ID returns 404 Not Found."""
    client = test_setup["client"]
    headers_a = test_setup["headers_a"]
    fake_analysis_id = str(uuid.uuid4())
    docker_id = str(test_setup["skill_docker"].id)

    res = client.post(
        "/api/v1/matching/simulate",
        json={"match_analysis_id": fake_analysis_id, "simulated_skill_ids": [docker_id]},
        headers=headers_a,
    )
    assert res.status_code == 404
