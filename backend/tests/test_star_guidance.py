"""Deterministic Unit Test Suite for SkillBridge AI Phase 8.3:
STAR Resume Guidance Analyzer.

Covers:
A. Complete STAR bullet
B. Action + Result
C. Missing Result
D. Missing Action
E. Missing Situation
F. Missing Task
G. Empty input & whitespace
H. Short fragments & punctuation
I. Technical project bullet
J. Multiple component detection
K. Percentage result
L. Multiplier result
M. Scale/volume result
N. Currency result
O. Latency/time result
P. Year false-positive protection
Q. Date-range false-positive protection
R. Technology-version false-positive protection
S. GPA false-positive protection
T. Generic isolated number false-positive protection
U. Task phrase detection
V. Situation phrase detection
W. Technical action verb detection
X. Deterministic repeated execution
Y. Approved heuristic weights & exact score calculations
Z. Formatting, bullet glyphs, and Unicode normalization
"""

import pytest
from app.ai.guidance.star_analyzer import (
    STARAnalyzer,
    ComponentAnalysis,
    BulletAnalysisResult,
    WEIGHT_ACTION,
    WEIGHT_RESULT,
    WEIGHT_TASK,
    WEIGHT_SITUATION,
)


@pytest.fixture
def analyzer() -> STARAnalyzer:
    """Provides a fresh instance of STARAnalyzer for testing."""
    return STARAnalyzer()


# =========================================================================
# 1. Structural Component & Scenario Tests (A - J)
# =========================================================================

def test_complete_star_bullet(analyzer: STARAnalyzer):
    """Scenario A & J: Complete STAR bullet with all four components present."""
    text = (
        "In a high-volume microservices environment, tasked with reducing latency, "
        "architected an asynchronous caching layer with Redis, reducing response times by 40% for 50k users."
    )
    result = analyzer.analyze_bullet(text)

    assert result.situation.detected is True
    assert result.task.detected is True
    assert result.action.detected is True
    assert result.result.detected is True

    assert result.situation.evidence_text is not None
    assert result.task.evidence_text is not None
    assert result.action.evidence_text == "architected"
    assert result.result.evidence_text is not None

    assert result.completeness_score == 100.0
    assert result.missing_components == []
    assert len(result.improvement_guidance) >= 1
    assert "Comprehensive STAR evidence detected" in result.improvement_guidance[0]


def test_action_plus_result(analyzer: STARAnalyzer):
    """Scenario B: Bullet with Action + Result only (missing Situation and Task)."""
    text = "Engineered distributed caching layer, reducing latency by 35%."
    result = analyzer.analyze_bullet(text)

    assert result.action.detected is True
    assert result.action.evidence_text == "engineered"
    assert result.result.detected is True
    assert result.result.evidence_text == "35%"
    assert result.situation.detected is False
    assert result.task.detected is False

    assert result.completeness_score == 65.0  # 30.0 (Action) + 35.0 (Result)
    assert "TASK" in result.missing_components
    assert "SITUATION" in result.missing_components
    assert "ACTION" not in result.missing_components
    assert "RESULT" not in result.missing_components


def test_missing_result(analyzer: STARAnalyzer):
    """Scenario C: Bullet with Action + Situation + Task, but missing measurable Result."""
    text = "Architected microservices using FastAPI in a cloud-native environment to enable horizontal scaling."
    result = analyzer.analyze_bullet(text)

    assert result.action.detected is True
    assert result.situation.detected is True
    assert result.task.detected is True
    assert result.result.detected is False

    assert result.completeness_score == 65.0  # 30.0 + 15.0 + 20.0
    assert result.missing_components == ["RESULT"]
    assert any("Result evidence not detected" in g for g in result.improvement_guidance)


def test_missing_action(analyzer: STARAnalyzer):
    """Scenario D: Bullet stating responsibility/task without an active verb."""
    text = "Responsible for database maintenance and query optimization planning."
    result = analyzer.analyze_bullet(text)

    assert result.action.detected is False
    assert result.task.detected is True
    assert "ACTION" in result.missing_components
    assert any("Action evidence not detected" in g for g in result.improvement_guidance)


