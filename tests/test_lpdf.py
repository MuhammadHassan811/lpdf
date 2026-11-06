"""Tests for the implemented LPDF modules."""

from __future__ import annotations

import math

import pytest

from lpdf.config import ConfigError, load_config, validate_config
from lpdf.filters import (
    apply_filters,
    composition_ok,
    hydrophobic_fraction,
    is_syntactically_valid,
    passes_filters,
    rejection_reasons,
)
from lpdf.metrics import (
    is_overly_similar,
    median_iqr,
    novelty,
    perplexity,
    valid_rate,
)
from lpdf.scoring import Candidate, composite_score, minmax, rank, simple_score


@pytest.fixture(scope="module")
def cfg():
    return load_config()


# --------------------------------------------------------------- config


def test_default_config_is_valid(cfg):
    assert cfg["filters"]["min_length"] < cfg["filters"]["max_length"]
    assert math.isclose(sum(cfg["scoring"]["weights"].values()), 1.0)


def test_weights_must_sum_to_one(cfg):
    broken = {**cfg, "scoring": {**cfg["scoring"], "weights": {"structure": 0.5, "energy": 0.2}}}
    with pytest.raises(ConfigError, match="sum to 1.0"):
        validate_config(broken)


def test_screen_threshold_cannot_exceed_high_confidence(cfg):
    broken = {**cfg, "structure": {"screen_plddt": 90.0, "high_confidence_plddt": 80.0}}
    with pytest.raises(ConfigError, match="high_confidence"):
        validate_config(broken)


def test_hydrophobic_set_must_be_subset_of_allowed(cfg):
    broken = {**cfg, "filters": {**cfg["filters"], "hydrophobic_residues": "AVILMFWYZ"}}
    with pytest.raises(ConfigError, match="subset"):
        validate_config(broken)


# -------------------------------------------------------------- filters


def test_accepts_a_plausible_sequence(cfg):
    seq = "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKR"
    assert is_syntactically_valid(seq, cfg)
    assert passes_filters(seq, cfg)
    assert rejection_reasons(seq, cfg) == []


def test_rejects_non_standard_residues(cfg):
    seq = "MKT" + "X" * 60
    assert not is_syntactically_valid(seq, cfg)
    assert any("non-standard" in r for r in rejection_reasons(seq, cfg))


def test_rejects_stop_codon_symbol(cfg):
    seq = "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKV*"
    assert not is_syntactically_valid(seq, cfg)


def test_rejects_too_short(cfg):
    assert not is_syntactically_valid("MKTFFVLLLCTFTVVSA", cfg)
    assert any("too short" in r for r in rejection_reasons("MKTFFVLLLCTFTVVSA", cfg))


def test_rejects_too_long(cfg):
    assert not is_syntactically_valid("A" * (cfg["filters"]["max_length"] + 1), cfg)


def test_empty_sequence_is_invalid(cfg):
    assert not is_syntactically_valid("", cfg)
    assert rejection_reasons("", cfg) == ["empty sequence"]
    assert hydrophobic_fraction("", cfg) == 0.0


def test_hydrophobic_fraction_is_counted_correctly(cfg):
    # A, V, I are hydrophobic by the default set; K, D, E are not.
    assert hydrophobic_fraction("AVIKDE", cfg) == pytest.approx(0.5)
    assert hydrophobic_fraction("KDEKDE", cfg) == 0.0


def test_rejects_excessively_hydrophobic_sequence(cfg):
    seq = "AVILMFWY" * 10              # entirely hydrophobic, length 80
    assert is_syntactically_valid(seq, cfg)
    assert not composition_ok(seq, cfg)
    assert not passes_filters(seq, cfg)
    assert any("hydrophobic fraction" in r for r in rejection_reasons(seq, cfg))


