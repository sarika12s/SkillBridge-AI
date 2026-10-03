"""Unit tests for Phase 8.4 Mathematical Roadmap Prioritization Engine."""

import pytest
from app.ai.learning.prioritizer import (
    calculate_role_criticality,
    calculate_gap_impact,
    calculate_dependency_leverage,
    calculate_learning_efficiency,
    calculate_priority_score,
    evaluate_readiness,
    find_downstream_unlocked_skills,
    sort_prioritized_skills,
    select_next_best_skill,
    generate_deterministic_explanation,
    clamp_score,
    clamp_learning_hours,
)


def test_clamp_score():
    assert clamp_score(150.0) == 100.0
    assert clamp_score(-10.0) == 0.0
    assert clamp_score(45.678) == 45.68
    assert clamp_score(float("nan")) == 0.0
    assert clamp_score(float("inf")) == 0.0


def test_clamp_learning_hours():
    assert clamp_learning_hours(2.0) == 4.0
    assert clamp_learning_hours(4.0) == 4.0
    assert clamp_learning_hours(15.0) == 15.0
    assert clamp_learning_hours(40.0) == 40.0
    assert clamp_learning_hours(50.0) == 40.0
    assert clamp_learning_hours(None) == 6.0
    assert clamp_learning_hours(0.0) == 6.0
    assert clamp_learning_hours(-5.0) == 6.0


def test_role_criticality_job_skills():
    assert calculate_role_criticality("REQUIRED") == 100.0
    assert calculate_role_criticality("PREFERRED") == 50.0
    assert calculate_role_criticality("UNKNOWN") == 75.0
    assert calculate_role_criticality(None) == 100.0


def test_role_criticality_occupation_skills():
    # Weight scaling
    assert calculate_role_criticality("REQUIRED", importance_weight=0.85) == 85.0
    assert calculate_role_criticality("REQUIRED", importance_weight=1.0) == 100.0
    assert calculate_role_criticality("PREFERRED", importance_weight=0.80) == 40.0
    assert calculate_role_criticality("REQUIRED", importance_weight=0.65) == 65.0


def test_role_criticality_implicit_prerequisite_inheritance():
    # Inherits 90% of max dependent criticality
    dep_criticalities = [50.0, 100.0, 75.0]
    rc = calculate_role_criticality(
        is_implicit_prerequisite=True,
        dependent_criticalities=dep_criticalities,
    )
    assert rc == 90.0  # 100.0 * 0.90


def test_gap_impact_depth():
    assert calculate_gap_impact("MISSING_REQUIRED") == 100.0
    assert calculate_gap_impact("MISSING_PREFERRED") == 100.0
    assert calculate_gap_impact("PARTIAL_REQUIRED") == 50.0
    assert calculate_gap_impact("PARTIAL_PREFERRED") == 50.0
    assert calculate_gap_impact("RELATED_SUPPORT") == 25.0
    assert calculate_gap_impact("MATCHED_REQUIRED") == 0.0
    assert calculate_gap_impact("MATCHED_PREFERRED") == 0.0
    assert calculate_gap_impact("UNCERTAIN") == 50.0
    assert calculate_gap_impact(None) == 50.0

    # Similarity fallback
    assert calculate_gap_impact(similarity_score=0.45) == 100.0
    assert calculate_gap_impact(similarity_score=0.75) == 50.0
    assert calculate_gap_impact(similarity_score=0.90) == 0.0


def test_dependency_leverage():
    assert calculate_dependency_leverage(0) == 0.0
    assert calculate_dependency_leverage(1) == 50.0
    assert calculate_dependency_leverage(2) == 66.67
    assert calculate_dependency_leverage(3) == 75.0
    assert calculate_dependency_leverage(4) == 80.0
    assert calculate_dependency_leverage(-1) == 0.0


def test_learning_efficiency():
    # Raw ROI = delta / hours
    # If delta = 5.0, hours = 10.0 -> ROI = 0.5. With k_roi = 0.75:
    # LE = 100 * (0.5 / (0.5 + 0.75)) = 100 * (0.5 / 1.25) = 40.0
    assert calculate_learning_efficiency(5.0, 10.0) == 40.0

    # Edge cases
    assert calculate_learning_efficiency(0.0, 10.0) == 0.0
    assert calculate_learning_efficiency(-2.0, 10.0) == 0.0
    assert calculate_learning_efficiency(5.0, 0.0) == 0.0
    assert calculate_learning_efficiency(5.0, -4.0) == 0.0


