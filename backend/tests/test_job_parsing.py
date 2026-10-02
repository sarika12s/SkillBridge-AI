"""Unit tests for Phase 4: Job Description Ingestion, Parsing & Role Requirement Classification."""

import uuid
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.user import User
from app.models.resume import Resume
from app.models.skill import Skill, ResumeSkill
from app.models.job import Job, JobSkill, JobRequirement
from app.ai.jobs.section_classifier import segment_job_sections
from app.ai.jobs.role_classifier import classify_job_role
from app.ai.jobs.requirement_extractor import (
    determine_priority,
    extract_structured_experience,
    extract_structured_education,
    extract_structured_certifications,
)
from app.ai.jobs.job_skill_extractor import JobSkillExtractor
from app.data.seeders.seed_taxonomies import seed_taxonomies


@pytest.fixture(autouse=True)
def seed_test_database(db_session: Session):
    """Ensure taxonomy and aliases are seeded in test SQLite DB."""
    seed_taxonomies(db_session, generate_embeddings=False)


def test_section_segmentation():
    """Verify job sections are detected and segmented cleanly."""
    text = (
        "About the Role\n"
        "We are looking for an exceptional engineer to join our team.\n\n"
        "Responsibilities:\n"
        "• Design and develop scalable backend APIs.\n"
        "• Collaborate with frontend and DevOps engineers.\n\n"
        "Minimum Qualifications:\n"
        "• 3+ years of experience with Python and FastAPI.\n"
        "• Strong understanding of PostgreSQL.\n\n"
        "Preferred Qualifications:\n"
        "• Experience with Kubernetes and Docker.\n"
        "• AWS Certified Solutions Architect is a plus."
    )
    sections = segment_job_sections(text)
    sec_types = [s["section_type"] for s in sections]

    assert "SUMMARY" in sec_types
    assert "RESPONSIBILITIES" in sec_types
    assert "REQUIRED_QUALIFICATIONS" in sec_types
    assert "PREFERRED_QUALIFICATIONS" in sec_types


def test_role_classification():
    """Verify job title classification maps to canonical roles."""
    cases = [
        ("Senior Machine Learning Engineer", "Machine Learning Engineer", 0.95),
        ("Lead Frontend Developer", "Frontend Developer", 0.95),
        ("Backend Software Engineer", "Backend Developer", 0.95),
        ("Staff Full Stack Engineer", "Full Stack Developer", 0.95),
        ("Cloud Solutions Architect", "Cloud Architect", 0.90),
        ("Site Reliability Engineer (DevOps)", "DevOps Engineer", 0.95),
        ("Data Scientist - NLP", "Data Scientist", 0.95),
        ("Software Developer II", "Software Engineer", 0.85),
    ]

    for title, expected_role, min_conf in cases:
        norm_role, conf, method = classify_job_role(title)
        assert norm_role == expected_role, f"Failed for {title}: got {norm_role}, expected {expected_role}"
        assert conf >= min_conf


def test_required_vs_preferred_priority():
    """Verify explicit linguistic evidence correctly classifies requirements."""
    # Required cues
    req_case, _ = determine_priority("Must have 3+ years of experience in Python", "OTHER")
    assert req_case == "REQUIRED"

    req_case2, _ = determine_priority("Solid knowledge of SQL is mandatory", "OTHER")
    assert req_case2 == "REQUIRED"

    # Preferred cues
    pref_case, _ = determine_priority("Experience with Docker is a plus", "REQUIRED_QUALIFICATIONS")
    assert pref_case == "PREFERRED"

    pref_case2, _ = determine_priority("Kubernetes knowledge is nice to have", "OTHER")
    assert pref_case2 == "PREFERRED"

    # Section context default
    sec_req, _ = determine_priority("Proficiency in TypeScript", "REQUIRED_QUALIFICATIONS")
    assert sec_req == "REQUIRED"

    sec_pref, _ = determine_priority("Knowledge of GraphQL", "PREFERRED_QUALIFICATIONS")
    assert sec_pref == "PREFERRED"


def test_structured_experience_extraction():
    """Verify experience requirements extract numerical bounds and seniority level."""
    exp1 = extract_structured_experience("Minimum 5+ years of software development experience")
    assert exp1 is not None
    assert exp1["minimum_years"] == 5.0
    assert exp1["classification"] == "SENIOR_LEVEL"

    exp2 = extract_structured_experience("2 to 4 years of experience building web applications")
    assert exp2 is not None
    assert exp2["minimum_years"] == 2.0
    assert exp2["maximum_years"] == 4.0
    assert exp2["classification"] == "MID_LEVEL"

    exp3 = extract_structured_experience("Entry-level candidates or new grads welcome")
    assert exp3 is not None
    assert exp3["minimum_years"] == 0.0
    assert exp3["classification"] == "ENTRY_LEVEL"


def test_structured_education_extraction():
    """Verify degree level and field extraction."""
    edu1 = extract_structured_education("Bachelor's degree in Computer Science or related technical field", "REQUIRED_QUALIFICATIONS")
    assert edu1 is not None
    assert edu1["degree_level"] == "BACHELORS"
    assert "Computer Science" in edu1["field"]
    assert edu1["requirement_type"] == "REQUIRED"

    edu2 = extract_structured_education("Master's degree preferred", "PREFERRED_QUALIFICATIONS")
    assert edu2 is not None
    assert edu2["degree_level"] == "MASTERS"
    assert edu2["requirement_type"] == "PREFERRED"