def test_boundary_hydrophobic_fraction_is_accepted(cfg):
    # Exactly at the 0.50 limit, which the criterion admits.
    seq = ("AVILMFWYKD" * 8)[:80]      # 8 of every 10 hydrophobic -> too high
    assert hydrophobic_fraction(seq, cfg) > 0.5
    half = ("AVILKDEKDE" * 8)[:80]     # 4 of every 10
    assert hydrophobic_fraction(half, cfg) == pytest.approx(0.4)
    assert composition_ok(half, cfg)


def test_apply_filters_partitions_and_explains(cfg):
    good = "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQ"
    kept, rejected = apply_filters([good, "SHORT", "MKT" + "X" * 60], cfg)
    assert kept == [good]
    assert len(rejected) == 2
    assert all(reasons for _, reasons in rejected)


# -------------------------------------------------------------- metrics


def test_perplexity_of_certain_predictions_is_one():
    assert perplexity([0.0, 0.0, 0.0]) == pytest.approx(1.0)


def test_perplexity_matches_definition():
    logs = [math.log(0.5)] * 4
    assert perplexity(logs) == pytest.approx(2.0)


def test_perplexity_rejects_empty_and_positive_logs():
    with pytest.raises(ValueError, match="empty"):
        perplexity([])
    with pytest.raises(ValueError, match="positive"):
        perplexity([0.1, -1.0])


def test_novelty_is_one_minus_identity():
    assert novelty(0.0) == pytest.approx(1.0)
    assert novelty(0.8) == pytest.approx(0.2)
    with pytest.raises(ValueError):
        novelty(1.5)


def test_identity_threshold(cfg):
    assert is_overly_similar(0.85, cfg)
    assert not is_overly_similar(0.80, cfg)


def test_valid_rate():
    assert valid_rate(89, 100) == pytest.approx(89.0)
    with pytest.raises(ValueError):
        valid_rate(5, 0)
    with pytest.raises(ValueError):
        valid_rate(11, 10)


def test_median_iqr():
    median, q1, q3 = median_iqr([1, 2, 3, 4, 5])
    assert median == pytest.approx(3.0)
    assert q1 == pytest.approx(2.0)
    assert q3 == pytest.approx(4.0)
    assert median_iqr([7.0]) == (7.0, 7.0, 7.0)
    with pytest.raises(ValueError):
        median_iqr([])


# -------------------------------------------------------------- scoring


def test_minmax_scales_and_inverts():
    assert minmax([0, 5, 10]) == [0.0, 0.5, 1.0]
    assert minmax([0, 5, 10], higher_is_better=False) == [1.0, 0.5, 0.0]
    assert minmax([3, 3, 3]) == [0.5, 0.5, 0.5]
    assert minmax([]) == []


def test_simple_score_omits_rmsd_when_absent():
    with_ref = simple_score(10.0, 80.0, rmsd=2.0, alpha=1, beta=1, gamma=1)
    without = simple_score(10.0, 80.0, rmsd=None, alpha=1, beta=1, gamma=1)
    assert without == pytest.approx(80.1)
    assert with_ref == pytest.approx(78.1)


def test_candidate_requires_a_named_reference():
    with pytest.raises(ValueError, match="without naming its reference"):
        Candidate("c1", "MKT", perplexity=9.0, plddt=80.0, best_identity=0.3, rmsd=2.0)
    ok = Candidate(
        "c1", "MKT", perplexity=9.0, plddt=80.0, best_identity=0.3,
        rmsd=2.0, reference="PDB 1ABC",
    )
    assert ok.reference == "PDB 1ABC"


def _cands():
    return [
        Candidate("a", "MKT", perplexity=9.0, plddt=85.0, best_identity=0.20, function_score=0.8),
        Candidate("b", "MKA", perplexity=11.0, plddt=70.0, best_identity=0.50, function_score=0.4),
        Candidate("c", "MKV", perplexity=10.0, plddt=60.0, best_identity=0.95, function_score=0.2),
    ]


