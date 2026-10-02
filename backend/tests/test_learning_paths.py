"""Unit and integration tests for Phase 6 Learning Path Recommendation Engine and APIs."""

import pytest
import uuid
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.resume import Resume
from app.models.job import Job, JobSkill
from app.models.skill import Skill, ResumeSkill
from app.models.career import Occupation, OccupationSkill
from app.models.learning import LearningResource, LearningPath, LearningPathItem
from app.ai.learning.dependency_graph import SkillDependencyGraph
from app.ai.learning.learning_engine import LearningEngine


def test_dependency_graph_cycle_detection():
    """Verifies that the dependency graph detects cycles and resolves topological sorting."""
    graph = SkillDependencyGraph(db=None)

    # Invalidate with an intentional cyclic graph: A -> B -> C -> A
    graph.skills = {"A", "B", "C"}
    graph.adj = {"A": ["B"], "B": ["C"], "C": ["A"]}
    graph.in_edges = {"B": ["A"], "C": ["B"], "A": ["C"]}

    cycles = graph.detect_cycles()
    assert len(cycles) > 0

    # Test clean DAG: Python -> FastAPI -> Microservices
    dag = SkillDependencyGraph(db=None)
    dag.skills = {"Python", "FastAPI", "Microservices"}
    dag.adj = {"Python": ["FastAPI"], "FastAPI": ["Microservices"], "Microservices": []}
    dag.in_edges = {"FastAPI": ["Python"], "Microservices": ["FastAPI"], "Python": []}

    cycles_clean = dag.detect_cycles()
    assert len(cycles_clean) == 0

    # Topological stages when candidate already knows Python
    res = dag.organize_learning_stages(
        target_skills=["Python", "FastAPI", "Microservices"],
        acquired_skills={"Python"},
    )
    stages = res["stages"]
    # Python is acquired, so missing skills are FastAPI and Microservices
    # Stage 1 should be FastAPI (since Python is already satisfied)
    # Stage 2 should be Microservices (depends on FastAPI)
    assert 1 in stages
    assert "FastAPI" in stages[1]
    assert 2 in stages
    assert "Microservices" in stages[2]
    assert "Python" not in stages[1] and "Python" not in stages[2]


def test_learning_engine_career_path_generation():
    """Verifies dual-mode path generation and effort estimation."""
    engine = LearningEngine(db=None)

    # Candidate knows Python
    resume = Resume(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Python Resume",
        file_name="res.pdf",
        stored_path="/tmp/res.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        raw_text="Python developer",
    )
    sk_py = Skill(id=uuid.uuid4(), name="Python", normalized_name="python")
    rs = ResumeSkill(
        resume_id=resume.id,
        skill_id=sk_py.id,
        raw_skill_text="Python",
        canonical_skill_name="Python",
        source_section="SKILLS",
        evidence_sentence="Python development",
    )
    rs.skill = sk_py
    resume.skills = [rs]

    # Target: Backend Dev (Requires: Python, FastAPI, Docker)
    sk_fastapi = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi")
    sk_docker = Skill(id=uuid.uuid4(), name="Docker", normalized_name="docker")

    occ = Occupation(
        id=uuid.uuid4(),
        code="TEST-BE",
        title="Backend Engineer",
        normalized_title="backend engineer",
        description="Backend API engineer",
    )
    os1 = OccupationSkill(occupation_id=occ.id, skill_id=sk_py.id, requirement_type="REQUIRED")
    os1.skill = sk_py
    os2 = OccupationSkill(occupation_id=occ.id, skill_id=sk_fastapi.id, requirement_type="REQUIRED")
    os2.skill = sk_fastapi
    os3 = OccupationSkill(occupation_id=occ.id, skill_id=sk_docker.id, requirement_type="REQUIRED")
    os3.skill = sk_docker
    occ.skills = [os1, os2, os3]

    path = engine.generate_career_learning_path(resume, occ, user_id=resume.user_id)

    assert path.target_type == "CAREER"
    assert "Backend Engineer" in path.title
    assert path.total_estimated_hours_min > 0
    assert path.total_estimated_hours_max >= path.total_estimated_hours_min
    assert path.overall_progress_percentage == 0.0

    # Check items: Python must be skipped since candidate already possesses it!
    item_names = [it.skill.name if it.skill else "" for it in path.items]
    assert "Python" not in item_names
    assert len(path.items) >= 2


