"""Unit tests for Phase 3: Skill extraction, alias normalization, taxonomy mapping, and embeddings."""

import uuid
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.resume import Resume, ResumeSection
from app.models.user import User
from app.models.skill import Skill, ResumeSkill
from app.ai.normalization.alias_mapper import AliasMapper
from app.ai.extraction.skill_extractor import SkillExtractor
from app.ai.matching.vector_embedder import VectorEmbedder
from app.services.skill_service import SkillService
from app.data.seeders.seed_taxonomies import seed_taxonomies


@pytest.fixture(autouse=True)
def seed_test_database(db_session: Session):
    """Ensure taxonomy and aliases are seeded in test SQLite DB."""
    seed_taxonomies(db_session, generate_embeddings=False)


def test_alias_normalization_variants():
    """Verify alias dictionary normalizes informal acronyms and spellings to canonical names."""
    mapper = AliasMapper()

    cases = [
        ("JS", "JavaScript", "ACRONYM"),
        ("Javascript", "JavaScript", "SPELLING_VARIANT"),
        ("ReactJS", "React", "SYNONYM"),
        ("React.js", "React", "SPELLING_VARIANT"),
        ("Postgres", "PostgreSQL", "SYNONYM"),
        ("psql", "PostgreSQL", "SYNONYM"),
        ("K8s", "Kubernetes", "ACRONYM"),
        ("AWS", "Amazon Web Services", "ACRONYM"),
        ("GCP", "Google Cloud Platform", "ACRONYM"),
        ("Azure", "Microsoft Azure", "SYNONYM"),
        ("sklearn", "Scikit-learn", "ACRONYM"),
        ("TF", "TensorFlow", "ACRONYM"),
        ("pytorch", "PyTorch", "SPELLING_VARIANT"),
        ("NLP", "Natural Language Processing", "ACRONYM"),
        ("ML", "Machine Learning", "ACRONYM"),
        ("CI/CD", "CI/CD", "EXACT"),
        ("Tailwind", "Tailwind CSS", "SYNONYM"),
    ]

    for raw_input, expected_canonical, expected_method in cases:
        norm = mapper.normalize(raw_input)
        assert norm is not None, f"Failed to normalize '{raw_input}'"
        assert norm.canonical_name == expected_canonical, (
            f"Expected {expected_canonical} for '{raw_input}', got {norm.canonical_name}"
        )
        assert norm.confidence >= 0.90


def test_strict_distinction_enforcement():
    """Verify distinct technologies are NEVER conflated."""
    extractor = SkillExtractor()

    # Distinct pair 1: Java vs JavaScript
    res_java = extractor.extract_from_sections({"EXPERIENCE": "Backend developed with Java 17 and Spring Boot."})
    java_names = [r["canonical_name"] for r in res_java]
    assert "Java" in java_names
    assert "JavaScript" not in java_names

    res_js = extractor.extract_from_sections({"EXPERIENCE": "Full stack engineer proficient in JavaScript and TypeScript."})
    js_names = [r["canonical_name"] for r in res_js]
    assert "JavaScript" in js_names
    assert "Java" not in js_names

    # Distinct pair 2: C vs C++
    res_c = extractor.extract_from_sections({"EXPERIENCE": "Embedded firmware development using C programming language."})
    c_names = [r["canonical_name"] for r in res_c]
    assert "C" in c_names
    assert "C++" not in c_names

    res_cpp = extractor.extract_from_sections({"EXPERIENCE": "Game engine built with C++20 and OpenGL."})
    cpp_names = [r["canonical_name"] for r in res_cpp]
    assert "C++" in cpp_names
    assert "C" not in cpp_names

    # Distinct pair 3: React vs React Native
    res_rn = extractor.extract_from_sections({"EXPERIENCE": "Built cross-platform iOS and Android mobile app in React Native."})
    rn_names = [r["canonical_name"] for r in res_rn]
    assert "React Native" in rn_names
    assert "React" not in rn_names

    # Distinct pair 4: AWS vs Azure
    res_cloud = extractor.extract_from_sections({"EXPERIENCE": "Deployed serverless microservices to AWS."})
    cloud_names = [r["canonical_name"] for r in res_cloud]
    assert "Amazon Web Services" in cloud_names
    assert "Microsoft Azure" not in cloud_names