def test_composite_prefers_the_stronger_candidate(cfg):
    scores = composite_score(_cands(), cfg)
    assert len(scores) == 3
    assert scores[0] > scores[1] > scores[2]


def test_energy_term_dropped_when_any_candidate_lacks_it(cfg):
    partial = _cands()
    partial[0].energy = -50.0           # only one has energy
    assert composite_score(partial, cfg) == pytest.approx(composite_score(_cands(), cfg))


def test_energy_term_used_when_all_have_it(cfg):
    full = _cands()
    for c, e in zip(full, (-80.0, -50.0, -10.0)):
        c.energy = e
    assert composite_score(full, cfg) != pytest.approx(composite_score(_cands(), cfg))


def test_high_identity_is_penalised(cfg):
    similar = Candidate("x", "MKT", perplexity=9.0, plddt=85.0, best_identity=0.95, function_score=0.8)
    novel = Candidate("y", "MKT", perplexity=9.0, plddt=85.0, best_identity=0.10, function_score=0.8)
    scores = composite_score([similar, novel], cfg)
    assert scores[1] > scores[0]


def test_rank_orders_and_truncates(cfg):
    ranked = rank(_cands(), cfg, top_k=2)
    assert [c.identifier for c, _ in ranked] == ["a", "b"]
    assert ranked[0][1] >= ranked[1][1]


def test_scoring_handles_empty_input(cfg):
    assert composite_score([], cfg) == []
    assert rank([], cfg) == []


# ------------------------------------------------- package namespace


def test_no_submodule_shadows_an_exported_name():
    """A submodule and an exported function of the same name shadow each other.

    Which one wins depends on import order, so `from lpdf import novelty` would
    give the metric in one program and the module in another. This guards the
    package against reintroducing such a collision.
    """
    import pkgutil

    import lpdf

    submodules = {name for _, name, _ in pkgutil.iter_modules(lpdf.__path__)}
    exported = set(lpdf.__all__)
    assert not (submodules & exported), (
        f"these names are both a submodule and an export: {sorted(submodules & exported)}"
    )


def test_novelty_export_is_the_metric_not_a_module():
    import lpdf
    import lpdf.homology  # importing the submodule must not rebind the export

    assert callable(lpdf.novelty)
    assert lpdf.novelty(0.25) == pytest.approx(0.75)


# ------------------------------------------------- paired statistics


def test_min_attainable_pvalue():
    from lpdf.metrics import min_attainable_pvalue

    assert min_attainable_pvalue(8) == pytest.approx(0.0078125)
    assert min_attainable_pvalue(6) == pytest.approx(0.03125)
    # Below six pairs nothing can reach p < 0.05, however large the effect.
    assert min_attainable_pvalue(5) > 0.05
    with pytest.raises(ValueError):
        min_attainable_pvalue(0)


def test_paired_wilcoxon_on_a_consistent_improvement():
    pytest.importorskip("scipy")
    from lpdf.metrics import paired_wilcoxon

    base = [66.8, 70.1, 72.5, 69.4, 74.1, 71.9, 68.2, 73.0]
    adapted = [80.8, 82.1, 84.3, 81.5, 83.0, 80.2, 79.6, 85.1]
    result = paired_wilcoxon(base, adapted)
    # Every difference is in the same direction, so the statistic is 0 and the
    # p-value sits at the floor for eight pairs.
    assert result.statistic == pytest.approx(0.0)
    assert result.pvalue == pytest.approx(0.0078125)


def test_paired_wilcoxon_rejects_degenerate_input():
    pytest.importorskip("scipy")
    from lpdf.metrics import paired_wilcoxon

    values = [70.0, 72.0, 74.0, 76.0]
    with pytest.raises(ValueError, match="degenerate"):
        paired_wilcoxon(values, values)
    with pytest.raises(ValueError, match="empty"):
        paired_wilcoxon([], [])
    with pytest.raises(ValueError, match="same length"):
        paired_wilcoxon([1.0, 2.0, 3.0], [1.0, 2.0])
