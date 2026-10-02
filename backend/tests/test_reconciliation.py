"""Unit, integration, idempotency, and security tests for SkillBridge AI Phase 8.2:
Dynamic Roadmap Reconciliation Across Resume Versions.

Test Scenarios:
1. Happy path: Reconcile with newer resume containing exact skill match and authoritative evidence
2. Alias match: Reconcile with alias match and confidence >= 0.90
3. Disqualify SEMANTIC_EMBEDDING: Semantic matches are prohibited from milestone verification
4. Disqualify low confidence: Confidence below threshold (<0.90 for EXACT/ALIAS, <0.85 for LEXICON)
5. Disqualify short/missing evidence: Evidence sentence < 10 characters is disqualified
6. Out-of-order verification: Later stage milestone verified while earlier stage remains NOT_STARTED
7. Monotonicity: Already completed items (e.g. manually completed) are never demoted or overwritten
8. Full roadmap completion: When all milestones are verified, path status transitions to COMPLETED
9. Idempotency: Multiple sequential calls produce identical state with newly_verified_count=0
10. Explicit target resume_id specification in request payload
11. Reject reconciliation against an older resume version (v1 < baseline v2) -> 400 Bad Request
12. Tenant authorization: User cannot reconcile another candidate's learning path -> 404 Not Found
13. Tenant authorization: User cannot supply another candidate's resume -> 404 Not Found
14. Serialization integrity: GET /learning-paths/{id} returns verification provenance and version
"""

import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.resume import Resume
from app.models.skill import Skill, ResumeSkill
from app.models.career import Occupation, OccupationSkill
from app.models.learning import LearningPath, LearningPathItem, LearningResource
from app.services.learning_service import LearningService
from app.schemas.learning import ReconciliationRequest


