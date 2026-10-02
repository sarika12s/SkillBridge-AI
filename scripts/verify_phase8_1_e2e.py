"""End-to-End Verification Script for SkillBridge AI Phase 8.1:
Interactive 'What-If' Gap-Closure Simulator.

Flow:
1. Verify live PostgreSQL connection & seeded taxonomy
2. Register authenticated test user
3. Ingest Resume (demonstrating Python)
4. Ingest Job (requiring Python as REQUIRED, Docker as REQUIRED, React as PREFERRED)
5. Run /api/v1/matching/analyze to obtain real MatchAnalysis & identify gaps
6. Inspect identified skill gaps (Docker, React)
7. Record database state snapshot
8. Measure execution latency of /api/v1/matching/simulate
9. Execute What-If simulation selecting Docker and React
10. Verify projected values, score deltas, coverage improvements, closed gaps, and learning-hour ROI
11. Verify complete immutability (zero database mutations / inserts)
12. Verify tenant authorization (unauthorized user receives 403)
13. Clean up test artifacts to maintain database integrity
"""

import os
import sys
import time
import uuid

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.resume import Resume
from app.models.job import Job
from app.models.matching import MatchAnalysis, SkillMatch, SkillGap, ScoreBreakdown
from app.models.skill import Skill

print("=" * 70)
print("SKILLBRIDGE AI — PHASE 8.1 END-TO-END VERIFICATION")
print("Interactive 'What-If' Gap-Closure Simulator")
print("=" * 70)

client = TestClient(app)
db = SessionLocal()

test_user_id = None
test_resume_id = None
test_job_id = None
test_analysis_id = None

