"""Structural validation (paper, Section III-G).

Interface only. Validation is two-tier to control cost: every candidate is
folded with ESMFold, and only those whose mean pLDDT reaches the screening
threshold are folded again with AlphaFold2.

**RMSD and TM-score require a reference.** An unconditionally generated
sequence has none, so these metrics apply only in family-specific experiments
with a benchmark structure, or in backbone-conditioned generation where the
target backbone supplies the reference. Functions here take the reference as a
required argument rather than an optional one, so that it cannot be omitted by
accident.

Requires: esmfold or fair-esm, and AlphaFold2 or ColabFold.
"""

from __future__ import annotations

from typing import Any


def fold_screen(sequence: str, cfg: dict[str, Any]):
    """Fold with ESMFold as a fast screen. Returns a structure and mean pLDDT."""
    raise NotImplementedError(
        "fold_screen is not implemented. It should return both the predicted "
        "structure and its mean pLDDT, so the caller can apply the screening "
        "threshold without refolding."
    )


def fold_confirm(sequence: str, cfg: dict[str, Any]):
    """Fold with AlphaFold2 for a higher-fidelity model."""
    raise NotImplementedError(
        "fold_confirm is not implemented. Apply it only to candidates that "
        "passed fold_screen, since it dominates pipeline cost."
    )


def mean_plddt(structure) -> float:
    """Mean per-residue confidence over a predicted structure, equation (9)."""
    raise NotImplementedError("mean_plddt is not implemented.")


def rmsd(structure, reference, reference_name: str) -> float:
    """C-alpha RMSD against a reference, equation (10).

    Args:
        reference_name: what the reference is — a PDB identifier, or the
            target backbone. Required, and recorded with the result.
    """
    if not reference_name:
        raise ValueError(
            "reference_name is required: an RMSD reported without naming its "
            "reference cannot be interpreted"
        )
    raise NotImplementedError("rmsd is not implemented.")


def tm_score(structure, reference, reference_name: str) -> float:
    """TM-score against a reference, equation (11). Above 0.5 indicates the same fold."""
    if not reference_name:
        raise ValueError("reference_name is required; see rmsd()")
    raise NotImplementedError("tm_score is not implemented.")


def self_consistency(screen_structure, confirm_structure) -> float:
    """Agreement between the ESMFold and AlphaFold2 models of one sequence.

    This is the reference-free alternative reported for unconditioned
    generation, where rmsd() and tm_score() do not apply.
    """
    raise NotImplementedError("self_consistency is not implemented.")