def create_user_and_token(client: TestClient, email: str = "reconciler@skillbridge.ai"):
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": "Roadmap Reconciler",
        },
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    user_id = uuid.UUID(reg_resp.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {token}"}
    return user_id, headers


def test_reconcile_happy_path_exact_match(client: TestClient, db_session: Session):
    """Test 1: Happy path reconciliation with newer resume containing exact match and evidence."""
    user_id, headers = create_user_and_token(client, "happy_path@skillbridge.ai")

    # 1. Baseline Resume v1
    resume_v1 = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Resume v1",
        file_name="resume_v1.pdf",
        stored_path="/tmp/v1.pdf",
        file_type="pdf",
        file_size_bytes=1000,
        version=1,
    )
    db_session.add(resume_v1)

    # 2. Canonical Skills
    sk_python = Skill(id=uuid.uuid4(), name="Python", normalized_name="python", category="PROGRAMMING_LANGUAGE")
    sk_fastapi = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    sk_docker = Skill(id=uuid.uuid4(), name="Docker", normalized_name="docker", category="CLOUD_DEVOPS")
    db_session.add_all([sk_python, sk_fastapi, sk_docker])
    db_session.flush()

    # 3. Learning Path targeting Backend Engineer with 2 gap items (FastAPI, Docker)
    path = LearningPath(
        id=uuid.uuid4(),
        user_id=user_id,
        resume_id=resume_v1.id,
        target_type="CAREER",
        title="Career Pathway: Backend Engineer",
        status="IN_PROGRESS",
        overall_progress_percentage=0.0,
    )
    db_session.add(path)
    db_session.flush()

    item1 = LearningPathItem(
        id=uuid.uuid4(),
        learning_path_id=path.id,
        skill_id=sk_fastapi.id,
        stage_order=1,
        sequence_in_stage=1,
        status="NOT_STARTED",
        estimated_hours=10.0,
    )
    item2 = LearningPathItem(
        id=uuid.uuid4(),
        learning_path_id=path.id,
        skill_id=sk_docker.id,
        stage_order=2,
        sequence_in_stage=1,
        status="NOT_STARTED",
        estimated_hours=15.0,
    )
    db_session.add_all([item1, item2])
    db_session.commit()

    # 4. Candidate uploads Resume v2 (version=2) demonstrating FastAPI with authoritative evidence
    resume_v2 = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Resume v2",
        file_name="resume_v2.pdf",
        stored_path="/tmp/v2.pdf",
        file_type="pdf",
        file_size_bytes=1200,
        version=2,
    )
    db_session.add(resume_v2)
    db_session.flush()

    rs_fastapi = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk_fastapi.id,
        raw_skill_text="FastAPI",
        canonical_skill_name="FastAPI",
        source_section="EXPERIENCE",
        evidence_sentence="Architected and deployed production REST APIs using FastAPI and Pydantic.",
        confidence=0.96,
        match_method="EXACT",
    )
    db_session.add(rs_fastapi)
    db_session.commit()

    # 5. Execute Reconciliation POST /api/v1/learning-paths/{id}/reconcile
    resp = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["learning_path_id"] == str(path.id)
    assert data["baseline_resume_id"] == str(resume_v1.id)
    assert data["verifying_resume_id"] == str(resume_v2.id)
    assert data["verifying_resume_version"] == 2
    assert data["items_evaluated"] == 2
    assert data["newly_verified_count"] == 1
    assert data["already_completed_count"] == 0
    assert data["remaining_unverified_count"] == 1
    assert data["previous_progress_percentage"] == 0.0
    assert data["new_progress_percentage"] == 50.0
    assert data["previous_remaining_hours"] == 25.0
    assert data["new_remaining_hours"] == 15.0
    assert data["path_status"] == "IN_PROGRESS"
    assert len(data["verified_items"]) == 1
    assert data["verified_items"][0]["skill_name"] == "FastAPI"
    assert data["verified_items"][0]["match_method"] == "EXACT"

    # Verify Database State
    db_session.expire_all()
    updated_item1 = db_session.query(LearningPathItem).filter_by(id=item1.id).one()
    assert updated_item1.status == "COMPLETED"
    assert updated_item1.verified_by_resume_id == resume_v2.id
    assert updated_item1.verification_method == "RESUME_EVIDENCE"
    assert updated_item1.verified_at is not None
    assert "Auto-verified by Resume v2" in updated_item1.notes

    updated_item2 = db_session.query(LearningPathItem).filter_by(id=item2.id).one()
    assert updated_item2.status == "NOT_STARTED"
    assert updated_item2.verified_by_resume_id is None


def test_reconcile_alias_match(client: TestClient, db_session: Session):
    """Test 2: Reconcile with alias match and confidence >= 0.90."""
    user_id, headers = create_user_and_token(client, "alias_match@skillbridge.ai")

    resume_v1 = Resume(id=uuid.uuid4(), user_id=user_id, title="v1", file_name="v1.pdf", stored_path="v1", file_type="pdf", file_size_bytes=100, version=1)
    sk_k8s = Skill(id=uuid.uuid4(), name="Kubernetes", normalized_name="kubernetes", category="CLOUD_DEVOPS")
    db_session.add_all([resume_v1, sk_k8s])
    db_session.flush()

    path = LearningPath(id=uuid.uuid4(), user_id=user_id, resume_id=resume_v1.id, target_type="CAREER", title="DevOps Path", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path)
    db_session.flush()

    item = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk_k8s.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=12.0)
    db_session.add(item)

    resume_v2 = Resume(id=uuid.uuid4(), user_id=user_id, title="v2", file_name="v2.pdf", stored_path="v2", file_type="pdf", file_size_bytes=100, version=2)
    db_session.add(resume_v2)
    db_session.flush()

    rs_k8s = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk_k8s.id,
        raw_skill_text="K8s",
        canonical_skill_name="Kubernetes",
        source_section="PROJECTS",
        evidence_sentence="Configured K8s ingress controllers and stateful sets on AWS EKS.",
        confidence=0.94,
        match_method="ALIAS",
    )
    db_session.add(rs_k8s)
    db_session.commit()

    resp = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["newly_verified_count"] == 1
    assert resp.json()["verified_items"][0]["match_method"] == "ALIAS"
    assert resp.json()["new_progress_percentage"] == 100.0