def test_priority_score_formula():
    # RC=100.0, DL=50.0, GI=100.0, LE=40.0
    # Score = 0.35*100 + 0.25*50 + 0.25*100 + 0.15*40
    # = 35.0 + 12.5 + 25.0 + 6.0 = 78.5
    score = calculate_priority_score(
        role_criticality=100.0,
        dependency_leverage=50.0,
        gap_impact=100.0,
        learning_efficiency=40.0,
    )
    assert score == 78.5


def test_readiness_hard_gatekeeper():
    # Scenario 1: Already acquired or completed
    status, unsat, sat = evaluate_readiness(
        skill_key="Python",
        direct_prerequisites=[],
        satisfied_skill_keys={"Python"},
    )
    assert status == "COMPLETED"

    # Scenario 2: Direct prereq satisfied
    status, unsat, sat = evaluate_readiness(
        skill_key="FastAPI",
        direct_prerequisites=["Python"],
        satisfied_skill_keys={"Python"},
    )
    assert status == "READY"
    assert unsat == []
    assert sat == ["Python"]

    # Scenario 3: Direct prereq unsatisfied
    status, unsat, sat = evaluate_readiness(
        skill_key="FastAPI",
        direct_prerequisites=["Python"],
        satisfied_skill_keys=set(),
    )
    assert status == "BLOCKED"
    assert unsat == ["Python"]
    assert sat == []


def test_blocked_skill_loses_to_ready_skill_in_next_best_selection():
    # Invariant: A BLOCKED skill with score 99.0 MUST lose to a READY skill with score 60.0
    skills = [
        {
            "skill_id": "1",
            "skill_name": "Advanced Distributed Systems",
            "category": "TECHNICAL_SKILL",
            "priority_score": 99.0,
            "role_criticality": 100.0,
            "dependency_leverage": 80.0,
            "gap_impact": 100.0,
            "learning_efficiency": 90.0,
            "readiness_status": "BLOCKED",
            "status": "NOT_STARTED",
            "estimated_hours": 20.0,
            "delta_compatibility": 10.0,
            "downstream_unlocked_count": 4,
            "downstream_unlocked_skills": ["Raft", "Paxos"],
            "explanation": "Blocked by Distributed Theory",
            "is_implicit_prerequisite": False,
        },
        {
            "skill_id": "2",
            "skill_name": "Docker Basics",
            "category": "CLOUD_DEVOPS",
            "priority_score": 60.0,
            "role_criticality": 75.0,
            "dependency_leverage": 50.0,
            "gap_impact": 50.0,
            "learning_efficiency": 40.0,
            "readiness_status": "READY",
            "status": "NOT_STARTED",
            "estimated_hours": 6.0,
            "delta_compatibility": 3.0,
            "downstream_unlocked_count": 1,
            "downstream_unlocked_skills": ["Kubernetes"],
            "explanation": "Ready to learn now",
            "is_implicit_prerequisite": False,
        },
    ]

    sorted_skills = sort_prioritized_skills(skills)
    # The sorted list preserves ranking order by score
    assert sorted_skills[0]["skill_name"] == "Advanced Distributed Systems"

    # But the Next Best Skill selector strictly filters out BLOCKED skills
    next_best = select_next_best_skill(sorted_skills)
    assert next_best is not None
    assert next_best["skill_name"] == "Docker Basics"
    assert next_best["readiness_status"] == "READY"


