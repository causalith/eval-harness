"""Claim identity: map (subject, object, direction) to a stable hash.

The hash is the primary key used across all claim_stances, claim_mutations,
and claim_epistemic_history rows. Two different phrasings of the same causal
relationship (e.g. "estrogen reduces CV risk" vs "HRT lowers cardiovascular
events") produce different hashes unless concept resolution unifies them —
which is acceptable for v1 because search-query matching will surface the
same papers regardless.
"""

from __future__ import annotations

import hashlib
import re


def normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation for identity matching."""
    lowered = text.lower().strip()
    lowered = re.sub(r"[^\w\s]", " ", lowered)
    return " ".join(lowered.split())


def compute_claim_identity_hash(
    subject: str,
    object_: str,
    predicate_direction: str,
) -> str:
    """Return a SHA-256 hex digest stable across minor phrasings.

    Falls back to normalized text when no concept resolution is available
    (v1 behavior). The pipe character is used as a separator because it cannot
    appear in a normalized concept name.
    """
    subj = normalize_text(subject)
    obj = normalize_text(object_)
    direction = predicate_direction.lower().strip()
    raw = f"{subj}|{obj}|{direction}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
