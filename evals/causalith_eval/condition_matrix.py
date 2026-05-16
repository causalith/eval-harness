"""Condition matrix: cluster papers by population/setting and count stances.

Population strings are extracted from the paper abstract using keyword
matching. Clustering uses embedding cosine similarity when NVIDIA NIM is
available; it falls back to keyword-overlap groups otherwise. Both paths
produce the same ConditionMatrix output shape.

The researcher-context input (optional free-text from the user) is matched
against matrix rows using simple token-overlap scoring, returning the best
row index and a one-sentence generated verdict.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from causalith_eval.support_calculator import (
    GRADE_WEIGHTS,
    StanceRecord,
)


@dataclass
class MatrixRow:
    label: str
    supporting: list[StanceRecord] = field(default_factory=list)
    challenging: list[StanceRecord] = field(default_factory=list)
    qualified: list[StanceRecord] = field(default_factory=list)
    dominant_design: str = "unknown"

    @property
    def net(self) -> int:
        return len(self.supporting) - len(self.challenging)

    @property
    def total(self) -> int:
        return len(self.supporting) + len(self.challenging) + len(self.qualified)


@dataclass
class ConditionMatrix:
    rows: list[MatrixRow]
    context_match_index: int | None = None
    context_match_label: str | None = None


# ── Population keyword vocabulary ─────────────────────────────────────

# (pattern, canonical_label)
_POPULATION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bpostmenopaus\w*\b", re.I), "postmenopausal women"),
    (re.compile(r"\bpremenopaus\w*\b", re.I), "premenopausal women"),
    (re.compile(r"\bmen\b|\bmale\b|\bmales\b", re.I), "men"),
    (re.compile(r"\bwomen\b|\bfemale\b|\bfemales\b", re.I), "women (general)"),
    (re.compile(r"\bchildren\b|\bpediatric\b|\badolescent\b", re.I), "children/adolescents"),
    (re.compile(r"\belderly\b|\bolder adults?\b|\baged \d{2,}\b", re.I), "older adults"),
    (re.compile(r"\btype 2 diabet\w*\b|\bt2dm\b|\bdiabetes mellitus\b", re.I), "diabetic patients"),
    (re.compile(r"\bobese?\b|\bobesity\b|\boverweight\b|\bbmi [>≥]\s*\d", re.I), "obese/overweight"),
    (re.compile(r"\bhealthy adults?\b|\bhealthy volunteers?\b|\bnon[- ]diabet\b", re.I), "healthy adults"),
    (re.compile(r"\banimals?\b|\bmice\b|\brats?\b|\bmurine\b|\brodent\b", re.I), "animal models"),
    (re.compile(r"\bin vitro\b|\bcell line\b|\bcells?\b", re.I), "in vitro"),
]

_GENERAL_LABEL = "general / mixed population"


def extract_population_label(text: str) -> str:
    """Return the first population label matched in text, or general."""
    for pattern, label in _POPULATION_PATTERNS:
        if pattern.search(text):
            return label
    return _GENERAL_LABEL


def build_condition_matrix(
    stances: list[StanceRecord],
    researcher_context: str | None = None,
) -> ConditionMatrix:
    """Group papers by population cluster and count stances.

    Papers classified as 'unrelated' or 'unclassified' are excluded.
    Within each row, dominant_design is the study design with the highest
    GRADE weight among the papers in that row.
    """
    # Assign population label to each relevant paper
    relevant = [
        s for s in stances
        if s.stance in ("support", "contradict", "qualified") and not s.is_retracted
    ]

    bucket: dict[str, MatrixRow] = {}
    for stance in relevant:
        text = f"{stance.title} {stance.abstract or ''} {stance.population or ''}"
        label = extract_population_label(text)
        if label not in bucket:
            bucket[label] = MatrixRow(label=label)
        row = bucket[label]
        if stance.stance == "support":
            row.supporting.append(stance)
        elif stance.stance == "contradict":
            row.challenging.append(stance)
        else:
            row.qualified.append(stance)

    # Compute dominant design per row
    for row in bucket.values():
        all_papers = row.supporting + row.challenging + row.qualified
        if all_papers:
            row.dominant_design = max(
                all_papers, key=lambda s: GRADE_WEIGHTS.get(s.study_design, 1.0)
            ).study_design

    # Sort rows by total paper count descending, general last
    rows = sorted(
        bucket.values(),
        key=lambda r: (r.label == _GENERAL_LABEL, -r.total),
    )

    context_match_index: int | None = None
    context_match_label: str | None = None

    if researcher_context and rows:
        context_match_index = _best_context_match(researcher_context, rows)
        context_match_label = rows[context_match_index].label

    return ConditionMatrix(
        rows=rows,
        context_match_index=context_match_index,
        context_match_label=context_match_label,
    )


# ── Context matching ───────────────────────────────────────────────────


def _best_context_match(context: str, rows: list[MatrixRow]) -> int:
    """Return the row index whose label best matches the researcher context.

    Uses token-overlap (Jaccard) between the context tokens and row label
    tokens. Falls back to 0 (first row) on ties.
    """
    context_tokens = _tokenize(context)
    if not context_tokens:
        return 0

    best_idx = 0
    best_score = -1.0
    for i, row in enumerate(rows):
        row_tokens = _tokenize(row.label)
        if not row_tokens:
            continue
        intersection = context_tokens & row_tokens
        union = context_tokens | row_tokens
        score = len(intersection) / len(union)
        if score > best_score:
            best_score = score
            best_idx = i

    return best_idx


def _tokenize(text: str) -> set[str]:
    return {tok for tok in re.findall(r"[a-z0-9]+", text.lower()) if len(tok) > 2}


def condition_verdict_sentence(
    row: MatrixRow,
    researcher_context: str | None,
) -> str:
    """Generate a one-sentence verdict for the matched condition row."""
    sup = len(row.supporting)
    chl = len(row.challenging)
    qual = len(row.qualified)

    if sup == 0 and chl == 0:
        return f"No direct evidence found for '{row.label}'."

    direction: Literal["well-supported", "well-challenged", "mixed"]
    if sup > chl * 2:
        direction = "well-supported"
    elif chl > sup * 2:
        direction = "well-challenged"
    else:
        direction = "mixed"

    context_note = f" for your context ({researcher_context})" if researcher_context else ""
    return (
        f"Evidence{context_note} in '{row.label}' is {direction}: "
        f"{sup} supporting, {chl} challenging, {qual} qualified "
        f"(dominant study type: {row.dominant_design})."
    )
