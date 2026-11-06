"""Multi-objective ranking (paper, Section III-I).

Two scoring functions are provided.

``simple_score`` is the general form, paper equation (13):

    S = alpha * (1 / perplexity) + beta * pLDDT - gamma * RMSD

``composite_score`` is the form used in practice: a weighted sum over
components normalised across the candidate set, so that quantities on
different scales can be combined, and so that the structural-deviation term can
be dropped when no reference structure exists.

**On missing references.** RMSD and TM-score are undefined for an
unconditionally generated sequence. When ``rmsd`` is ``None`` the structural
deviation term is omitted and the remaining weights are renormalised. It is
never replaced by a default value, because substituting one would silently
invent a comparison that was never made.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass
class Candidate:
    """One generated sequence and the measurements taken on it.

    Attributes:
        identifier: stable identifier for the candidate.
        sequence: the amino acid sequence.
        perplexity: model perplexity, lower is better.
        plddt: mean predicted confidence in [0, 100], higher is better.
        energy: folding energy in Rosetta energy units, lower is better.
            ``None`` if no energy calculation was run.
        best_identity: identity to the closest natural homologue, in [0, 1].
        function_score: predicted functional plausibility in [0, 1].
        rmsd: deviation from a reference structure, or ``None`` when no
            reference exists. See the module docstring.
        tm_score: fold similarity to a reference, or ``None``.
        reference: what ``rmsd`` and ``tm_score`` were measured against. Must
            be given whenever either is present.
    """

    identifier: str
    sequence: str
    perplexity: float
    plddt: float
    best_identity: float
    function_score: float = 0.0
    energy: float | None = None
    rmsd: float | None = None
    tm_score: float | None = None
    reference: str | None = None

    def __post_init__(self) -> None:
        if (self.rmsd is not None or self.tm_score is not None) and not self.reference:
            raise ValueError(
                f"candidate {self.identifier!r} carries a reference-dependent "
                "metric without naming its reference; set `reference` to the "
                "structure the comparison was made against"
            )


def simple_score(
    perplexity: float,
    plddt: float,
    rmsd: float | None = None,
    alpha: float = 1.0,
    beta: float = 1.0,
    gamma: float = 1.0,
) -> float:
    """Paper equation (13). The RMSD term is omitted when no reference exists."""
    if perplexity <= 0:
        raise ValueError("perplexity must be positive")
    score = alpha * (1.0 / perplexity) + beta * plddt
    if rmsd is not None:
        score -= gamma * rmsd
    return score


def minmax(values: Sequence[float], higher_is_better: bool = True) -> list[float]:
    """Scale ``values`` onto [0, 1] across the candidate set.

    A set whose values are all equal maps to 0.5 throughout, so that a
    component carrying no information neither rewards nor penalises anything.
    """
    if not values:
        return []
    low, high = min(values), max(values)
    if high == low:
        return [0.5] * len(values)
    scaled = [(v - low) / (high - low) for v in values]
    return scaled if higher_is_better else [1.0 - s for s in scaled]


def composite_score(
    candidates: Sequence[Candidate], cfg: dict[str, Any]
) -> list[float]:
    """Score each candidate against the rest of the set.

    Components are structure (pLDDT), energy (lower is better), novelty, and
    predicted function, weighted as configured. Components that are absent for
    every candidate are dropped and the remaining weights renormalised.

    Returns:
        One score per candidate, in the order supplied.
    """
    if not candidates:
        return []

    weights = dict(cfg["scoring"]["weights"])
    penalty = cfg["scoring"]["identity_penalty"]
    max_identity = cfg["novelty"]["max_identity"]

    components: dict[str, list[float]] = {
        "structure": minmax([c.plddt for c in candidates], higher_is_better=True),
        "function": minmax([c.function_score for c in candidates], higher_is_better=True),
    }

    novelties = []
    for c in candidates:
        value = 1.0 - c.best_identity
        if c.best_identity > max_identity:
            value *= penalty
        novelties.append(value)
    components["novelty"] = minmax(novelties, higher_is_better=True)

    if all(c.energy is not None for c in candidates):
        components["energy"] = minmax(
            [float(c.energy) for c in candidates], higher_is_better=False
        )
    else:
        # No energy calculation was run for at least one candidate; drop the
        # term rather than guessing a value for it.
        weights.pop("energy", None)

    total = sum(weights.values())
    if total <= 0:
        raise ValueError("no scoring components remain after dropping absent ones")
    weights = {k: w / total for k, w in weights.items()}

    return [
        sum(weights[name] * components[name][i] for name in weights)
        for i in range(len(candidates))
    ]


def rank(
    candidates: Sequence[Candidate], cfg: dict[str, Any], top_k: int | None = None
) -> list[tuple[Candidate, float]]:
    """Rank candidates best first, discarding those below the score threshold.

    Args:
        candidates: the scored candidate set.
        cfg: protocol configuration.
        top_k: keep only this many, or all of them when ``None``.

    Returns:
        ``(candidate, score)`` pairs in descending score order.
    """
    scores = composite_score(candidates, cfg)
    threshold = cfg["scoring"]["min_score"]
    kept = [(c, s) for c, s in zip(candidates, scores) if s >= threshold]
    kept.sort(key=lambda pair: pair[1], reverse=True)
    return kept[:top_k] if top_k is not None else kept
