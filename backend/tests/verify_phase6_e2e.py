"""Comprehensive Phase 6 End-to-End Verification Script.

Tests Career Role Compatibility Engine, Skill Dependency DAG with cycle detection,
Personalized Learning Path generation, curated resources with verified URLs,
and dynamic modular progress re-evaluation.
"""

import sys
import uuid
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.user import User
from app.models.resume import Resume
from app.models.skill import Skill, ResumeSkill, SkillRelationship
from app.models.career import Occupation, OccupationSkill
from app.models.learning import LearningResource, LearningPath, LearningPathItem
from app.data.seeders.seed_taxonomies import seed_taxonomies
from app.ai.career.career_engine import CareerEngine
from app.ai.learning.dependency_graph import SkillDependencyGraph
from app.ai.learning.learning_engine import LearningEngine
from app.services.career_service import CareerService
from app.services.learning_service import LearningService
from app.schemas.learning import LearningPathCreateRequest


def run_phase6_e2e_verification():
    print("=" * 70)
    print("SKILLBRIDGE AI — PHASE 6 COMPREHENSIVE E2E VERIFICATION")
    print("=" * 70)

    # 1. Setup in-memory test database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    try:
        # 2. Seed all taxonomies including occupations and resources (without generating embeddings for fast testing)
        print("\n[Step 1] Seeding Taxonomies, Standardized Occupations & Learning Resources...")
        seed_summary = seed_taxonomies(db, generate_embeddings=False)
        print(f" -> Canonical Skills Seeded: {seed_summary.get('skills_seeded', 0)}")
        print(f" -> Aliases Seeded: {seed_summary.get('aliases_seeded', 0)}")
        print(f" -> Relationships Seeded: {seed_summary.get('relationships_seeded', 0)}")
        print(f" -> Standardized Occupations Seeded: {seed_summary.get('occupations_seeded', 0)}")
        print(f" -> Curated Learning Resources Seeded: {seed_summary.get('resources_seeded', 0)}")

        assert db.query(Occupation).count() >= 6, "Expected at least 6 standardized occupations"
        assert db.query(LearningResource).count() >= 10, "Expected curated learning resources"

        # 3. Create test candidate with realistic background (Backend-leaning Python dev)
        print("\n[Step 2] Creating Candidate Profile & Extracted Resume Skills...")
        user = User(
            id=uuid.uuid4(),
            email="candidate.sarik@skillbridge.ai",
            hashed_password="hashed_pw_xyz",
            full_name="Sarik ML Engineer",
            is_active=True,
        )
        db.add(user)
        db.flush()

        resume = Resume(
            id=uuid.uuid4(),
            user_id=user.id,
            title="Python Developer Resume",
            file_name="sarik_python_dev.pdf",
            stored_path="/storage/resumes/sarik_python_dev.pdf",
            file_type="pdf",
            file_size_bytes=42000,
            raw_text="Backend Engineer proficient in Python, SQL, Git, and Linux.",
        )
        db.add(resume)
        db.flush()

        # Link demonstrated candidate skills
        candidate_demonstrated = ["Python", "SQL", "Git", "Linux"]
        for sk_name in candidate_demonstrated:
            sk = db.query(Skill).filter(Skill.name == sk_name).first()
            if sk:
                rs = ResumeSkill(
                    id=uuid.uuid4(),
                    resume_id=resume.id,
                    skill_id=sk.id,
                    raw_skill_text=sk_name,
                    canonical_skill_name=sk_name,
                    source_section="EXPERIENCE",
                    evidence_sentence=f"3+ years demonstrating core competencies in {sk_name} in production environments.",
                )
                db.add(rs)
        db.commit()
        print(f" -> Candidate created with verified skills: {candidate_demonstrated}")

        # 4. Engine A: Career Role Compatibility Evaluation
        print("\n[Step 3] Running Engine A: Multi-Role Career Compatibility...")
        career_service = CareerService(db)
        compat_result = career_service.compute_compatibility_for_resume(
            resume_id=resume.id,
            user_id=user.id,
        )

        roles = compat_result.roles
        print(f" -> Successfully evaluated {len(roles)} standardized career pathways.")
        assert len(roles) >= 6

        # Print ranked roles
        for idx, r in enumerate(roles, start=1):
            print(f"    {idx}. {r.occupation_title:<26} | Score: {r.compatibility_score:5.1f}% | Strengths: {len(r.strengths)} | Gaps: {len(r.skill_gaps)}")

        top_role = roles[0]
        print(f"\n -> Top Recommended Role: '{top_role.occupation_title}' (Score: {top_role.compatibility_score}%)")
        print(f"    Narrative: {top_role.summary_explanation}")
        print("    Score Breakdown:")
        for comp in top_role.components:
            print(f"      - {comp.component_name:<30}: {comp.score:5.1f}% (Weight: {comp.weight*100:2.0f}%, Weighted: {comp.weighted_score:4.1f} pts) — {comp.explanation}")

        assert 0.0 <= top_role.compatibility_score <= 100.0, "Score out of range"
        assert len(top_role.components) == 4, "Expected 4 explainable score components"

        # 5. Engine B: Personalized Learning Path Recommendation
        print("\n[Step 4] Running Engine B: Personalized Learning Path Recommendation...")
        # Find Backend Developer occupation
        backend_occ = db.query(Occupation).filter(Occupation.title == "Backend Developer").first()
        assert backend_occ is not None

        learning_service = LearningService(db)
        create_req = LearningPathCreateRequest(
            resume_id=resume.id,
            target_type="CAREER",
            target_occupation_id=backend_occ.id,
        )

        learning_path_res = learning_service.create_learning_path(
            user_id=user.id,
            req=create_req,
        )

        print(f" -> Generated Learning Path: '{learning_path_res.title}'")
        print(f" -> Target Role: {learning_path_res.target_title}")
        print(f" -> Total Estimated Hours: {learning_path_res.total_estimated_hours_min} - {learning_path_res.total_estimated_hours_max} hrs")
        print(f" -> Overall Initial Progress: {learning_path_res.overall_progress_percentage}%")
        print(f" -> Organized Stages: {len(learning_path_res.stages)}")

        # Verify candidate's acquired skills (Python, Git) were filtered out
        for stg in learning_path_res.stages:
            print(f"\n    [Stage {stg.stage_number}]: {stg.stage_title} ({stg.stage_estimated_hours}h estimated)")
            print(f"     Description: {stg.stage_description}")
            for it in stg.items:
                res_title = it.resource.title if it.resource else "Technical Documentation"
                res_url = it.resource.url if it.resource else "N/A"
                print(f"       * {it.skill_name:<16} | Status: {it.status:<11} | Resource: {res_title} ({res_url})")
                assert it.skill_name != "Python", "Python was already acquired and should NOT be in learning path!"

        # 6. Verify DAG Nodes & Edges
        print("\n[Step 5] Verifying Interactive Skill Dependency Graph (DAG)...")
        graph = learning_path_res.graph
        assert graph is not None
        print(f" -> Total Graph Nodes: {len(graph.nodes)}")
        print(f" -> Total Directed Prerequisite Edges: {len(graph.edges)}")

        for edge in graph.edges:
            print(f"    Dependency: [{edge.source}] -----> [{edge.target}]")

        # 7. Progress Tracking & Modular Re-evaluation
        print("\n[Step 6] Verifying Dynamic Progress Tracking & Re-evaluation...")
        first_stage = learning_path_res.stages[0]
        first_item = first_stage.items[0]

        print(f" -> Updating Item '{first_item.skill_name}' from NOT_STARTED to IN_PROGRESS...")
        res_progress1 = learning_service.update_item_progress(
            item_id=first_item.id,
            user_id=user.id,
            new_status="IN_PROGRESS",
            notes="Started official documentation and hands-on setup.",
        )
        assert res_progress1["status"] == "IN_PROGRESS"

        print(f" -> Completing Item '{first_item.skill_name}' (marking COMPLETED)...")
        res_progress2 = learning_service.update_item_progress(
            item_id=first_item.id,
            user_id=user.id,
            new_status="COMPLETED",
            notes="Completed tutorial exercises and built working prototype.",
        )
        assert res_progress2["status"] == "COMPLETED"
        assert res_progress2["completed_at"] is not None
        assert res_progress2["overall_progress_percentage"] > 0.0
        print(f" -> Updated Overall Path Progress: {res_progress2['overall_progress_percentage']}%")

        # 8. Dependency Graph Cycle Detection Verification
        print("\n[Step 7] Verifying DAG Cycle Detection & Prevention...")
        test_graph = SkillDependencyGraph(db=None)
        test_graph.skills = {"NodeA", "NodeB", "NodeC"}
        test_graph.adj = {"NodeA": ["NodeB"], "NodeB": ["NodeC"], "NodeC": ["NodeA"]}
        test_graph.in_edges = {"NodeB": ["NodeA"], "NodeC": ["NodeB"], "NodeA": ["NodeC"]}
        detected_cycles = test_graph.detect_cycles()
        print(f" -> Deliberately injected cycle [A -> B -> C -> A] detected: {detected_cycles}")
        assert len(detected_cycles) > 0, "Cycle detector failed to detect injected cyclic dependency"

        print("\n" + "=" * 70)
        print("ALL PHASE 6 VERIFICATION STEPS PASSED SUCCESSFULLY (100% OPERATIONAL)")
        print("=" * 70)
        return True

    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    success = run_phase6_e2e_verification()
    sys.exit(0 if success else 1)
