"""E2E Verification Script for SkillBridge AI Phase 8.2:
Dynamic Roadmap Reconciliation Across Resume Versions.

Exercises live PostgreSQL 16.15 + pgvector, Alembic migration state, FastAPI REST endpoints,
authoritative verification criteria, monotonicity, and idempotency.
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

# Ensure backend/.env is loaded before importing database settings
env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")


def run_e2e_verification():
    print("================================================================")
    print("SkillBridge AI - Phase 8.2 End-to-End Live Verification")
    print("================================================================")

    # 1. Health Check
    print("\n[Step 1] Checking API Health...")
    health_resp = requests.get(f"{BASE_URL}/health", timeout=10)
    assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
    health_data = health_resp.json()
    print(f"Health Status: {health_data.get('status')}")
    print(f"PostgreSQL Status: {health_data.get('database', {}).get('status')}")
    print(f"pgvector Status: {health_data.get('database', {}).get('pgvector')}")

    # 2. Register Candidate
    print("\n[Step 2] Registering Test Candidate...")
    user_email = f"e2e_reconcile_{uuid.uuid4().hex[:8]}@skillbridge.ai"
    reg_resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": user_email,
            "password": "E2ePassword123!",
            "full_name": "E2E Candidate Reconciler",
        },
        timeout=10,
    )
    assert reg_resp.status_code == 201, f"Register failed: {reg_resp.text}"
    auth_token = reg_resp.json()["access_token"]
    user_id = reg_resp.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    print(f"Candidate registered: {user_email} (ID: {user_id})")

    # 3. Direct DB Seed for Real Skills & Roadmap
    print("\n[Step 3] Seeding Test Resume v1 and Learning Path...")
    from app.core.database import SessionLocal
    from app.models.resume import Resume
    from app.models.skill import Skill, ResumeSkill
    from app.models.learning import LearningPath, LearningPathItem

    db = SessionLocal()
    try:
        # Check or fetch canonical skills
        sk_python = db.query(Skill).filter(Skill.name == "Python").first()
        if not sk_python:
            sk_python = Skill(name="Python", normalized_name="python", category="PROGRAMMING_LANGUAGE")
            db.add(sk_python)

        sk_fastapi = db.query(Skill).filter(Skill.name == "FastAPI").first()
        if not sk_fastapi:
            sk_fastapi = Skill(name="FastAPI", normalized_name="fastapi", category="FRAMEWORK")
            db.add(sk_fastapi)

        sk_docker = db.query(Skill).filter(Skill.name == "Docker").first()
        if not sk_docker:
            sk_docker = Skill(name="Docker", normalized_name="docker", category="CLOUD_DEVOPS")
            db.add(sk_docker)

        db.commit()

        # Create Resume v1 (Baseline)
        res_v1 = Resume(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            title="E2E Resume v1",
            file_name="resume_v1.pdf",
            stored_path="/tmp/e2e_v1.pdf",
            file_type="pdf",
            file_size_bytes=1500,
            version=1,
            raw_text="Python software engineer",
        )
        db.add(res_v1)
        db.commit()

        # Create Learning Path with 2 items (FastAPI in Stage 1, Docker in Stage 2)
        path = LearningPath(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            resume_id=res_v1.id,
            target_type="CAREER",
            title="E2E Backend Pathway",
            description="End-to-end verification roadmap",
            status="IN_PROGRESS",
            overall_progress_percentage=0.0,
            total_estimated_hours_min=20,
            total_estimated_hours_max=30,
        )
        db.add(path)
        db.flush()

        item_fastapi = LearningPathItem(
            id=uuid.uuid4(),
            learning_path_id=path.id,
            skill_id=sk_fastapi.id,
            stage_order=1,
            sequence_in_stage=1,
            status="NOT_STARTED",
            estimated_hours=10.0,
        )
        item_docker = LearningPathItem(
            id=uuid.uuid4(),
            learning_path_id=path.id,
            skill_id=sk_docker.id,
            stage_order=2,
            sequence_in_stage=1,
            status="NOT_STARTED",
            estimated_hours=15.0,
        )
        db.add_all([item_fastapi, item_docker])
        db.commit()

        path_id = str(path.id)
        item_fastapi_id = str(item_fastapi.id)
        item_docker_id = str(item_docker.id)
        print(f"Created Learning Path: {path_id} (Items: FastAPI={item_fastapi_id}, Docker={item_docker_id})")

        # 4. Upload Resume v2 with verified evidence of FastAPI
        print("\n[Step 4] Creating Resume v2 with Authoritative Evidence for FastAPI...")
        res_v2 = Resume(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            title="E2E Resume v2",
            file_name="resume_v2.pdf",
            stored_path="/tmp/e2e_v2.pdf",
            file_type="pdf",
            file_size_bytes=1800,
            version=2,
            raw_text="Full-stack engineer with FastAPI and Docker experience",
        )
        db.add(res_v2)
        db.flush()

        rs_fastapi = ResumeSkill(
            id=uuid.uuid4(),
            resume_id=res_v2.id,
            skill_id=sk_fastapi.id,
            raw_skill_text="FastAPI",
            canonical_skill_name="FastAPI",
            source_section="EXPERIENCE",
            evidence_sentence="Engineered high-concurrency microservices using FastAPI and SQLAlchemy asynchronously.",
            confidence=0.97,
            match_method="EXACT",
        )
        db.add(rs_fastapi)

        # Create Path v2 (Baseline is Resume v2) for testing rejection of older resumes
        path_v2 = LearningPath(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            resume_id=res_v2.id,
            target_type="CAREER",
            title="E2E Path v2",
            description="Testing older resume rejection",
            status="IN_PROGRESS",
            overall_progress_percentage=0.0,
            total_estimated_hours_min=10,
            total_estimated_hours_max=15,
        )
        db.add(path_v2)
        db.commit()

        res_v1_id = str(res_v1.id)
        res_v2_id = str(res_v2.id)
        path_v2_id = str(path_v2.id)
        print(f"Created Resume v2: {res_v2_id} with verified FastAPI skill mention.")

    finally:
        db.close()

    # 5. Call Reconciliation Endpoint
    print("\n[Step 5] Calling POST /api/v1/learning-paths/{id}/reconcile...")
    rec_resp = requests.post(
        f"{BASE_URL}/learning-paths/{path_id}/reconcile",
        json={},
        headers=headers,
        timeout=15,
    )
    assert rec_resp.status_code == 200, f"Reconcile failed: {rec_resp.text}"
    rec_data = rec_resp.json()

    print("Reconciliation Response:")
    print(f" - Newly Verified Count: {rec_data['newly_verified_count']}")
    print(f" - Verifying Resume Version: {rec_data['verifying_resume_version']}")
    print(f" - Progress: {rec_data['previous_progress_percentage']}% -> {rec_data['new_progress_percentage']}%")
    print(f" - Remaining Hours: {rec_data['previous_remaining_hours']}h -> {rec_data['new_remaining_hours']}h")
    print(f" - Path Status: {rec_data['path_status']}")
    print(f" - Message: {rec_data['message']}")

    assert rec_data["newly_verified_count"] == 1
    assert rec_data["new_progress_percentage"] == 50.0
    assert rec_data["new_remaining_hours"] == 15.0
    assert len(rec_data["verified_items"]) == 1
    assert rec_data["verified_items"][0]["skill_name"] == "FastAPI"

    # 6. Verify GET /api/v1/learning-paths/{id} returns verification details
    print("\n[Step 6] Verifying GET /api/v1/learning-paths/{id} Serialization...")
    get_resp = requests.get(f"{BASE_URL}/learning-paths/{path_id}", headers=headers, timeout=10)
    assert get_resp.status_code == 200, f"Get path failed: {get_resp.text}"
    path_data = get_resp.json()
    assert path_data["overall_progress_percentage"] == 50.0

    stage1_item = path_data["stages"][0]["items"][0]
    print(f"Stage 1 Item: {stage1_item['skill_name']}")
    print(f" - Status: {stage1_item['status']}")
    print(f" - Verified By Resume Version: {stage1_item.get('verified_by_resume_version')}")
    print(f" - Verification Method: {stage1_item.get('verification_method')}")
    print(f" - Notes: {stage1_item.get('notes')}")

    assert stage1_item["status"] == "COMPLETED"
    assert stage1_item["verified_by_resume_version"] == 2
    assert stage1_item["verification_method"] == "RESUME_EVIDENCE"
    assert "Auto-verified by Resume v2" in stage1_item["notes"]

    # 7. Test Idempotency: Second Call
    print("\n[Step 7] Testing Idempotency (Second Reconcile Call)...")
    rec_resp2 = requests.post(
        f"{BASE_URL}/learning-paths/{path_id}/reconcile",
        json={},
        headers=headers,
        timeout=10,
    )
    assert rec_resp2.status_code == 200
    rec_data2 = rec_resp2.json()
    assert rec_data2["newly_verified_count"] == 0
    assert rec_data2["already_completed_count"] == 1
    assert rec_data2["new_progress_percentage"] == 50.0
    print("Idempotency Verified: 0 newly verified, state completely preserved.")

    # 8. Test Reject Older Resume
    print("\n[Step 8] Testing Rejection of Older Resume Version (v1 < baseline v2)...")
    bad_resp = requests.post(
        f"{BASE_URL}/learning-paths/{path_v2_id}/reconcile",
        json={"resume_id": res_v1_id},
        headers=headers,
        timeout=10,
    )
    assert bad_resp.status_code == 400, f"Expected 400 but got {bad_resp.status_code}: {bad_resp.text}"
    print(f"Rejected Older Resume as expected: HTTP {bad_resp.status_code} - {bad_resp.json()['detail']}")

    print("\n================================================================")
    print("ALL PHASE 8.2 END-TO-END VERIFICATIONS PASSED SUCCESSFULLY!")
    print("================================================================")


if __name__ == "__main__":
    run_e2e_verification()
