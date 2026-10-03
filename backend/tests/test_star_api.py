"""Focused API integration tests for Phase 8.3 STAR Resume Guidance.

Tests the endpoint:
  GET /api/v1/resumes/{resume_id}/star-guidance

Covers:
1. Authenticated successful request
2. Unauthenticated request (401)
3. Invalid UUID path parameter (422)
4. Nonexistent resume ID (404)
5. Cross-user unauthorized access rejection (404)
6. Empty resume handling (0 bullets, 0.0 completeness)
7. Multi-bullet experience and project evaluation
8. Pydantic response schema validation
9. Exact requested resume version preservation
10. Deterministic repeated API requests
11. Zero database mutations (compute-on-read)
"""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.resume import Resume, ResumeExperience, ResumeProject
from app.schemas.star_guidance import ResumeSTARGuidanceResponse


def _register_user(client: TestClient, email: str, name: str) -> tuple[dict, uuid.UUID]:
    """Helper to register a user and return auth headers and user_id."""
    reg_data = {
        "email": email,
        "password": "Password123!",
        "full_name": name,
    }
    resp = client.post("/api/v1/auth/register", json=reg_data)
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    token = resp.json()["access_token"]
    user_id = uuid.UUID(resp.json()["user"]["id"])
    return {"Authorization": f"Bearer {token}"}, user_id