def test_disqualify_semantic_embedding_match(client: TestClient, db_session: Session):
    """Test 3: SEMANTIC_EMBEDDING matches are strictly prohibited from milestone auto-verification."""
    user_id, headers = create_user_and_token(client, "semantic_match@skillbridge.ai")

    resume_v1 = Resume(id=uuid.uuid4(), user_id=user_id, title="v1", file_name="v1.pdf", stored_path="v1", file_type="pdf", file_size_bytes=100, version=1)
    sk = Skill(id=uuid.uuid4(), name="PostgreSQL", normalized_name="postgresql", category="DATABASE")
    db_session.add_all([resume_v1, sk])
    db_session.flush()

    path = LearningPath(id=uuid.uuid4(), user_id=user_id, resume_id=resume_v1.id, target_type="CAREER", title="DB Path", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path)
    db_session.flush()

    item = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=8.0)
    db_session.add(item)

    resume_v2 = Resume(id=uuid.uuid4(), user_id=user_id, title="v2", file_name="v2.pdf", stored_path="v2", file_type="pdf", file_size_bytes=100, version=2)
    db_session.add(resume_v2)
    db_session.flush()

    # Weak match via semantic embedding
    rs = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk.id,
        raw_skill_text="relational data store",
        canonical_skill_name="PostgreSQL",
        source_section="EXPERIENCE",
        evidence_sentence="Maintained cloud relational databases and query pipelines.",
        confidence=0.92,
        match_method="SEMANTIC_EMBEDDING",
    )
    db_session.add(rs)
    db_session.commit()

    resp = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["newly_verified_count"] == 0
    assert resp.json()["new_progress_percentage"] == 0.0

    db_session.expire_all()
    it = db_session.query(LearningPathItem).filter_by(id=item.id).one()
    assert it.status == "NOT_STARTED"
    assert it.verified_by_resume_id is None


def test_disqualify_low_confidence(client: TestClient, db_session: Session):
    """Test 4: Disqualify matches with confidence below threshold (<0.90 for EXACT, <0.85 for LEXICON)."""
    user_id, headers = create_user_and_token(client, "low_conf@skillbridge.ai")

    resume_v1 = Resume(id=uuid.uuid4(), user_id=user_id, title="v1", file_name="v1.pdf", stored_path="v1", file_type="pdf", file_size_bytes=100, version=1)
    sk1 = Skill(id=uuid.uuid4(), name="GraphQL", normalized_name="graphql", category="FRAMEWORK")
    sk2 = Skill(id=uuid.uuid4(), name="Redis", normalized_name="redis", category="DATABASE")
    db_session.add_all([resume_v1, sk1, sk2])
    db_session.flush()

    path = LearningPath(id=uuid.uuid4(), user_id=user_id, resume_id=resume_v1.id, target_type="CAREER", title="Path", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path)
    db_session.flush()

    item1 = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk1.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=6.0)
    item2 = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk2.id, stage_order=1, sequence_in_stage=2, status="NOT_STARTED", estimated_hours=6.0)
    db_session.add_all([item1, item2])

    resume_v2 = Resume(id=uuid.uuid4(), user_id=user_id, title="v2", file_name="v2.pdf", stored_path="v2", file_type="pdf", file_size_bytes=100, version=2)
    db_session.add(resume_v2)
    db_session.flush()

    rs1 = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk1.id,
        raw_skill_text="GraphQL",
        canonical_skill_name="GraphQL",
        source_section="SKILLS",
        evidence_sentence="GraphQL query schemas and resolvers.",
        confidence=0.88,  # Below 0.90
        match_method="EXACT",
    )
    rs2 = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk2.id,
        raw_skill_text="Redis",
        canonical_skill_name="Redis",
        source_section="SKILLS",
        evidence_sentence="Redis caching and pub-sub pipelines.",
        confidence=0.80,  # Below 0.85
        match_method="LEXICON_MATCH",
    )
    db_session.add_all([rs1, rs2])
    db_session.commit()

    resp = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["newly_verified_count"] == 0
    assert resp.json()["new_progress_percentage"] == 0.0


