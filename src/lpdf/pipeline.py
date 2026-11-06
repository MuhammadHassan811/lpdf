"""End-to-end orchestration (paper, Algorithm 1).

The stages that are implemented can be run today; the rest raise
NotImplementedError with a message naming what they need. The ordering here is
the contract: filter before folding, screen before confirming, and never score
a reference-dependent metric that has no reference.
"""

from __future__ import annotations

from typing import Any, Iterable

from lpdf.filters import apply_filters
from lpdf.scoring import Candidate, rank


def run(corpus_path: str, base_model: str, n: int, cfg: dict[str, Any]):
    """Run the full pipeline from corpus to ranked candidates."""
    raise NotImplementedError(
        "run is not implemented end to end. The generation, folding and "
        "homology stages must be wired up first; see lpdf.generate, "
        "lpdf.structure and lpdf.homology."
    )


def score_existing(candidates: Iterable[Candidate], cfg: dict[str, Any], top_k: int | None = None):
    """Rank candidates that have already been measured.

    This part of the pipeline is usable now: given sequences with their
    perplexity, pLDDT, identity and optional energy already computed, it
    applies the configured weighting and returns the ranked set.
    """
    return rank(list(candidates), cfg, top_k=top_k)


def filter_sequences(sequences: Iterable[str], cfg: dict[str, Any]):
    """Apply the syntactic and composition filters. Usable now."""
    return apply_filters(sequences, cfg)
