"""Evaluation metrics (paper, Sections III-F to III-I and IV-C).

Only metrics that are well defined without external tooling live here:
perplexity from model log-probabilities, novelty from a homology search result,
the valid sequence rate, and the summary statistics the protocol requires.

Structural metrics are in :mod:`lpdf.structure`, because they need a folding
model, and RMSD and TM-score additionally need a reference structure.
"""

from __future__ import annotations

import math
from typing import Any, Sequence


def perplexity(token_log_probs: Sequence[float]) -> float:
    """Perplexity of a sequence under the model, paper equation (14).

    Args:
        token_log_probs: natural-log probabilities assigned to each generated
            token, one per residue.

    Returns:
        ``exp(-mean(log p))``. Lower is better.

    Raises:
        ValueError: if no log-probabilities are supplied, or any is positive
            (a log-probability cannot exceed zero).
    """
    if not token_log_probs:
        raise ValueError("token_log_probs is empty; perplexity is undefined")
    if any(lp > 0.0 for lp in token_log_probs):
        raise ValueError(
            "token_log_probs contains a positive value; expected natural-log "
            "probabilities, which are at most 0"
        )
    mean_log_prob = sum(token_log_probs) / len(token_log_probs)
    return math.exp(-mean_log_prob)


def novelty(best_identity: float) -> float:
    """Novelty of a candidate, paper equation (12).

    Args:
        best_identity: fractional sequence identity to the closest natural
            homologue, in [0, 1], as returned by the homology search.

    Returns:
        ``1 - best_identity``. Higher is more novel.
    """
    if not 0.0 <= best_identity <= 1.0:
        raise ValueError(f"best_identity must lie in [0, 1], got {best_identity}")
    return 1.0 - best_identity


def is_overly_similar(best_identity: float, cfg: dict[str, Any]) -> bool:
    """Return True if a candidate reproduces an existing protein too closely."""
    return best_identity > cfg["novelty"]["max_identity"]


def valid_rate(n_valid: int, n_total: int) -> float:
    """Percentage of generated sequences that survive filtering, equation (8)."""
    if n_total <= 0:
        raise ValueError("n_total must be positive")
    if not 0 <= n_valid <= n_total:
        raise ValueError(f"n_valid ({n_valid}) must lie in [0, {n_total}]")
    return 100.0 * n_valid / n_total


def median_iqr(values: Sequence[float]) -> tuple[float, float, float]:
    """Median and interquartile range, the protocol's required summary.

    The protocol asks for distributions rather than point estimates, so this
    returns ``(median, q1, q3)`` using linear interpolation between order
    statistics.
    """
    if not values:
        raise ValueError("values is empty")
    ordered = sorted(values)

    def quantile(q: float) -> float:
        if len(ordered) == 1:
            return float(ordered[0])
        position = q * (len(ordered) - 1)
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return float(ordered[lower])
        weight = position - lower
        return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)

    return quantile(0.5), quantile(0.25), quantile(0.75)


def min_attainable_pvalue(n_pairs: int) -> float:
    """Smallest two-sided p-value the signed-rank test can return for ``n_pairs``.

    With every difference in the same direction the two-sided p-value is
    ``2 / 2**n``. Below six pairs this floor exceeds 0.05, so no result can
    reach conventional significance however large the effect. Check this before
    deciding how many candidates to generate per model.
    """
    if n_pairs < 1:
        raise ValueError("n_pairs must be at least 1")
    return 2.0 ** (1 - n_pairs)


def paired_wilcoxon(a: Sequence[float], b: Sequence[float]):
    """Wilcoxon signed-rank test between paired per-candidate values.

    The protocol requires this test when comparing an adapted model against its
    unadapted baseline. It delegates to SciPy rather than reimplementing the
    test, since the tie and zero-difference corrections matter.

    Two guards are applied first. Samples of unequal length are rejected,
    because the test is paired. Samples with no non-zero difference are also
    rejected: SciPy returns ``p = 1.0`` for these after an internal division by
    zero, which looks like a legitimate null result rather than a degenerate
    comparison.

    Note that the attainable p-value is bounded by the number of pairs; see
    :func:`min_attainable_pvalue`.

    Raises:
        ImportError: if SciPy is not installed.
        ValueError: if the samples differ in length, are empty, or are identical.
    """
    if len(a) != len(b):
        raise ValueError(
            f"paired samples must be the same length, got {len(a)} and {len(b)}"
        )
    if not a:
        raise ValueError("paired samples are empty")
    if all(x == y for x, y in zip(a, b)):
        raise ValueError(
            "every pair is identical, so the signed-rank test is degenerate; "
            "SciPy would report p = 1.0 here after dividing by zero"
        )
    try:
        from scipy.stats import wilcoxon
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "paired_wilcoxon requires SciPy; install it with 'pip install scipy'"
        ) from exc
    return wilcoxon(a, b)