def test_disqualify_short_or_missing_evidence(client: TestClient, db_session: Session):
    """Test 5: Disqualify evidence sentences with length < 10 characters."""
    user_id, headers = create_user_and_token(client, "short_evidence@skillbridge.ai")

    resume_v1 = Resume(id=uuid.uuid4(), user_id=user_id, title="v1", file_name="v1.pdf", stored_path="v1", file_type="pdf", file_size_bytes=100, version=1)
    sk = Skill(id=uuid.uuid4(), name="Docker", normalized_name="docker", category="CLOUD_DEVOPS")
    db_session.add_all([resume_v1, sk])
    db_session.flush()

    path = LearningPath(id=uuid.uuid4(), user_id=user_id, resume_id=resume_v1.id, target_type="CAREER", title="Path", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path)
    db_session.flush()

    item = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=6.0)
    db_session.add(item)

    resume_v2 = Resume(id=uuid.uuid4(), user_id=user_id, title="v2", file_name="v2.pdf", stored_path="v2", file_type="pdf", file_size_bytes=100, version=2)
    db_session.add(resume_v2)
    db_session.flush()

    # Evidence sentence is too brief (< 10 chars)
    rs = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk.id,
        raw_skill_text="Docker",
        canonical_skill_name="Docker",
        source_section="SKILLS",
        evidence_sentence="Docker.",  # Only 7 chars
        confidence=0.99,
        match_method="EXACT",
    )
    db_session.add(rs)
    db_session.commit()

    resp = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["newly_verified_count"] == 0
    assert resp.json()["new_progress_percentage"] == 0.0


def test_out_of_order_verification(client: TestClient, db_session: Session):
    """Test 6: Out-of-order verification: Later stage milestone verified while earlier stage remains NOT_STARTED."""
    user_id, headers = create_user_and_token(client, "out_of_order@skillbridge.ai")

    resume_v1 = Resume(id=uuid.uuid4(), user_id=user_id, title="v1", file_name="v1.pdf", stored_path="v1", file_type="pdf", file_size_bytes=100, version=1)
    sk_stage1 = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    sk_stage2 = Skill(id=uuid.uuid4(), name="Kubernetes", normalized_name="kubernetes", category="CLOUD_DEVOPS")
    db_session.add_all([resume_v1, sk_stage1, sk_stage2])
    db_session.flush()

    path = LearningPath(id=uuid.uuid4(), user_id=user_id, resume_id=resume_v1.id, target_type="CAREER", title="Path", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path)
    db_session.flush()

    item_stg1 = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk_stage1.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=10.0)
    item_stg2 = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk_stage2.id, stage_order=2, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=20.0)
    db_session.add_all([item_stg1, item_stg2])

    resume_v2 = Resume(id=uuid.uuid4(), user_id=user_id, title="v2", file_name="v2.pdf", stored_path="v2", file_type="pdf", file_size_bytes=100, version=2)
    db_session.add(resume_v2)
    db_session.flush()

    # Candidate only acquired Kubernetes (Stage 2)
    rs_k8s = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk_stage2.id,
        raw_skill_text="Kubernetes",
        canonical_skill_name="Kubernetes",
        source_section="EXPERIENCE",
        evidence_sentence="Managed multi-cluster Kubernetes deployments and Helm charts.",
        confidence=0.95,
        match_method="EXACT",
    )
    db_session.add(rs_k8s)
    db_session.commit()

    resp = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["newly_verified_count"] == 1
    assert data["verified_items"][0]["skill_name"] == "Kubernetes"
    assert data["verified_items"][0]["stage_order"] == 2

    db_session.expire_all()
    it1 = db_session.query(LearningPathItem).filter_by(id=item_stg1.id).one()
    it2 = db_session.query(LearningPathItem).filter_by(id=item_stg2.id).one()
    assert it1.status == "NOT_STARTED"
    assert it2.status == "COMPLETED"
    assert it2.verification_method == "RESUME_EVIDENCE"


