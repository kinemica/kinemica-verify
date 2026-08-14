"""Evidence helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def artifact_failure(
    evidence_dir: Path,
    artifact_name: str,
    artifact: Any,
) -> str | None:
    """Return an evidence failure string, or None when the artifact is acceptable."""

    if artifact is None:
        return f"required evidence '{artifact_name}' is missing"

    if not isinstance(artifact, dict):
        return None

    if "path" not in artifact:
        return None

    relative = Path(artifact["path"])
    if relative.is_absolute():
        return f"evidence '{artifact_name}' uses an absolute path"

    root = evidence_dir.resolve()
    candidate = (root / relative).resolve()

    try:
        candidate.relative_to(root)
    except ValueError:
        return f"evidence '{artifact_name}' escapes the evidence directory"

    if not candidate.is_file():
        return f"evidence '{artifact_name}' file does not exist: {relative.as_posix()}"

    return None
