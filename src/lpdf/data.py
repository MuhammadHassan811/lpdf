"""Corpus ingest, annotation and preprocessing (paper, Section III-B).

Interface only. Preprocessing must remove duplicates, sequences with ambiguous
or non-standard residues, and sequences outside the configured length range,
and must record a provenance entry for every annotation it derives: the tool,
its version, the parameters and the date. Family benchmark subsets record the
PDB identifiers of their reference structures, since those are what make
reference-dependent structural metrics applicable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator


def load_corpus(path: str | Path) -> Iterator[str]:
    """Stream sequences from a FASTA corpus."""
    raise NotImplementedError(
        "load_corpus is not implemented. It should stream records from a FASTA "
        "file rather than reading the corpus into memory."
    )


def preprocess(sequences: Iterator[str], cfg: dict[str, Any]) -> Iterator[str]:
    """Deduplicate, clean and length-filter a corpus."""
    raise NotImplementedError(
        "preprocess is not implemented. See lpdf.filters for the residue and "
        "length rules it must apply."
    )
