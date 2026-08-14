"""Deterministic Work Contract verification."""

from __future__ import annotations

import operator
from pathlib import Path
from typing import Any, Callable

from .contracts import load_evidence_manifest, load_work_contract
from .evidence import artifact_failure
from .models import CheckGroup, VerificationReport

_NUMERIC_OPERATORS: dict[str, Callable[[float, float], bool]] = {
    "eq": operator.eq,
    "lt": operator.lt,
    "lte": operator.le,
    "gt": operator.gt,
    "gte": operator.ge,
}


def _mapping_check(
    name: str,
    expected: dict[str, Any],
    observed: dict[str, Any],
) -> CheckGroup:
    failures: list[str] = []
    for key, expected_value in expected.items():
        if key not in observed:
            failures.append(f"'{key}' is missing")
        elif observed[key] != expected_value:
            failures.append(
                f"'{key}' expected {expected_value!r}, observed {observed[key]!r}"
            )
    return CheckGroup(name=name, passed=not failures, failures=tuple(failures))


def _steps_check(required: list[str], completed: list[str]) -> CheckGroup:
    completed_set = set(completed)
    failures = tuple(
        f"required step '{step}' was not completed"
        for step in required
        if step not in completed_set
    )
    return CheckGroup("Required steps", not failures, failures)


def _constraints_check(
    constraints: dict[str, dict[str, Any]],
    measurements: dict[str, float],
) -> CheckGroup:
    failures: list[str] = []

    for measurement_name, rule in constraints.items():
        if measurement_name not in measurements:
            failures.append(f"measurement '{measurement_name}' is missing")
            continue

        observed = measurements[measurement_name]
        expected = rule["value"]
        op_name = rule["op"]
        op = _NUMERIC_OPERATORS[op_name]

        if not op(observed, expected):
            failures.append(
                f"measurement '{measurement_name}' observed {observed!r}; "
                f"requirement is {op_name} {expected!r}"
            )

    return CheckGroup("Safety constraints", not failures, tuple(failures))


def _evidence_check(
    required: list[str],
    artifacts: dict[str, Any],
    evidence_dir: Path,
) -> CheckGroup:
    failures: list[str] = []

    for name in required:
        failure = artifact_failure(evidence_dir, name, artifacts.get(name))
        if failure is not None:
            failures.append(failure)

    return CheckGroup("Evidence", not failures, tuple(failures))


def verify_work(contract_path: Path | str, evidence_dir: Path | str) -> VerificationReport:
    """Verify one Work Contract against one evidence directory."""

    contract_path = Path(contract_path)
    evidence_dir = Path(evidence_dir)

    contract = load_work_contract(contract_path)
    manifest = load_evidence_manifest(evidence_dir)

    groups = (
        _mapping_check(
            "Preconditions",
            contract["preconditions"],
            manifest["preconditions"],
        ),
        _steps_check(contract["required_steps"], manifest["steps"]),
        _constraints_check(contract["constraints"], manifest["measurements"]),
        _evidence_check(
            contract["evidence"]["required"],
            manifest["artifacts"],
            evidence_dir,
        ),
        _mapping_check(
            "Final state",
            contract["final_state"],
            manifest["final_state"],
        ),
    )

    return VerificationReport(groups=groups)
