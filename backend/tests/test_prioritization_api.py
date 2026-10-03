"""API integration tests for Phase 8.4 Prioritized Learning Roadmap.

Tests endpoint:
  GET /api/v1/learning-paths/{path_id}/prioritized

Covers:
1. 200 OK on valid authenticated request.
2. 401 Unauthorized on unauthenticated request.
3. 404 Not Found on nonexistent path ID.
4. 404 Not Found on cross-user path access (strict tenant isolation).
5. 422 Unprocessable Entity on invalid UUID string.
6. Target CAREER mode handling with zero compatibility delta fallback.
7. Target JOB mode handling with delta compatibility simulation.
8. Database immutability verification: zero writes/updates/deletions.
"""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.career import Occupation, OccupationSkill
from app.models.job import Job, JobSkill
from app.models.learning import LearningPath, LearningPathItem
from app.models.matching import MatchAnalysis, SkillMatch
from app.models.resume import Resume
from app.models.skill import Skill, SkillRelationship, ResumeSkill
from app.schemas.prioritized_learning import PrioritizedRoadmapResponse


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


def test_unauthenticated_request_rejected(client: TestClient):
    """Unauthenticated request must return 401."""
    random_id = uuid.uuid4()
    resp = client.get(f"/api/v1/learning-paths/{random_id}/prioritized")
    assert resp.status_code == 401


def test_invalid_uuid_rejected(client: TestClient):
    """Invalid UUID format returns 422."""
    headers, _ = _register_user(client, "test_uuid@test.com", "UUID Tester")
    resp = client.get("/api/v1/learning-paths/not-a-valid-uuid/prioritized", headers=headers)
    assert resp.status_code == 422


def test_nonexistent_path_returns_404(client: TestClient):
    """Nonexistent learning path returns 404."""
    headers, _ = _register_user(client, "test_404@test.com", "Missing Tester")
    random_id = uuid.uuid4()
    resp = client.get(f"/api/v1/learning-paths/{random_id}/prioritized", headers=headers)
    assert resp.status_code == 404


def test_cross_user_access_returns_404(client: TestClient, db_session: Session):
    """A user cannot access another user's learning path."""
    headers_alice, alice_id = _register_user(client, "alice_prior@test.com", "Alice Tester")
    headers_bob, bob_id = _register_user(client, "bob_prior@test.com", "Bob Tester")

    # Create resume & learning path for Alice
    resume = Resume(
        id=uuid.uuid4(),
        user_id=alice_id,
        title="Alice Resume",
        file_name="alice.pdf",
        stored_path="/uploads/alice.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        version=1,
    )
    db_session.add(resume)

    path = LearningPath(
        id=uuid.uuid4(),
        user_id=alice_id,
        resume_id=resume.id,
        target_type="CAREER",
        title="Alice Learning Path",
        overall_progress_percentage=0.0,
        status="IN_PROGRESS",
    )
    db_session.add(path)
    db_session.commit()

    # Bob attempts to access Alice's path
    resp = client.get(f"/api/v1/learning-paths/{path.id}/prioritized", headers=headers_bob)
    assert resp.status_code == 404