def test_missing_situation(analyzer: STARAnalyzer):
    """Scenario E: Bullet with Task, Action, and Result but missing operational context."""
    text = "Tasked with improving API throughput, developed connection pooling, increasing requests per second by 50%."
    result = analyzer.analyze_bullet(text)

    assert result.task.detected is True
    assert result.action.detected is True
    assert result.result.detected is True
    assert result.situation.detected is False

    assert result.completeness_score == 85.0  # 20.0 + 30.0 + 35.0
    assert result.missing_components == ["SITUATION"]
    assert any("Situation evidence not detected" in g for g in result.improvement_guidance)


def test_missing_task(analyzer: STARAnalyzer):
    """Scenario F: Bullet with Situation, Action, and Result but missing explicit objective directive."""
    text = "In a distributed environment, migrated monolithic services to Kubernetes, achieving 99.9% uptime."
    result = analyzer.analyze_bullet(text)

    assert result.situation.detected is True
    assert result.action.detected is True
    assert result.result.detected is True
    assert result.task.detected is False

    assert result.completeness_score == 80.0  # 15.0 + 30.0 + 35.0
    assert result.missing_components == ["TASK"]
    assert any("Task evidence not detected" in g for g in result.improvement_guidance)


def test_technical_project_bullet(analyzer: STARAnalyzer):
    """Scenario I: Realistic real-world full-stack technical project bullet."""
    text = (
        "Within a multi-tenant platform facing scalability issues, tasked with backend modernization, "
        "refactored SQL queries and containerized services with Docker, cutting response time by 45ms for 100k users."
    )
    result = analyzer.analyze_bullet(text)

    assert result.situation.detected is True
    assert result.task.detected is True
    assert result.action.detected is True
    assert result.result.detected is True
    assert result.completeness_score == 100.0
    assert result.missing_components == []


# =========================================================================
# 2. Approved Heuristic Weight and Scoring Tests
# =========================================================================

def test_approved_weights_action_only(analyzer: STARAnalyzer):
    """Verifies that an Action-only statement scores exactly 30.0."""
    text = "Implemented custom telemetry pipelines."
    result = analyzer.analyze_bullet(text)

    assert result.action.detected is True
    assert result.result.detected is False
    assert result.task.detected is False
    assert result.situation.detected is False
    assert result.completeness_score == 30.0
    assert result.completeness_score == WEIGHT_ACTION


def test_approved_weights_result_only(analyzer: STARAnalyzer):
    """Verifies that a Result-only statement scores exactly 35.0."""
    text = "Resulted in 35% performance gain."
    result = analyzer.analyze_bullet(text)

    assert result.result.detected is True
    assert result.action.detected is False
    assert result.task.detected is False
    assert result.situation.detected is False
    assert result.completeness_score == 35.0
    assert result.completeness_score == WEIGHT_RESULT


def test_approved_weights_task_only(analyzer: STARAnalyzer):
    """Verifies that a Task-only statement scores exactly 20.0."""
    text = "Tasked with internal tooling roadmap."
    result = analyzer.analyze_bullet(text)

    assert result.task.detected is True
    assert result.action.detected is False
    assert result.result.detected is False
    assert result.situation.detected is False
    assert result.completeness_score == 20.0
    assert result.completeness_score == WEIGHT_TASK


def test_approved_weights_situation_only(analyzer: STARAnalyzer):
    """Verifies that a Situation-only statement scores exactly 15.0."""
    text = "In a high-volume environment."
    result = analyzer.analyze_bullet(text)

    assert result.situation.detected is True
    assert result.action.detected is False
    assert result.task.detected is False
    assert result.result.detected is False
    assert result.completeness_score == 15.0
    assert result.completeness_score == WEIGHT_SITUATION


