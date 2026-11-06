"""LPDF — LLM-Based Protein Design Framework.

Reference implementation of the pipeline described in "A Technique to Design
Novel Protein Sequences Using Large Language Models: A Unified Framework and
Evaluation Protocol".

The filtering, metric and scoring modules are implemented. The stages that
depend on external tooling — corpus ingest, model adaptation, generation,
structural prediction, homology search and refinement — define their interfaces
and raise NotImplementedError until wired up.
"""

__version__ = "0.1.0"

from lpdf.config import load_config
from lpdf.filters import apply_filters, passes_filters, rejection_reasons
from lpdf.metrics import median_iqr, novelty, perplexity, valid_rate
from lpdf.scoring import Candidate, composite_score, rank, simple_score

__all__ = [
    "__version__",
    "load_config",
    "apply_filters",
    "passes_filters",
    "rejection_reasons",
    "perplexity",
    "novelty",
    "valid_rate",
    "median_iqr",
    "Candidate",
    "composite_score",
    "rank",
    "simple_score",
]