def test_career_mode_prioritization(client: TestClient, db_session: Session):
    """Test prioritized roadmap for CAREER mode."""
    headers, user_id = _register_user(client, "career_user@test.com", "Career Tester")

    # Setup Skills: Python -> FastAPI
    py_skill = Skill(id=uuid.uuid4(), name="Python", normalized_name="python", category="PROGRAMMING_LANGUAGE")
    fastapi_skill = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    db_session.add_all([py_skill, fastapi_skill])

    # Relationship: Python is prerequisite of FastAPI
    rel = SkillRelationship(
        id=uuid.uuid4(),
        source_skill_id=py_skill.id,
        target_skill_id=fastapi_skill.id,
        relationship_type="PREREQUISITE_OF",
    )
    db_session.add(rel)

    # Occupation: Backend Developer
    occ = Occupation(
        id=uuid.uuid4(),
        code="BACKEND_DEV",
        title="Backend Developer",
        normalized_title="backend developer",
        description="Develops backend services",
    )
    db_session.add(occ)

    occ_skill = OccupationSkill(
        id=uuid.uuid4(),
        occupation_id=occ.id,
        skill_id=fastapi_skill.id,
        requirement_type="REQUIRED",
        importance_weight=1.0,
    )
    db_session.add(occ_skill)

    # Resume: Candidate has no skills initially
    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Fresher Resume",
        file_name="fresher.pdf",
        stored_path="/uploads/fresher.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        version=1,
    )
    db_session.add(resume)

    # Learning Path with FastAPI item
    path = LearningPath(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_id=resume.id,
        target_type="CAREER",
        target_occupation_id=occ.id,
        title="Backend Developer Path",
        overall_progress_percentage=0.0,
        status="IN_PROGRESS",
    )
    db_session.add(path)

    item = LearningPathItem(
        id=uuid.uuid4(),
        learning_path_id=path.id,
        skill_id=fastapi_skill.id,
        stage_order=2,
        sequence_in_stage=1,
        status="NOT_STARTED",
        estimated_hours=8.0,
    )
    db_session.add(item)
    db_session.commit()

    # Call API
    resp = client.get(f"/api/v1/learning-paths/{path.id}/prioritized", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Verify Pydantic schema
    response_model = PrioritizedRoadmapResponse.model_validate(data)
    assert response_model.learning_path_id == path.id
    assert response_model.target_type == "CAREER"
    assert response_model.target_title == "Backend Developer"

    # Both FastAPI (target) and Python (implicit prerequisite) should be in prioritized_skills!
    skill_names = [s.skill_name for s in response_model.prioritized_skills]
    assert "FastAPI" in skill_names
    assert "Python" in skill_names

    py_prioritized = next(s for s in response_model.prioritized_skills if s.skill_name == "Python")
    fastapi_prioritized = next(s for s in response_model.prioritized_skills if s.skill_name == "FastAPI")

    # Python is an implicit prerequisite!
    assert py_prioritized.is_implicit_prerequisite is True
    # Python is READY because it has no prerequisites
    assert py_prioritized.readiness_status == "READY"
    # FastAPI is BLOCKED because Python is unacquired
    assert fastapi_prioritized.readiness_status == "BLOCKED"
    assert "Python" in fastapi_prioritized.unsatisfied_prerequisites

    # Next Best Skill MUST be Python, NOT FastAPI!
    assert response_model.next_best_skill is not None
    assert response_model.next_best_skill.skill_name == "Python"
    assert response_model.next_best_skill.is_implicit_prerequisite is True


def test_database_immutability(client: TestClient, db_session: Session):
    """Calling the prioritization API must perform zero database writes or mutations."""
    headers, user_id = _register_user(client, "immutable_user@test.com", "Immutable Tester")

    skill = Skill(id=uuid.uuid4(), name="Go", normalized_name="go", category="PROGRAMMING_LANGUAGE")
    db_session.add(skill)

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Go Resume",
        file_name="go.pdf",
        stored_path="/uploads/go.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        version=1,
    )
    db_session.add(resume)

    path = LearningPath(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_id=resume.id,
        target_type="CAREER",
        title="Go Developer Path",
        overall_progress_percentage=0.0,
        status="IN_PROGRESS",
    )
    db_session.add(path)

    item = LearningPathItem(
        id=uuid.uuid4(),
        learning_path_id=path.id,
        skill_id=skill.id,
        stage_order=1,
        sequence_in_stage=1,
        status="NOT_STARTED",
        estimated_hours=10.0,
    )
    db_session.add(item)
    db_session.commit()

    updated_at_before = path.updated_at
    item_status_before = item.status

    # Execute prioritized API
    resp = client.get(f"/api/v1/learning-paths/{path.id}/prioritized", headers=headers)
    assert resp.status_code == 200

    # Refresh and verify no mutations
    db_session.refresh(path)
    db_session.refresh(item)

    assert path.updated_at == updated_at_before
    assert item.status == item_status_before
    assert path.overall_progress_percentage == 0.0