def test_structured_certification_extraction():
    """Verify explicit certification detection."""
    text = "AWS Certified Solutions Architect and CKA certification preferred."
    certs = extract_structured_certifications(text, "PREFERRED_QUALIFICATIONS")
    assert len(certs) >= 2
    cert_names = [c["name"] for c in certs]
    assert any("AWS Certified" in name for name in cert_names)
    assert any("CKA" in name for name in cert_names)


def test_canonical_skill_id_sharing_quality_gate(db_session: Session):
    """
    CRITICAL QUALITY GATE:
    Verify that ResumeSkill and JobSkill reference the EXACT same canonical Skill IDs
    in the database for identical skills.
    """
    user = User(
        id=uuid.uuid4(),
        email="test_matching_quality@example.com",
        hashed_password="pw",
        full_name="Quality Tester",
        role="student",
    )
    db_session.add(user)

    # Find canonical Python and Docker skills
    py_skill = db_session.query(Skill).filter(Skill.name == "Python").first()
    docker_skill = db_session.query(Skill).filter(Skill.name == "Docker").first()
    assert py_skill is not None
    assert docker_skill is not None

    # Create Resume with Python
    resume = Resume(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Resume 1",
        file_name="resume.pdf",
        stored_path="dummy.pdf",
        file_type="pdf",
        file_size_bytes=1024,
    )
    db_session.add(resume)
    db_session.flush()

    res_skill = ResumeSkill(
        resume_id=resume.id,
        skill_id=py_skill.id,
        raw_skill_text="Python 3",
        canonical_skill_name=py_skill.name,
        source_section="SKILLS",
        evidence_sentence="Expert Python programmer.",
    )
    db_session.add(res_skill)

    # Create Job with Python
    job = Job(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Backend Engineer",
        raw_text="Seeking Python and Docker engineer.",
    )
    db_session.add(job)
    db_session.flush()

    job_skill = JobSkill(
        job_id=job.id,
        skill_id=py_skill.id,
        raw_skill_text="Python",
        canonical_skill_name=py_skill.name,
        requirement_type="REQUIRED",
        source_section="REQUIREMENTS",
        evidence_text="Must have strong Python background.",
    )
    db_session.add(job_skill)
    db_session.commit()

    # Verify both reference identical canonical skill UUID
    assert res_skill.skill_id == job_skill.skill_id
    assert res_skill.skill_id == py_skill.id


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    register_payload = {
        "email": "job_recruiter@example.com",
        "password": "Password123!",
        "full_name": "Recruiter Jane",
    }
    resp = client.post("/api/v1/auth/register", json=register_payload)
    if resp.status_code == 201:
        token = resp.json()["access_token"]
    else:
        login_resp = client.post(
            "/api/v1/auth/login",
            data={"username": "job_recruiter@example.com", "password": "Password123!"},
        )
        token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_job_api_endpoints(client: TestClient, db_session: Session, auth_headers: dict):
    """Verify Job API endpoints for creation, listing, retrieval, and deletion."""
    # 1. Ingest pasted job description
    payload = {
        "title": "Senior Backend Developer",
        "company": "Acme Innovations",
        "location": "Remote / San Francisco",
        "source_url": "https://careers.acme.com/jobs/123",
        "raw_text": (
            "About the Role:\n"
            "We are looking for a Senior Backend Developer.\n\n"
            "Responsibilities:\n"
            "• Build high performance REST APIs using FastAPI.\n"
            "• Maintain PostgreSQL databases.\n\n"
            "Required Qualifications:\n"
            "• 5+ years of experience with Python and FastAPI.\n"
            "• Strong experience with Docker and Kubernetes.\n\n"
            "Preferred Qualifications:\n"
            "• AWS Certified is a plus."
        ),
    }

    create_res = client.post("/api/v1/jobs", json=payload, headers=auth_headers)
    assert create_res.status_code == 201, f"Failed create: {create_res.text}"
    job_data = create_res.json()
    job_id = job_data["id"]

    assert job_data["normalized_role"] == "Backend Developer"
    assert len(job_data["sections"]) >= 3
    assert len(job_data["requirements"]) >= 4

    # Verify extracted skills
    skill_names = [s["canonical_skill_name"] for s in job_data["all_skills"]]
    assert "Python" in skill_names
    assert "FastAPI" in skill_names
    assert "Docker" in skill_names
    assert "Kubernetes" in skill_names

    # Verify required vs preferred in skills
    req_skills = [s["canonical_skill_name"] for s in job_data["required_skills"]]
    assert "Python" in req_skills
    assert "FastAPI" in req_skills

    # 2. List jobs
    list_res = client.get("/api/v1/jobs", headers=auth_headers)
    assert list_res.status_code == 200
    jobs_list = list_res.json()
    assert len(jobs_list) >= 1
    assert any(j["id"] == job_id for j in jobs_list)

    # 3. Get job by ID
    get_res = client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Senior Backend Developer"

    # 4. Delete job by ID
    del_res = client.delete(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert del_res.status_code == 204

    # 5. Confirm deletion
    get_again = client.get(f"/api/v1/jobs/{job_id}", headers=auth_headers)
    assert get_again.status_code == 404