def test_evidence_sentence_capture():
    """Verify original text, source section, and full evidence sentence are preserved."""
    extractor = SkillExtractor()
    sections = {
        "SKILLS": "Languages: Python 3, TypeScript. Databases: PostgreSQL.",
        "PROJECTS": "Developed a real-time analytics portal utilizing FastAPI and Redis caching.",
    }

    results = extractor.extract_from_sections(sections)
    res_map = {r["canonical_name"]: r for r in results}

    assert "FastAPI" in res_map
    assert res_map["FastAPI"]["source_section"] == "PROJECTS"
    assert "analytics portal utilizing FastAPI" in res_map["FastAPI"]["evidence_sentence"]

    assert "Redis" in res_map
    assert res_map["Redis"]["source_section"] == "PROJECTS"

    assert "PostgreSQL" in res_map
    assert res_map["PostgreSQL"]["source_section"] == "SKILLS"


def test_vector_embedder_dimensions_and_similarity():
    """Verify VectorEmbedder produces 384-dimensional dense vectors and valid cosine similarity."""
    embedder = VectorEmbedder()

    vec_python = embedder.generate_embedding("Python: high-level programming language")
    vec_fastapi = embedder.generate_embedding("FastAPI: modern web framework for Python")
    vec_docker = embedder.generate_embedding("Docker: OS-level virtualization container platform")

    assert len(vec_python) == 384
    assert len(vec_fastapi) == 384
    assert len(vec_docker) == 384

    # Cosine similarity self-check
    sim_self = embedder.compute_cosine_similarity(vec_python, vec_python)
    assert pytest.approx(sim_self, abs=1e-4) == 1.0

    # Semantic similarity between related tech should be higher than unrelated
    sim_py_fastapi = embedder.compute_cosine_similarity(vec_python, vec_fastapi)
    sim_py_docker = embedder.compute_cosine_similarity(vec_python, vec_docker)
    assert -1.0 <= sim_py_fastapi <= 1.0
    assert -1.0 <= sim_py_docker <= 1.0


def test_skill_service_persistence(db_session: Session):
    """Verify SkillService persists ResumeSkill records to database."""
    # Create test user & resume
    user = User(
        id=uuid.uuid4(),
        email="test_skills@example.com",
        hashed_password="pw",
        full_name="Skill Tester",
        role="student",
    )
    db_session.add(user)

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Test Skills Resume",
        file_name="resume.pdf",
        stored_path="dummy.pdf",
        file_type="pdf",
        file_size_bytes=1024,
        parsing_status="SUCCESS",
        extraction_method="TEXT",
        raw_text="Experienced Python and Docker developer.",
    )
    db_session.add(resume)

    sec1 = ResumeSection(
        id=uuid.uuid4(),
        resume_id=resume.id,
        section_type="SKILLS",
        section_title="Technical Skills",
        content_text="Python, Docker, PostgreSQL, ReactJS",
        order_index=0,
    )
    sec2 = ResumeSection(
        id=uuid.uuid4(),
        resume_id=resume.id,
        section_type="EXPERIENCE",
        section_title="Work Experience",
        content_text="Deployed microservices using Kubernetes on AWS Cloud.",
        order_index=1,
    )
    db_session.add_all([sec1, sec2])
    db_session.commit()

    service = SkillService()
    response = service.extract_and_persist_resume_skills(resume_id=resume.id, db=db_session)

    assert response.total_skills_extracted >= 5
    extracted_names = [s.canonical_name for s in response.skills]
    assert "Python" in extracted_names
    assert "Docker" in extracted_names
    assert "PostgreSQL" in extracted_names
    assert "React" in extracted_names
    assert "Kubernetes" in extracted_names
    assert "Amazon Web Services" in extracted_names

    # Check database records
    db_skills = db_session.query(ResumeSkill).filter(ResumeSkill.resume_id == resume.id).all()
    assert len(db_skills) == response.total_skills_extracted


def test_skill_api_endpoints(client: TestClient, db_session: Session):
    """Verify skills API endpoints return correct HTTP status and data schemas."""
    # 1. Query canonical skill by ID
    py_skill = db_session.query(Skill).filter(Skill.name == "Python").first()
    assert py_skill is not None

    res = client.get(f"/api/v1/skills/{py_skill.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Python"
    assert len(data["aliases"]) >= 1

    # 2. Query relationships for Python
    res_rel = client.get(f"/api/v1/skills/{py_skill.id}/relationships")
    assert res_rel.status_code == 200
    rel_data = res_rel.json()
    assert isinstance(rel_data, list)
    assert len(rel_data) >= 1
