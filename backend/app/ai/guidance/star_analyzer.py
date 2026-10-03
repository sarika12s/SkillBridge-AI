"""Deterministic rule-based STAR Resume Guidance analyzer.

Evaluates resume achievement bullet points across the four competency pillars:
  S (Situation): Context, operational scale, platform, or problem environment
  T (Task): Objective, assignment directive, responsibility, or defined scope
  A (Action): Active technical/operational verbs and methodology ownership
  R (Result): Measurable outcomes, quantified metrics, or performance impact

Zero LLMs, zero external APIs, zero database mutations.
100% deterministic, explainable, and reproducible.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set

# Project-defined deterministic heuristic weights (total = 100.0)
WEIGHT_ACTION: float = 30.0
WEIGHT_RESULT: float = 35.0
WEIGHT_TASK: float = 20.0
WEIGHT_SITUATION: float = 15.0

# -------------------------------------------------------------------------
# Lexicons and Rule Compilations
# -------------------------------------------------------------------------

# Action Verbs (Past tense and active present technical/operational verbs)
ACTION_VERB_LIST: Set[str] = {
    # Engineering & Architecture
    "architected", "developed", "engineered", "implemented", "designed",
    "orchestrated", "deployed", "configured", "refactored", "containerized",
    "migrated", "automated", "integrated", "benchmarked", "optimized",
    "trained", "monitored", "audited", "scaled", "authored", "built",
    "created", "established", "spearheaded", "administered", "debugged",
    "resolved", "executed", "provisioned", "maintained", "instrumented",
    "streamlined", "constructed", "delivered", "standardized", "published",
    "formulated", "fine-tuned", "centralized", "modernized", "compiled",
    "profiled", "secured", "upgraded", "accelerated", "overhauled",
    # Active Present / 3rd Person
    "develops", "architects", "engineers", "implements", "designs",
    "deploys", "builds", "automates", "optimizes", "creates", "maintains",
}

# Task / Objective Phrases
TASK_OBJECTIVE_PATTERNS: List[str] = [
    r"\bin order to\b",
    r"\baiming to\b",
    r"\btasked with\b",
    r"\bresponsible for\b",
    r"\bassigned to\b",
    r"\bwith the goal of\b",
    r"\bwith the objective of\b",
    r"\bto enable\b",
    r"\bto support\b",
    r"\bto achieve\b",
    r"\bto ensure\b",
    r"\bto facilitate\b",
    r"\bmandated to\b",
    r"\bserve(?:d)? as\b",
]

TASK_SCOPE_PATTERNS: List[str] = [
    r"\blead developer\b",
    r"\bsole developer\b",
    r"\bprimary developer\b",
    r"\bcore developer\b",
    r"\blead engineer\b",
    r"\bprimary engineer\b",
    r"\blead architect\b",
    r"\bprimary contributor\b",
    r"\bspearheaded the effort to\b",
    r"\bproject lead\b",
    r"\btech lead\b",
]

# Situation / Environment Phrases & Problem Constraints
SITUATION_COMPOUND_NOUNS: List[str] = [
    r"\bhigh-volume environment\b",
    r"\bdistributed environment\b",
    r"\bcloud-native environment\b",
    r"\blegacy system(?:s)?\b",
    r"\blegacy architecture\b",
    r"\blegacy codebase\b",
    r"\benterprise platform\b",
    r"\bproduction environment\b",
    r"\bmulti-tenant platform\b",
    r"\be-commerce platform\b",
    r"\bfintech environment\b",
    r"\bhealthcare system\b",
    r"\bcross-functional team\b",
    r"\btechnical debt\b",
    r"\bscalability issues\b",
    r"\blatency spikes\b",
    r"\bsecurity vulnerabilities\b",
    r"\bdata inconsistencies\b",
    r"\bmonolithic architecture\b",
    r"\bmicroservices architecture\b",
    r"\bmicroservices environment\b",
    r"\bdistributed systems\b",
    r"\bhigh concurrency\b",
    r"\blarge-scale data\b",
    r"\bbottlenecks\b",
]

SITUATION_CONTEXT_PREPOSITIONS: List[str] = [
    r"\b(?:in|within|for)\s+(?:a|an|the)?\s*(?:[a-zA-Z0-9-]+\s+)*(?:high-volume|distributed|cloud-native|legacy|enterprise|production|multi-tenant|fast-paced|e-commerce|fintech|healthcare|cross-functional)\s+(?:environment|platform|system|application|infrastructure|team|codebase)\b",
    r"\b(?:facing|amid|to address|dealing with|overcoming|in response to)\s+(?:bottlenecks|scalability issues|technical debt|latency spikes|downtime|security vulnerabilities|data inconsistencies|legacy limitations|system constraints)\b",
]

# Metric False-Positive Masking Patterns (Items that must NOT count as Results)
DATE_YEAR_REGEX = re.compile(r"\b(?:19|20)\d{2}\b")
DATE_RANGE_REGEX = re.compile(r"\b(?:19|20)\d{2}\s*[-–—]\s*(?:(?:19|20)\d{2}|Present|Current)\b", re.IGNORECASE)
MONTH_YEAR_REGEX = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+(?:19|20)\d{2}\b", re.IGNORECASE)

TECH_VERSION_PATTERNS = [
    re.compile(r"\bPython\s+[23](?:\.\d+)*\b", re.IGNORECASE),
    re.compile(r"\bReact(?:\s+Native)?\s+(?:1[6-9]|18|\d+)\b", re.IGNORECASE),
    re.compile(r"\bPostgreSQL\s+(?:9|1[0-7]|\d+)\b", re.IGNORECASE),
    re.compile(r"\bNode(?:\.js)?\s+\d+\b", re.IGNORECASE),
    re.compile(r"\bJava\s+(?:8|11|17|21|\d+)\b", re.IGNORECASE),
    re.compile(r"\b(?:Vue|Angular|Next|Nuxt|Django|FastAPI|Spring(?:\s+Boot)?|Ubuntu|Debian|Windows)\s+(?:v?\d+(?:\.\d+)*)\b", re.IGNORECASE),
    re.compile(r"\b(?:v|version)\s*\d+(?:\.\d+)*\b", re.IGNORECASE),
    re.compile(r"\b(?:HTML|CSS|ECMAScript|ES)\s*[3-6]\b", re.IGNORECASE),
]

ACADEMIC_GPA_REGEX = re.compile(r"\b[0-4]\.\d{1,2}(?:\s*/\s*4(?:\.0)?)?\b")

# Valid Metric Result Patterns
PERCENTAGE_METRIC_REGEX = re.compile(r"\b\d+(?:\.\d+)?%(?!\w)")
MULTIPLIER_METRIC_REGEX = re.compile(r"\b\d+(?:\.\d+)?x\b", re.IGNORECASE)
CURRENCY_METRIC_REGEX = re.compile(r"[\$€£]\s*\d+(?:[.,]\d+)*(?:\s*(?:k|m|b|thousand|million|billion))?\b", re.IGNORECASE)

SCALE_VOLUME_METRIC_REGEX = re.compile(
    r"\b\d+(?:,\d{3})*\+?\s*(?:users|clients|customers|subscribers|requests|rps|qps|endpoints|records|queries|tickets|nodes|services|transactions|pipeline runs|daily active users|dau|mau)\b",
    re.IGNORECASE,
)
ABBREVIATED_SCALE_METRIC_REGEX = re.compile(
    r"\b\d+(?:\.\d+)?\s*[kKmMbB]\s*(?:users|clients|customers|requests|rps|qps|records|queries)\b",
    re.IGNORECASE,
)

LATENCY_DURATION_METRIC_REGEX = re.compile(
    r"\b(?:reduced|reducing|decreased|decreasing|cut|cutting|improved|improving|accelerated|accelerating)\b.*?\b(?:by\s+\d+|to\s+\d+)\s*(?:ms|milliseconds?|s|seconds?|minutes?|hours?|days?|weeks?)\b",
    re.IGNORECASE,
)

COMPARATIVE_IMPACT_METRIC_REGEX = re.compile(
    r"\b(?:reduced|reducing|decreased|decreasing|cut|cutting|boosted|boosting|increased|increasing|improved|improving|minimized|minimizing|achieved|achieving|saved|saving|generated|generating|eliminated|eliminating)\b.*?\b(?:by\s+\d+(?:\.\d+)?%|from\s+\d+.*?to\s+\d+|\d+(?:\.\d+)?%)(?!\w)",
    re.IGNORECASE,
)

DOWNTIME_SLA_METRIC_REGEX = re.compile(
    r"\b(?:zero|0)\s+downtime\b|\b99\.\d+%(?!\w)\s*(?:uptime|availability|sla)\b",
    re.IGNORECASE,
)


# -------------------------------------------------------------------------
# Output Data Structures
# -------------------------------------------------------------------------

@dataclass(frozen=True)
class ComponentAnalysis:
    """Detailed structural evidence report for a single STAR component."""
    detected: bool
    evidence_text: Optional[str] = None
    signals_detected: List[str] = field(default_factory=list)
    explanation: str = ""


@dataclass(frozen=True)
class BulletAnalysisResult:
    """Comprehensive STAR analysis for a single resume achievement bullet."""
    raw_text: str
    clean_text: str
    situation: ComponentAnalysis
    task: ComponentAnalysis
    action: ComponentAnalysis
    result: ComponentAnalysis
    completeness_score: float
    missing_components: List[str] = field(default_factory=list)
    improvement_guidance: List[str] = field(default_factory=list)


# -------------------------------------------------------------------------
# Core Deterministic STAR Analyzer Engine
# -------------------------------------------------------------------------

class STARAnalyzer:
    """
    Pure Python, deterministic rule-based STAR Resume Guidance Analyzer.
    Evaluates individual achievement statements for Situation, Task, Action, and Result evidence.
    """

    def __init__(self) -> None:
        # Precompile task patterns
        self._task_patterns = [
            re.compile(p, re.IGNORECASE) for p in TASK_OBJECTIVE_PATTERNS + TASK_SCOPE_PATTERNS
        ]
        # Precompile situation patterns
        self._situation_patterns = [
            re.compile(p, re.IGNORECASE) for p in SITUATION_COMPOUND_NOUNS + SITUATION_CONTEXT_PREPOSITIONS
        ]

    def clean_bullet_text(self, text: str) -> str:
        """Strips leading bullet point glyphs, excess whitespace, and list numbering."""
        if not text:
            return ""
        # Remove leading bullet symbols (•, *, -, –, —, etc.) or numerical list markers (e.g. "1. ")
        cleaned = re.sub(r"^[\s•\*\-\–\—\>#]+\s*", "", text.strip())
        cleaned = re.sub(r"^\d+[\.\)]\s+", "", cleaned)
        return cleaned.strip()

    def analyze_bullet(self, text: str) -> BulletAnalysisResult:
        """
        Analyzes a single bullet text string for S, T, A, R components deterministically.
        Guarantees identical output for identical input text.
        """
        raw_input = text or ""
        cleaned = self.clean_bullet_text(raw_input)

        if not cleaned:
            return BulletAnalysisResult(
                raw_text=raw_input,
                clean_text="",
                situation=ComponentAnalysis(
                    detected=False,
                    explanation="Situation evidence not detected: statement is empty.",
                ),
                task=ComponentAnalysis(
                    detected=False,
                    explanation="Task evidence not detected: statement is empty.",
                ),
                action=ComponentAnalysis(
                    detected=False,
                    explanation="Action evidence not detected: statement is empty.",
                ),
                result=ComponentAnalysis(
                    detected=False,
                    explanation="Result evidence not detected: statement is empty.",
                ),
                completeness_score=0.0,
                missing_components=["ACTION", "RESULT", "TASK", "SITUATION"],
                improvement_guidance=["Empty statement provided. Add complete achievement descriptions using the STAR framework."],
            )

        # 1. Detect Action
        action_analysis = self._detect_action(cleaned)

        # 2. Detect Result (with false-positive protection)
        result_analysis = self._detect_result(cleaned)

        # 3. Detect Task
        task_analysis = self._detect_task(cleaned)

        # 4. Detect Situation
        situation_analysis = self._detect_situation(cleaned)

        # 5. Compute Heuristic Score
        score = 0.0
        if action_analysis.detected:
            score += WEIGHT_ACTION
        if result_analysis.detected:
            score += WEIGHT_RESULT
        if task_analysis.detected:
            score += WEIGHT_TASK
        if situation_analysis.detected:
            score += WEIGHT_SITUATION
        score = round(score, 1)

        # 6. Identify Missing Components
        missing: List[str] = []
        if not action_analysis.detected:
            missing.append("ACTION")
        if not result_analysis.detected:
            missing.append("RESULT")
        if not task_analysis.detected:
            missing.append("TASK")
        if not situation_analysis.detected:
            missing.append("SITUATION")

        # 7. Generate Actionable Template Guidance
        guidance = self._generate_guidance(
            action_detected=action_analysis.detected,
            result_detected=result_analysis.detected,
            task_detected=task_analysis.detected,
            situation_detected=situation_analysis.detected,
        )

        return BulletAnalysisResult(
            raw_text=raw_input,
            clean_text=cleaned,
            situation=situation_analysis,
            task=task_analysis,
            action=action_analysis,
            result=result_analysis,
            completeness_score=score,
            missing_components=missing,
            improvement_guidance=guidance,
        )

    def analyze_bullets(self, bullets: List[str]) -> List[BulletAnalysisResult]:
        """Analyzes a collection of bullet points sequentially."""
        return [self.analyze_bullet(b) for b in bullets]

    # ---------------------------------------------------------------------
    # Internal Component Detectors
    # ---------------------------------------------------------------------

    def _detect_action(self, text: str) -> ComponentAnalysis:
        """Detects strong active technical or operational verbs demonstrating agency."""
        words = re.findall(r"\b[a-zA-Z]+(?:-[a-zA-Z]+)?\b", text)
        if not words:
            return ComponentAnalysis(
                detected=False,
                explanation="Action evidence not detected: statement lacks words.",
            )

        found_verbs: List[str] = []
        signals: List[str] = []

        # Check early tokens (initial 4 tokens) for action verbs
        early_tokens = [w.lower() for w in words[:4]]
        for token in early_tokens:
            if token in ACTION_VERB_LIST and token not in found_verbs:
                found_verbs.append(token)
                signals.append(f"sentence_initial_active_verb: '{token}'")

        # Check all other tokens if none found in opening
        if not found_verbs:
            for w in words:
                w_lower = w.lower()
                if w_lower in ACTION_VERB_LIST and w_lower not in found_verbs:
                    found_verbs.append(w_lower)
                    signals.append(f"active_verb: '{w_lower}'")

        if found_verbs:
            return ComponentAnalysis(
                detected=True,
                evidence_text=found_verbs[0],
                signals_detected=signals,
                explanation=f"Action evidence detected: active technical verb '{found_verbs[0]}' identified.",
            )

        return ComponentAnalysis(
            detected=False,
            evidence_text=None,
            signals_detected=[],
            explanation="Action evidence not detected: bullet lacks a strong active technical verb.",
        )

    def _detect_task(self, text: str) -> ComponentAnalysis:
        """Detects explicit objective markers, assigned directives, or defined scope."""
        found_matches: List[str] = []
        signals: List[str] = []

        for pat in self._task_patterns:
            m = pat.search(text)
            if m:
                matched_str = m.group(0).strip()
                if matched_str not in found_matches:
                    found_matches.append(matched_str)
                    signals.append(f"task_objective_marker: '{matched_str}'")

        if found_matches:
            return ComponentAnalysis(
                detected=True,
                evidence_text=found_matches[0],
                signals_detected=signals,
                explanation=f"Task evidence detected: explicit objective marker '{found_matches[0]}' identified.",
            )

        return ComponentAnalysis(
            detected=False,
            evidence_text=None,
            signals_detected=[],
            explanation="Task evidence not detected: no explicit objective or responsibility directive identified.",
        )

    def _detect_situation(self, text: str) -> ComponentAnalysis:
        """Detects operational scale, problem environment, platform constraints, or context."""
        found_matches: List[str] = []
        signals: List[str] = []

        for pat in self._situation_patterns:
            m = pat.search(text)
            if m:
                matched_str = m.group(0).strip()
                if matched_str not in found_matches:
                    found_matches.append(matched_str)
                    signals.append(f"situation_context_marker: '{matched_str}'")

        if found_matches:
            return ComponentAnalysis(
                detected=True,
                evidence_text=found_matches[0],
                signals_detected=signals,
                explanation=f"Situation evidence detected: operational context '{found_matches[0]}' identified.",
            )

        return ComponentAnalysis(
            detected=False,
            evidence_text=None,
            signals_detected=[],
            explanation="Situation evidence not detected: no operational context, constraint, or problem environment identified.",
        )

    def _detect_result(self, text: str) -> ComponentAnalysis:
        """
        Detects measurable outcome and metric evidence with strict false-positive masking.
        Excludes calendar years, date intervals, software versions, and academic GPAs.
        """
        # Step 1: Create masked text with non-metric patterns replaced by neutral placeholder tokens
        masked_text = text

        # Mask date ranges first
        masked_text = DATE_RANGE_REGEX.sub(" [DATE_RANGE] ", masked_text)
        # Mask month + years
        masked_text = MONTH_YEAR_REGEX.sub(" [MONTH_YEAR] ", masked_text)
        # Mask calendar years
        masked_text = DATE_YEAR_REGEX.sub(" [YEAR] ", masked_text)

        # Mask technology versions (e.g. Python 3.12, React 18, PostgreSQL 16)
        for tech_pat in TECH_VERSION_PATTERNS:
            masked_text = tech_pat.sub(" [TECH_VERSION] ", masked_text)

        # Mask academic GPAs
        masked_text = ACADEMIC_GPA_REGEX.sub(" [GPA] ", masked_text)

        found_results: List[str] = []
        signals: List[str] = []

        # Step 2: Evaluate valid outcome metrics against masked text

        # A. Downtime / SLA guarantees
        m_sla = DOWNTIME_SLA_METRIC_REGEX.search(masked_text)
        if m_sla:
            match_str = m_sla.group(0).strip()
            found_results.append(match_str)
            signals.append(f"availability_sla_metric: '{match_str}'")

        # B. Percentages
        for m in PERCENTAGE_METRIC_REGEX.finditer(masked_text):
            pct_str = m.group(0).strip()
            found_results.append(pct_str)
            signals.append(f"percentage_metric: '{pct_str}'")

        # C. Multipliers (e.g. 3x, 10x)
        for m in MULTIPLIER_METRIC_REGEX.finditer(masked_text):
            mult_str = m.group(0).strip()
            found_results.append(mult_str)
            signals.append(f"multiplier_metric: '{mult_str}'")

        # D. Currency / Monetary Impact
        for m in CURRENCY_METRIC_REGEX.finditer(masked_text):
            curr_str = m.group(0).strip()
            found_results.append(curr_str)
            signals.append(f"monetary_impact_metric: '{curr_str}'")

        # E. Scale / Volume with Units (e.g. 50k users, 10,000 requests)
        for m in SCALE_VOLUME_METRIC_REGEX.finditer(masked_text):
            scale_str = m.group(0).strip()
            found_results.append(scale_str)
            signals.append(f"scale_volume_metric: '{scale_str}'")

        for m in ABBREVIATED_SCALE_METRIC_REGEX.finditer(masked_text):
            scale_str = m.group(0).strip()
            found_results.append(scale_str)
            signals.append(f"abbreviated_scale_metric: '{scale_str}'")

        # F. Latency / Duration Reductions
        m_lat = LATENCY_DURATION_METRIC_REGEX.search(masked_text)
        if m_lat:
            lat_str = m_lat.group(0).strip()
            found_results.append(lat_str)
            signals.append(f"latency_reduction_metric: '{lat_str}'")

        # G. Comparative Impact Phrases
        m_comp = COMPARATIVE_IMPACT_METRIC_REGEX.search(masked_text)
        if m_comp:
            comp_str = m_comp.group(0).strip()
            found_results.append(comp_str)
            signals.append(f"comparative_impact_metric: '{comp_str}'")

        if found_results:
            return ComponentAnalysis(
                detected=True,
                evidence_text=found_results[0],
                signals_detected=signals,
                explanation=f"Result evidence detected: quantifiable metric '{found_results[0]}' identified.",
            )

        return ComponentAnalysis(
            detected=False,
            evidence_text=None,
            signals_detected=[],
            explanation="Result evidence not detected: no qualifying outcome metric found.",
        )

    # ---------------------------------------------------------------------
    # Deterministic Guidance Generation
    # ---------------------------------------------------------------------

    def _generate_guidance(
        self,
        action_detected: bool,
        result_detected: bool,
        task_detected: bool,
        situation_detected: bool,
    ) -> List[str]:
        """Generates template structural guidance based on missing components."""
        guidance: List[str] = []

        if action_detected and result_detected and task_detected and situation_detected:
            guidance.append(
                "Comprehensive STAR evidence detected: statement demonstrates operational context, objective, active implementation, and measurable impact."
            )
            return guidance

        if not action_detected:
            guidance.append(
                "Action evidence not detected: bullet lacks an active technical or operational verb. Consider starting with an active verb (e.g., Developed, Architected, Implemented)."
            )

        if not result_detected:
            guidance.append(
                "Result evidence not detected: bullet lacks quantifiable outcomes or performance metrics. Consider adding a measurable outcome (e.g., percentage improvement, latency reduction, volume handled) if verified in your project."
            )

        if not task_detected:
            guidance.append(
                "Task evidence not detected: bullet does not explicitly state the assigned directive or goal. Consider clarifying your objective (e.g., 'tasked with...', 'in order to...')."
            )

        if not situation_detected:
            guidance.append(
                "Situation evidence not detected: operational context or problem constraint is not explicitly stated. Consider mentioning the system environment or problem context (e.g., 'in a high-volume microservices environment')."
            )

        return guidance
