"""Configuration loading for the LPDF pipeline.

The configuration file holds the acceptance criteria declared in the paper's
evaluation protocol. Loading validates them, so that a run cannot silently
proceed with a weighting that does not sum to one or a length range that is
inverted.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Mapping

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "default.yaml"


class ConfigError(ValueError):
    """Raised when a configuration file is missing a key or is inconsistent."""


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate a protocol configuration.

    Args:
        path: configuration file to read. Defaults to ``configs/default.yaml``.

    Returns:
        The validated configuration as a nested dictionary.

    Raises:
        ConfigError: if a required section is absent or a value is inconsistent.
    """
    path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not path.exists():
        raise ConfigError(f"configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)
    if not isinstance(cfg, Mapping):
        raise ConfigError(f"configuration must be a mapping, got {type(cfg).__name__}")
    return validate_config(copy.deepcopy(dict(cfg)))


def validate_config(cfg: dict[str, Any]) -> dict[str, Any]:
    """Check that a configuration is internally consistent.

    Returns the configuration unchanged if it is valid.
    """
    for section in ("filters", "structure", "novelty", "scoring"):
        if section not in cfg:
            raise ConfigError(f"missing required section: {section!r}")

    f = cfg["filters"]
    if f["min_length"] > f["max_length"]:
        raise ConfigError(
            f"min_length ({f['min_length']}) exceeds max_length ({f['max_length']})"
        )
    if not 0.0 <= f["max_hydrophobic_fraction"] <= 1.0:
        raise ConfigError("max_hydrophobic_fraction must lie in [0, 1]")
    if not set(f["hydrophobic_residues"]) <= set(f["allowed_residues"]):
        raise ConfigError("hydrophobic_residues must be a subset of allowed_residues")

    s = cfg["structure"]
    if s["screen_plddt"] > s["high_confidence_plddt"]:
        raise ConfigError(
            "screen_plddt must not exceed high_confidence_plddt; a candidate "
            "cannot be high confidence without first passing the screen"
        )

    if not 0.0 <= cfg["novelty"]["max_identity"] <= 1.0:
        raise ConfigError("novelty.max_identity must lie in [0, 1]")

    weights = cfg["scoring"]["weights"]
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-9:
        raise ConfigError(f"scoring weights must sum to 1.0, got {total:.6f}")
    if any(w < 0 for w in weights.values()):
        raise ConfigError("scoring weights must be non-negative")

    return cfg
