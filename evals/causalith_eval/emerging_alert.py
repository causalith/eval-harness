"""Emerging-challenge alert with Bayesian regime-shift gate.

The alert fires only when:
  1. ≥3 recent papers (within 3 years) exist in the relevant pool.
  2. ≥5 historical papers exist (otherwise the prior is too weak).
  3. Bayesian posterior probability of a support-rate regime shift is > 0.70.

This kills false positives on sparse data (the friend's plan fired on 2
recent papers, which is noise, not signal).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from causalith_eval.support_calculator import (
    StanceRecord,
    weighted_support_ratio,
)


AlertLevel = Literal["none", "amber", "red"]


@dataclass(frozen=True, slots=True)
class EmergingAlert:
    level: AlertLevel
    historical_ratio: float | None
    recent_ratio: float | None
    recent_count: int
    historical_count: int
    has_high_quality_challenger: bool
    posterior_probability: float


def emerging_challenge_alert(
    stances: list[StanceRecord],
    *,
    today: date | None = None,
    posterior_threshold: float = 0.70,
    recency_years: int = 3,
    min_recent: int = 3,
    min_historical: int = 5,
) -> EmergingAlert:
    """Compute the emerging-challenge alert for a set of stances.

    Returns an alert with level='none' when the gate conditions are not met.
    The Bayesian computation uses a beta-binomial model with the historical
    support rate as the prior. We ask: given recent observations, what is
    the posterior probability that the current support rate is below 0.5?
    """
    _today = today or date.today()

    relevant = [
        s for s in stances
        if s.stance in ("support", "contradict") and not s.is_retracted
    ]
    recent = [s for s in relevant if s.year is not None and (_today.year - s.year) <= recency_years]
    historical = [s for s in relevant if s.year is None or (_today.year - s.year) > recency_years]

    if len(recent) < min_recent or len(historical) < min_historical:
        return EmergingAlert(
            level="none",
            historical_ratio=weighted_support_ratio(historical),
            recent_ratio=weighted_support_ratio(recent),
            recent_count=len(recent),
            historical_count=len(historical),
            has_high_quality_challenger=False,
            posterior_probability=0.0,
        )

    hist_ratio = weighted_support_ratio(historical)
    rec_ratio = weighted_support_ratio(recent)

    if hist_ratio is None or rec_ratio is None:
        return EmergingAlert(
            level="none",
            historical_ratio=hist_ratio,
            recent_ratio=rec_ratio,
            recent_count=len(recent),
            historical_count=len(historical),
            has_high_quality_challenger=False,
            posterior_probability=0.0,
        )

    # Only alert on declining support
    if rec_ratio >= hist_ratio - 0.15:
        return EmergingAlert(
            level="none",
            historical_ratio=hist_ratio,
            recent_ratio=rec_ratio,
            recent_count=len(recent),
            historical_count=len(historical),
            has_high_quality_challenger=False,
            posterior_probability=0.0,
        )

    posterior = _bayesian_shift_probability(historical, recent)

    if posterior < posterior_threshold:
        return EmergingAlert(
            level="none",
            historical_ratio=hist_ratio,
            recent_ratio=rec_ratio,
            recent_count=len(recent),
            historical_count=len(historical),
            has_high_quality_challenger=False,
            posterior_probability=posterior,
        )

    recent_challengers = [s for s in recent if s.stance == "contradict"]
    has_hq = any(s.study_design in ("rct", "meta_analysis") for s in recent_challengers)

    level: AlertLevel = "red" if has_hq else "amber"
    return EmergingAlert(
        level=level,
        historical_ratio=hist_ratio,
        recent_ratio=rec_ratio,
        recent_count=len(recent),
        historical_count=len(historical),
        has_high_quality_challenger=has_hq,
        posterior_probability=posterior,
    )


def _bayesian_shift_probability(
    historical: list[StanceRecord],
    recent: list[StanceRecord],
) -> float:
    """Bayesian beta-binomial posterior P(current_rate < 0.5).

    Prior: beta(alpha, beta) derived from historical support counts.
    Likelihood: recent paper counts.

    Uses scipy if available for the CDF; falls back to a Gaussian
    approximation otherwise so the module has no hard scipy dependency.
    """
    hist_support = sum(1 for s in historical if s.stance == "support")
    hist_total = len(historical)
    hist_contra = hist_total - hist_support

    # Beta prior parameters (add 1 for uniform start)
    alpha_prior = hist_support + 1
    beta_prior = hist_contra + 1

    rec_support = sum(1 for s in recent if s.stance == "support")
    rec_total = len(recent)
    rec_contra = rec_total - rec_support

    # Posterior parameters
    alpha_post = alpha_prior + rec_support
    beta_post = beta_prior + rec_contra

    try:
        from scipy.stats import beta as scipy_beta  # type: ignore[import-not-found]
        return float(scipy_beta.cdf(0.5, alpha_post, beta_post))
    except ImportError:
        return _gaussian_approx_cdf(alpha_post, beta_post)


def _gaussian_approx_cdf(alpha: float, beta: float) -> float:
    """Normal approximation to beta CDF P(X < 0.5)."""
    import math

    mean = alpha / (alpha + beta)
    variance = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1))
    std = math.sqrt(variance)
    if std == 0:
        return 1.0 if mean < 0.5 else 0.0
    z = (0.5 - mean) / std
    return _standard_normal_cdf(z)


def _standard_normal_cdf(z: float) -> float:
    import math
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2)))
