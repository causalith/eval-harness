"""Epistemic-state mapping foundation."""

from __future__ import annotations

from typing import Literal

EpistemicState = Literal[
    "Hypothesis",
    "Emerging",
    "Consolidating",
    "Established",
    "Contested",
    "Overturned",
    "Fragmented",
]


def compute_epistemic_state(
    *,
    evidence_count: int,
    supporting_count: int,
    contradicting_count: int,
    null_finding_count: int = 0,
    avg_evidence_quality: float = 0.0,
) -> EpistemicState:
    if evidence_count <= 0:
        return "Hypothesis"
    if evidence_count < 3:
        return "Emerging"

    total_clear = supporting_count + contradicting_count
    ratio = supporting_count / total_clear if total_clear > 0 else 1.0

    # Hard overturn: contradicting dominates clearly
    if contradicting_count >= supporting_count and contradicting_count >= 2:
        return "Overturned" if supporting_count == 0 else "Contested"

    # Fragmented: both sides present + conditional/qualified papers indicate population split.
    # The classic case: HRT (true for early-start, false for late-start), where
    # supporting > contradicting (so not "Contested") but qualified papers signal conditions.
    if (
        null_finding_count >= 2
        and contradicting_count >= 2
        and supporting_count >= 2
    ):
        return "Fragmented"

    # Contested: near-parity evidence without clear population split
    # Fires on ±30pp balance (35-65% support) with meaningful challenge volume
    if contradicting_count >= 2 and 0.35 <= ratio <= 0.65:
        return "Contested"

    # Established: strong, clean consensus (no challengers, quality evidence)
    # Relaxed quality threshold (0.60 instead of 0.75) for sparse corpora
    if supporting_count >= 5 and avg_evidence_quality >= 0.60 and contradicting_count == 0:
        return "Established"

    # Legacy strong-opposition fallback (matches old behavior for contradicting ≥ supporting)
    if null_finding_count >= supporting_count and null_finding_count >= 2:
        return "Fragmented"

    return "Consolidating"
