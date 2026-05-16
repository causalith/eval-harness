"""Mutation lineage detection between paper-level claim assertions.

Mutations are detected in a background job (not the hot path) to avoid
blocking the first render. The pre-filter uses simple text similarity to
whittle 50+ papers down to ~30 candidate pairs before calling the LLM.

The 8-way mutation taxonomy (per the plan):
  REPLICATED, NARROWED, BROADENED, QUALIFIED,
  REVERSED, FRAGMENTED, RETRACTED, REHABILITATED

Cost envelope: ~30 pairs × $0.0003 (Groq Llama-3.3-70b) = $0.01/claim,
cached aggressively (90-day TTL) so subsequent views are free.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any, Literal

from causalith_eval.support_calculator import StanceRecord

logger = logging.getLogger(__name__)

MutationType = Literal[
    "REPLICATED",
    "NARROWED",
    "BROADENED",
    "QUALIFIED",
    "REVERSED",
    "FRAGMENTED",
    "RETRACTED",
    "REHABILITATED",
    "UNRELATED",
]

VALID_MUTATION_TYPES: frozenset[str] = frozenset(
    ["REPLICATED", "NARROWED", "BROADENED", "QUALIFIED",
     "REVERSED", "FRAGMENTED", "RETRACTED", "REHABILITATED", "UNRELATED"]
)

MUTATION_CLASSIFY_TIMEOUT_S = 6.0
MUTATION_CLASSIFY_MAX_TOKENS = 120
MIN_CONFIDENCE_TO_PERSIST = 0.75
MAX_PAIRS_PER_CLAIM = 40  # tighter budget: 40 pairs × $0.0003 = $0.012/claim


@dataclass(frozen=True, slots=True)
class Mutation:
    parent_paper_id: str
    child_paper_id: str
    parent_title: str
    child_title: str
    parent_year: int | None
    child_year: int | None
    mutation_type: MutationType
    what_changed: str
    confidence: float
    detector_model: str


MUTATION_PROMPT = """You classify how one scientific paper's claim about a topic MUTATED relative to an earlier paper on the same topic.

EARLIER PAPER (parent):
Title: {parent_title}
Year: {parent_year}
Abstract: {parent_text}

LATER PAPER (child):
Title: {child_title}
Year: {child_year}
Abstract: {child_text}

Choose the mutation type that best describes how the child paper's finding relates to the parent's:

REPLICATED: Child confirms same claim in same or similar population, same effect direction.
NARROWED: Child restricts the claim to a subpopulation or subset of conditions.
BROADENED: Child extends the claim to a new population or domain.
QUALIFIED: Child adds conditions or caveats but keeps the same general direction.
REVERSED: Child reports opposite direction (same intervention/outcome, opposite effect).
FRAGMENTED: Child splits the claim into distinct sub-claims for different conditions.
RETRACTED: Child paper is a retraction notice for the parent.
REHABILITATED: Child partially restores a previously challenged or reversed claim in a narrower form.
UNRELATED: Papers study different topics despite superficial keyword overlap.

Reply on a single line:
[TYPE] confidence=0.XX — one sentence describing what changed

