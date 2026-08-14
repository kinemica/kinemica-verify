from __future__ import annotations

import shutil
from pathlib import Path

import yaml

from kinemica_verify.verifier import verify_work

EXAMPLE = Path(__file__).parents[1] / "examples" / "filter-replacement"


def _copy_example(tmp_path: Path) -> tuple[Path, Path]:
    contract = tmp_path / "work.yaml"
    evidence = tmp_path / "evidence"
    shutil.copy(EXAMPLE / "work.yaml", contract)
    shutil.copytree(EXAMPLE / "evidence", evidence)
    return contract, evidence


def _manifest(evidence: Path) -> dict:
    return yaml.safe_load((evidence / "manifest.yaml").read_text(encoding="utf-8"))


def _write_manifest(evidence: Path, data: dict) -> None:
    (evidence / "manifest.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False),
        encoding="utf-8",
    )


def test_reference_example_verifies() -> None:
    report = verify_work(EXAMPLE / "work.yaml", EXAMPLE / "evidence")
    assert report.verified
    assert all(group.passed for group in report.groups)


def test_missing_step_fails(tmp_path: Path) -> None:
    contract, evidence = _copy_example(tmp_path)
    data = _manifest(evidence)
    data["steps"].remove("secure_cover")
    _write_manifest(evidence, data)

    report = verify_work(contract, evidence)

    assert not report.verified
    assert not next(group for group in report.groups if group.name == "Required steps").passed


def test_constraint_violation_fails(tmp_path: Path) -> None:
    contract, evidence = _copy_example(tmp_path)
    data = _manifest(evidence)
    data["measurements"]["max_force_n"] = 45
    _write_manifest(evidence, data)

    report = verify_work(contract, evidence)

    group = next(group for group in report.groups if group.name == "Safety constraints")
    assert not report.verified
    assert not group.passed
    assert "max_force_n" in group.failures[0]


def test_missing_artifact_file_fails(tmp_path: Path) -> None:
    contract, evidence = _copy_example(tmp_path)
    (evidence / "before_image.txt").unlink()

    report = verify_work(contract, evidence)

    group = next(group for group in report.groups if group.name == "Evidence")
    assert not report.verified
    assert not group.passed


def test_artifact_path_cannot_escape_evidence_directory(tmp_path: Path) -> None:
    contract, evidence = _copy_example(tmp_path)
    data = _manifest(evidence)
    data["artifacts"]["before_image"]["path"] = "../outside.txt"
    _write_manifest(evidence, data)
    (tmp_path / "outside.txt").write_text("outside", encoding="utf-8")

    report = verify_work(contract, evidence)

    group = next(group for group in report.groups if group.name == "Evidence")
    assert not report.verified
    assert "escapes the evidence directory" in group.failures[0]


def test_precondition_mismatch_fails(tmp_path: Path) -> None:
    contract, evidence = _copy_example(tmp_path)
    data = _manifest(evidence)
    data["preconditions"]["machine_powered_down"] = False
    _write_manifest(evidence, data)

    report = verify_work(contract, evidence)

    group = next(group for group in report.groups if group.name == "Preconditions")
    assert not report.verified
    assert not group.passed


def test_final_state_mismatch_fails(tmp_path: Path) -> None:
    contract, evidence = _copy_example(tmp_path)
    data = _manifest(evidence)
    data["final_state"]["system_test_passed"] = False
    _write_manifest(evidence, data)

    report = verify_work(contract, evidence)

    group = next(group for group in report.groups if group.name == "Final state")
    assert not report.verified
    assert not group.passed
