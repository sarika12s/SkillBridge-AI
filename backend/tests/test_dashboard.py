"""Unit and integration tests for Phase 7 Career Intelligence Dashboard APIs and Services."""

import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.models.resume import Resume, ResumeSection
from app.models.skill import Skill, ResumeSkill
from app.models.job import Job
from app.models.matching import MatchAnalysis


def test_dashboard_overview_lifecycle_states(client: TestClient, db_session):
    """Verifies that /api/v1/dashboard/overview correctly evaluates operational lifecycle states."""
    # 1. State: NEW_USER / NO_RESUME
    reg_data = {
        "email": "dash_user@skillbridge.ai",
        "password": "Password123!",
        "full_name": "Dashboard Tester",
    }
    resp = client.post("/api/v1/auth/register", json=reg_data)
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    user_id = uuid.UUID(resp.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    dash_resp = client.get("/api/v1/dashboard/overview", headers=headers)
    assert dash_resp.status_code == 200
    data = dash_resp.json()
    assert data["state"] in ["NEW_USER", "NO_RESUME"]
    assert data["resume_versions_count"] == 0
    assert len(data["insights"]) > 0

    # 2. State: RESUME_ONLY
    now = datetime.now(timezone.utc)
    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Software Engineer Resume",
        file_name="resume_v1.pdf",
        stored_path="/uploads/test.pdf",
        file_type="pdf",
        file_size_bytes=2048,
        parsing_status="COMPLETED",
        version=1,
        page_count=1,
        character_count=1200,
        created_at=now,
    )
    db_session.add(resume)
    db_session.flush()

    dash_resp2 = client.get("/api/v1/dashboard/overview", headers=headers)
    assert dash_resp2.status_code == 200
    data2 = dash_resp2.json()
    assert data2["state"] == "RESUME_ONLY"
    assert data2["resume_versions_count"] == 1
    assert data2["latest_resume"]["version"] == 1

    # 3. State: RESUME_ANALYZED (with Job Match)
    job = Job(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Senior Python Engineer",
        company="TechCorp",
        ingestion_type="PASTED",
        raw_text="Looking for a Python Engineer with FastAPI and Docker.",
    )
    db_session.add(job)
    db_session.flush()

    match = MatchAnalysis(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_id=resume.id,
        job_id=job.id,
        compatibility_score=85.0,
        ats_readiness_score=90.0,
        matching_engine_version="1.0.0",
        scoring_version="1.0.0-heuristic",
    )
    db_session.add(match)
    db_session.flush()

    dash_resp3 = client.get("/api/v1/dashboard/overview", headers=headers)
    assert dash_resp3.status_code == 200
    data3 = dash_resp3.json()
    assert data3["state"] == "RESUME_ANALYZED"
    assert data3["latest_ats_readiness_score"] == 90.0
    assert data3["latest_job_compatibility_score"] == 85.0
    assert 0.0 <= data3["latest_ats_readiness_score"] <= 100.0
    assert 0.0 <= data3["latest_job_compatibility_score"] <= 100.0


def test_progress_endpoints(client: TestClient, db_session):
    """Verifies /api/v1/progress/skills, /api/v1/progress/learning, and /api/v1/progress/scores."""
    reg_data = {
        "email": "progress_user@skillbridge.ai",
        "password": "Password123!",
        "full_name": "Progress Candidate",
    }
    resp = client.post("/api/v1/auth/register", json=reg_data)
    token = resp.json()["access_token"]
    user_id = uuid.UUID(resp.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    # Seed skill evolution across 2 resumes
    now = datetime.now(timezone.utc)
    sk = Skill(name="Docker", normalized_name="docker", category="CLOUD_DEVOPS")
    db_session.add(sk)
    db_session.flush()

    # Resume v1: Docker in SKILLS
    r1 = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Resume V1",
        file_name="v1.pdf",
        stored_path="/uploads/v1.pdf",
        file_type="pdf",
        file_size_bytes=1000,
        version=1,
        created_at=now,
    )
    db_session.add(r1)
    db_session.flush()

    rs1 = ResumeSkill(
        resume_id=r1.id,
        skill_id=sk.id,
        raw_skill_text="Docker",
        canonical_skill_name="Docker",
        source_section="SKILLS",
        evidence_sentence="Docker, Git, Linux",
    )
    db_session.add(rs1)

    # Resume v2: Docker strengthened into PROJECTS
    r2 = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Resume V2",
        file_name="v2.pdf",
        stored_path="/uploads/v2.pdf",
        file_type="pdf",
        file_size_bytes=1100,
        version=2,
        created_at=now,
    )
    db_session.add(r2)
    db_session.flush()

    rs2 = ResumeSkill(
        resume_id=r2.id,
        skill_id=sk.id,
        raw_skill_text="Docker",
        canonical_skill_name="Docker",
        source_section="PROJECTS",
        evidence_sentence="Containerized backend services with Docker Compose",
    )
    db_session.add(rs2)
    db_session.flush()

    # Test /api/v1/progress/skills
    skills_resp = client.get("/api/v1/progress/skills", headers=headers)
    assert skills_resp.status_code == 200
    skills_data = skills_resp.json()
    assert len(skills_data) >= 1
    docker_item = next(s for s in skills_data if s["skill_name"] == "Docker")
    assert docker_item["current_status"] == "STRENGTHENED"
    assert len(docker_item["history"]) == 2

    # Test /api/v1/progress/learning
    learn_resp = client.get("/api/v1/progress/learning", headers=headers)
    assert learn_resp.status_code == 200
    learn_data = learn_resp.json()
    assert "total_paths" in learn_data
    assert "overall_completion_percentage" in learn_data

    # Test /api/v1/progress/scores
    scores_resp = client.get("/api/v1/progress/scores", headers=headers)
    assert scores_resp.status_code == 200
    assert isinstance(scores_resp.json(), list)