def test_approved_weights_action_plus_result(analyzer: STARAnalyzer):
    """Verifies that Action + Result scores exactly 65.0 (30.0 + 35.0)."""
    text = "Engineered distributed caching layer, reducing latency by 35%."
    result = analyzer.analyze_bullet(text)
    assert result.completeness_score == 65.0
    assert result.completeness_score == (WEIGHT_ACTION + WEIGHT_RESULT)


def test_approved_weights_action_task_situation(analyzer: STARAnalyzer):
    """Verifies that Action + Task + Situation scores exactly 65.0 (30.0 + 20.0 + 15.0)."""
    text = "In a cloud-native environment, tasked with reliability, architected event-driven pipelines."
    result = analyzer.analyze_bullet(text)
    assert result.completeness_score == 65.0
    assert result.completeness_score == (WEIGHT_ACTION + WEIGHT_TASK + WEIGHT_SITUATION)


def test_approved_weights_all_four_sum(analyzer: STARAnalyzer):
    """Verifies that the sum of all four components equals 100.0."""
    assert WEIGHT_ACTION + WEIGHT_RESULT + WEIGHT_TASK + WEIGHT_SITUATION == 100.0


# =========================================================================
# 3. Quantified Result Metric Tests (K - O)
# =========================================================================

def test_percentage_result_metric(analyzer: STARAnalyzer):
    """Scenario K: Valid percentage metrics."""
    result1 = analyzer.analyze_bullet("Reduced memory consumption by 35%.")
    assert result1.result.detected is True
    assert "35%" in (result1.result.evidence_text or "")

    result2 = analyzer.analyze_bullet("Improved model accuracy by 12.5%.")
    assert result2.result.detected is True
    assert "12.5%" in (result2.result.evidence_text or "")


def test_multiplier_result_metric(analyzer: STARAnalyzer):
    """Scenario L: Multiplier performance metrics (e.g. 3x, 10x)."""
    result = analyzer.analyze_bullet("Improved throughput by 3x.")
    assert result.result.detected is True
    assert "3x" in (result.result.evidence_text or "").lower()


def test_scale_volume_result_metric(analyzer: STARAnalyzer):
    """Scenario M: Volume and scale metrics with explicit units."""
    result1 = analyzer.analyze_bullet("Supported 50k users.")
    assert result1.result.detected is True
    assert "50k users" in (result1.result.evidence_text or "")

    result2 = analyzer.analyze_bullet("Processed 10,000 requests per second.")
    assert result2.result.detected is True
    assert "10,000 requests" in (result2.result.evidence_text or "")


def test_currency_result_metric(analyzer: STARAnalyzer):
    """Scenario N: Financial and cost savings metrics ($50k, €100k)."""
    result1 = analyzer.analyze_bullet("Saved $50k in annual cloud infrastructure expenses.")
    assert result1.result.detected is True
    assert "$50k" in (result1.result.evidence_text or "")

    result2 = analyzer.analyze_bullet("Cut hosting costs by €20,000.")
    assert result2.result.detected is True
    assert "€20,000" in (result2.result.evidence_text or "")


def test_latency_time_result_metric(analyzer: STARAnalyzer):
    """Scenario O: Latency and duration metrics."""
    result = analyzer.analyze_bullet("Reduced response time to 40ms.")
    assert result.result.detected is True
    assert "40ms" in (result.result.evidence_text or "")


def test_uptime_sla_result_metric(analyzer: STARAnalyzer):
    """Availability, uptime, and zero-downtime SLA metrics."""
    result1 = analyzer.analyze_bullet("Achieved zero downtime during migration.")
    assert result1.result.detected is True
    assert "zero downtime" in (result1.result.evidence_text or "").lower()

    result2 = analyzer.analyze_bullet("Maintained 99.99% uptime across production clusters.")
    assert result2.result.detected is True
    assert "99.99%" in (result2.result.evidence_text or "")


