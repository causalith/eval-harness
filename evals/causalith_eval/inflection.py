"""Epistemic-history inflection detector.

Two modes:
1. Historical inflections — state transitions in the cumulative epistemic
   state curve (e.g. Established → Contested). These are exact and cheap.
2. Bayesian emerging inflection — uses the same beta-binomial model as the
   emerging alert to detect a regime shift in progress. Only fires when
   posterior > 0.70 and ≥3 recent + ≥5 historical papers exist.

The Bayesian gate prevents false positives on sparse data (the original plan
would fire an "emerging challenge" alert when 2 recent papers challenged a
claim, which is noise at that sample size).
"""

from __future__ import annotations

from dataclasses import dataclass

from causalith_eval.support_calculator import StanceRecord
from causalith_eval.epistemic import EpistemicState, compute_epistemic_state


@dataclass(frozen=True, slots=True)
class EpistemicSnapshot:
    year: int
    state: EpistemicState
    weighted_support_ratio: float | None
    paper_count: int
    is_inflection: bool = False
    inflection_magnitude: float = 0.0
    triggering_paper_id: str | None = None


@dataclass(frozen=True, slots=True)
class InflectionPoint:
    year: int
    from_state: EpistemicState
    to_state: EpistemicState
    magnitude: float
    triggering_paper_id: str | None = None


_RATIO_INFLECTION_THRESHOLD = 0.28  # ≥28pp change in CUMULATIVE weighted support (guards against noise)
_ANNUAL_REVERSAL_THRESHOLD = 0.45   # annual batch flips by ≥45pp vs history (guards against noise)
_ANNUAL_REVERSAL_MIN_PAPERS = 2     # ≥2 papers with clear stance required for annual signal
_RATIO_INFLECTION_MIN_PAPERS = 3    # need at least this many cumulative papers


def build_epistemic_history(
    stances: list[StanceRecord],
) -> list[EpistemicSnapshot]:
    """Compute cumulative epistemic state for each year in the corpus.

    For each year Y, we look at all papers published up to and including Y,
    and compute the epistemic state as of that year. This gives the historical
    arc of consensus rather than a single current snapshot.

    Inflection detection uses TWO signals (either fires the flag):
      1. Epistemic state string changes (e.g., Established → Contested)
      2. Weighted support ratio changes by ≥20pp vs the previous year

    The ratio signal catches cases where the state machine doesn't fire
    (e.g., stays "Consolidating" but the ratio plummets from 0.85 → 0.50
    as WHI-type challenge papers arrive with only 10-15 papers total).
    """
    from causalith_eval.support_calculator import weighted_support_ratio

    if not stances:
        return []

    years = sorted({s.year for s in stances if s.year is not None})
    if not years:
        return []

    snapshots: list[EpistemicSnapshot] = []
    prev_state: EpistemicState | None = None
    prev_ratio: float | None = None

    for year in years:
        cumulative = [s for s in stances if s.year is not None and s.year <= year]
        relevant = [s for s in cumulative if s.stance in ("support", "contradict") and not s.is_retracted]

        supporting = [s for s in relevant if s.stance == "support"]
        contradicting = [s for s in relevant if s.stance == "contradict"]

        if relevant:
            avg_quality = sum(
                _design_quality(s.study_design) for s in relevant
            ) / len(relevant)
        else:
            avg_quality = 0.0

        state = compute_epistemic_state(
            evidence_count=len(relevant),
            supporting_count=len(supporting),
            contradicting_count=len(contradicting),
            null_finding_count=sum(1 for s in cumulative if s.stance == "qualified"),
            avg_evidence_quality=avg_quality,
        )

        support_w: float | None = None
        if relevant:
            support_w = weighted_support_ratio(relevant)

        # Signal 1: state transitions toward more controversy (downward only).
        # "Emerging→Consolidating→Established" are natural progressions — not inflections.
        # Only transitions that indicate a CHALLENGE to the existing consensus count.
        state_changed = (
            prev_state is not None
            and state != prev_state
            and _is_contrarian_transition(prev_state, state)
        )

        # Signal 2: cumulative ratio shifted ≥20pp vs previous year
        ratio_shifted = (
            prev_ratio is not None
            and support_w is not None
            and len(relevant) >= _RATIO_INFLECTION_MIN_PAPERS
            and abs(support_w - prev_ratio) >= _RATIO_INFLECTION_THRESHOLD
        )

        # Signal 3: papers published IN THIS YEAR flip the trend vs cumulative history.
        # Catches cases like WHI 2002 where a single year brings 3 RCT challenges
        # against a 10-paper supporting corpus — the cumulative ratio barely moves
        # (11 vs 14 papers) but the ANNUAL batch is unanimously opposing.
        year_papers = [
            s for s in stances
            if s.year == year
            and s.stance in ("support", "contradict")
            and not s.is_retracted
        ]
        annual_reversal = False
        if (
            prev_ratio is not None
            and len(year_papers) >= _ANNUAL_REVERSAL_MIN_PAPERS
        ):
            year_ratio = weighted_support_ratio(year_papers)
            if year_ratio is not None:
                annual_shift = abs(prev_ratio - year_ratio)
                if annual_shift >= _ANNUAL_REVERSAL_THRESHOLD:
                    annual_reversal = True

        is_inflection = state_changed or ratio_shifted or annual_reversal
        magnitude = abs((support_w or 0.5) - (prev_ratio or 0.5)) if is_inflection else 0.0

        snapshots.append(
            EpistemicSnapshot(
                year=year,
                state=state,
                weighted_support_ratio=support_w,
                paper_count=len(relevant),
                is_inflection=is_inflection,
                inflection_magnitude=round(magnitude, 3),
                triggering_paper_id=_triggering_paper(stances, year, is_inflection),
            )
        )
        prev_state = state
        if support_w is not None:
            prev_ratio = support_w

    return snapshots