def test_monotonicity_already_completed_preserved(client: TestClient, db_session: Session):
    """Test 7: Monotonicity guarantee: Already completed items (e.g. manually completed) are never demoted or overwritten."""
    user_id, headers = create_user_and_token(client, "monotonicity@skillbridge.ai")

    resume_v1 = Resume(id=uuid.uuid4(), user_id=user_id, title="v1", file_name="v1.pdf", stored_path="v1", file_type="pdf", file_size_bytes=100, version=1)
    sk1 = Skill(id=uuid.uuid4(), name="Python", normalized_name="python", category="PROGRAMMING_LANGUAGE")
    sk2 = Skill(id=uuid.uuid4(), name="Docker", normalized_name="docker", category="CLOUD_DEVOPS")
    db_session.add_all([resume_v1, sk1, sk2])
    db_session.flush()

    path = LearningPath(id=uuid.uuid4(), user_id=user_id, resume_id=resume_v1.id, target_type="CAREER", title="Path", status="IN_PROGRESS", overall_progress_percentage=50.0)
    db_session.add(path)
    db_session.flush()

    # Item 1 was completed manually earlier
    completed_time = datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc)
    item1 = LearningPathItem(
        id=uuid.uuid4(),
        learning_path_id=path.id,
        skill_id=sk1.id,
        stage_order=1,
        sequence_in_stage=1,
        status="COMPLETED",
        completed_at=completed_time,
        notes="Self-study completed and tested locally.",
        verification_method="MANUAL",
        estimated_hours=10.0,
    )
    item2 = LearningPathItem(
        id=uuid.uuid4(),
        learning_path_id=path.id,
        skill_id=sk2.id,
        stage_order=2,
        sequence_in_stage=1,
        status="NOT_STARTED",
        estimated_hours=10.0,
    )
    db_session.add_all([item1, item2])

    resume_v2 = Resume(id=uuid.uuid4(), user_id=user_id, title="v2", file_name="v2.pdf", stored_path="v2", file_type="pdf", file_size_bytes=100, version=2)
    db_session.add(resume_v2)
    db_session.flush()

    # Resume v2 does NOT have Python, but has Docker
    rs_docker = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk2.id,
        raw_skill_text="Docker",
        canonical_skill_name="Docker",
        source_section="EXPERIENCE",
        evidence_sentence="Containerized Python backend services using Docker multi-stage builds.",
        confidence=0.95,
        match_method="EXACT",
    )
    db_session.add(rs_docker)
    db_session.commit()

    resp = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["already_completed_count"] == 1
    assert data["newly_verified_count"] == 1
    assert data["new_progress_percentage"] == 100.0

    # Verify Item 1 was untouched
    db_session.expire_all()
    it1 = db_session.query(LearningPathItem).filter_by(id=item1.id).one()
    assert it1.status == "COMPLETED"
    assert it1.completed_at.year == completed_time.year
    assert it1.completed_at.month == completed_time.month
    assert it1.completed_at.day == completed_time.day
    assert it1.notes == "Self-study completed and tested locally."
    assert it1.verification_method == "MANUAL"