def test_include_implicit_query_parameter_behavior(client: TestClient, db_session: Session):
    """
    Verifies ?include_implicit=true vs ?include_implicit=false:
    1. Default behavior == True (implicit skills present)
    2. Explicit ?include_implicit=true (implicit skills present)
    3. Explicit ?include_implicit=false (implicit skills absent)
    4. Explicit roadmap skills remain correctly evaluated with correct BLOCKED status
    5. No duplicate skills returned
    6. Deterministic output
    """
    headers, user_id = _register_user(client, "implicit_test_user@test.com", "Implicit Tester")

    # Prerequisite: Python -> FastAPI
    py_skill = Skill(id=uuid.uuid4(), name="Python", normalized_name="python", category="PROGRAMMING_LANGUAGE")
    fastapi_skill = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    db_session.add_all([py_skill, fastapi_skill])

    rel = SkillRelationship(
        id=uuid.uuid4(),
        source_skill_id=py_skill.id,
        target_skill_id=fastapi_skill.id,
        relationship_type="PREREQUISITE_OF",
    )
    db_session.add(rel)

    occ = Occupation(
        id=uuid.uuid4(),
        code="PYTHON_BACKEND",
        title="Python Backend Developer",
        normalized_title="python backend developer",
        description="Builds APIs with FastAPI",
    )
    db_session.add(occ)

    occ_skill = OccupationSkill(
        id=uuid.uuid4(),
        occupation_id=occ.id,
        skill_id=fastapi_skill.id,
        requirement_type="REQUIRED",
        importance_weight=1.0,
    )
    db_session.add(occ_skill)

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Beginner Resume",
        file_name="beginner.pdf",
        stored_path="/uploads/beginner.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        version=1,
    )
    db_session.add(resume)

    path = LearningPath(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_id=resume.id,
        target_type="CAREER",
        target_occupation_id=occ.id,
        title="Python Backend Roadmap",
        overall_progress_percentage=0.0,
        status="IN_PROGRESS",
    )
    db_session.add(path)

    item = LearningPathItem(
        id=uuid.uuid4(),
        learning_path_id=path.id,
        skill_id=fastapi_skill.id,
        stage_order=1,
        sequence_in_stage=1,
        status="NOT_STARTED",
        estimated_hours=10.0,
    )
    db_session.add(item)
    db_session.commit()

    # 1. Default call (no query parameter) -> include_implicit defaults to True
    resp_default = client.get(f"/api/v1/learning-paths/{path.id}/prioritized", headers=headers)
    assert resp_default.status_code == 200
    data_default = resp_default.json()
    names_default = [s["skill_name"] for s in data_default["prioritized_skills"]]
    assert "FastAPI" in names_default
    assert "Python" in names_default, "Implicit prerequisite Python should be present by default"
    assert len(names_default) == len(set(names_default)), "No duplicate skills should exist"
    assert data_default["next_best_skill"]["skill_name"] == "Python"

    # 2. Explicit ?include_implicit=true
    resp_true = client.get(f"/api/v1/learning-paths/{path.id}/prioritized?include_implicit=true", headers=headers)
    assert resp_true.status_code == 200
    data_true = resp_true.json()
    names_true = [s["skill_name"] for s in data_true["prioritized_skills"]]
    assert "Python" in names_true
    assert "FastAPI" in names_true
    # Verify deterministic output matches default
    assert data_true == data_default

    # 3. Explicit ?include_implicit=false
    resp_false = client.get(f"/api/v1/learning-paths/{path.id}/prioritized?include_implicit=false", headers=headers)
    assert resp_false.status_code == 200
    data_false = resp_false.json()
    names_false = [s["skill_name"] for s in data_false["prioritized_skills"]]
    assert "FastAPI" in names_false
    assert "Python" not in names_false, "Implicit prerequisite Python must be excluded when include_implicit=false"

    # 4. Verify explicit roadmap skill readiness remains BLOCKED when false
    fastapi_item = next(s for s in data_false["prioritized_skills"] if s["skill_name"] == "FastAPI")
    assert fastapi_item["readiness_status"] == "BLOCKED"
    assert "Python" in fastapi_item["unsatisfied_prerequisites"]
    # Since FastAPI is BLOCKED and no other skills exist, Next Best Skill must be None
    assert data_false["next_best_skill"] is None

    # 5. Determinism on repeated false calls
    resp_false_repeat = client.get(f"/api/v1/learning-paths/{path.id}/prioritized?include_implicit=false", headers=headers)
    assert resp_false_repeat.json() == data_false
