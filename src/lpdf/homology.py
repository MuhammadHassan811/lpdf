"""Homology search for novelty assessment (paper, Section III-H).

Named ``homology`` rather than ``novelty`` so that it does not collide with
the ``novelty()`` metric exported from :mod:`lpdf.metrics`; a module and a
function of the same name on the package shadow each other depending on
import order.

Interface only. Novelty is one minus the identity of the closest natural
homologue, found with BLAST or profile search with HHsearch. The tool, its
version, the database and the coverage threshold are recorded with every
result, since a novelty figure cannot be interpreted without them.

Requires: BLAST+ or HH-suite on PATH.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SearchResult:
    """The closest homologue found, with the provenance of the search."""

    best_identity: float
    best_hit_id: str | None
    coverage: float
    tool: str
    tool_version: str
    database: str


def search(sequence: str, cfg: dict[str, Any]) -> SearchResult:
    """Find the closest natural homologue of ``sequence``."""
    raise NotImplementedError(
        "search is not implemented. It must populate every field of "
        "SearchResult, including tool version and database, because a novelty "
        "score reported without them is not reproducible."
    )