def test_full_roadmap_completion_status(client: TestClient, db_session: Session):
    """Test 8: Full roadmap completion: When all milestones are verified, path status transitions to COMPLETED."""
    user_id, headers = create_user_and_token(client, "full_complete@skillbridge.ai")

    resume_v1 = Resume(id=uuid.uuid4(), user_id=user_id, title="v1", file_name="v1.pdf", stored_path="v1", file_type="pdf", file_size_bytes=100, version=1)
    sk1 = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    sk2 = Skill(id=uuid.uuid4(), name="Docker", normalized_name="docker", category="CLOUD_DEVOPS")
    db_session.add_all([resume_v1, sk1, sk2])
    db_session.flush()

    path = LearningPath(id=uuid.uuid4(), user_id=user_id, resume_id=resume_v1.id, target_type="CAREER", title="Path", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path)
    db_session.flush()

    item1 = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk1.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=10.0)
    item2 = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk2.id, stage_order=2, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=10.0)
    db_session.add_all([item1, item2])

    resume_v2 = Resume(id=uuid.uuid4(), user_id=user_id, title="v2", file_name="v2.pdf", stored_path="v2", file_type="pdf", file_size_bytes=100, version=2)
    db_session.add(resume_v2)
    db_session.flush()

    rs1 = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk1.id,
        raw_skill_text="FastAPI",
        canonical_skill_name="FastAPI",
        source_section="EXPERIENCE",
        evidence_sentence="Engineered performant backend microservices with FastAPI.",
        confidence=0.95,
        match_method="EXACT",
    )
    rs2 = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk2.id,
        raw_skill_text="Docker",
        canonical_skill_name="Docker",
        source_section="EXPERIENCE",
        evidence_sentence="Built and pushed multi-platform images using Docker Buildx.",
        confidence=0.96,
        match_method="EXACT",
    )
    db_session.add_all([rs1, rs2])
    db_session.commit()

    resp = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["newly_verified_count"] == 2
    assert data["new_progress_percentage"] == 100.0
    assert data["new_remaining_hours"] == 0.0
    assert data["path_status"] == "COMPLETED"

    db_session.expire_all()
    p = db_session.query(LearningPath).filter_by(id=path.id).one()
    assert p.status == "COMPLETED"
    assert p.overall_progress_percentage == 100.0


def test_idempotency_sequential_reconciliation(client: TestClient, db_session: Session):
    """Test 9: Idempotency: Multiple sequential calls produce identical state with newly_verified_count=0 on repetition."""
    user_id, headers = create_user_and_token(client, "idempotency@skillbridge.ai")

    resume_v1 = Resume(id=uuid.uuid4(), user_id=user_id, title="v1", file_name="v1.pdf", stored_path="v1", file_type="pdf", file_size_bytes=100, version=1)
    sk = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    db_session.add_all([resume_v1, sk])
    db_session.flush()

    path = LearningPath(id=uuid.uuid4(), user_id=user_id, resume_id=resume_v1.id, target_type="CAREER", title="Path", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path)
    db_session.flush()

    item = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=10.0)
    db_session.add(item)

    resume_v2 = Resume(id=uuid.uuid4(), user_id=user_id, title="v2", file_name="v2.pdf", stored_path="v2", file_type="pdf", file_size_bytes=100, version=2)
    db_session.add(resume_v2)
    db_session.flush()

    rs = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk.id,
        raw_skill_text="FastAPI",
        canonical_skill_name="FastAPI",
        source_section="EXPERIENCE",
        evidence_sentence="Engineered performant backend microservices with FastAPI.",
        confidence=0.95,
        match_method="EXACT",
    )
    db_session.add(rs)
    db_session.commit()

    # Call 1: Auto-verifies 1 item
    resp1 = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["newly_verified_count"] == 1
    assert resp1.json()["new_progress_percentage"] == 100.0

    # Call 2: No duplicate verification, newly_verified_count=0
    resp2 = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["newly_verified_count"] == 0
    assert resp2.json()["already_completed_count"] == 1
    assert resp2.json()["new_progress_percentage"] == 100.0

    # Call 3: Still 0
    resp3 = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert resp3.status_code == 200
    assert resp3.json()["newly_verified_count"] == 0


