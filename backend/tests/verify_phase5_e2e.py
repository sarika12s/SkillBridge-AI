"""End-to-End verification script for SkillBridge AI Phase 5:
Semantic Matching, Skill Gap Analysis & Explainable Scoring Engine.
"""

import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.resume import Resume, ResumeSection, ResumeExperience, ResumeCertification
from app.models.skill import Skill, SkillAlias, SkillRelationship, ResumeSkill
from app.models.job import (
    Job,
    JobSection,
    JobRequirement,
    JobSkill,
    JobExperienceRequirement,
    JobEducationRequirement,
    JobCertification,
)
from app.models.matching import (
    MatchAnalysis,
    SkillMatch,
    SkillGap,
    ScoreBreakdown,
)
from app.data.seeders.seed_taxonomies import seed_taxonomies
from app.ai.matching.matcher import SkillMatchingEngine


def run_phase5_e2e_verification():
    print("=" * 75)
    print("Starting SkillBridge AI Phase 5 End-to-End Verification Pipeline")
    print("=" * 75)

    # 1. Setup isolated in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 2. Seed ESCO, O*NET, Curated Aliases & Generate Dense Vector Embeddings
    print("\n[Step 1] Seeding ESCO, O*NET, Curated Aliases & Dense Embeddings...")
    seed_summary = seed_taxonomies(db, generate_embeddings=True)
    print(f"  -> Canonical Skills Seeded: {seed_summary['total_canonical_skills']}")
    print(f"  -> Curated Aliases Seeded: {seed_summary['total_aliases']}")

    # 3. Create & Authenticate Test User
    print("\n[Step 2] Authenticating Test User for API Access...")
    register_payload = {
        "email": "lead_ml_engineer@skillbridge.ai",
        "password": "Password123!",
        "full_name": "Lead ML Engineer",
    }
    reg_res = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201, f"User registration failed: {reg_res.text}"
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = uuid.UUID(reg_res.json()["user"]["id"])
    print("  -> Authenticated successfully with JWT Bearer token.")

    # 4. Fetch canonical skill IDs from database
    py_skill = db.query(Skill).filter(Skill.name == "Python").first()
    fastapi_skill = db.query(Skill).filter(Skill.name == "FastAPI").first()
    docker_skill = db.query(Skill).filter(Skill.name == "Docker").first()
    sql_skill = db.query(Skill).filter(Skill.name == "SQL").first()
    k8s_skill = db.query(Skill).filter(Skill.name == "Kubernetes").first()
    aws_skill = db.query(Skill).filter(Skill.name == "Amazon Web Services").first()
    react_skill = db.query(Skill).filter(Skill.name == "React").first()
    redis_skill = db.query(Skill).filter(Skill.name == "Redis").first()

    assert py_skill is not None, "Python canonical skill missing"
    assert docker_skill is not None, "Docker canonical skill missing"
    assert k8s_skill is not None, "Kubernetes canonical skill missing"
    assert redis_skill is not None, "Redis canonical skill missing"

    # 5. Create Candidate Resume (Senior Backend Engineer)
    print("\n[Step 3] Ingesting & Persisting Candidate Resume...")
    resume_id = uuid.uuid4()
    resume_record = Resume(
        id=resume_id,
        user_id=user_id,
        title="Senior Python Backend Resume",
        file_name="resume_jane_doe.pdf",
        stored_path="uploads/resume_jane_doe.pdf",
        file_type="pdf",
        file_size_bytes=2048,
        raw_text=(
            "Jane Doe - Senior Backend Engineer. 4 years of professional backend software development experience. "
            "Bachelor of Science in Computer Science. Proficient in Python, FastAPI, Docker, and SQL databases. "
            "AWS Certified Solutions Architect Associate."
        ),
    )
    db.add(resume_record)
    db.flush()

    # Add resume canonical skills
    r_skills_data = [
        (py_skill, "Python", "TECHNICAL_SKILLS", "4 years developing scalable REST APIs with Python."),
        (fastapi_skill, "FastAPI", "TECHNICAL_SKILLS", "Built microservices using FastAPI framework."),
        (docker_skill, "Docker", "TECHNICAL_SKILLS", "Containerized microservices using Docker."),
        (sql_skill, "SQL", "TECHNICAL_SKILLS", "Optimized complex SQL queries and relational schemas."),
        (aws_skill, "AWS", "TECHNICAL_SKILLS", "Deployed distributed systems to AWS Cloud."),
    ]
    for sk, raw_text, sec, evid in r_skills_data:
        r_sk = ResumeSkill(
            id=uuid.uuid4(),
            resume_id=resume_id,
            skill_id=sk.id,
            raw_skill_text=raw_text,
            canonical_skill_name=sk.name,
            source_section=sec,
            evidence_sentence=evid,
            confidence=1.0,
            match_method="EXACT",
        )
        db.add(r_sk)

    # Add experience and certification to resume
    db.add(ResumeExperience(
        id=uuid.uuid4(),
        resume_id=resume_id,
        company_name="Starlight Cloud Inc",
        job_title="Senior Backend Engineer",
        description="4 years of backend software engineering experience building microservices.",
    ))
    db.add(ResumeCertification(
        id=uuid.uuid4(),
        resume_id=resume_id,
        name="AWS Certified Solutions Architect",
    ))
    db.commit()
    print(f"  -> Resume Created: ID {resume_id} with 5 canonical skills, 4 yrs experience, AWS Certification.")

    # 6. Create Target Job Description
    print("\n[Step 4] Ingesting & Persisting Target Job Description...")
    job_id = uuid.uuid4()
    job_record = Job(
        id=job_id,
        user_id=user_id,
        title="Senior Backend Software Engineer",
        company="Nexis Systems",
        location="Remote",
        normalized_role="Backend Developer",
        raw_text="Seeking Senior Backend Software Engineer with Python, FastAPI, Docker, SQL, and Kubernetes.",
    )
    db.add(job_record)
    db.flush()

    # Job Skills: Python (REQUIRED), FastAPI (REQUIRED), Docker (REQUIRED), SQL (REQUIRED), Kubernetes (REQUIRED - MISSING!), React (PREFERRED - MISSING!)
    j_skills_data = [
        (py_skill, "Python", "REQUIRED", "Must have extensive Python development experience."),
        (fastapi_skill, "FastAPI", "REQUIRED", "Production FastAPI experience required."),
        (docker_skill, "Docker", "REQUIRED", "Docker containerization mandatory."),
        (sql_skill, "SQL", "REQUIRED", "Advanced SQL database proficiency required."),
        (k8s_skill, "Kubernetes", "REQUIRED", "Kubernetes cluster orchestration required."),
        (redis_skill, "Redis", "REQUIRED", "Redis in-memory caching experience required."),
        (react_skill, "React", "PREFERRED", "Knowledge of React is a plus for full-stack integration."),
    ]
    for sk, raw_text, priority, evid in j_skills_data:
        j_sk = JobSkill(
            id=uuid.uuid4(),
            job_id=job_id,
            skill_id=sk.id,
            raw_skill_text=raw_text,
            canonical_skill_name=sk.name,
            requirement_type=priority,
            source_section="REQUIRED_QUALIFICATIONS" if priority == "REQUIRED" else "PREFERRED_QUALIFICATIONS",
            evidence_text=evid,
            confidence=1.0,
        )
        db.add(j_sk)

    # Job Experience, Education, Certification requirements
    db.add(JobExperienceRequirement(
        id=uuid.uuid4(),
        job_id=job_id,
        minimum_years=4.0,
        classification="SENIOR_LEVEL",
        experience_text="4+ years of professional software engineering experience.",
    ))
    db.add(JobEducationRequirement(
        id=uuid.uuid4(),
        job_id=job_id,
        degree_level="BACHELORS",
        field="Computer Science",
        original_text="Bachelor of Science in Computer Science required.",
        requirement_type="REQUIRED",
    ))
    db.add(JobCertification(
        id=uuid.uuid4(),
        job_id=job_id,
        name="AWS Certified Solutions Architect",
        requirement_type="PREFERRED",
    ))
    db.commit()
    print(f"  -> Job Created: ID {job_id} with 5 REQUIRED skills (incl. Kubernetes) and 1 PREFERRED skill (React).")

    # 7. Check Quality Gate: Verify Shared Canonical Skill IDs
    print("\n[Step 5] Checking Quality Gate: Canonical Skill ID Alignment...")
    for sk in [py_skill, fastapi_skill, docker_skill, sql_skill]:
        r_entry = db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume_id, ResumeSkill.skill_id == sk.id).first()
        j_entry = db.query(JobSkill).filter(JobSkill.job_id == job_id, JobSkill.skill_id == sk.id).first()
        assert r_entry is not None and j_entry is not None
        assert r_entry.skill_id == j_entry.skill_id == sk.id
    print("  -> Quality Gate Passed: 100% canonical skill ID parity verified.")

    # 8. Execute Match Analysis via API
    print("\n[Step 6] Testing POST /api/v1/matching/analyze Endpoint...")
    match_payload = {
        "resume_id": str(resume_id),
        "job_id": str(job_id),
    }
    analyze_res = client.post("/api/v1/matching/analyze", json=match_payload, headers=headers)
    assert analyze_res.status_code == 201, f"Match analysis failed: {analyze_res.text}"
    analysis = analyze_res.json()
    analysis_id = analysis["id"]
    print(f"  -> Analysis Executed Successfully! Analysis ID: {analysis_id}")
    print(f"  -> Job Compatibility Score: {analysis['compatibility_score']:.1f}%")
    print(f"  -> SkillBridge ATS Readiness Score: {analysis['ats_readiness_score']:.1f}%")

    # 9. Verify Skill Matches & Gaps
    print("\n[Step 7] Verifying Skill Matches, Match Types & Gap Classifications...")
    matches = analysis["skill_matches"]
    gaps = analysis["skill_gaps"]

    match_dict = {m["canonical_skill_name"]: m for m in matches}

    # Verify DIRECT_MATCH on Python, FastAPI, Docker, SQL
    assert match_dict["Python"]["match_type"] == "DIRECT_MATCH"
    assert match_dict["Python"]["match_status"] == "MATCHED_REQUIRED"
    assert match_dict["FastAPI"]["match_type"] == "DIRECT_MATCH"
    assert match_dict["Docker"]["match_type"] == "DIRECT_MATCH"
    assert match_dict["SQL"]["match_type"] == "DIRECT_MATCH"
    print("  -> Direct Canonical Matches: Python, FastAPI, Docker, SQL verified.")

    # Verify RELATED_SUPPORT on Kubernetes (Docker on resume is a prerequisite/related)
    assert match_dict["Kubernetes"]["match_type"] == "RELATED_SUPPORT"
    assert match_dict["Kubernetes"]["match_status"] == "RELATED_SUPPORT"
    print("  -> Taxonomy Relationship: Kubernetes detected as RELATED_SUPPORT via Docker.")

    # Verify MISSING_REQUIRED on Redis
    assert match_dict["Redis"]["match_type"] == "NO_MATCH"
    assert match_dict["Redis"]["match_status"] == "MISSING_REQUIRED"
    print("  -> Missing Required Gap: Redis correctly flagged as MISSING_REQUIRED.")

    # Verify MISSING_PREFERRED on React
    assert match_dict["React"]["match_type"] == "NO_MATCH"
    assert match_dict["React"]["match_status"] == "MISSING_PREFERRED"
    print("  -> Missing Preferred Gap: React correctly flagged as MISSING_PREFERRED.")

    # Verify Gap List
    gap_skills = [g["canonical_skill_name"] for g in gaps]
    assert "Redis" in gap_skills
    assert "React" in gap_skills
    # Redis must have higher importance weight than React (2.0 vs 1.0)
    redis_gap = next(g for g in gaps if g["canonical_skill_name"] == "Redis")
    react_gap = next(g for g in gaps if g["canonical_skill_name"] == "React")
    assert redis_gap["importance_weight"] > react_gap["importance_weight"]
    print("  -> Gap Prioritization Verified: Redis (Weight 2.0) prioritized over React (Weight 1.0).")

    # 10. Verify Structured Alignment
    print("\n[Step 8] Verifying Experience, Education & Certification Alignment...")
    alignment = analysis["alignment"]
    print(f"  -> Experience Status: {alignment['experience_status']} ({alignment['experience_explanation']})")
    assert alignment["experience_status"] == "MEETS"
    assert alignment["resume_years"] == 4.0

    print(f"  -> Education Status: {alignment['education_status']} ({alignment['education_explanation']})")
    assert alignment["education_status"] == "MEETS"

    print(f"  -> Certification Status: {alignment['certification_status']} ({alignment['certification_explanation']})")
    assert alignment["certification_status"] == "MATCHED"

    # 11. Verify Explainability Engine Output
    print("\n[Step 9] Verifying Explainability Narrative and Factor Breakdown...")
    expl = analysis["explainability"]
    assert len(expl["strengths"]) >= 4, "Expected direct strengths identified"
    assert len(expl["critical_gaps"]) >= 1, "Expected Kubernetes critical gap identified"
    assert any("Kubernetes" in g for g in expl["critical_gaps"])
    assert analysis["summary_explanation"] is not None and len(analysis["summary_explanation"]) > 50
    print(f"  -> Summary Narrative: {analysis['summary_explanation'][:120]}...")

    # 12. Verify GET Endpoints & Persistence
    print("\n[Step 10] Testing GET Retrieval Endpoints...")
    # GET /api/v1/matching/{analysis_id}
    get_res = client.get(f"/api/v1/matching/{analysis_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == analysis_id
    print("  -> GET /matching/{analysis_id} verified.")

    # GET /api/v1/resumes/{resume_id}/jobs/{job_id}/match
    cached_match_res = client.get(f"/api/v1/resumes/{resume_id}/jobs/{job_id}/match", headers=headers)
    assert cached_match_res.status_code == 200
    assert cached_match_res.json()["id"] == analysis_id
    print("  -> GET /resumes/{resume_id}/jobs/{job_id}/match verified.")

    # GET /api/v1/resumes/{resume_id}/skill-gaps
    skill_gaps_res = client.get(f"/api/v1/resumes/{resume_id}/skill-gaps", headers=headers)
    assert skill_gaps_res.status_code == 200
    gaps_payload = skill_gaps_res.json()
    assert gaps_payload["total_gaps"] >= 2
    assert len(gaps_payload["required_gaps"]) >= 1
    assert len(gaps_payload["preferred_gaps"]) >= 1
    print("  -> GET /resumes/{resume_id}/skill-gaps verified.")

    # 13. Critical False-Positive Check
    print("\n[Step 11] Verifying Critical False-Positive Guards...")
    engine_matcher = SkillMatchingEngine()
    prohib_checks = [
        ("Java", "JavaScript"),
        ("React", "React Native"),
        ("Amazon Web Services", "Microsoft Azure"),
        ("SQL", "PostgreSQL"),
        ("TensorFlow", "PyTorch"),
    ]
    for c_a, c_b in prohib_checks:
        assert engine_matcher._is_strictly_prohibited_pair(c_a, c_b) is True
        assert engine_matcher._is_strictly_prohibited_pair(c_b, c_a) is True
    print("  -> All 5 domain false-positive guard pairs strictly prevented.")

    print("\n" + "=" * 75)
    print("ALL PHASE 5 END-TO-END VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    run_phase5_e2e_verification()
