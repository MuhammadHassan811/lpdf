# LPDF — LLM-Based Protein Design Framework

Reference implementation of the pipeline described in *"A Technique to Design
Novel Protein Sequences Using Large Language Models: A Unified Framework and
Evaluation Protocol."*

LPDF turns a protein corpus into a ranked set of candidate sequences. It couples
parameter-efficient adaptation of a language model with conditional generation,
syntactic and biophysical filtering, two-tier structural validation, homology-based
novelty assessment and multi-objective ranking.

## Status

> **This repository is under development.** The filtering, metric and scoring
> modules are implemented and tested. The generation, adaptation, structural
> prediction and refinement modules define their interfaces but delegate to
> external tools that are not yet wired up — they raise `NotImplementedError`
> with a message naming what is required.
>
> **No experimental results are included.** The accompanying paper specifies an
> evaluation protocol; the empirical study applying it is in progress. When that
> study is published, generated sequences, evaluation outputs and predicted
> structures will be released here with a DOI.

| Module | Status |
|---|---|
| `filters` — syntactic and composition filtering | Implemented, tested |
| `metrics` — perplexity, novelty, valid rate | Implemented, tested |
| `scoring` — multi-objective ranking | Implemented, tested |
| `config` — configuration loading | Implemented, tested |
| `data` — corpus ingest and preprocessing | Interface only |
| `adapt` — LoRA / full fine-tuning | Interface only |
| `generate` — conditional generation | Interface only |
| `structure` — ESMFold screen, AlphaFold2 confirm | Interface only |
| `homology` — BLAST / HHsearch search | Interface only |
| `refine` — masked re-sampling | Interface only |

## Pipeline

```
corpus ──▶ preprocess ──▶ adapt model ──▶ generate (conditional)
                                              │
                                              ▼
                              syntactic + composition filter
                                              │
                                              ▼
                               ESMFold screen (pLDDT ≥ 70)
                                              │
                        ┌─────────────────────┴───────────┐
                   below threshold                   at or above
                        │                                 │
                        ▼                                 ▼
                 masked re-sampling                 AlphaFold2 confirm
                 (3–5 iterations)                         │
                        │                                 ▼
                        └────────────────▶   novelty search (BLAST/HHsearch)
                                                          │
                                                          ▼
                                             multi-objective ranking
                                                          │
                                                          ▼
                                                   top-k candidates
```

## Acceptance criteria

These are fixed by the protocol, not tuned after the fact. They live in
`configs/default.yaml` and anything that changes them must say so when reporting
results.

| Criterion | Default |
|---|---|
| Allowed residues | the 20 standard amino acids |
| Sequence length | 50–1024 |
| Max hydrophobic fraction | 0.50 |
| ESMFold screening threshold | mean pLDDT ≥ 70 |
| High-confidence threshold | mean pLDDT ≥ 80 |
| Novelty penalty | applied above 80% identity to closest homologue |
| Refinement acceptance | pLDDT +5, or Rosetta energy −2 REU |
| Ranking weights | 0.35 structure, 0.30 energy, 0.20 novelty, 0.15 function |

### A note on RMSD and TM-score

Both metrics compare a predicted structure to a **reference**, and an
unconditionally generated sequence has none. This implementation therefore
computes them only when a reference is supplied — a benchmark structure in
family-specific experiments, or the target backbone in backbone-conditioned
generation. For unconditioned generation, structural quality is reported by
pLDDT alone, with ESMFold/AlphaFold2 agreement available as a self-consistency
measure.

`scoring.composite_score` omits the structural-deviation term when no reference
is present rather than substituting a default. This is deliberate: reporting a
reference-dependent metric without naming its reference is a reporting error.

## Install

```bash
git clone https://github.com/MuhammadHassan811/lpdf.git
cd lpdf
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

SciPy is optional and needed only by `metrics.paired_wilcoxon`:

```bash
pip install -e ".[stats]"
```

External tools are not installed by pip and are needed only for the stages that
use them: ESMFold and AlphaFold2 (or ColabFold) for structural prediction,
BLAST+ or HH-suite for novelty search, and optionally PyRosetta for energy terms.

### Sample size and the paired test

The signed-rank test's attainable p-value is bounded by the number of pairs: with
every difference in the same direction the two-sided p-value is `2 / 2**n`. That
floor is 0.0625 at five pairs and 0.031 at six, so **fewer than six paired
candidates cannot reach p < 0.05 however large the effect.** Call
`metrics.min_attainable_pvalue(n)` when planning how many candidates to generate.

## Use

Filtering a batch, with reasons for anything discarded:

```python
from lpdf.config import load_config
from lpdf.filters import apply_filters

cfg = load_config()

seqs = [
    "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQ",  # passes
    "MKTFFVLLLCTFTVVSA",                                                    # too short
    "AVILMFWY" * 10,                                                        # too hydrophobic
]
kept, rejected = apply_filters(seqs, cfg)

for seq, reasons in rejected:
    print(f"{seq[:20]}... rejected: {'; '.join(reasons)}")
```

Ranking candidates whose measurements you already have:

```python
from lpdf.scoring import Candidate, rank

candidates = [
    Candidate("c1", seq_a, perplexity=9.0, plddt=85.0, best_identity=0.20, function_score=0.8),
    Candidate("c2", seq_b, perplexity=11.0, plddt=70.0, best_identity=0.50, function_score=0.4),
]
for candidate, score in rank(candidates, cfg, top_k=10):
    print(f"{candidate.identifier}\t{score:.3f}")
```

A candidate carrying an RMSD or TM-score must name what it was measured
against, or construction fails:

```python
Candidate("c3", seq_c, perplexity=9.0, plddt=80.0, best_identity=0.3,
          rmsd=2.0, reference="PDB 1ABC")
```

Run the tests:

```bash
pytest -q
```

## Layout

```
lpdf/
├── configs/default.yaml      protocol thresholds and weights
├── src/lpdf/
│   ├── config.py             configuration loading
│   ├── filters.py            syntactic and composition filters
│   ├── metrics.py            perplexity, novelty, valid rate
│   ├── scoring.py            multi-objective ranking
│   ├── data.py               corpus ingest (interface)
│   ├── adapt.py              model adaptation (interface)
│   ├── generate.py           conditional generation (interface)
│   ├── structure.py          folding and structural metrics (interface)
│   ├── homology.py           homology search (interface)
│   ├── refine.py             masked re-sampling (interface)
│   └── pipeline.py           orchestration
├── figures/                  scripts that generate the paper's figures
└── tests/
```

## Reproducibility

Every run records its random seeds, resolved configuration, package versions and
the version of each external tool invoked. Reported figures must name the
configuration they came from. The protocol requires distributions rather than
point estimates: report the number of sequences generated per model, the length
range, the sampling parameters, and the number of independent runs, with medians
and interquartile ranges, and Wilcoxon signed-rank tests for paired comparisons.

## Citation

See `CITATION.cff`. Once the preprint is posted, cite it by DOI.

## Licence

MIT — see `LICENSE`.