# =========================================================================
# 4. Metric False-Positive Protection Tests (P - T)
# =========================================================================

def test_year_false_positive_protection(analyzer: STARAnalyzer):
    """Scenario P: Calendar years must NOT be detected as Result metrics."""
    text = "Graduated in 2024."
    result = analyzer.analyze_bullet(text)
    assert result.result.detected is False
    assert result.result.evidence_text is None


def test_date_range_false_positive_protection(analyzer: STARAnalyzer):
    """Scenario Q: Date intervals and ranges must NOT be detected as Result metrics."""
    text = "Worked from 2021-2023."
    result = analyzer.analyze_bullet(text)
    assert result.result.detected is False
    assert result.result.evidence_text is None


def test_tech_version_false_positive_protection(analyzer: STARAnalyzer):
    """Scenario R: Technology version numbers must NOT be detected as Result metrics."""
    text1 = "Built the application using Python 3.12."
    result1 = analyzer.analyze_bullet(text1)
    assert result1.result.detected is False
    assert result1.action.detected is True  # Built is valid action

    text2 = "Used React 18 and PostgreSQL 16."
    result2 = analyzer.analyze_bullet(text2)
    assert result2.result.detected is False


def test_gpa_false_positive_protection(analyzer: STARAnalyzer):
    """Scenario S: Academic GPAs must NOT be detected as Result metrics."""
    text = "Completed GPA 3.8/4.0."
    result = analyzer.analyze_bullet(text)
    assert result.result.detected is False
    assert result.result.evidence_text is None


def test_generic_isolated_number_protection(analyzer: STARAnalyzer):
    """Scenario T: Isolated generic numbers without metric units must NOT produce Result evidence."""
    text = "Handled 5 projects."
    result = analyzer.analyze_bullet(text)
    assert result.result.detected is False
    assert result.result.evidence_text is None


# =========================================================================
# 5. Action Verb Positive & Negative False-Positive Tests (W & Guards)
# =========================================================================

def test_action_false_positive_role_titles(analyzer: STARAnalyzer):
    """Verifies that role titles and technology nouns are NOT classified as Action."""
    negative_cases = [
        "FastAPI developer.",
        "Python developer.",
        "Software engineer.",
        "Database maintenance.",
        "Full stack architect.",
    ]
    for text in negative_cases:
        result = analyzer.analyze_bullet(text)
        assert result.action.detected is False, f"False positive Action detected for: '{text}'"


@pytest.mark.parametrize(
    "verb",
    [
        "developed",
        "architected",
        "deployed",
        "optimized",
        "containerized",
        "refactored",
        "automated",
        "integrated",
        "instrumented",
        "overhauled",
    ],
)
def test_technical_action_verb_detection(analyzer: STARAnalyzer, verb: str):
    """Scenario W: Verifies detection of genuine active technical verbs."""
    text = f"{verb.capitalize()} the analytics ingestion service."
    result = analyzer.analyze_bullet(text)
    assert result.action.detected is True
    assert result.action.evidence_text == verb


# =========================================================================
# 6. Task & Situation Phrase Detection Tests (U & V)
# =========================================================================

@pytest.mark.parametrize(
    "phrase",
    [
        "tasked with",
        "responsible for",
        "in order to",
        "with the goal of",
        "to enable",
        "lead developer",
    ],
)
def test_task_phrase_detection(analyzer: STARAnalyzer, phrase: str):
    """Scenario U: Explicit task markers and directives are accurately detected."""
    text = f"Acted as {phrase} backend modernization."
    result = analyzer.analyze_bullet(text)
    assert result.task.detected is True
    assert phrase in (result.task.evidence_text or "").lower()


@pytest.mark.parametrize(
    "context",
    [
        "high-volume environment",
        "distributed systems",
        "cloud-native environment",
        "legacy codebase",
        "production environment",
        "multi-tenant platform",
        "technical debt",
        "scalability issues",
    ],
)
def test_situation_phrase_detection(analyzer: STARAnalyzer, context: str):
    """Scenario V: Operational scale and problem environments are accurately detected."""
    text = f"Faced with {context} across multiple data centers."
    result = analyzer.analyze_bullet(text)
    assert result.situation.detected is True
    assert context in (result.situation.evidence_text or "").lower()


