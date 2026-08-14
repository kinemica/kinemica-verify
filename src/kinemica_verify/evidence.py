"""Evidence helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def resolve_artifact_file(
    evidence_dir: Path,
    artifact_name: str,
    artifact: Any,
) -> tuple[Path | None, str | None]:
    """Resolve a declared artifact file without allowing escape from the evidence root."""

    if artifact is None:
        return None, f"required evidence '{artifact_name}' is missing"

    if not isinstance(artifact, dict) or "path" not in artifact:
        return None, None

    relative = Path(artifact["path"])
    if relative.is_absolute():
        return None, f"evidence '{artifact_name}' uses an absolute path"

    root = evidence_dir.resolve()
    candidate = (root / relative).resolve()

    try:
        candidate.relative_to(root)
    except ValueError:
        return None, f"evidence '{artifact_name}' escapes the evidence directory"

    if not candidate.is_file():
        return None, f"evidence '{artifact_name}' file does not exist: {relative.as_posix()}"

    return candidate, None


def artifact_failure(
    evidence_dir: Path,
    artifact_name: str,
    artifact: Any,
) -> str | None:
    """Return an evidence failure string, or None when the artifact is acceptable."""

    _, failure = resolve_artifact_file(evidence_dir, artifact_name, artifact)
    return failure
