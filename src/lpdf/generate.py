"""Conditional sequence generation (paper, Section III-E).

Interface only. Generation is autoregressive, with prompts carrying control
tags derived from the dataset annotations so that output can be conditioned on
a family, structural constraint or functional requirement. Temperature, top-k
and nucleus sampling are all supported; parameters are in the configuration.

Requires: torch, transformers.
"""

from __future__ import annotations

from typing import Any


def generate(model, n: int, cfg: dict[str, Any], control_tags: dict[str, str] | None = None):
    """Generate ``n`` candidate sequences.

    Returns:
        Pairs of (sequence, per-token natural-log probabilities), the latter
        being what lpdf.metrics.perplexity consumes.
    """
    raise NotImplementedError(
        "generate is not implemented. It must return per-token log "
        "probabilities alongside each sequence, since perplexity cannot be "
        "recovered from the sequence alone."
    )
