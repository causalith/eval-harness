"""GRADE-weighted support ratio and trend indicator.

GRADE_WEIGHTS map study design to an evidence quality weight. An RCT counts
2.5× more than an observational study when computing the support ratio. This
prevents a flood of low-quality observational papers from swamping one
high-quality RCT that contradicts them.

Study design is inferred from keyword patterns in the paper title/abstract;
no additional LLM call is made in the hot path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

StudyDesign = Literal[
    "meta_analysis",
    "rct",
    "cohort",
    "case_control",
    "observational",
    "in_vitro",
    "computational",
    "unknown",
]

TrendIndicator = Literal["stable", "amber_up", "amber_down", "red_down"]

GRADE_WEIGHTS: dict[str, float] = {
    "meta_analysis": 3.0,
    "rct": 2.5,
    "cohort": 1.5,
    "case_control": 1.2,
    "observational": 1.0,
    "in_vitro": 0.8,
    "computational": 0.6,
    "unknown": 1.0,
}

# Keyword patterns for study design inference (checked in priority order)
_DESIGN_PATTERNS: list[tuple[StudyDesign, re.Pattern[str]]] = [
    ("meta_analysis", re.compile(
        r"\b(?:meta[- ]?analysis|systematic[- ]review|pooled[- ]analysis|pooled meta|meta-analytic)",
        re.IGNORECASE,
    )),
    ("rct", re.compile(
        r"\b(randomis|randomiz|rct\b|randomized controlled trial|double[- ]blind|placebo[- ]controlled)\b",
        re.IGNORECASE,
    )),
    ("cohort", re.compile(
        r"\b(cohort study|longitudinal|prospective study|retrospective cohort|follow[- ]up study)\b",
        re.IGNORECASE,
    )),
    ("case_control", re.compile(
        r"\b(case[- ]control|case control study|matched control)\b", re.IGNORECASE
    )),
    ("in_vitro", re.compile(
        r"\b(in vitro|cell line|cell culture|in-vitro|cultured cells?|murine model|mouse model|animal model)\b",
        re.IGNORECASE,
    )),
    ("computational", re.compile(
        r"\b(simulation|computational model|in silico|machine learning model|neural network|algorithm)\b",
        re.IGNORECASE,
    )),
    ("observational", re.compile(
        r"\b(cross[- ]sectional|survey|observational|epidemiolog|registry|population[- ]based)\b",
        re.IGNORECASE,
    )),
]


@dataclass(frozen=True, slots=True)
class StanceRecord:
    """A single paper's stance on a claim, with metadata for weighting."""

    paper_id: str
    title: str
    stance: Literal["support", "contradict", "qualified", "unrelated", "unclassified"]
    reason: str
    year: int | None = None
    citations: int = 0
    study_design: StudyDesign = "unknown"
    population: str = ""
    is_retracted: bool = False
    doi: str | None = None
    abstract: str | None = None
    source: str = "openalex"


@dataclass
class EvidenceSummary:
    total_papers: int
    supporting_count: int
    challenging_count: int
    qualified_count: int
    unrelated_count: int
    rct_count: int
    meta_count: int
    cohort_count: int
    year_range: tuple[int, int] | None
    weighted_support: float | None
    trend: TrendIndicator
    workspace_count: int = 0
    fetched_count: int = 0
    study_design_breakdown: dict[str, int] = field(default_factory=dict)


def infer_study_design(title: str, abstract: str | None) -> StudyDesign:
    """Infer study design from title and abstract without an LLM call."""
    text = f"{title} {abstract or ''}"
    for design, pattern in _DESIGN_PATTERNS:
        if pattern.search(text):
            return design
    return "unknown"


def weighted_support_ratio(stances: list[StanceRecord]) -> float | None:
    """GRADE-weighted ratio of supporting vs challenging papers.

    Papers classified as 'unrelated', 'unclassified', or retracted are
    excluded. Returns None when no relevant evidence exists.
    """
    relevant = [
        s for s in stances
        if s.stance in ("support", "contradict") and not s.is_retracted
    ]
    if not relevant:
        return None

    supporting_w = sum(
        GRADE_WEIGHTS.get(s.study_design, 1.0)
        for s in relevant
        if s.stance == "support"
    )
    challenging_w = sum(
        GRADE_WEIGHTS.get(s.study_design, 1.0)
        for s in relevant
        if s.stance == "contradict"
    )
    total = supporting_w + challenging_w
    return supporting_w / total if total > 0 else None


def trend_indicator(stances: list[StanceRecord], today: date) -> TrendIndicator:
    """Compare recent (≤3y) vs historical support ratios.

    Returns "stable" when there are fewer than 3 recent papers — sparse data
    is not enough to declare a trend. Escalates to "red_down" when at least
    one RCT or meta-analysis appears in the recent challenging papers.
    """
    relevant = [s for s in stances if s.stance in ("support", "contradict") and not s.is_retracted]
    recent = [s for s in relevant if s.year is not None and (today.year - s.year) <= 3]
    historical = [s for s in relevant if s.year is None or (today.year - s.year) > 3]

    if len(recent) < 3:
        return "stable"

    r_recent = weighted_support_ratio(recent) or 0.5
    r_hist = weighted_support_ratio(historical) or 0.5
    delta = r_recent - r_hist

    if abs(delta) < 0.15:
        return "stable"
    if delta > 0.15:
        return "amber_up"

    # delta < -0.15: determine severity
    recent_challengers = [s for s in recent if s.stance == "contradict"]
    has_high_quality = any(
        s.study_design in ("rct", "meta_analysis") for s in recent_challengers
    )
    return "red_down" if has_high_quality else "amber_down"


def build_evidence_summary(
    stances: list[StanceRecord],
    *,
    workspace_count: int = 0,
    fetched_count: int = 0,
    today: date | None = None,
) -> EvidenceSummary:
    """Assemble the top-level evidence numbers shown in the panel header."""
    _today = today or date.today()
    relevant = [s for s in stances if not s.is_retracted]

    years = [s.year for s in relevant if s.year is not None]
    year_range = (min(years), max(years)) if years else None

    design_counts: dict[str, int] = {}
    for s in relevant:
        design_counts[s.study_design] = design_counts.get(s.study_design, 0) + 1

    return EvidenceSummary(
        total_papers=len(relevant),
        supporting_count=sum(1 for s in relevant if s.stance == "support"),
        challenging_count=sum(1 for s in relevant if s.stance == "contradict"),
        qualified_count=sum(1 for s in relevant if s.stance == "qualified"),
        unrelated_count=sum(1 for s in relevant if s.stance == "unrelated"),
        rct_count=design_counts.get("rct", 0),
        meta_count=design_counts.get("meta_analysis", 0),
        cohort_count=design_counts.get("cohort", 0),
        year_range=year_range,
        weighted_support=weighted_support_ratio(relevant),
        trend=trend_indicator(relevant, _today),
        workspace_count=workspace_count,
        fetched_count=fetched_count,
        study_design_breakdown=design_counts,
    )
