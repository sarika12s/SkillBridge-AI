"""End-to-End verification script for SkillBridge AI Phase 4:
Job Description Ingestion, Parsing & Role Requirement Classification.
"""
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import io
import uuid
import fitz
import docx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.resume import Resume
from app.models.skill import Skill, ResumeSkill
from app.models.job import (
    Job,
    JobSection,
    JobRequirement,
    JobSkill,
    JobExperienceRequirement,
    JobEducationRequirement,
    JobCertification,
)
from app.data.seeders.seed_taxonomies import seed_taxonomies


def create_in_memory_pdf(content: str) -> bytes:
    """Create in-memory valid text-based PDF using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(fitz.Point(40, 50), content)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_in_memory_docx(lines: list[tuple[str, int]]) -> bytes:
    """Create in-memory valid DOCX using python-docx."""
    doc = docx.Document()
    for text, level in lines:
        if level == 0:
            doc.add_paragraph(text)
        else:
            doc.add_heading(text, level=level)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def run_phase4_e2e_verification():
    print("=" * 75)
    print("Starting SkillBridge AI Phase 4 End-to-End Verification Pipeline")
    print("=" * 75)

    # 1. Setup isolated in-memory test database with StaticPool for thread-safe FastAPI TestClient
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

    # 2. Seed Taxonomies
    print("\n[Step 1] Seeding ESCO, O*NET, Curated Aliases & Generating Dense Embeddings...")
    seed_summary = seed_taxonomies(db, generate_embeddings=True)
    print(f"  -> Canonical Skills Seeded: {seed_summary['total_canonical_skills']}")
    print(f"  -> Curated Aliases Seeded: {seed_summary['total_aliases']}")

    # 3. Create & Authenticate User
    print("\n[Step 2] Authenticating Test User for API Access...")
    register_payload = {
        "email": "hiring_manager@enterprise.ai",
        "password": "Password123!",
        "full_name": "Hiring Manager",
    }
    reg_res = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201, f"User registration failed: {reg_res.text}"
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    user_id = uuid.UUID(reg_res.json()["user"]["id"])
    print("  -> Authenticated successfully with JWT Bearer token.")

    # 4. Ingest Pasted Job Description
    print("\n[Step 3] Testing Pasted Job Description Ingestion...")
    pasted_text = (
        "About the Role:\n"
        "We are seeking a Senior Backend Software Engineer to lead the design and implementation "
        "of our next-generation cloud services and distributed data systems.\n\n"
        "Responsibilities:\n"
        "• Design, build, and maintain robust, high-performance REST APIs using FastAPI and Python.\n"
        "• Architect distributed microservices deployed via Docker and Kubernetes on AWS Cloud.\n"
        "• Optimize PostgreSQL relational databases and Redis caching layers.\n"
        "• Collaborate with cross-functional teams to deliver scalable product features.\n\n"
        "Minimum Qualifications:\n"
        "• 4+ years of professional software engineering experience.\n"
        "• Bachelor's degree in Computer Science, Software Engineering, or equivalent practical experience.\n"
        "• Strong proficiency in Python, FastAPI, and SQL.\n"
        "• Solid hands-on experience with Docker containerization and CI/CD pipelines.\n\n"
        "Preferred Qualifications:\n"
        "• Experience with Kubernetes orchestration.\n"
        "• Knowledge of ReactJS and TypeScript for full-stack integration.\n"
        "• AWS Certified Solutions Architect is a plus."
    )

    pasted_payload = {
        "title": "Senior Backend Software Engineer",
        "company": "Starlight Cloud Networks",
        "location": "San Francisco, CA / Remote",
        "source_url": "https://careers.starlight.io/jobs/backend-sr-902",
        "raw_text": pasted_text,
    }

    res_pasted = client.post("/api/v1/jobs", json=pasted_payload, headers=headers)
    assert res_pasted.status_code == 201, f"Failed pasted job ingestion: {res_pasted.text}"
    pasted_job = res_pasted.json()
    job_id = pasted_job["id"]

    print(f"  -> Ingestion Succeeded! Job ID: {job_id}")
    print(f"  -> Title: '{pasted_job['title']}'")
    print(f"  -> Normalized Role: '{pasted_job['normalized_role']}' (Confidence: {pasted_job['role_confidence']:.2f}, Method: {pasted_job['role_classification_method']})")
    assert pasted_job["normalized_role"] == "Backend Developer"

    # 5. Verify Section Segmentation
    print("\n[Step 4] Verifying Section Segmentation...")
    sec_types = [s["section_type"] for s in pasted_job["sections"]]
    print(f"  -> Detected Sections: {sec_types}")
    assert "SUMMARY" in sec_types
    assert "RESPONSIBILITIES" in sec_types
    assert "REQUIRED_QUALIFICATIONS" in sec_types
    assert "PREFERRED_QUALIFICATIONS" in sec_types

    # 6. Verify Requirements & Category Classification
    print("\n[Step 5] Verifying Granular Requirement Categorization & Priority...")
    reqs = pasted_job["requirements"]
    print(f"  -> Total Requirements Extracted: {len(reqs)}")
    assert len(reqs) >= 8

    req_categories = set(r["requirement_category"] for r in reqs)
    print(f"  -> Extracted Requirement Categories: {sorted(list(req_categories))}")
    assert "RESPONSIBILITY" in req_categories
    assert "EXPERIENCE" in req_categories
    assert "EDUCATION" in req_categories
    assert "SKILL" in req_categories

    # 7. Verify Required vs Preferred Classification
    print("\n[Step 6] Verifying Required vs. Preferred Skill Classification...")
    required_skills = [s["canonical_skill_name"] for s in pasted_job["required_skills"]]
    preferred_skills = [s["canonical_skill_name"] for s in pasted_job["preferred_skills"]]
    print(f"  -> Required Skills ({len(required_skills)}): {required_skills}")
    print(f"  -> Preferred Skills ({len(preferred_skills)}): {preferred_skills}")

    assert "Python" in required_skills
    assert "FastAPI" in required_skills
    assert "Docker" in required_skills
    assert "CI/CD" in required_skills

    assert "Kubernetes" in preferred_skills
    assert "React" in preferred_skills
    assert "TypeScript" in preferred_skills

    # 8. Verify Structured Experience & Education Extraction
    print("\n[Step 7] Verifying Structured Experience & Education Entity Extraction...")
    exp_reqs = pasted_job["experience_requirements"]
    assert len(exp_reqs) >= 1
    print(f"  -> Minimum Experience Years: {exp_reqs[0]['minimum_years']} (Classification: {exp_reqs[0]['classification']})")
    assert exp_reqs[0]["minimum_years"] == 4.0
    assert exp_reqs[0]["classification"] == "MID_LEVEL"

    edu_reqs = pasted_job["education_requirements"]
    assert len(edu_reqs) >= 1
    print(f"  -> Degree Level: {edu_reqs[0]['degree_level']} (Field: {edu_reqs[0]['field']}, Priority: {edu_reqs[0]['requirement_type']})")
    assert edu_reqs[0]["degree_level"] == "BACHELORS"
    assert "Computer Science" in edu_reqs[0]["field"]
    assert edu_reqs[0]["requirement_type"] == "REQUIRED"

    cert_reqs = pasted_job["certifications"]
    assert len(cert_reqs) >= 1
    print(f"  -> Detected Certification: '{cert_reqs[0]['name']}' (Priority: {cert_reqs[0]['requirement_type']})")
    assert "AWS Certified" in cert_reqs[0]["name"]
    assert cert_reqs[0]["requirement_type"] == "PREFERRED"

    # 9. CRITICAL QUALITY GATE: Unified Canonical Skill ID Matching
    print("\n[Step 8] Checking Quality Gate: Unified Canonical Skill ID Sharing between Resumes and Jobs...")
    # Create test resume with Python and Docker
    test_resume = Resume(
        id=uuid.uuid4(),
        user_id=user_id,
        title="Candidate Alex Resume",
        file_name="alex_resume.pdf",
        stored_path="dummy.pdf",
        file_type="pdf",
        file_size_bytes=1024,
    )
    db.add(test_resume)
    db.flush()

    py_skill = db.query(Skill).filter(Skill.name == "Python").first()
    res_py = ResumeSkill(
        resume_id=test_resume.id,
        skill_id=py_skill.id,
        raw_skill_text="Python 3",
        canonical_skill_name=py_skill.name,
        source_section="SKILLS",
        evidence_sentence="Expert Python engineer.",
    )
    db.add(res_py)
    db.commit()

    # Find the JobSkill for Python from the ingested job
    job_py_skill = db.query(JobSkill).filter(
        JobSkill.job_id == uuid.UUID(job_id),
        JobSkill.canonical_skill_name == "Python",
    ).first()

    assert job_py_skill is not None, "Python job skill not found in DB"
    assert job_py_skill.skill_id == res_py.skill_id == py_skill.id, (
        f"Quality Gate Failed: Job skill ID {job_py_skill.skill_id} does not match Resume skill ID {res_py.skill_id}!"
    )
    print(f"  [PASS] Resume Skill ID == Job Skill ID == Canonical Skill ID: {py_skill.id}")

    # 10. Test PDF Job Ingestion
    print("\n[Step 9] Testing PDF Job Description File Upload...")
    pdf_text = (
        "Role: Machine Learning Engineer\n\n"
        "About the Job:\n"
        "Join our AI lab developing cutting-edge deep learning systems.\n\n"
        "Requirements:\n"
        "• 3+ years of experience with PyTorch and Python.\n"
        "• Solid background in Natural Language Processing.\n\n"
        "Nice to Have:\n"
        "• Experience deploying models with Docker on Google Cloud Platform."
    )
    pdf_bytes = create_in_memory_pdf(pdf_text)
    files = {"file": ("job_posting.pdf", pdf_bytes, "application/pdf")}
    data = {"title": "Machine Learning Engineer", "company": "DeepAI Corp"}

    res_pdf = client.post("/api/v1/jobs/upload", files=files, data=data, headers=headers)
    assert res_pdf.status_code == 201, f"Failed PDF job upload: {res_pdf.text}"
    pdf_job = res_pdf.json()
    assert pdf_job["ingestion_type"] == "PDF"
    assert pdf_job["normalized_role"] == "Machine Learning Engineer"
    pdf_skills = [s["canonical_skill_name"] for s in pdf_job["all_skills"]]
    assert "PyTorch" in pdf_skills
    assert "Natural Language Processing" in pdf_skills
    print(f"  -> PDF Upload Succeeded! Role: {pdf_job['normalized_role']}, Skills Detected: {pdf_skills}")

    # 11. Test DOCX Job Ingestion
    print("\n[Step 10] Testing DOCX Job Description File Upload...")
    docx_lines = [
        ("Frontend Developer", 1),
        ("About the Company", 2),
        ("We are a fast-growing digital agency.", 0),
        ("Responsibilities", 2),
        ("Build responsive modern web applications.", 0),
        ("Requirements", 2),
        ("• Minimum 2 years of experience with React and TypeScript.", 0),
        ("• Strong proficiency in Tailwind CSS and HTML.", 0),
    ]
    docx_bytes = create_in_memory_docx(docx_lines)
    docx_files = {"file": ("frontend_job.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    docx_data = {"title": "Frontend Web Developer", "company": "Creative UI Labs"}

    res_docx = client.post("/api/v1/jobs/upload", files=docx_files, data=docx_data, headers=headers)
    assert res_docx.status_code == 201, f"Failed DOCX job upload: {res_docx.text}"
    docx_job = res_docx.json()
    assert docx_job["ingestion_type"] == "DOCX"
    assert docx_job["normalized_role"] == "Frontend Developer"
    docx_skills = [s["canonical_skill_name"] for s in docx_job["all_skills"]]
    assert "React" in docx_skills
    assert "TypeScript" in docx_skills
    assert "Tailwind CSS" in docx_skills
    print(f"  -> DOCX Upload Succeeded! Role: {docx_job['normalized_role']}, Skills Detected: {docx_skills}")

    # 12. Test Listing and Deletion
    print("\n[Step 11] Verifying Jobs Listing and Deletion Endpoints...")
    res_list = client.get("/api/v1/jobs", headers=headers)
    assert res_list.status_code == 200
    all_user_jobs = res_list.json()
    assert len(all_user_jobs) == 3  # Pasted + PDF + DOCX
    print(f"  -> GET /api/v1/jobs returned {len(all_user_jobs)} ingested jobs.")

    # Delete the pasted job
    res_del = client.delete(f"/api/v1/jobs/{job_id}", headers=headers)
    assert res_del.status_code == 204
    res_get_deleted = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
    assert res_get_deleted.status_code == 404
    print("  -> DELETE /api/v1/jobs/{id} successfully cascaded and removed the job.")

    print("\n" + "=" * 75)
    print("ALL PHASE 4 END-TO-END VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    run_phase4_e2e_verification()
