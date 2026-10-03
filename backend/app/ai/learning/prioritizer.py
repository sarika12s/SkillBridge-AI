"""Intelligent Skill Dependency & Roadmap Prioritization Engine for SkillBridge AI Phase 8.4.

A deterministic, explainable, compute-on-read mathematical prioritization engine designed
for students and freshers.
Evaluates:
  1. Role Criticality (RC, weight: 0.35)
  2. Dependency Leverage (DL, weight: 0.25)
  3. Gap Impact (GI, weight: 0.25)
  4. Learning Efficiency (LE, weight: 0.15)
Enforces a hard readiness gatekeeper (READY vs BLOCKED vs COMPLETED) and
a deterministic tie-breaking cascade.
Zero LLMs, zero non-deterministic components.
"""

from collections import deque
import math
from typing import Any, Dict, List, Optional, Set, Tuple


def clamp_score(value: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """Clamps a floating point score safely between min_val and max_val, preventing NaN and Inf."""
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return float(max(min_val, min(max_val, round(value, 2))))


def clamp_learning_hours(raw_hours: Optional[float] = None) -> float:
    """
    Resolves and clamps estimated learning hours to [4.0, 40.0].
    Precedence fallback: 6.0 hours.
    """
    if raw_hours is None or raw_hours <= 0.0 or math.isnan(raw_hours) or math.isinf(raw_hours):
        hours = 6.0
    else:
        hours = float(raw_hours)
    return float(min(40.0, max(4.0, round(hours, 2))))


def calculate_role_criticality(
    requirement_type: Optional[str] = "REQUIRED",
    importance_weight: Optional[float] = 1.0,
    is_implicit_prerequisite: bool = False,
    dependent_criticalities: Optional[List[float]] = None,
) -> float:
    """
    Calculates Role Criticality (RC) bounded in [0.0, 100.0].

    Rules:
    - JobSkill: REQUIRED = 100.0, PREFERRED = 50.0, UNKNOWN = 75.0.
    - OccupationSkill: min(100.0, base_criticality * importance_weight) where weight in [0.65, 1.0].
    - Implicit Prerequisite: max(dependent_criticalities) * 0.90 (inherits 90% of downstream demand).
    """
    if is_implicit_prerequisite and dependent_criticalities:
        max_dep = max(dependent_criticalities) if dependent_criticalities else 50.0
        return clamp_score(max_dep * 0.90)

    req_upper = (requirement_type or "REQUIRED").upper()
    if req_upper == "REQUIRED":
        base = 100.0
    elif req_upper == "PREFERRED":
        base = 50.0
    elif req_upper == "UNKNOWN":
        base = 75.0
    else:
        base = 60.0

    weight = float(importance_weight) if importance_weight is not None else 1.0
    weight = max(0.0, min(1.0, weight))
    return clamp_score(base * weight)


def calculate_gap_impact(
    match_status: Optional[str] = None,
    similarity_score: Optional[float] = None,
) -> float:
    """
    Calculates Gap Impact (GI) bounded in [0.0, 100.0].
    Measures candidate deficiency depth only (decoupled from role criticality to prevent double counting).

    Rules:
    - Complete deficiency (MISSING_REQUIRED, MISSING_PREFERRED): 100.0
    - Partial deficiency (PARTIAL_REQUIRED, PARTIAL_PREFERRED): 50.0
    - Supporting context (RELATED_SUPPORT): 25.0
    - Acquired (MATCHED_REQUIRED, MATCHED_PREFERRED): 0.0
    - UNCERTAIN / Fallback: 50.0 (conservative deficiency)
    - If similarity_score provided without match_status:
      < 0.70 -> 100.0, 0.70 <= sim < 0.85 -> 50.0, >= 0.85 -> 0.0.
    """
    if match_status:
        st = match_status.upper()
        if st in ("MISSING_REQUIRED", "MISSING_PREFERRED"):
            return 100.0
        if st in ("PARTIAL_REQUIRED", "PARTIAL_PREFERRED"):
            return 50.0
        if st == "RELATED_SUPPORT":
            return 25.0
        if st in ("MATCHED_REQUIRED", "MATCHED_PREFERRED"):
            return 0.0
        if st == "UNCERTAIN":
            return 50.0

    if similarity_score is not None:
        if similarity_score < 0.70:
            return 100.0
        if similarity_score < 0.85:
            return 50.0
        return 0.0

    # Default conservative deficiency for unanalyzed gaps
    return 50.0


def calculate_dependency_leverage(unlocked_count: int) -> float:
    """
    Calculates Dependency Leverage (DL) bounded in [0.0, 100.0].
    U = count of directly or transitively reachable target-relevant downstream skills
        that are currently unacquired.

    Formula:
        DL = 100.0 * (U / (U + 1.0))
        U=0 -> 0.0
        U=1 -> 50.0
        U=2 -> 66.67
        U=3 -> 75.0
        U=4 -> 80.0
    """
    u = max(0, int(unlocked_count))
    if u == 0:
        return 0.0
    dl = 100.0 * (float(u) / (float(u) + 1.0))
    return clamp_score(dl)


def calculate_learning_efficiency(
    delta_compatibility: float,
    estimated_hours: float,
    k_roi: float = 0.75,
) -> float:
    """
    Calculates Learning Efficiency (LE) bounded in [0.0, 100.0].
    Measures ROI: compatibility gain per unit of study time.

    Formula:
        Raw ROI = delta_compatibility / estimated_hours
        LE = 100.0 * (Raw ROI / (Raw ROI + k_roi))
    If delta_compatibility <= 0 or estimated_hours <= 0: return 0.0.
    """
    delta = float(delta_compatibility) if delta_compatibility is not None else 0.0
    hours = float(estimated_hours) if estimated_hours is not None else 0.0

    if delta <= 0.0 or hours <= 0.0:
        return 0.0

    raw_roi = delta / hours
    le = 100.0 * (raw_roi / (raw_roi + k_roi))
    return clamp_score(le)


def calculate_priority_score(
    role_criticality: float,
    dependency_leverage: float,
    gap_impact: float,
    learning_efficiency: float,
) -> float:
    """
    Calculates the combined PriorityScore bounded in [0.0, 100.0].

    Weights:
        PriorityScore = 0.35 * RC + 0.25 * DL + 0.25 * GI + 0.15 * LE
    """
    rc = clamp_score(role_criticality)
    dl = clamp_score(dependency_leverage)
    gi = clamp_score(gap_impact)
    le = clamp_score(learning_efficiency)

    score = (0.35 * rc) + (0.25 * dl) + (0.25 * gi) + (0.15 * le)
    return clamp_score(score)


def evaluate_readiness(
    skill_key: Any,
    direct_prerequisites: List[Any],
    satisfied_skill_keys: Set[Any],
    is_already_completed: bool = False,
) -> Tuple[str, List[Any], List[Any]]:
    """
    Determines readiness status under the hard gatekeeper rule.

    Returns:
        (readiness_status, unsatisfied_prerequisites, satisfied_prerequisites)
        readiness_status in {'COMPLETED', 'BLOCKED', 'READY'}

    Rules:
    - If already completed or in satisfied set: 'COMPLETED'
    - Otherwise, check all direct prerequisites:
        - If any prerequisite is unsatisfied: 'BLOCKED'
        - If all prerequisites are satisfied: 'READY'
    """
    if is_already_completed or skill_key in satisfied_skill_keys:
        return "COMPLETED", [], list(direct_prerequisites)

    unsatisfied = []
    satisfied = []

    for prereq in direct_prerequisites:
        if prereq in satisfied_skill_keys:
            satisfied.append(prereq)
        else:
            unsatisfied.append(prereq)

    if unsatisfied:
        return "BLOCKED", unsatisfied, satisfied
    return "READY", unsatisfied, satisfied


def find_downstream_unlocked_skills(
    skill_key: Any,
    prereq_to_dependents: Dict[Any, List[Any]],
    target_skill_keys: Set[Any],
    satisfied_skill_keys: Set[Any],
) -> List[Any]:
    """
    Executes a multi-hop BFS forward through the prerequisite graph (prereq -> dependent)
    to find all target-relevant downstream skills that are currently unacquired.

    Returns list of downstream unacquired target skill keys.
    """
    unlocked: List[Any] = []
    visited: Set[Any] = {skill_key}
    queue = deque([skill_key])

    while queue:
        curr = queue.popleft()
        for dep in prereq_to_dependents.get(curr, []):
            if dep not in visited:
                visited.add(dep)
                # If target-relevant and not satisfied, it is unlocked downstream
                if dep in target_skill_keys and dep not in satisfied_skill_keys:
                    unlocked.append(dep)
                queue.append(dep)

    return unlocked


def tie_break_key(item: Dict[str, Any]) -> Tuple[float, float, float, float, float, str]:
    """
    Constructs a sort key implementing the Phase 8.4 tie-breaking cascade.
    We sort in descending priority, so higher values come first.

    Sequence:
    1. Score bucket (quantized to 0.10 resolution so scores within 0.10 are treated as ties)
    2. Role Criticality (RC) descending
    3. Dependency Leverage (DL) descending
    4. Gap Impact (GI) descending
    5. Learning Hours ascending (negated for descending sort)
    6. Canonical skill name ascending (handled via inverted string or separate ordering)
    """
    raw_score = float(item.get("priority_score", 0.0))
    # Score bucket: round to 1 decimal place (0.10 window)
    score_bucket = round(raw_score, 1)

    rc = float(item.get("role_criticality", 0.0))
    dl = float(item.get("dependency_leverage", 0.0))
    gi = float(item.get("gap_impact", 0.0))
    # Lower hours should rank higher: negate hours
    hours = -float(item.get("estimated_hours", 6.0))
    name = str(item.get("skill_name", "")).lower()

    return (score_bucket, rc, dl, gi, hours, name)


def sort_prioritized_skills(
    skills: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Sorts prioritized skill records using the frozen Phase 8.4 tie-breaking sequence.
    Handles exact name tie-breaking safely in ascending alphabetical order.
    """
    def custom_sort_comparator(a: Dict[str, Any], b: Dict[str, Any]) -> int:
        score_diff = round(float(a.get("priority_score", 0.0)) - float(b.get("priority_score", 0.0)), 2)
        # Significant difference >= 0.10
        if abs(score_diff) >= 0.10:
            return 1 if score_diff > 0 else -1

        # Within 0.10 tie window:
        # 1. Higher Role Criticality
        rc_diff = round(float(a.get("role_criticality", 0.0)) - float(b.get("role_criticality", 0.0)), 2)
        if abs(rc_diff) >= 0.01:
            return 1 if rc_diff > 0 else -1

        # 2. Higher Dependency Leverage
        dl_diff = round(float(a.get("dependency_leverage", 0.0)) - float(b.get("dependency_leverage", 0.0)), 2)
        if abs(dl_diff) >= 0.01:
            return 1 if dl_diff > 0 else -1

        # 3. Higher Gap Impact
        gi_diff = round(float(a.get("gap_impact", 0.0)) - float(b.get("gap_impact", 0.0)), 2)
        if abs(gi_diff) >= 0.01:
            return 1 if gi_diff > 0 else -1

        # 4. Lower Estimated Hours (fewer hours ranks higher)
        h_diff = round(float(a.get("estimated_hours", 6.0)) - float(b.get("estimated_hours", 6.0)), 2)
        if abs(h_diff) >= 0.01:
            return -1 if h_diff > 0 else 1

        # 5. Canonical name ascending (A ranks before Z)
        name_a = str(a.get("skill_name", "")).lower()
        name_b = str(b.get("skill_name", "")).lower()
        if name_a < name_b:
            return 1
        elif name_a > name_b:
            return -1
        return 0

    from functools import cmp_to_key

    # Sort descending
    return sorted(skills, key=cmp_to_key(custom_sort_comparator), reverse=True)


def select_next_best_skill(
    prioritized_skills: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Selects the single Next Best Skill from the prioritized list.
    Enforces the Hard Readiness Gatekeeper:
    - Skill MUST be 'READY'.
    - Skill MUST NOT be 'COMPLETED'.
    - 'BLOCKED' skills are strictly excluded.
    Returns None if no uncompleted READY skills exist.
    """
    for skill in prioritized_skills:
        status = skill.get("status", "NOT_STARTED")
        readiness = skill.get("readiness_status", "BLOCKED")
        if readiness == "READY" and status != "COMPLETED":
            return skill
    return None


def generate_deterministic_explanation(
    skill_name: str,
    readiness_status: str,
    priority_score: float,
    role_criticality: float,
    downstream_unlocked_count: int,
    downstream_unlocked_names: List[str],
    estimated_hours: float,
    delta_compatibility: float,
    unsatisfied_prerequisites: List[str],
    is_implicit_prerequisite: bool,
) -> str:
    """Generates an explainable, student-friendly narrative explaining the recommendation."""
    if readiness_status == "COMPLETED":
        return f"Already completed or demonstrated on your resume. You have acquired {skill_name}."

    if readiness_status == "BLOCKED":
        prereqs_str = ", ".join(unsatisfied_prerequisites)
        return (
            f"Blocked by unsatisfied prerequisite{'s' if len(unsatisfied_prerequisites) > 1 else ''}: "
            f"{prereqs_str}. Master prerequisites first before starting {skill_name}."
        )

    # Readiness is READY
    parts = []
    if is_implicit_prerequisite:
        parts.append(
            f"Foundational prerequisite required for your target competencies (Priority {priority_score:.1f})."
        )
    else:
        crit_desc = "High role criticality" if role_criticality >= 80 else "Valuable skill"
        parts.append(f"Ready to learn now with {crit_desc.lower()} ({role_criticality:.1f}/100).")

    if downstream_unlocked_count > 0:
        names_str = ", ".join(downstream_unlocked_names[:3])
        if downstream_unlocked_count > 3:
            names_str += f" and {downstream_unlocked_count - 3} more"
        parts.append(
            f"Unlocks {downstream_unlocked_count} downstream skill{'s' if downstream_unlocked_count > 1 else ''} ({names_str})."
        )

    if delta_compatibility > 0:
        parts.append(
            f"Expected to boost your match compatibility by +{delta_compatibility:.1f}% (~{estimated_hours:.0f} hrs study)."
        )
    else:
        parts.append(f"Estimated effort: {estimated_hours:.0f} hours.")

    return " ".join(parts)