def test_tie_breaking_cascade():
    # Two skills with identical priority_score (within 0.10)
    skill_a = {
        "skill_id": "1",
        "skill_name": "Alpha Skill",
        "priority_score": 75.05,
        "role_criticality": 90.0,
        "dependency_leverage": 66.67,
        "gap_impact": 100.0,
        "estimated_hours": 6.0,
        "readiness_status": "READY",
        "status": "NOT_STARTED",
    }
    skill_b = {
        "skill_id": "2",
        "skill_name": "Beta Skill",
        "priority_score": 75.00,
        "role_criticality": 80.0,
        "dependency_leverage": 66.67,
        "gap_impact": 100.0,
        "estimated_hours": 6.0,
        "readiness_status": "READY",
        "status": "NOT_STARTED",
    }
    # Within 0.10 diff -> Higher RC (90 vs 80) wins!
    sorted_res = sort_prioritized_skills([skill_b, skill_a])
    assert sorted_res[0]["skill_name"] == "Alpha Skill"

    # Same RC, higher DL wins
    skill_b["role_criticality"] = 90.0
    skill_b["dependency_leverage"] = 75.0
    sorted_res = sort_prioritized_skills([skill_a, skill_b])
    assert sorted_res[0]["skill_name"] == "Beta Skill"

    # Same RC, DL, higher GI wins
    skill_b["dependency_leverage"] = 66.67
    skill_a["gap_impact"] = 50.0
    skill_b["gap_impact"] = 100.0
    sorted_res = sort_prioritized_skills([skill_a, skill_b])
    assert sorted_res[0]["skill_name"] == "Beta Skill"

    # Same RC, DL, GI, lower hours wins
    skill_a["gap_impact"] = 100.0
    skill_a["estimated_hours"] = 4.0
    skill_b["estimated_hours"] = 8.0
    sorted_res = sort_prioritized_skills([skill_a, skill_b])
    assert sorted_res[0]["skill_name"] == "Alpha Skill"

    # All metrics equal -> alphabetical ascending wins
    skill_b["estimated_hours"] = 4.0
    sorted_res = sort_prioritized_skills([skill_b, skill_a])
    assert sorted_res[0]["skill_name"] == "Alpha Skill"


def test_multi_hop_bfs():
    # Graph: A -> B -> C -> D
    # Target skills: {B, C, D}
    # Satisfied skills: set()
    prereq_to_dependents = {
        "A": ["B"],
        "B": ["C"],
        "C": ["D"],
    }
    target_skills = {"B", "C", "D"}
    satisfied = set()

    unlocked_for_a = find_downstream_unlocked_skills("A", prereq_to_dependents, target_skills, satisfied)
    assert set(unlocked_for_a) == {"B", "C", "D"}
    assert len(unlocked_for_a) == 3

    unlocked_for_c = find_downstream_unlocked_skills("C", prereq_to_dependents, target_skills, satisfied)
    assert unlocked_for_c == ["D"]

    unlocked_for_d = find_downstream_unlocked_skills("D", prereq_to_dependents, target_skills, satisfied)
    assert unlocked_for_d == []


def test_cycle_safety():
    # Graph: A -> B -> A (cycle)
    prereq_to_dependents = {
        "A": ["B"],
        "B": ["A"],
    }
    target_skills = {"A", "B"}
    # Must terminate without infinite recursion
    unlocked = find_downstream_unlocked_skills("A", prereq_to_dependents, target_skills, set())
    assert "B" in unlocked


def test_deterministic_explanation_generation():
    expl_ready = generate_deterministic_explanation(
        skill_name="FastAPI",
        readiness_status="READY",
        priority_score=85.0,
        role_criticality=100.0,
        downstream_unlocked_count=2,
        downstream_unlocked_names=["Microservices", "Docker"],
        estimated_hours=6.0,
        delta_compatibility=4.5,
        unsatisfied_prerequisites=[],
        is_implicit_prerequisite=False,
    )
    assert "Ready to learn now" in expl_ready
    assert "Unlocks 2 downstream skills" in expl_ready
    assert "+4.5%" in expl_ready

    expl_blocked = generate_deterministic_explanation(
        skill_name="Kubernetes",
        readiness_status="BLOCKED",
        priority_score=70.0,
        role_criticality=75.0,
        downstream_unlocked_count=0,
        downstream_unlocked_names=[],
        estimated_hours=10.0,
        delta_compatibility=0.0,
        unsatisfied_prerequisites=["Docker", "Linux"],
        is_implicit_prerequisite=False,
    )
    assert "Blocked by unsatisfied prerequisites: Docker, Linux" in expl_blocked

    expl_completed = generate_deterministic_explanation(
        skill_name="Python",
        readiness_status="COMPLETED",
        priority_score=0.0,
        role_criticality=100.0,
        downstream_unlocked_count=0,
        downstream_unlocked_names=[],
        estimated_hours=6.0,
        delta_compatibility=0.0,
        unsatisfied_prerequisites=[],
        is_implicit_prerequisite=False,
    )
    assert "Already completed or demonstrated" in expl_completed
