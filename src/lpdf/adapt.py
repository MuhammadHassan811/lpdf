"""Model adaptation (paper, Section III-D).

Interface only. Supports two regimes: LoRA, which leaves base weights frozen,
and full fine-tuning of the attention and output layers. Reference settings are
in configs/default.yaml and Table II of the paper.

Requires: torch, transformers, peft.
"""

from __future__ import annotations

from typing import Any


def adapt(base_model: str, corpus_path: str, cfg: dict[str, Any], method: str = "lora"):
    """Adapt ``base_model`` to a protein corpus.

    Args:
        base_model: HuggingFace identifier of the base model.
        corpus_path: preprocessed corpus.
        cfg: protocol configuration.
        method: ``"lora"`` or ``"full"``.
    """
    raise NotImplementedError(
        "adapt is not implemented. It requires torch, transformers and peft, "
        "and should record the resolved hyperparameters and random seed with "
        "the resulting checkpoint."
    )
