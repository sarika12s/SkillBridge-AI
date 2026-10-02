"""Unit and integration tests for Phase 6 Career Role Compatibility Engine and APIs."""

import pytest
import uuid
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.resume import Resume
from app.models.skill import Skill, ResumeSkill
from app.models.career import Occupation, OccupationSkill
from app.ai.career.career_engine import CareerEngine


def test_career_engine_analytical_scoring():
    """Verifies CareerEngine generates bounded, explainable scores and detects strengths and gaps."""
    engine = CareerEngine(db=None)

    # Mock resume with skills: Python (in PROJECTS), FastAPI, Git
    user_id = uuid.uuid4()
    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Backend Resume",
        file_name="res.pdf",
        stored_path="/tmp/res.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        raw_text="Experienced Backend Developer with Python and FastAPI",
    )
    
    sk_python = Skill(id=uuid.uuid4(), name="Python", normalized_name="python", category="PROGRAMMING_LANGUAGE")
    sk_fastapi = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    sk_git = Skill(id=uuid.uuid4(), name="Git", normalized_name="git", category="VERSION_CONTROL")

    rs1 = ResumeSkill(
        resume_id=resume.id,
        skill_id=sk_python.id,
        raw_skill_text="Python",
        canonical_skill_name="Python",
        source_section="PROJECTS",
        evidence_sentence="Built Python microservices",
    )
    rs1.skill = sk_python
    rs2 = ResumeSkill(
        resume_id=resume.id,
        skill_id=sk_fastapi.id,
        raw_skill_text="FastAPI",
        canonical_skill_name="FastAPI",
        source_section="EXPERIENCE",
        evidence_sentence="Deployed FastAPI APIs",
    )
    rs2.skill = sk_fastapi
    rs3 = ResumeSkill(
        resume_id=resume.id,
        skill_id=sk_git.id,
        raw_skill_text="Git",
        canonical_skill_name="Git",
        source_section="SKILLS",
        evidence_sentence="Used Git daily",
    )
    rs3.skill = sk_git
    resume.skills = [rs1, rs2, rs3]

    # Target Occupation: Backend Developer (Requires: Python, FastAPI, PostgreSQL, Docker)
    sk_pg = Skill(id=uuid.uuid4(), name="PostgreSQL", normalized_name="postgresql", category="DATABASE")
    sk_docker = Skill(id=uuid.uuid4(), name="Docker", normalized_name="docker", category="CLOUD_DEVOPS")

    occ = Occupation(
        id=uuid.uuid4(),
        code="TEST-2512.1",
        title="Backend Developer",
        normalized_title="backend developer",
        description="Builds server side APIs",
        category="SOFTWARE_DEVELOPMENT",
    )
    
    os1 = OccupationSkill(occupation_id=occ.id, skill_id=sk_python.id, requirement_type="REQUIRED")
    os1.skill = sk_python
    os2 = OccupationSkill(occupation_id=occ.id, skill_id=sk_fastapi.id, requirement_type="REQUIRED")
    os2.skill = sk_fastapi
    os3 = OccupationSkill(occupation_id=occ.id, skill_id=sk_pg.id, requirement_type="REQUIRED")
    os3.skill = sk_pg
    os4 = OccupationSkill(occupation_id=occ.id, skill_id=sk_docker.id, requirement_type="REQUIRED")
    os4.skill = sk_docker
    occ.skills = [os1, os2, os3, os4]

    results = engine.evaluate_role_compatibility(resume, [occ])
    assert len(results) == 1
    res = results[0]

    # Check bounds
    assert 0.0 <= res["compatibility_score"] <= 100.0
    # Required skills: 2 out of 4 matched (50% of 50% = 25.0)
    # Check components
    comp_map = {c["component_name"]: c for c in res["components"]}
    assert "Required Skills Match" in comp_map
    assert comp_map["Required Skills Match"]["score"] == 50.0

    # Check strengths and gaps
    assert "Python" in res["strengths"]
    assert "FastAPI" in res["strengths"]
    assert "PostgreSQL" in res["skill_gaps"]
    assert "Docker" in res["skill_gaps"]
    assert "Candidate displays" in res["summary_explanation"]


def test_career_api_occupations_and_compatibility(client: TestClient, db_session):
    """Tests /api/v1/careers/occupations and /api/v1/careers/compatibility endpoints."""
    # Register user
    register_data = {
        "email": "career_user@skillbridge.ai",
        "password": "SecurePassword123!",
        "full_name": "Career Candidate",
    }
    reg_resp = client.post("/api/v1/auth/register", json=register_data)
    token = reg_resp.json()["access_token"]
    user_id = uuid.UUID(reg_resp.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    # Seed an occupation in the test db
    occ = Occupation(
        code="API-TEST-DEV",
        title="Full Stack Engineer",
        normalized_title="full stack engineer",
        description="Full stack web app development",
        category="SOFTWARE_DEVELOPMENT",
    )
    db_session.add(occ)
    db_session.flush()

    sk = Skill(name="JavaScript", normalized_name="javascript", category="PROGRAMMING_LANGUAGE")
    db_session.add(sk)
    db_session.flush()

    occ_sk = OccupationSkill(occupation_id=occ.id, skill_id=sk.id, requirement_type="REQUIRED")
    db_session.add(occ_sk)

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Full Stack Resume",
        file_name="resume.pdf",
        stored_path="/tmp/res.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        raw_text="Experienced engineer in JavaScript",
    )
    db_session.add(resume)
    db_session.flush()

    rs = ResumeSkill(
        resume_id=resume.id,
        skill_id=sk.id,
        raw_skill_text="JavaScript",
        canonical_skill_name="JavaScript",
        source_section="SKILLS",
        evidence_sentence="5 years JavaScript experience",
    )
    db_session.add(rs)
    db_session.commit()

    # 1. Test GET /occupations
    occ_resp = client.get("/api/v1/careers/occupations", headers=headers)
    assert occ_resp.status_code == 200
    occ_list = occ_resp.json()
    assert len(occ_list) >= 1
    assert any(o["title"] == "Full Stack Engineer" for o in occ_list)

    # 2. Test GET /compatibility/{resume_id}
    compat_resp = client.get(f"/api/v1/careers/compatibility/{resume.id}", headers=headers)
    assert compat_resp.status_code == 200
    compat_data = compat_resp.json()
    assert compat_data["resume_id"] == str(resume.id)
    assert len(compat_data["roles"]) >= 1

    first_role = compat_data["roles"][0]
    assert first_role["occupation_title"] == "Full Stack Engineer"
    assert first_role["compatibility_score"] > 0
    assert "JavaScript" in first_role["strengths"]
    assert len(first_role["components"]) == 4