def test_learning_item_progress_update():
    """Verifies that updating item progress dynamically recomputes overall path percentage."""
    engine = LearningEngine(db=None)
    path = LearningPath(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        resume_id=uuid.uuid4(),
        target_type="CAREER",
        title="Test Path",
        overall_progress_percentage=0.0,
        status="IN_PROGRESS",
    )
    item1 = LearningPathItem(
        id=uuid.uuid4(),
        learning_path_id=path.id,
        stage_order=1,
        sequence_in_stage=1,
        status="NOT_STARTED",
    )
    item1.learning_path = path
    item2 = LearningPathItem(
        id=uuid.uuid4(),
        learning_path_id=path.id,
        stage_order=2,
        sequence_in_stage=1,
        status="NOT_STARTED",
    )
    item2.learning_path = path
    path.items = [item1, item2]

    # Update item 1 to COMPLETED -> 50%
    engine.update_item_progress(item1, "COMPLETED", "Mastered module 1")
    assert item1.status == "COMPLETED"
    assert item1.completed_at is not None
    assert path.overall_progress_percentage == 50.0
    assert path.status == "IN_PROGRESS"

    # Update item 2 to COMPLETED -> 100%
    engine.update_item_progress(item2, "COMPLETED")
    assert path.overall_progress_percentage == 100.0
    assert path.status == "COMPLETED"


def test_learning_paths_api_end_to_end(client: TestClient, db_session):
    """End-to-end API test for creating, fetching, and updating learning paths."""
    # 1. Register & Login
    register_data = {
        "email": "learner@skillbridge.ai",
        "password": "SecurePassword123!",
        "full_name": "Active Learner",
    }
    reg_resp = client.post("/api/v1/auth/register", json=register_data)
    token = reg_resp.json()["access_token"]
    user_id = uuid.UUID(reg_resp.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Seed data
    resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Junior Developer Resume",
        file_name="res.pdf",
        stored_path="/tmp/r.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        raw_text="Junior Developer",
    )
    db_session.add(resume)
    db_session.flush()

    sk_git = Skill(name="Git", normalized_name="git", category="VERSION_CONTROL")
    sk_react = Skill(name="React", normalized_name="react", category="FRAMEWORK")
    db_session.add(sk_git)
    db_session.add(sk_react)
    db_session.flush()

    occ = Occupation(
        code="OCC-FRONTEND-TEST",
        title="Junior Frontend Dev",
        normalized_title="junior frontend dev",
        description="Frontend dev",
        category="SOFTWARE_DEVELOPMENT",
    )
    db_session.add(occ)
    db_session.flush()

    db_session.add(OccupationSkill(occupation_id=occ.id, skill_id=sk_git.id, requirement_type="REQUIRED"))
    db_session.add(OccupationSkill(occupation_id=occ.id, skill_id=sk_react.id, requirement_type="REQUIRED"))
    db_session.commit()

    # 3. POST /api/v1/learning-paths (Create Path)
    create_payload = {
        "resume_id": str(resume.id),
        "target_type": "CAREER",
        "target_occupation_id": str(occ.id),
    }
    create_resp = client.post("/api/v1/learning-paths", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    path_data = create_resp.json()
    path_id = path_data["id"]
    assert path_data["target_type"] == "CAREER"
    assert len(path_data["stages"]) > 0
    assert "graph" in path_data
    assert len(path_data["graph"]["nodes"]) >= 2

    # 4. GET /api/v1/learning-paths/{id}
    get_resp = client.get(f"/api/v1/learning-paths/{path_id}", headers=headers)
    assert get_resp.status_code == 200
    fetched_path = get_resp.json()
    assert fetched_path["id"] == path_id
    first_item = fetched_path["stages"][0]["items"][0]
    first_item_id = first_item["id"]

    # 5. PATCH /api/v1/learning-paths/items/{id}/progress
    update_payload = {"status": "COMPLETED", "notes": "Completed chapter 1 & 2 exercises"}
    patch_resp = client.patch(
        f"/api/v1/learning-paths/items/{first_item_id}/progress",
        json=update_payload,
        headers=headers,
    )
    assert patch_resp.status_code == 200
    progress_result = patch_resp.json()
    assert progress_result["status"] == "COMPLETED"
    assert progress_result["overall_progress_percentage"] > 0