def test_explicit_resume_id_specification(client: TestClient, db_session: Session):
    """Test 10: Explicit target resume_id specification in request payload."""
    user_id, headers = create_user_and_token(client, "explicit_resume@skillbridge.ai")

    resume_v1 = Resume(id=uuid.uuid4(), user_id=user_id, title="v1", file_name="v1.pdf", stored_path="v1", file_type="pdf", file_size_bytes=100, version=1)
    sk = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    db_session.add_all([resume_v1, sk])
    db_session.flush()

    path = LearningPath(id=uuid.uuid4(), user_id=user_id, resume_id=resume_v1.id, target_type="CAREER", title="Path", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path)
    db_session.flush()

    item = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=10.0)
    db_session.add(item)

    resume_v2 = Resume(id=uuid.uuid4(), user_id=user_id, title="v2", file_name="v2.pdf", stored_path="v2", file_type="pdf", file_size_bytes=100, version=2)
    db_session.add(resume_v2)
    db_session.flush()

    rs = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk.id,
        raw_skill_text="FastAPI",
        canonical_skill_name="FastAPI",
        source_section="EXPERIENCE",
        evidence_sentence="Engineered performant backend microservices with FastAPI.",
        confidence=0.95,
        match_method="EXACT",
    )
    db_session.add(rs)
    db_session.commit()

    payload = {"resume_id": str(resume_v2.id)}
    resp = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json=payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["verifying_resume_id"] == str(resume_v2.id)
    assert resp.json()["newly_verified_count"] == 1


def test_reject_older_resume_version(client: TestClient, db_session: Session):
    """Test 11: Reject reconciliation against an older resume version (v1 < baseline v2) -> 400 Bad Request."""
    user_id, headers = create_user_and_token(client, "older_resume@skillbridge.ai")

    resume_v1 = Resume(id=uuid.uuid4(), user_id=user_id, title="v1", file_name="v1.pdf", stored_path="v1", file_type="pdf", file_size_bytes=100, version=1)
    resume_v2 = Resume(id=uuid.uuid4(), user_id=user_id, title="v2", file_name="v2.pdf", stored_path="v2", file_type="pdf", file_size_bytes=100, version=2)
    sk = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    db_session.add_all([resume_v1, resume_v2, sk])
    db_session.flush()

    # Path created against baseline v2
    path = LearningPath(id=uuid.uuid4(), user_id=user_id, resume_id=resume_v2.id, target_type="CAREER", title="Path", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path)
    db_session.flush()

    item = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=10.0)
    db_session.add(item)
    db_session.commit()

    # User attempts to reconcile path against older resume v1
    payload = {"resume_id": str(resume_v1.id)}
    resp = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json=payload, headers=headers)
    assert resp.status_code == 400
    assert "older resume version" in resp.json()["detail"].lower()


def test_tenant_authorization_path_isolation(client: TestClient, db_session: Session):
    """Test 12: Tenant authorization: User cannot reconcile another candidate's learning path -> 404 Not Found."""
    user_a_id, headers_a = create_user_and_token(client, "user_a@skillbridge.ai")
    user_b_id, headers_b = create_user_and_token(client, "user_b@skillbridge.ai")

    resume_a = Resume(id=uuid.uuid4(), user_id=user_a_id, title="A v1", file_name="a.pdf", stored_path="a", file_type="pdf", file_size_bytes=100, version=1)
    sk = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    db_session.add_all([resume_a, sk])
    db_session.flush()

    path_a = LearningPath(id=uuid.uuid4(), user_id=user_a_id, resume_id=resume_a.id, target_type="CAREER", title="Path A", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path_a)
    db_session.flush()

    item = LearningPathItem(id=uuid.uuid4(), learning_path_id=path_a.id, skill_id=sk.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=10.0)
    db_session.add(item)
    db_session.commit()

    # User B tries to reconcile User A's path
    resp = client.post(f"/api/v1/learning-paths/{path_a.id}/reconcile", json={}, headers=headers_b)
    assert resp.status_code == 404