# =========================================================================
# 7. Edge Cases & Robustness Tests (G, H, Formatting)
# =========================================================================

def test_empty_and_whitespace_inputs(analyzer: STARAnalyzer):
    """Scenario G: Empty, whitespace-only, and None-equivalent strings."""
    for text in ["", "   ", "\t\t\n  \r\n"]:
        res = analyzer.analyze_bullet(text)
        assert res.completeness_score == 0.0
        assert res.action.detected is False
        assert res.result.detected is False
        assert res.task.detected is False
        assert res.situation.detected is False
        assert res.missing_components == ["ACTION", "RESULT", "TASK", "SITUATION"]


def test_short_and_punctuation_fragments(analyzer: STARAnalyzer):
    """Scenario H: Very short fragments and punctuation-only strings."""
    for text in [".", "...", "---", "Developer", "React"]:
        res = analyzer.analyze_bullet(text)
        assert res.completeness_score == 0.0
        assert res.action.detected is False
        assert res.result.detected is False


def test_formatting_glyphs_and_unicode_normalization(analyzer: STARAnalyzer):
    """Bullet markers, numbers, Unicode dashes, and abnormal spacing do not break detection."""
    variations = [
        "• Architected service, reducing latency by 20%.",
        "- Architected service, reducing latency by 20%.",
        "* Architected service, reducing latency by 20%.",
        "1. Architected service, reducing latency by 20%.",
        "— Architected service, reducing latency by 20%.",
        "Architected    a   service,   reducing  latency   by   20%.",
        "aRcHiTeCtEd a service, reducing latency by 20%.",
    ]
    for text in variations:
        res = analyzer.analyze_bullet(text)
        assert res.action.detected is True
        assert res.result.detected is True
        assert res.completeness_score == 65.0


def test_multiline_and_multiple_sentences(analyzer: STARAnalyzer):
    """Multi-sentence and newline-delimited bullet points."""
    text = (
        "Tasked with reliability across clusters.\n"
        "Architected fault-tolerant queues. Reduced latency by 25%."
    )
    res = analyzer.analyze_bullet(text)
    assert res.task.detected is True
    assert res.action.detected is True
    assert res.result.detected is True
    assert res.completeness_score == 85.0


def test_batch_bullet_analysis(analyzer: STARAnalyzer):
    """Batch analysis returns correct sequential results."""
    bullets = [
        "Architected caching layer, reducing latency by 35%.",
        "Graduated in 2024.",
        "",
    ]
    results = analyzer.analyze_bullets(bullets)
    assert len(results) == 3
    assert results[0].completeness_score == 65.0
    assert results[1].completeness_score == 0.0
    assert results[2].completeness_score == 0.0


# =========================================================================
# 8. Determinism & Repeatability (Scenario X)
# =========================================================================

def test_deterministic_repeated_execution(analyzer: STARAnalyzer):
    """Scenario X: Analyzes identical input across multiple iterations; asserts strict equality."""
    text = (
        "In a high-volume microservices environment, tasked with reducing latency, "
        "architected an asynchronous caching layer with Redis, reducing response times by 40% for 50k users."
    )

    baseline = analyzer.analyze_bullet(text)

    for _ in range(10):
        subsequent = analyzer.analyze_bullet(text)
        assert subsequent == baseline
        assert subsequent.completeness_score == baseline.completeness_score
        assert subsequent.missing_components == baseline.missing_components
        assert subsequent.improvement_guidance == baseline.improvement_guidance
        assert subsequent.action == baseline.action
        assert subsequent.result == baseline.result
        assert subsequent.task == baseline.task
        assert subsequent.situation == baseline.situation
