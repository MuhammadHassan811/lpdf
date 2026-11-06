"""Syntactic and biophysical filtering (paper, Section III-F).

Filtering runs before any structural prediction, because prediction is the most
expensive stage in the pipeline. A sequence must clear both checks to proceed:

1. Syntactic validity — only the 20 standard amino acids, no stop codons or
   other non-residue symbols, and a length inside the configured range.
2. Composition — a sequence whose hydrophobic fraction exceeds the configured
   maximum is rejected, since such sequences are unlikely to fold or express.

The set of residues counted as hydrophobic is configuration, not a constant,
because definitions differ between sources and a study must be able to state
which one it used.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence


def _filters(cfg: dict[str, Any]) -> dict[str, Any]:
    return cfg["filters"]


def is_syntactically_valid(seq: str, cfg: dict[str, Any]) -> bool:
    """Return True if ``seq`` uses only allowed residues and has a legal length."""
    f = _filters(cfg)
    if not seq:
        return False
    if not f["min_length"] <= len(seq) <= f["max_length"]:
        return False
    allowed = set(f["allowed_residues"])
    return all(residue in allowed for residue in seq)


def hydrophobic_fraction(seq: str, cfg: dict[str, Any]) -> float:
    """Fraction of residues in ``seq`` that are hydrophobic.

    Returns 0.0 for an empty sequence.
    """
    if not seq:
        return 0.0
    hydrophobic = set(_filters(cfg)["hydrophobic_residues"])
    return sum(1 for residue in seq if residue in hydrophobic) / len(seq)


def composition_ok(seq: str, cfg: dict[str, Any]) -> bool:
    """Return True if ``seq`` is not excessively hydrophobic."""
    return hydrophobic_fraction(seq, cfg) <= _filters(cfg)["max_hydrophobic_fraction"]


def passes_filters(seq: str, cfg: dict[str, Any]) -> bool:
    """Return True if ``seq`` clears both the syntactic and composition checks."""
    return is_syntactically_valid(seq, cfg) and composition_ok(seq, cfg)


def rejection_reasons(seq: str, cfg: dict[str, Any]) -> list[str]:
    """Explain why ``seq`` was rejected.

    Returns an empty list when the sequence passes. Reasons are reported rather
    than counted only, so that a study can say which filter removed what.
    """
    f = _filters(cfg)
    reasons: list[str] = []

    if not seq:
        return ["empty sequence"]

    if len(seq) < f["min_length"]:
        reasons.append(f"too short: {len(seq)} < {f['min_length']}")
    elif len(seq) > f["max_length"]:
        reasons.append(f"too long: {len(seq)} > {f['max_length']}")

    allowed = set(f["allowed_residues"])
    bad = sorted({residue for residue in seq if residue not in allowed})
    if bad:
        reasons.append("non-standard residues: " + ", ".join(repr(b) for b in bad))

    fraction = hydrophobic_fraction(seq, cfg)
    limit = f["max_hydrophobic_fraction"]
    if fraction > limit:
        reasons.append(f"hydrophobic fraction {fraction:.2f} exceeds {limit:.2f}")

    return reasons


def apply_filters(
    sequences: Iterable[str], cfg: dict[str, Any]
) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Partition ``sequences`` into those that pass and those that do not.

    Returns:
        ``(kept, rejected)`` where ``rejected`` pairs each discarded sequence
        with its reasons, so the filtering stage is auditable.
    """
    kept: list[str] = []
    rejected: list[tuple[str, list[str]]] = []
    for seq in sequences:
        reasons = rejection_reasons(seq, cfg)
        if reasons:
            rejected.append((seq, reasons))
        else:
            kept.append(seq)
    return kept, rejected
