from __future__ import annotations

import os
from pathlib import Path


def _find_resource_root() -> Path:
    """Resolve the repository's resources directory as an absolute Path."""
    env_root = os.environ.get("PCM_RESOURCE_ROOT")
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        if candidate.is_dir():
            return candidate
        raise FileNotFoundError(
            f"PCM_RESOURCE_ROOT is set but is not a directory: {candidate}"
        )

    module_path = Path(__file__).resolve()
    for parent in module_path.parents:
        candidate = parent / "resources"
        if candidate.is_dir():
            return candidate

    raise FileNotFoundError(
        "Could not find a 'resources' directory by walking upward from "
        f"{module_path}."
    )


RESOURCE_ROOT = _find_resource_root()
IMAGES_ROOT = RESOURCE_ROOT / "images"
DATA_ROOT = RESOURCE_ROOT / "data"
PAPERS_ROOT = RESOURCE_ROOT / "papers"
CLIPS_ROOT = RESOURCE_ROOT / "clips"
OCIO_ROOT = RESOURCE_ROOT / "ocio"

__all__ = [
    "RESOURCE_ROOT",
    "IMAGES_ROOT",
    "DATA_ROOT",
    "PAPERS_ROOT",
    "CLIPS_ROOT",
    "OCIO_ROOT"
]
