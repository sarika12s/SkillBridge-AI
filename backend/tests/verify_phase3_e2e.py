"""End-to-End verification script for SkillBridge AI Phase 3:
Skill Extraction, Normalization & Taxonomy Integration.
"""

import sys
import uuid
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.resume import Resume, ResumeSection
from app.models.skill import Skill, SkillAlias, SkillRelationship, ResumeSkill
from app.data.seeders.seed_taxonomies import seed_taxonomies
from app.services.skill_service import SkillService
from app.ai.matching.vector_embedder import VectorEmbedder


def run_phase3_e2e_verification():
    print("=" * 70)
    print("Starting SkillBridge AI Phase 3 End-to-End Verification Pipeline")
    print("=" * 70)

    # 1. Setup isolated in-memory test database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    # Override FastAPI dependency
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 2. Seed Taxonomies & Generate Real 384-d Dense Embeddings
    print("\n[Step 1] Seeding ESCO, O*NET, Curated Aliases & Knowledge Graph Relationships...")
    summary = seed_taxonomies(db, generate_embeddings=True)
    print(f"  -> Canonical Skills Seeded: {summary['total_canonical_skills']}")
    print(f"  -> Curated Aliases Seeded: {summary['total_aliases']}")
    print(f"  -> Ontology Relationships Seeded: {summary['total_relationships']}")
    print(f"  -> 384-d Dense Vectors Generated: {summary['embeddings_generated']}")

    assert summary["total_canonical_skills"] == 38, f"Expected 38 canonical skills, got {summary['total_canonical_skills']}"
    assert summary["total_aliases"] >= 70, f"Expected >= 70 aliases, got {summary['total_aliases']}"
    assert summary["total_relationships"] == 40, f"Expected 40 relationships, got {summary['total_relationships']}"
    assert summary["embeddings_generated"] == 38, f"Expected 38 embeddings, got {summary['embeddings_generated']}"

    # 3. Verify Vector Embedder Properties
    print("\n[Step 2] Verifying 384-dimensional Dense Vector Embeddings...")
    embedder = VectorEmbedder()
    py_skill = db.query(Skill).filter(Skill.name == "Python").first()
    fastapi_skill = db.query(Skill).filter(Skill.name == "FastAPI").first()
    docker_skill = db.query(Skill).filter(Skill.name == "Docker").first()

    assert py_skill is not None and py_skill.embedding is not None
    assert len(py_skill.embedding) == 384, f"Expected 384 dims, got {len(py_skill.embedding)}"
    assert len(fastapi_skill.embedding) == 384
    assert len(docker_skill.embedding) == 384

    sim_py_fastapi = embedder.compute_cosine_similarity(py_skill.embedding, fastapi_skill.embedding)
    sim_py_docker = embedder.compute_cosine_similarity(py_skill.embedding, docker_skill.embedding)
    print(f"  -> Cosine Sim (Python <-> FastAPI): {sim_py_fastapi:.4f}")
    print(f"  -> Cosine Sim (Python <-> Docker):  {sim_py_docker:.4f}")
    assert sim_py_fastapi > sim_py_docker, "Expected Python to be semantically closer to FastAPI than Docker"

    # 4. Create Test Resume with Varied Technical Mentions & Evidence
    print("\n[Step 3] Creating Realistic Parsed Resume in Database...")
    user = User(
        id=uuid.uuid4(),
        email="candidate.ai@example.com",
        hashed_password="hash",
        full_name="Alex Rivera",
        role="student",
    )
    db.add(user)

    resume = Resume(
        id=uuid.uuid4(),
        user_id=user.id,
        title="Alex Rivera - Full Stack AI Resume",
        file_name="alex_rivera_resume.pdf",
        stored_path="storage/alex_rivera_resume.pdf",
        file_type="pdf",
        file_size_bytes=1048576,
        parsing_status="SUCCESS",
        extraction_method="TEXT",
        raw_text="Full Stack AI Engineer with experience in Python, React, and Cloud Systems.",
    )
    db.add(resume)

    sections = [
        ResumeSection(
            id=uuid.uuid4(),
            resume_id=resume.id,
            section_type="SKILLS",
            section_title="Technical Skills",
            content_text="Core Languages: Python 3, Java 17, TypeScript, C++20, SQL. Web: ReactJS, FastAPI, TailwindCSS.",
            order_index=0,
        ),
        ResumeSection(
            id=uuid.uuid4(),
            resume_id=resume.id,
            section_type="EXPERIENCE",
            section_title="Professional Experience",
            content_text="Architected distributed backend microservices on AWS Cloud using Docker and K8s. Configured automated CI/CD deployment pipelines with PostgreSQL and Redis caching.",
            order_index=1,
        ),
        ResumeSection(
            id=uuid.uuid4(),
            resume_id=resume.id,
            section_type="PROJECTS",
            section_title="Selected Projects",
            content_text="Developed an end-to-end NLP Question Answering platform using PyTorch and Scikit-learn.",
            order_index=2,
        ),
    ]
    db.add_all(sections)
    db.commit()

    # 5. Execute Skill Extraction & Persistence
    print("\n[Step 4] Running Skill Extraction & Normalization Service...")
    service = SkillService()
    extraction_result = service.extract_and_persist_resume_skills(resume_id=resume.id, db=db)
    print(f"  -> Total Skills Extracted & Normalized: {extraction_result.total_skills_extracted}")

    extracted_dict = {s.canonical_name: s for s in extraction_result.skills}

    # Verify key canonical mappings
    expected_mappings = [
        ("Python", "Python 3", "SYNONYM", "SKILLS"),
        ("Java", "Java 17", "SPELLING_VARIANT", "SKILLS"),
        ("TypeScript", "TypeScript", "EXACT", "SKILLS"),
        ("C++", "C++20", "SPELLING_VARIANT", "SKILLS"),
        ("SQL", "SQL", "EXACT", "SKILLS"),
        ("React", "ReactJS", "SYNONYM", "SKILLS"),
        ("FastAPI", "FastAPI", "EXACT", "SKILLS"),
        ("Tailwind CSS", "TailwindCSS", "SPELLING_VARIANT", "SKILLS"),
        ("Amazon Web Services", "AWS Cloud", "SYNONYM", "EXPERIENCE"),
        ("Docker", "Docker", "EXACT", "EXPERIENCE"),
        ("Kubernetes", "K8s", "ACRONYM", "EXPERIENCE"),
        ("CI/CD", "CI/CD", "EXACT", "EXPERIENCE"),
        ("PostgreSQL", "PostgreSQL", "EXACT", "EXPERIENCE"),
        ("Redis", "Redis", "EXACT", "EXPERIENCE"),
        ("Natural Language Processing", "NLP", "ACRONYM", "PROJECTS"),
        ("PyTorch", "PyTorch", "EXACT", "PROJECTS"),
        ("Scikit-learn", "Scikit-learn", "EXACT", "PROJECTS"),
    ]

    for canon, orig, method, sec in expected_mappings:
        assert canon in extracted_dict, f"Expected '{canon}' to be extracted"
        match = extracted_dict[canon]
        assert match.original_text == orig, f"Expected orig '{orig}', got '{match.original_text}' for {canon}"
        assert match.normalization_method == method, f"Expected method '{method}', got '{match.normalization_method}' for {canon}"
        assert match.source_section == sec, f"Expected section '{sec}', got '{match.source_section}' for {canon}"
        assert len(match.evidence_sentence) > 5, f"Missing evidence sentence for {canon}"
        print(f"  [OK] {canon:28} | '{orig:15}' -> {method:16} | Sec: {sec:12} | Conf: {match.confidence:.2f}")

    # 6. Verify Distinction Enforcement
    print("\n[Step 5] Verifying Strict Distinction Enforcement...")
    assert "JavaScript" not in extracted_dict, "False positive: Java 17 must not conflate with JavaScript!"
    assert "C" not in extracted_dict, "False positive: C++20 must not conflate with C!"
    assert "Microsoft Azure" not in extracted_dict, "False positive: AWS must not conflate with Azure!"
    print("  -> Distinction Verified: Java != JavaScript, C != C++, AWS != Azure.")

    # 7. Verify Database Persistence of ResumeSkill records
    print("\n[Step 6] Verifying Database Persistence of ResumeSkill...")
    persisted_rows = db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume.id).all()
    assert len(persisted_rows) == extraction_result.total_skills_extracted
    print(f"  -> Persisted ResumeSkill records in database: {len(persisted_rows)}")

    # 8. Test API Endpoints via TestClient
    print("\n[Step 7] Testing FastAPI Endpoints...")

    # GET /api/v1/resumes/{id}/skills
    res_skills = client.get(f"/api/v1/resumes/{resume.id}/skills")
    assert res_skills.status_code == 200, f"Failed GET resumes/{resume.id}/skills: {res_skills.text}"
    skills_json = res_skills.json()
    assert skills_json["total_skills_extracted"] == len(persisted_rows)
    print("  -> GET /api/v1/resumes/{id}/skills: 200 OK")

    # POST /api/v1/skills/extract/{resume_id}
    res_extract = client.post(f"/api/v1/skills/extract/{resume.id}")
    assert res_extract.status_code == 200, f"Failed POST skills/extract/{resume.id}: {res_extract.text}"
    print("  -> POST /api/v1/skills/extract/{resume_id}: 200 OK")

    # GET /api/v1/skills/{id}
    res_skill_detail = client.get(f"/api/v1/skills/{py_skill.id}")
    assert res_skill_detail.status_code == 200
    detail_data = res_skill_detail.json()
    assert detail_data["name"] == "Python"
    assert len(detail_data["aliases"]) >= 1
    assert detail_data["embedding_available"] is True
    print(f"  -> GET /api/v1/skills/{{id}} (Python): 200 OK (Aliases: {len(detail_data['aliases'])})")

    # GET /api/v1/skills/{id}/relationships
    res_rels = client.get(f"/api/v1/skills/{py_skill.id}/relationships")
    assert res_rels.status_code == 200
    rels_data = res_rels.json()
    assert len(rels_data) >= 1
    print(f"  -> GET /api/v1/skills/{{id}}/relationships (Python): 200 OK (Relationships: {len(rels_data)})")

    print("\n" + "=" * 70)
    print("ALL PHASE 3 END-TO-END VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_phase3_e2e_verification()