def test_authenticated_successful_request(client: TestClient, db_session: Session):
    """1. Authenticated request successfully returns 200 with full STAR guidance."""
    headers, user_id = _register_user(client, "user_success@test.com", "Alice Tester")

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Alice Senior Resume",
        file_name="alice_resume.pdf",
        stored_path="/uploads/alice_resume.pdf",
        file_type="pdf",
        file_size_bytes=2048,
        version=1,
    )
    db_session.add(resume)
    db_session.commit()

    exp = ResumeExperience(
        id=uuid.uuid4(),
        resume_id=resume.id,
        company_name="CloudScale Inc",
        job_title="Senior Backend Engineer",
        description=(
            "• In a high-volume microservices environment, tasked with reducing latency, "
            "architected an asynchronous caching layer with Redis, reducing response times by 40% for 50k users."
        ),
    )
    db_session.add(exp)
    db_session.commit()

    resp = client.get(f"/api/v1/resumes/{resume.id}/star-guidance", headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    assert data["resume_id"] == str(resume.id)
    assert data["resume_version"] == 1
    assert data["resume_title"] == "Alice Senior Resume"
    assert data["methodology"] == "Deterministic Rule-Based STAR Structural Analysis"
    assert data["summary"]["total_bullets_analyzed"] == 1
    assert data["summary"]["bullets_with_action"] == 1
    assert data["summary"]["bullets_with_result"] == 1
    assert data["summary"]["strong_bullets_count"] == 1
    assert data["summary"]["overall_completeness_percentage"] == 100.0


def test_unauthenticated_request(client: TestClient):
    """2. Request without auth token returns 401 Unauthorized."""
    random_id = uuid.uuid4()
    resp = client.get(f"/api/v1/resumes/{random_id}/star-guidance")
    assert resp.status_code == 401


def test_invalid_uuid(client: TestClient, db_session: Session):
    """3. Invalid UUID path parameter returns 422 Unprocessable Entity."""
    headers, _ = _register_user(client, "user_uuid@test.com", "Bob Tester")
    resp = client.get("/api/v1/resumes/not-a-valid-uuid/star-guidance", headers=headers)
    assert resp.status_code == 422


def test_nonexistent_resume(client: TestClient, db_session: Session):
    """4. Nonexistent resume ID returns 404 Not Found."""
    headers, _ = _register_user(client, "user_404@test.com", "Charlie Tester")
    nonexistent_id = uuid.uuid4()
    resp = client.get(f"/api/v1/resumes/{nonexistent_id}/star-guidance", headers=headers)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_cross_user_resume_access(client: TestClient, db_session: Session):
    """5. User B cannot access User A's resume (returns 404, strictly tenant-isolated)."""
    headers_a, user_a_id = _register_user(client, "user_a@test.com", "User Alpha")
    headers_b, user_b_id = _register_user(client, "user_b@test.com", "User Beta")

    resume_a = Resume(
        id=uuid.uuid4(),
        user_id=user_a_id,
        title="Alpha Confidential Resume",
        file_name="alpha.pdf",
        stored_path="/uploads/alpha.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        version=1,
    )
    db_session.add(resume_a)
    db_session.commit()

    # User B attempts to access User A's resume
    resp = client.get(f"/api/v1/resumes/{resume_a.id}/star-guidance", headers=headers_b)
    assert resp.status_code == 404
    assert "access denied" in resp.json()["detail"].lower() or "not found" in resp.json()["detail"].lower()


def test_empty_resume(client: TestClient, db_session: Session):
    """6. Valid resume with zero experiences and projects returns 200 with empty metrics."""
    headers, user_id = _register_user(client, "user_empty@test.com", "Empty Tester")

    empty_resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Empty Resume",
        file_name="empty.pdf",
        stored_path="/uploads/empty.pdf",
        file_type="pdf",
        file_size_bytes=512,
        version=1,
    )
    db_session.add(empty_resume)
    db_session.commit()

    resp = client.get(f"/api/v1/resumes/{empty_resume.id}/star-guidance", headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    assert data["summary"]["total_bullets_analyzed"] == 0
    assert data["summary"]["overall_completeness_percentage"] == 0.0
    assert data["summary"]["strong_bullets_count"] == 0
    assert data["summary"]["needs_improvement_count"] == 0
    assert data["bullets"] == []


def test_multi_bullet_resume(client: TestClient, db_session: Session):
    """7. Multi-bullet resume across experience and project sections correctly categorized."""
    headers, user_id = _register_user(client, "user_multi@test.com", "Multi Tester")

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Full Stack Engineer",
        file_name="fullstack.pdf",
        stored_path="/uploads/fullstack.pdf",
        file_type="pdf",
        file_size_bytes=3000,
        version=1,
    )
    db_session.add(resume)
    db_session.commit()

    exp = ResumeExperience(
        id=uuid.uuid4(),
        resume_id=resume.id,
        company_name="Apex Systems",
        job_title="Lead Backend Architect",
        description=(
            "• In a high-volume microservices environment, tasked with reducing latency, "
            "architected an asynchronous caching layer with Redis, reducing response times by 40% for 50k users.\n"
            "• Responsible for team code reviews and mentoring in 2024."
        ),
    )
    proj = ResumeProject(
        id=uuid.uuid4(),
        resume_id=resume.id,
        project_name="DataSync Engine",
        description="Engineered distributed caching layer, reducing latency by 35%.",
    )
    db_session.add_all([exp, proj])
    db_session.commit()

    resp = client.get(f"/api/v1/resumes/{resume.id}/star-guidance", headers=headers)
    assert resp.status_code == 200

    data = resp.json()
    assert data["summary"]["total_bullets_analyzed"] == 3
    assert data["summary"]["bullets_with_action"] == 2
    assert data["summary"]["bullets_with_result"] == 2
    assert data["summary"]["strong_bullets_count"] == 2
    assert data["summary"]["needs_improvement_count"] == 1
    assert len(data["bullets"]) == 3

    # Check bullet 1 (Complete STAR)
    b1 = data["bullets"][0]
    assert b1["section_type"] == "EXPERIENCE"
    assert b1["completeness_score"] == 100.0
    assert b1["missing_components"] == []

    # Check bullet 2 (Missing Action & Result)
    b2 = data["bullets"][1]
    assert b2["section_type"] == "EXPERIENCE"
    assert "ACTION" in b2["missing_components"]
    assert "RESULT" in b2["missing_components"]

    # Check bullet 3 (Project bullet: Action + Result)
    b3 = data["bullets"][2]
    assert b3["section_type"] == "PROJECTS"
    assert b3["completeness_score"] == 65.0
    assert b3["parent_entry_title"] == "DataSync Engine"


