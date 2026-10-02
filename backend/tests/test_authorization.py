"""Unit and integration tests for multi-tenant data isolation and authorization security."""

import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.models.resume import Resume
from app.models.skill import Skill, ResumeSkill
from app.models.job import Job
from app.models.matching import MatchAnalysis


def test_cross_user_data_isolation(client: TestClient, db_session):
    """Verifies that authenticated users cannot access, compare, or leak another candidate's private data."""
    # 1. User Alpha
    alpha_reg = {
        "email": "user_alpha@skillbridge.ai",
        "password": "PasswordAlpha123!",
        "full_name": "User Alpha",
    }
    resp_alpha = client.post("/api/v1/auth/register", json=alpha_reg)
    token_alpha = resp_alpha.json()["access_token"]
    user_alpha_id = uuid.UUID(resp_alpha.json()["user"]["id"])
    headers_alpha = {"Authorization": f"Bearer {token_alpha}"}

    # 2. User Beta
    beta_reg = {
        "email": "user_beta@skillbridge.ai",
        "password": "PasswordBeta123!",
        "full_name": "User Beta",
    }
    resp_beta = client.post("/api/v1/auth/register", json=beta_reg)
    token_beta = resp_beta.json()["access_token"]
    user_beta_id = uuid.UUID(resp_beta.json()["user"]["id"])
    headers_beta = {"Authorization": f"Bearer {token_beta}"}

    # 3. Create private records for User Alpha
    now = datetime.now(timezone.utc)
    alpha_resume1 = Resume(
        id=uuid.uuid4(),
        user_id=user_alpha_id,
        title="Alpha Private Resume v1",
        file_name="alpha_v1.pdf",
        stored_path="/uploads/alpha_v1.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        version=1,
        created_at=now,
    )
    alpha_resume2 = Resume(
        id=uuid.uuid4(),
        user_id=user_alpha_id,
        title="Alpha Private Resume v2",
        file_name="alpha_v2.pdf",
        stored_path="/uploads/alpha_v2.pdf",
        file_type="pdf",
        file_size_bytes=1200,
        version=2,
        created_at=now,
    )
    db_session.add_all([alpha_resume1, alpha_resume2])
    db_session.flush()

    prop_skill = Skill(name="ProprietarySkill", normalized_name="proprietaryskill", category="TECHNICAL_SKILL")
    db_session.add(prop_skill)
    db_session.flush()

    alpha_skill = ResumeSkill(
        resume_id=alpha_resume1.id,
        skill_id=prop_skill.id,
        raw_skill_text="ProprietarySkill",
        canonical_skill_name="ProprietarySkill",
        source_section="SKILLS",
        evidence_sentence="Worked with ProprietarySkill",
    )
    db_session.add(alpha_skill)

    alpha_job = Job(
        id=uuid.uuid4(),
        user_id=user_alpha_id,
        title="Alpha Secret Role",
        company="AlphaCorp",
        ingestion_type="PASTED",
        raw_text="Confidential description",
    )
    db_session.add(alpha_job)
    db_session.flush()

    alpha_match = MatchAnalysis(
        id=uuid.uuid4(),
        user_id=user_alpha_id,
        resume_id=alpha_resume1.id,
        job_id=alpha_job.id,
        compatibility_score=92.0,
        ats_readiness_score=95.0,
        matching_engine_version="1.0.0",
        scoring_version="1.0.0-heuristic",
    )
    db_session.add(alpha_match)
    db_session.flush()

    # 4. Verify User Alpha sees Alpha's data
    overview_alpha = client.get("/api/v1/dashboard/overview", headers=headers_alpha).json()
    assert overview_alpha["resume_versions_count"] == 2
    assert overview_alpha["latest_job_compatibility_score"] == 92.0

    # 5. Verify User Beta cannot see Alpha's data on dashboard
    overview_beta = client.get("/api/v1/dashboard/overview", headers=headers_beta).json()
    assert overview_beta["resume_versions_count"] == 0
    assert overview_beta["latest_job_compatibility_score"] is None
    assert overview_beta["state"] in ["NEW_USER", "NO_RESUME"]

    # 6. Verify User Beta cannot view or compare Alpha's resumes
    comp_forbidden = client.get(
        f"/api/v1/resumes/compare?resume_id_1={alpha_resume1.id}&resume_id_2={alpha_resume2.id}",
        headers=headers_beta,
    )
    assert comp_forbidden.status_code == 404
    assert "access denied" in comp_forbidden.json()["detail"].lower()

    # 7. Verify User Beta cannot see Alpha's skill history
    beta_skills = client.get("/api/v1/progress/skills", headers=headers_beta).json()
    assert len(beta_skills) == 0
    for s in beta_skills:
        assert s["skill_name"] != "ProprietarySkill"

    # 8. Verify User Beta cannot see Alpha's score history
    beta_scores = client.get("/api/v1/progress/scores", headers=headers_beta).json()
    assert len(beta_scores) == 0