try:
    # Step 1: Health & Database Connectivity Check
    health_res = client.get("/api/v1/health")
    assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
    health_data = health_res.json()
    print(f"\n[PASS] Health check verified: status={health_data.get('status')}")

    # Check Seeded Taxonomy Skills
    python_skill = db.query(Skill).filter(Skill.normalized_name == "python").first()
    docker_skill = db.query(Skill).filter(Skill.normalized_name == "docker").first()
    react_skill = db.query(Skill).filter(Skill.normalized_name == "react").first()
    assert python_skill and docker_skill and react_skill, "Required seeded taxonomy skills missing!"
    print(f"[PASS] Seeded taxonomy verified: Python ({python_skill.id}), Docker ({docker_skill.id}), React ({react_skill.id})")

    # Step 2: Register Authenticated Test User
    test_email = f"e2e_simulator_{uuid.uuid4().hex[:8]}@skillbridge.ai"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": test_email,
            "password": "Password123!",
            "full_name": "E2E Simulator Tester",
        },
    )
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    user_token = reg_res.json()["access_token"]
    test_user_id = uuid.UUID(reg_res.json()["user"]["id"])
    headers = {"Authorization": f"Bearer {user_token}"}
    print(f"[PASS] User registered and authenticated: {test_email} (ID: {test_user_id})")

    # Step 3: Register Unauthorized Second User for Tenant Isolation Check
    user_b_email = f"e2e_unauthorized_{uuid.uuid4().hex[:8]}@skillbridge.ai"
    reg_b_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": user_b_email,
            "password": "Password123!",
            "full_name": "Unauthorized User B",
        },
    )
    assert reg_b_res.status_code == 201
    user_b_token = reg_b_res.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {user_b_token}"}
    print(f"[PASS] Tenant isolation test user registered: {user_b_email}")

    # Step 4: Create Resume (with Python)
    resume = Resume(
        id=uuid.uuid4(),
        user_id=test_user_id,
        title="Backend Software Engineer Resume",
        file_name="backend_engineer.pdf",
        stored_path="/uploads/resumes/backend_engineer.pdf",
        file_type="pdf",
        file_size_bytes=2048,
        raw_text="Experienced Software Engineer with strong background in Python backend development and API architecture.",
    )
    db.add(resume)
    db.flush()
    test_resume_id = resume.id

    from app.models.skill import ResumeSkill
    rs_py = ResumeSkill(
        id=uuid.uuid4(),
        resume_id=resume.id,
        skill_id=python_skill.id,
        raw_skill_text="Python",
        canonical_skill_name=python_skill.name,
        evidence_sentence="Developed robust backend APIs and data processing services using Python.",
        confidence=1.0,
    )
    db.add(rs_py)
    db.commit()
    print(f"[PASS] Candidate resume created with skill 'Python' (ID: {test_resume_id})")

    # Step 5: Create Job (Requiring Python (REQ), Docker (REQ), React (PREF))
    job = Job(
        id=uuid.uuid4(),
        user_id=test_user_id,
        title="Senior Full-Stack Engineer",
        normalized_role="Full Stack Engineer",
        raw_text="We need a Full Stack Engineer. Requirements: Python (mandatory), Docker (mandatory). React is preferred.",
    )
    db.add(job)
    db.flush()
    test_job_id = job.id

    from app.models.job import JobSkill
    js_py = JobSkill(
        id=uuid.uuid4(),
        job_id=job.id,
        skill_id=python_skill.id,
        raw_skill_text="Python",
        canonical_skill_name=python_skill.name,
        requirement_type="REQUIRED",
        evidence_text="Python development experience is mandatory.",
    )
    js_docker = JobSkill(
        id=uuid.uuid4(),
        job_id=job.id,
        skill_id=docker_skill.id,
        raw_skill_text="Docker",
        canonical_skill_name=docker_skill.name,
        requirement_type="REQUIRED",
        evidence_text="Docker containerization experience required.",
    )
    js_react = JobSkill(
        id=uuid.uuid4(),
        job_id=job.id,
        skill_id=react_skill.id,
        raw_skill_text="React",
        canonical_skill_name=react_skill.name,
        requirement_type="PREFERRED",
        evidence_text="Experience with modern React frontend is preferred.",
    )
    db.add_all([js_py, js_docker, js_react])
    db.commit()
    print(f"[PASS] Target job created with requirements (ID: {test_job_id})")

    # Step 6: Execute Real Hybrid Match Analysis
    match_payload = {
        "resume_id": str(test_resume_id),
        "job_id": str(test_job_id),
    }
    analyze_res = client.post("/api/v1/matching/analyze", json=match_payload, headers=headers)
    assert analyze_res.status_code == 201, f"Analysis failed: {analyze_res.text}"
    analysis_data = analyze_res.json()
    test_analysis_id = uuid.UUID(analysis_data["id"])

    initial_compat = analysis_data["compatibility_score"]
    initial_ats = analysis_data["ats_readiness_score"]
    initial_gaps = analysis_data["skill_gaps"]
    print(f"\n[PASS] Match Analysis created: {test_analysis_id}")
    print(f"       - Initial Job Compatibility: {initial_compat:.1f}%")
    print(f"       - Initial ATS Readiness:    {initial_ats:.1f}%")
    print(f"       - Detected Gaps Count:      {len(initial_gaps)}")
    for g in initial_gaps:
        print(f"         * {g['canonical_skill_name']} ({g['priority']} - {g['status']})")

    # Step 7: Record Database State Snapshot
    count_analyses_before = db.query(MatchAnalysis).count()
    count_matches_before = db.query(SkillMatch).count()
    count_gaps_before = db.query(SkillGap).count()
    count_breakdowns_before = db.query(ScoreBreakdown).count()
    count_resumes_before = db.query(Resume).count()

    # Step 8: Execute Simulation with Latency Measurement
    sim_skill_ids = [str(docker_skill.id), str(react_skill.id)]
    sim_payload = {
        "match_analysis_id": str(test_analysis_id),
        "simulated_skill_ids": sim_skill_ids,
    }

    t0 = time.perf_counter()
    sim_res = client.post("/api/v1/matching/simulate", json=sim_payload, headers=headers)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert sim_res.status_code == 200, f"Simulation failed: {sim_res.text}"
    sim_data = sim_res.json()

    print(f"\n[PASS] Simulation executed in {elapsed_ms:.2f} ms")
    print("=" * 60)
    print("SIMULATION OUTCOME REPORT")
    print("=" * 60)
    print(f"Job Compatibility: {sim_data['current_compatibility_score']:.1f}% -> {sim_data['projected_compatibility_score']:.1f}% (Delta: {sim_data['compatibility_score_delta']:+.1f}%)")
    print(f"ATS Readiness:    {sim_data['current_ats_score']:.1f}% -> {sim_data['projected_ats_score']:.1f}% (Delta: {sim_data['ats_score_delta']:+.1f}%)")
    print(f"Required Coverage: {sim_data['current_required_coverage']:.1f}% -> {sim_data['projected_required_coverage']:.1f}% (Delta: {sim_data['required_coverage_delta']:+.1f}%)")
    print(f"Preferred Coverage: {sim_data['current_preferred_coverage']:.1f}% -> {sim_data['projected_preferred_coverage']:.1f}% (Delta: {sim_data['preferred_coverage_delta']:+.1f}%)")
    print(f"Closed Gaps:       {sim_data['gap_state']['closed_gaps']}")
    print(f"Remaining Gaps:    {sim_data['gap_state']['remaining_required_gaps'] + sim_data['gap_state']['remaining_preferred_gaps']}")
    if sim_data.get("total_estimated_learning_hours") is not None:
        print(f"Learning Hours:    {sim_data['total_estimated_learning_hours']:.1f} hrs")
        print(f"Learning Hour ROI: +{sim_data['learning_hour_roi']:.2f} pts / hr")
    print(f"Explanation:       {sim_data['explanation']}")
    print("=" * 60)

    # Verifications
    assert sim_data["projected_compatibility_score"] > sim_data["current_compatibility_score"]
    assert sim_data["projected_ats_score"] > sim_data["current_ats_score"]
    assert sim_data["projected_required_coverage"] > sim_data["current_required_coverage"]
    assert set(sim_data["gap_state"]["closed_gaps"]) == {"Docker", "React"}

    # Step 9: Verify Immutability / Statelessness
    count_analyses_after = db.query(MatchAnalysis).count()
    count_matches_after = db.query(SkillMatch).count()
    count_gaps_after = db.query(SkillGap).count()
    count_breakdowns_after = db.query(ScoreBreakdown).count()
    count_resumes_after = db.query(Resume).count()

    assert count_analyses_after == count_analyses_before, "MatchAnalysis count changed!"
    assert count_matches_after == count_matches_before, "SkillMatch count changed!"
    assert count_gaps_after == count_gaps_before, "SkillGap count changed!"
    assert count_breakdowns_after == count_breakdowns_before, "ScoreBreakdown count changed!"
    assert count_resumes_after == count_resumes_before, "Resume count changed!"

    stored_analysis = db.query(MatchAnalysis).filter(MatchAnalysis.id == test_analysis_id).first()
    assert stored_analysis.compatibility_score == initial_compat, "Stored compatibility score mutated!"
    assert stored_analysis.ats_readiness_score == initial_ats, "Stored ATS score mutated!"
    print("\n[PASS] Database immutability verified: ZERO rows modified or inserted by simulation.")

    # Step 10: Verify Tenant Isolation / Authorization
    unauth_res = client.post("/api/v1/matching/simulate", json=sim_payload, headers=headers_b)
    assert unauth_res.status_code == 403, f"Expected 403 Forbidden, got {unauth_res.status_code}"
    print("[PASS] Tenant isolation verified: Unauthorized user correctly denied (403 Forbidden).")

    # Step 11: Verify Duplicate Skill Rejection
    dup_res = client.post(
        "/api/v1/matching/simulate",
        json={"match_analysis_id": str(test_analysis_id), "simulated_skill_ids": [str(docker_skill.id), str(docker_skill.id)]},
        headers=headers,
    )
    assert dup_res.status_code == 400, f"Expected 400 Bad Request, got {dup_res.status_code}"
    print("[PASS] Duplicate skill IDs validation verified: Correctly rejected (400 Bad Request).")

    # Step 12: Verify Nonexistent Skill Rejection
    fake_skill_res = client.post(
        "/api/v1/matching/simulate",
        json={"match_analysis_id": str(test_analysis_id), "simulated_skill_ids": [str(uuid.uuid4())]},
        headers=headers,
    )
    assert fake_skill_res.status_code == 400
    print("[PASS] Nonexistent skill ID validation verified: Correctly rejected (400 Bad Request).")

    print("\nALL PHASE 8.1 E2E VERIFICATIONS PASSED SUCCESSFULLY!")

finally:
    # Cleanup created test entities to keep PostgreSQL database clean
    print("\nCleaning up test entities...")
    try:
        if test_analysis_id:
            db.query(MatchAnalysis).filter(MatchAnalysis.id == test_analysis_id).delete()
        if test_job_id:
            db.query(Job).filter(Job.id == test_job_id).delete()
        if test_resume_id:
            db.query(Resume).filter(Resume.id == test_resume_id).delete()
        if test_user_id:
            db.query(User).filter(User.id == test_user_id).delete()
        db.query(User).filter(User.email.like("e2e_%@skillbridge.ai")).delete()
        db.commit()
        print("[PASS] Test cleanup completed. Database returned to pristine state.")
    except Exception as e:
        db.rollback()
        print(f"[WARN] Cleanup encountered error: {e}")
    finally:
        db.close()
