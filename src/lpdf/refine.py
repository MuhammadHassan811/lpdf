"""Iterative refinement (paper, Section III-J).

Interface only. Candidates that pass filtering but fall short of the confidence
threshold are refined rather than discarded: regions of low per-residue
confidence or high predicted energy are masked and re-sampled conditioned on
their neighbours, for three to five iterations, so the refined sequence does
not drift far from its design constraints.

A refined candidate is accepted if its pLDDT improves by more than
refine.accept_plddt_gain, or its energy improves by more than
refine.accept_energy_gain, relative to the previous iteration.
"""

from __future__ import annotations

from typing import Any


def refine(sequence: str, structure, model, cfg: dict[str, Any]) -> str:
    """Mask and re-sample low-confidence regions of ``sequence``."""
    raise NotImplementedError(
        "refine is not implemented. It should stop at "
        "cfg['refine']['max_iterations'] and return the best accepted variant, "
        "or the original sequence when no iteration meets the acceptance gain."
    )
