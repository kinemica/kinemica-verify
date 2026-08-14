"""Loading and schema validation for Work Contracts and evidence manifests."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from .errors import KinemicaVerifyError, SchemaValidationError


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise KinemicaVerifyError(f"Input file does not exist: {path}")

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise KinemicaVerifyError(f"Could not read YAML from {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise KinemicaVerifyError(f"Expected a mapping at the root of {path}")

    return data


def _schema(name: str) -> dict[str, Any]:
    schema_file = resources.files("kinemica_verify.schemas").joinpath(name)
    return json.loads(schema_file.read_text(encoding="utf-8"))


def _validate(data: dict[str, Any], schema_name: str, label: str) -> None:
    validator = Draft202012Validator(_schema(schema_name))
    errors = sorted(
        validator.iter_errors(data),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if not errors:
        return

    messages: list[str] = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        messages.append(f"{location}: {error.message}")

    raise SchemaValidationError(f"Invalid {label}: " + "; ".join(messages))


def load_work_contract(path: Path) -> dict[str, Any]:
    data = _load_yaml(path)
    _validate(data, "work-contract-v1.schema.json", "Work Contract")
    return data


def load_evidence_manifest(evidence_dir: Path) -> dict[str, Any]:
    if not evidence_dir.is_dir():
        raise KinemicaVerifyError(f"Evidence directory does not exist: {evidence_dir}")

    path = evidence_dir / "manifest.yaml"
    data = _load_yaml(path)
    _validate(data, "evidence-manifest-v1.schema.json", "Evidence Manifest")
    return data