def test_tenant_authorization_resume_isolation(client: TestClient, db_session: Session):
    """Test 13: Tenant authorization: User cannot supply another candidate's resume -> 404 Not Found."""
    user_a_id, headers_a = create_user_and_token(client, "owner_a@skillbridge.ai")
    user_b_id, headers_b = create_user_and_token(client, "owner_b@skillbridge.ai")

    resume_a = Resume(id=uuid.uuid4(), user_id=user_a_id, title="A v1", file_name="a.pdf", stored_path="a", file_type="pdf", file_size_bytes=100, version=1)
    resume_b = Resume(id=uuid.uuid4(), user_id=user_b_id, title="B v2", file_name="b.pdf", stored_path="b", file_type="pdf", file_size_bytes=100, version=2)
    sk = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    db_session.add_all([resume_a, resume_b, sk])
    db_session.flush()

    path_a = LearningPath(id=uuid.uuid4(), user_id=user_a_id, resume_id=resume_a.id, target_type="CAREER", title="Path A", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path_a)
    db_session.flush()

    item = LearningPathItem(id=uuid.uuid4(), learning_path_id=path_a.id, skill_id=sk.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=10.0)
    db_session.add(item)
    db_session.commit()

    # User A tries to pass User B's resume ID
    payload = {"resume_id": str(resume_b.id)}
    resp = client.post(f"/api/v1/learning-paths/{path_a.id}/reconcile", json=payload, headers=headers_a)
    assert resp.status_code == 404


def test_get_learning_path_returns_verification_metadata(client: TestClient, db_session: Session):
    """Test 14: Serialization integrity: GET /learning-paths/{id} returns verification provenance and version."""
    user_id, headers = create_user_and_token(client, "serialization@skillbridge.ai")

    resume_v1 = Resume(id=uuid.uuid4(), user_id=user_id, title="v1", file_name="v1.pdf", stored_path="v1", file_type="pdf", file_size_bytes=100, version=1)
    sk = Skill(id=uuid.uuid4(), name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
    db_session.add_all([resume_v1, sk])
    db_session.flush()

    path = LearningPath(id=uuid.uuid4(), user_id=user_id, resume_id=resume_v1.id, target_type="CAREER", title="Path", status="IN_PROGRESS", overall_progress_percentage=0.0)
    db_session.add(path)
    db_session.flush()

    item = LearningPathItem(id=uuid.uuid4(), learning_path_id=path.id, skill_id=sk.id, stage_order=1, sequence_in_stage=1, status="NOT_STARTED", estimated_hours=10.0)
    db_session.add(item)

    resume_v2 = Resume(id=uuid.uuid4(), user_id=user_id, title="v2", file_name="v2.pdf", stored_path="v2", file_type="pdf", file_size_bytes=100, version=2)
    db_session.add(resume_v2)
    db_session.flush()

    rs = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume_v2.id,
        skill_id=sk.id,
        raw_skill_text="FastAPI",
        canonical_skill_name="FastAPI",
        source_section="EXPERIENCE",
        evidence_sentence="Engineered performant backend microservices with FastAPI.",
        confidence=0.95,
        match_method="EXACT",
    )
    db_session.add(rs)
    db_session.commit()

    # Reconcile first
    reconcile_resp = client.post(f"/api/v1/learning-paths/{path.id}/reconcile", json={}, headers=headers)
    assert reconcile_resp.status_code == 200

    # Retrieve GET /learning-paths/{id}
    get_resp = client.get(f"/api/v1/learning-paths/{path.id}", headers=headers)
    assert get_resp.status_code == 200
    path_data = get_resp.json()

    verified_item = path_data["stages"][0]["items"][0]
    assert verified_item["status"] == "COMPLETED"
    assert verified_item["verified_by_resume_id"] == str(resume_v2.id)
    assert verified_item["verified_by_resume_version"] == 2
    assert verified_item["verification_method"] == "RESUME_EVIDENCE"
    assert verified_item["verified_at"] is not None