def test_response_schema_validation(client: TestClient, db_session: Session):
    """8. Verifies that the endpoint response strictly conforms to ResumeSTARGuidanceResponse."""
    headers, user_id = _register_user(client, "user_schema@test.com", "Schema Tester")

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Schema Validation Resume",
        file_name="schema.pdf",
        stored_path="/uploads/schema.pdf",
        file_type="pdf",
        file_size_bytes=1000,
        version=1,
    )
    db_session.add(resume)
    db_session.commit()

    resp = client.get(f"/api/v1/resumes/{resume.id}/star-guidance", headers=headers)
    assert resp.status_code == 200

    # Parse and validate using Pydantic schema model
    validated = ResumeSTARGuidanceResponse.model_validate(resp.json())
    assert validated.resume_id == resume.id
    assert validated.resume_version == 1
    assert validated.methodology == "Deterministic Rule-Based STAR Structural Analysis"


def test_exact_requested_resume_version_returned(client: TestClient, db_session: Session):
    """9. Requests to specific resume IDs return that exact version without auto-advancing."""
    headers, user_id = _register_user(client, "user_versions@test.com", "Version Tester")

    r_v1 = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Software Engineer v1",
        file_name="v1.pdf",
        stored_path="/uploads/v1.pdf",
        file_type="pdf",
        file_size_bytes=1000,
        version=1,
    )
    r_v2 = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Software Engineer v2",
        file_name="v2.pdf",
        stored_path="/uploads/v2.pdf",
        file_type="pdf",
        file_size_bytes=1200,
        version=2,
    )
    db_session.add_all([r_v1, r_v2])
    db_session.commit()

    # Query v1 explicitly
    resp_v1 = client.get(f"/api/v1/resumes/{r_v1.id}/star-guidance", headers=headers)
    assert resp_v1.status_code == 200
    assert resp_v1.json()["resume_version"] == 1
    assert resp_v1.json()["resume_id"] == str(r_v1.id)

    # Query v2 explicitly
    resp_v2 = client.get(f"/api/v1/resumes/{r_v2.id}/star-guidance", headers=headers)
    assert resp_v2.status_code == 200
    assert resp_v2.json()["resume_version"] == 2
    assert resp_v2.json()["resume_id"] == str(r_v2.id)


def test_deterministic_repeated_api_request(client: TestClient, db_session: Session):
    """10. Repeated API requests return identical payload representations."""
    headers, user_id = _register_user(client, "user_repeat@test.com", "Repeat Tester")

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Deterministic API Resume",
        file_name="repeat.pdf",
        stored_path="/uploads/repeat.pdf",
        file_type="pdf",
        file_size_bytes=1000,
        version=1,
    )
    exp = ResumeExperience(
        id=uuid.uuid4(),
        resume_id=resume.id,
        company_name="Innovate Ltd",
        job_title="Software Architect",
        description="Architected microservices caching layer, reducing latency by 35%.",
    )
    db_session.add_all([resume, exp])
    db_session.commit()

    responses = [
        client.get(f"/api/v1/resumes/{resume.id}/star-guidance", headers=headers).json()
        for _ in range(5)
    ]

    for subsequent in responses[1:]:
        assert subsequent == responses[0]


def test_no_database_mutations_on_read(client: TestClient, db_session: Session):
    """11. Reading STAR guidance does not write or mutate any database records."""
    headers, user_id = _register_user(client, "user_readonly@test.com", "Readonly Tester")

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Readonly Resume",
        file_name="readonly.pdf",
        stored_path="/uploads/readonly.pdf",
        file_type="pdf",
        file_size_bytes=1000,
        version=1,
    )
    db_session.add(resume)
    db_session.commit()

    count_resumes_before = db_session.query(Resume).count()
    count_exp_before = db_session.query(ResumeExperience).count()
    count_proj_before = db_session.query(ResumeProject).count()

    resp = client.get(f"/api/v1/resumes/{resume.id}/star-guidance", headers=headers)
    assert resp.status_code == 200

    assert db_session.query(Resume).count() == count_resumes_before
    assert db_session.query(ResumeExperience).count() == count_exp_before
    assert db_session.query(ResumeProject).count() == count_proj_before
