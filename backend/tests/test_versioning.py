"""Unit and integration tests for Phase 7 Resume Version Tracking and Comparison."""

import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.models.resume import Resume, ResumeSection
from app.models.skill import Skill, ResumeSkill
from app.models.job import Job
from app.models.matching import MatchAnalysis
from app.services.version_service import VersionService


def test_resume_version_comparison_and_comparability_guard(client: TestClient, db_session):
    """Verifies VersionService and /api/v1/resumes/compare endpoint enforce score comparability guards."""
    reg_data = {
        "email": "version_user@skillbridge.ai",
        "password": "Password123!",
        "full_name": "Version Tester",
    }
    resp = client.post("/api/v1/auth/register", json=reg_data)
    token = resp.json()["access_token"]
    user_id = uuid.UUID(resp.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(timezone.utc)

    # Seed Canonical Skills
    sk_python = Skill(name="Python", normalized_name="python", category="PROGRAMMING_LANGUAGE")
    sk_git = Skill(name="Git", normalized_name="git", category="VERSION_CONTROL")
    sk_docker = Skill(name="Docker", normalized_name="docker", category="CLOUD_DEVOPS")
    db_session.add_all([sk_python, sk_git, sk_docker])
    db_session.flush()

    # 1. Create Resume v1 (Skills: Python, Git)
    r1 = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Resume Version 1",
        file_name="res_v1.pdf",
        stored_path="/uploads/res_v1.pdf",
        file_type="pdf",
        file_size_bytes=1500,
        character_count=1000,
        version=1,
        created_at=now,
    )
    db_session.add(r1)
    db_session.flush()

    rs1_py = ResumeSkill(
        resume_id=r1.id,
        skill_id=sk_python.id,
        raw_skill_text="Python",
        canonical_skill_name="Python",
        source_section="SKILLS",
        evidence_sentence="Python programming",
    )
    rs1_git = ResumeSkill(
        resume_id=r1.id,
        skill_id=sk_git.id,
        raw_skill_text="Git",
        canonical_skill_name="Git",
        source_section="SKILLS",
        evidence_sentence="Git version control",
    )
    db_session.add_all([rs1_py, rs1_git])

    # 2. Create Resume v2 (Skills: Python [strengthened], Docker [new]; Git removed)
    r2 = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Resume Version 2",
        file_name="res_v2.pdf",
        stored_path="/uploads/res_v2.pdf",
        file_type="pdf",
        file_size_bytes=1800,
        character_count=1300,
        version=2,
        created_at=now,
    )
    db_session.add(r2)
    db_session.flush()

    rs2_py = ResumeSkill(
        resume_id=r2.id,
        skill_id=sk_python.id,
        raw_skill_text="Python",
        canonical_skill_name="Python",
        source_section="PROJECTS",
        evidence_sentence="Architected microservices using Python and AsyncIO",
    )
    rs2_docker = ResumeSkill(
        resume_id=r2.id,
        skill_id=sk_docker.id,
        raw_skill_text="Docker",
        canonical_skill_name="Docker",
        source_section="EXPERIENCE",
        evidence_sentence="Deployed containerized clusters using Docker",
    )
    db_session.add_all([rs2_py, rs2_docker])
    db_session.flush()

    # 3. Create Shared Target Job
    shared_job = Job(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Backend Engineer",
        company="CloudNet",
        ingestion_type="PASTED",
        raw_text="Backend Engineer with Python and Docker",
    )
    db_session.add(shared_job)
    db_session.flush()

    # Match analyses on same job
    m1 = MatchAnalysis(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_id=r1.id,
        job_id=shared_job.id,
        compatibility_score=60.0,
        ats_readiness_score=70.0,
        matching_engine_version="1.0.0",
        scoring_version="1.0.0-heuristic",
    )
    m2 = MatchAnalysis(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_id=r2.id,
        job_id=shared_job.id,
        compatibility_score=85.0,
        ats_readiness_score=88.0,
        matching_engine_version="1.0.0",
        scoring_version="1.0.0-heuristic",
    )
    db_session.add_all([m1, m2])
    db_session.flush()

    # Test /api/v1/resumes/versions
    ver_resp = client.get("/api/v1/resumes/versions", headers=headers)
    assert ver_resp.status_code == 200
    versions_list = ver_resp.json()
    assert len(versions_list) == 2
    assert versions_list[0]["version"] == 1
    assert versions_list[1]["version"] == 2

    # Test /api/v1/resumes/compare (Consistent target job)
    comp_resp = client.get(
        f"/api/v1/resumes/compare?resume_id_1={r1.id}&resume_id_2={r2.id}",
        headers=headers,
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()

    # Skill diffs
    assert "Docker" in comp_data["new_skills"]
    assert "Python" in comp_data["retained_skills"]
    assert "Git" in comp_data["removed_skills"]

    # Evidence changes
    assert len(comp_data["skill_evidence_changes"]) >= 1
    py_ev = next(e for e in comp_data["skill_evidence_changes"] if e["skill_name"] == "Python")
    assert py_ev["strengthened"] is True
    assert py_ev["previous_section"] == "SKILLS"
    assert py_ev["new_section"] == "PROJECTS"

    # Comparability guard: same job
    assert comp_data["is_same_job_comparison"] is True
    assert comp_data["target_job_title"] == "Backend Engineer"
    assert comp_data["job_compatibility_delta"] == 25.0
    assert comp_data["ats_score_delta"] == 18.0

    # 4. Test Comparability guard when jobs differ
    different_job = Job(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Frontend Designer",
        ingestion_type="PASTED",
        raw_text="Frontend UI Designer with Figma",
    )
    db_session.add(different_job)
    db_session.flush()

    # Change m2's job to different_job
    m2.job_id = different_job.id
    db_session.flush()

    comp_resp_diff = client.get(
        f"/api/v1/resumes/compare?resume_id_1={r1.id}&resume_id_2={r2.id}",
        headers=headers,
    )
    assert comp_resp_diff.status_code == 200
    diff_data = comp_resp_diff.json()
    assert diff_data["is_same_job_comparison"] is False
    assert diff_data["job_compatibility_delta"] is None
    assert "Scores are not directly comparable" in diff_data["comparability_notes"]