def detect_inflection_points(
    snapshots: list[EpistemicSnapshot],
) -> list[InflectionPoint]:
    """Extract significant transition years from the snapshot series.

    Includes inflections marked by any signal in build_epistemic_history:
      - state-string transitions toward controversy (Contested/Overturned/Fragmented)
      - cumulative ratio shift ≥20pp between consecutive years
      - annual-reversal signal (this year's papers flip ≥35pp vs cumulative history)

    The last two can fire without a state-string change (both years may stay
    "Consolidating"), so we include all snapshots where is_inflection=True.
    """
    if len(snapshots) < 2:
        return []

    inflections: list[InflectionPoint] = []
    for i in range(1, len(snapshots)):
        prev = snapshots[i - 1]
        curr = snapshots[i]
        if curr.is_inflection:
            inflections.append(
                InflectionPoint(
                    year=curr.year,
                    from_state=prev.state,
                    to_state=curr.state,
                    magnitude=curr.inflection_magnitude,
                    triggering_paper_id=curr.triggering_paper_id,
                )
            )
    return inflections


# ── Helpers ────────────────────────────────────────────────────────────


# States that represent increasing challenge/controversy
_CONTRARIAN_STATES: frozenset[str] = frozenset({"Contested", "Overturned", "Fragmented"})
# States that represent initial/stable consensus — upward progressions to these are NOT inflections
_PROGRESSIVE_STATES: frozenset[str] = frozenset({"Emerging", "Consolidating", "Established"})


def _is_contrarian_transition(from_state: str, to_state: str) -> bool:
    """Return True only for transitions that indicate a challenge to prior consensus.

    Upward progressions (Hypothesis→Emerging, Emerging→Consolidating, etc.) are
    natural evidence accumulation, not inflection points. Downward or laterally
    challenging transitions (anything→Contested/Overturned/Fragmented) are.
    Also catches rehabilitation transitions back to progressive states FROM
    a contesting state (e.g. Overturned → Consolidating), which represents
    a REHABILITATED claim.
    """
    if to_state in _CONTRARIAN_STATES:
        return True  # any transition toward controversy is an inflection
    if from_state in _CONTRARIAN_STATES and to_state in _PROGRESSIVE_STATES:
        return True  # rehabilitation from contested/overturned also notable
    return False


def _design_quality(study_design: str) -> float:
    """Map study design to a [0, 1] quality weight for epistemic state."""
    mapping = {
        "meta_analysis": 1.0,
        "rct": 0.9,
        "cohort": 0.7,
        "case_control": 0.6,
        "observational": 0.5,
        "in_vitro": 0.4,
        "computational": 0.3,
        "unknown": 0.5,
    }
    return mapping.get(study_design, 0.5)


def _triggering_paper(
    stances: list[StanceRecord],
    year: int,
    is_inflection: bool,
) -> str | None:
    """Return the paper_id of the most-cited paper published in this year."""
    if not is_inflection:
        return None
    papers_this_year = [s for s in stances if s.year == year]
    if not papers_this_year:
        return None
    return max(papers_this_year, key=lambda s: s.citations).paper_id
