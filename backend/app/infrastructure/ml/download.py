"""Download ML models from HuggingFace Hub.

Usage:
    python -m app.infrastructure.ml.download [--force] [--target DIR]
"""

from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

SAFETENSORS_PATTERNS = ["*.safetensors", "*.json", "*.txt", "*.model", "*.spm"]


@dataclass(frozen=True)
class ModelSpec:
    repo_id: str
    allow_patterns: list[str] = field(
        default_factory=lambda: list(SAFETENSORS_PATTERNS),
    )


MODEL_REGISTRY: list[ModelSpec] = [
    ModelSpec(
        repo_id="almanach/camemberta-chatgptdetect-noisy",
    ),
    ModelSpec(
        repo_id="cardiffnlp/camembert-base-tweet-sentiment-fr",
    ),
    ModelSpec(
        repo_id="mazancourt/politics-sentence-classifier",
    ),
]


def download_models(target_dir: str, *, force: bool = False) -> None:
    """Download all models in the registry."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        logger.error(
            "huggingface_hub is not installed. Run: pip install huggingface-hub",
        )
        sys.exit(1)

    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)

    for spec in MODEL_REGISTRY:
        model_dir = target / spec.repo_id.replace("/", "--")

        if model_dir.exists() and not force:
            logger.info("Model %s already downloaded, skipping", spec.repo_id)
            continue

        logger.info("Downloading %s ...", spec.repo_id)
        try:
            snapshot_download(
                repo_id=spec.repo_id,
                local_dir=str(model_dir),
                allow_patterns=spec.allow_patterns,
                ignore_patterns=["*.pkl", "*.pickle", "*.ckpt", "*.h5"],
            )
            logger.info("Downloaded %s -> %s", spec.repo_id, model_dir)
        except Exception:
            logger.exception("Failed to download %s", spec.repo_id)
            raise

    logger.info("All models downloaded to %s", target_dir)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    parser = argparse.ArgumentParser(description="Download ML models")
    parser.add_argument(
        "--target",
        default="models",
        help="Target directory (default: models)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if models exist",
    )
    args = parser.parse_args()

    download_models(args.target, force=args.force)


if __name__ == "__main__":
    main()
