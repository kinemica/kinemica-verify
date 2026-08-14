"""Execution-trace ingestion for deterministic evidence manifests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import yaml

from .contracts import validate_data
from .errors import KinemicaVerifyError
from .evidence import resolve_artifact_file

_TRACE_SCHEMA = "execution-trace-event-v1.schema.json"
_TRACE_ARTIFACT = "execution_trace"


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite numeric value {value!r}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"duplicate key {key!r}")
        output[key] = value
    return output


def _trace_relative_path(trace_path: Path, evidence_dir: Path) -> str:
    root = evidence_dir.resolve()
    trace = trace_path.resolve()
    try:
        relative = trace.relative_to(root)
    except ValueError as exc:
        raise KinemicaVerifyError("Execution trace must be inside the evidence directory") from exc
    if not trace.is_file():
        raise KinemicaVerifyError(f"Execution trace does not exist: {trace_path}")
    return relative.as_posix()


def load_execution_trace(path: Path | str) -> list[dict[str, Any]]:
    """Load and validate a JSON Lines execution trace."""

    path = Path(path)
    if not path.is_file():
        raise KinemicaVerifyError(f"Execution trace does not exist: {path}")

    events: list[dict[str, Any]] = []
    previous_sequence: int | None = None

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise KinemicaVerifyError(f"Could not read execution trace {path}: {exc}") from exc

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(
                line,
                parse_constant=_reject_constant,
                object_pairs_hook=_unique_object,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            detail = exc.msg if isinstance(exc, json.JSONDecodeError) else str(exc)
            raise KinemicaVerifyError(
                f"Invalid JSON in execution trace {path} at line {line_number}: {detail}"
            ) from exc
        if not isinstance(event, dict):
            raise KinemicaVerifyError(
                f"Execution trace event at line {line_number} must be a JSON object"
            )

        validate_data(event, _TRACE_SCHEMA, f"Execution Trace event at line {line_number}")
        sequence = event["sequence"]
        if previous_sequence is not None and sequence <= previous_sequence:
            raise KinemicaVerifyError(
                "Execution trace sequence numbers must be strictly increasing: "
                f"line {line_number} has {sequence} after {previous_sequence}"
            )
        previous_sequence = sequence
        events.append(event)

    if not events:
        raise KinemicaVerifyError(f"Execution trace contains no events: {path}")
    return events


def _put_unique(mapping: dict[str, Any], name: str, value: Any, *, kind: str) -> None:
    if name in mapping:
        raise KinemicaVerifyError(f"Execution trace contains duplicate {kind} '{name}'")
    mapping[name] = value


def _artifact_from_event(event: dict[str, Any], evidence_dir: Path) -> Any:
    artifact: dict[str, Any] = {}
    if "path" in event:
        declared_path = Path(event["path"])
        artifact["path"] = declared_path.as_posix()
        file_path, failure = resolve_artifact_file(evidence_dir, event["name"], artifact)
        if failure is not None or file_path is None:
            raise KinemicaVerifyError(failure or f"evidence '{event['name']}' has no file")
        artifact["path"] = file_path.relative_to(evidence_dir.resolve()).as_posix()
    if "value" in event:
        artifact["value"] = event["value"]

    if set(artifact) == {"value"}:
        return artifact
    return artifact


def manifest_from_trace(
    trace_path: Path | str,
    evidence_dir: Path | str,
) -> dict[str, Any]:
    """Convert a validated execution trace into Evidence Manifest v1."""

    trace_path = Path(trace_path)
    evidence_dir = Path(evidence_dir)
    if not evidence_dir.is_dir():
        raise KinemicaVerifyError(f"Evidence directory does not exist: {evidence_dir}")

    trace_relative = _trace_relative_path(trace_path, evidence_dir)
    events = load_execution_trace(trace_path)

    preconditions: dict[str, Any] = {}
    steps: list[str] = []
    step_names: set[str] = set()
    measurements: dict[str, float] = {}
    artifacts: dict[str, Any] = {}
    final_state: dict[str, Any] = {}

    for event in events:
        kind = event["kind"]
        name = event["name"]
        if kind == "precondition":
            _put_unique(preconditions, name, event["value"], kind="precondition")
        elif kind == "step":
            if name in step_names:
                raise KinemicaVerifyError(f"Execution trace contains duplicate step '{name}'")
            step_names.add(name)
            steps.append(name)
        elif kind == "measurement":
            _put_unique(measurements, name, event["value"], kind="measurement")
        elif kind == "artifact":
            _put_unique(
                artifacts,
                name,
                _artifact_from_event(event, evidence_dir),
                kind="artifact",
            )
        elif kind == "final_state":
            _put_unique(final_state, name, event["value"], kind="final state")

    if _TRACE_ARTIFACT in artifacts:
        raise KinemicaVerifyError(
            f"Execution trace reserves artifact name '{_TRACE_ARTIFACT}' for provenance"
        )
    artifacts[_TRACE_ARTIFACT] = {"path": trace_relative}

    manifest: dict[str, Any] = {
        "version": 1,
        "preconditions": preconditions,
        "steps": steps,
        "measurements": measurements,
        "artifacts": artifacts,
        "final_state": final_state,
    }
    validate_data(manifest, "evidence-manifest-v1.schema.json", "Generated Evidence Manifest")
    return manifest


def write_manifest_from_trace(
    trace_path: Path | str,
    evidence_dir: Path | str,
    *,
    force: bool = False,
) -> Path:
    """Generate evidence/manifest.yaml atomically from a trace."""

    evidence_dir = Path(evidence_dir)
    manifest = manifest_from_trace(trace_path, evidence_dir)
    output = evidence_dir / "manifest.yaml"
    if output.exists() and not force:
        raise KinemicaVerifyError(
            f"Evidence manifest already exists: {output}. Use --force to replace it"
        )

    text = yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=evidence_dir,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(text)
            temporary = Path(handle.name)
        temporary.replace(output)
    except OSError as exc:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        raise KinemicaVerifyError(f"Could not write Evidence Manifest to {output}: {exc}") from exc
    return output