Example: [NARROWED] confidence=0.85 — Protective effect found only in women aged 50-59, not the broader postmenopausal population.
"""


async def detect_mutations_for_claim(
    stances: list[StanceRecord],
    *,
    max_pairs: int = MAX_PAIRS_PER_CLAIM,
    confidence_threshold: float = MIN_CONFIDENCE_TO_PERSIST,
) -> list[Mutation]:
    """Detect mutations among a set of papers. Runs in background."""
    relevant = [
        s for s in stances
        if s.stance in ("support", "contradict", "qualified") and not s.is_retracted
    ]
    # Sort by year so parent always precedes child in pairs
    relevant_sorted = sorted(relevant, key=lambda s: (s.year or 9999, s.paper_id))

    candidate_pairs = _prefilter_pairs(relevant_sorted, max_pairs)
    if not candidate_pairs:
        return []

    sem = asyncio.Semaphore(5)

    async def _bound(parent: StanceRecord, child: StanceRecord) -> Mutation | None:
        async with sem:
            return await _classify_pair(parent, child)

    results = await asyncio.gather(
        *(_bound(p, c) for p, c in candidate_pairs),
        return_exceptions=True,
    )

    mutations: list[Mutation] = []
    for result in results:
        if isinstance(result, BaseException):
            logger.warning("mutation classify error: %s", result)
            continue
        if result is None:
            continue
        if result.mutation_type != "UNRELATED" and result.confidence >= confidence_threshold:
            mutations.append(result)

    return mutations


# ── Pre-filtering ──────────────────────────────────────────────────────


def _prefilter_pairs(
    papers: list[StanceRecord],
    max_pairs: int,
) -> list[tuple[StanceRecord, StanceRecord]]:
    """Select candidate (parent, child) pairs using token overlap.

    Two papers are candidates if their title tokens overlap significantly
    (≥3 shared content words). This is a cheap proxy for same-topic pairs
    without requiring an embedding API call in the hot path.
    """
    candidate_pairs: list[tuple[StanceRecord, StanceRecord]] = []
    tokenized = [(s, _content_tokens(s.title)) for s in papers]

    for i, (p1, tok1) in enumerate(tokenized):
        for p2, tok2 in tokenized[i + 1:]:
            if (p1.year or 0) >= (p2.year or 9999):
                continue  # parent must precede child chronologically
            overlap = len(tok1 & tok2)
            if overlap >= 4:  # ≥4 shared discriminating tokens (generic vocab already stripped)
                candidate_pairs.append((p1, p2))
            if len(candidate_pairs) >= max_pairs:
                return candidate_pairs

    return candidate_pairs


def _content_tokens(text: str) -> set[str]:
    # Generic structural words
    _STOP = frozenset({
        "the", "and", "for", "with", "this", "that", "from", "are", "was",
        "been", "have", "has", "had", "not", "its", "into", "than", "more",
        # Generic study-design vocabulary (too common across all papers in any domain)
        "study", "analysis", "review", "trial", "effect", "effects", "results",
        "findings", "outcomes", "evidence", "data", "methods", "patients",
        "subjects", "participants", "cohort", "based", "controlled", "randomized",
        "systematic", "clinical", "observational", "prospective", "retrospective",
        # Generic relationship vocabulary
        "association", "associations", "relationship", "between", "among",
        "compared", "comparison", "versus", "impact", "role", "factors",
        # Common medical/science qualifiers that don't discriminate claim pairs
        "treatment", "therapy", "therapies", "disease", "health", "risk",
        "risks", "rates", "levels", "dose", "doses", "high", "lower", "higher",
        "increased", "decreased", "significant", "significantly",
        # Common population terms
        "women", "adults", "patients", "population", "human", "humans",
        "mice", "male", "female", "older", "young",
    })
    return {t for t in re.findall(r"[a-z]{4,}", text.lower()) if t not in _STOP}


# ── LLM classification ─────────────────────────────────────────────────


async def _classify_pair(
    parent: StanceRecord,
    child: StanceRecord,
) -> Mutation | None:
    parent_text = (parent.abstract or parent.title)[:600]
    child_text = (child.abstract or child.title)[:600]

    prompt = MUTATION_PROMPT.format(
        parent_title=parent.title,
        parent_year=parent.year or "unknown",
        parent_text=parent_text,
        child_title=child.title,
        child_year=child.year or "unknown",
        child_text=child_text,
    )

    try:
        detector_model, raw = await asyncio.wait_for(
            _llm_call(prompt), timeout=MUTATION_CLASSIFY_TIMEOUT_S
        )
    except asyncio.TimeoutError:
        logger.info("mutation.classify timeout pair %s→%s", parent.paper_id, child.paper_id)
        return None
    except Exception as exc:
        logger.warning("mutation.classify error: %s", exc)
        return None

    return _parse_mutation_response(raw, parent, child, detector_model=detector_model)


async def _llm_call(prompt: str) -> tuple[str, str]:
    """Mutation LLM classification is intentionally not bundled publicly.

    The public harness keeps only the deterministic mutation pre-filter unit
    tests. Full mutation classification runs inside the Causalith API, where
    provider keys and cache policy stay private.
    """
    raise RuntimeError("mutation LLM classification is not part of the public eval harness")


_MUTATION_RE = re.compile(
    r"\[(REPLICATED|NARROWED|BROADENED|QUALIFIED|REVERSED|FRAGMENTED|RETRACTED|REHABILITATED|UNRELATED)\]"
    r"\s+confidence\s*=\s*(0\.\d+|1\.0)",
    re.IGNORECASE,
)


def _parse_mutation_response(
    raw: str,
    parent: StanceRecord,
    child: StanceRecord,
    *,
    detector_model: str = "unknown",
) -> Mutation | None:
    if not raw:
        return None

    match = _MUTATION_RE.search(raw)
    if not match:
        return None

    mutation_type_raw = match.group(1).upper()
    if mutation_type_raw not in VALID_MUTATION_TYPES:
        return None

    confidence = float(match.group(2))
    what_changed = raw[match.end():].lstrip(" —:-").strip()
    what_changed = what_changed[:300] if what_changed else "no description"

    return Mutation(
        parent_paper_id=parent.paper_id,
        child_paper_id=child.paper_id,
        parent_title=parent.title,
        child_title=child.title,
        parent_year=parent.year,
        child_year=child.year,
        mutation_type=mutation_type_raw,  # type: ignore[arg-type]
        what_changed=what_changed,
        confidence=confidence,
        detector_model=detector_model,
    )


def build_lineage_tree(mutations: list[Mutation]) -> list[dict[str, Any]]:
    """Convert a flat list of mutations into a tree structure for the frontend.

    Each node has: id, title, year, children (list of edges).
    Each edge has: mutation_type, what_changed, confidence, child_node.
    """
    if not mutations:
        return []

    children_of: dict[str, list[dict[str, Any]]] = {}
    all_child_ids: set[str] = set()

    for m in mutations:
        edge: dict[str, Any] = {
            "mutation_type": m.mutation_type,
            "what_changed": m.what_changed,
            "confidence": m.confidence,
            "child": {
                "id": m.child_paper_id,
                "title": m.child_title,
                "year": m.child_year,
                "children": [],
            },
        }
        children_of.setdefault(m.parent_paper_id, []).append(edge)
        all_child_ids.add(m.child_paper_id)

    # Root nodes are parents that are never a child
    roots: list[dict[str, Any]] = []
    for m in mutations:
        if m.parent_paper_id not in all_child_ids:
            node: dict[str, Any] = {
                "id": m.parent_paper_id,
                "title": m.parent_title,
                "year": m.parent_year,
                "children": children_of.get(m.parent_paper_id, []),
            }
            if not any(r["id"] == node["id"] for r in roots):
                roots.append(node)

    return roots
