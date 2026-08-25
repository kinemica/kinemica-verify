from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from kinemica_verify.errors import KinemicaVerifyError
from kinemica_verify.traces import (
    load_execution_trace,
    manifest_from_trace,
    write_manifest_from_trace,
)

EXAMPLE = Path(__file__).parents[1] / "examples" / "filter-replacement"


def _copy_evidence(tmp_path: Path) -> Path:
    target = tmp_path / "evidence"
    shutil.copytree(EXAMPLE / "evidence", target)
    (target / "manifest.yaml").unlink(missing_ok=True)
    return target


def _write_events(path: Path, events: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(event, separators=(",", ":")) + "\n" for event in events),
        encoding="utf-8",
    )


def test_trace_generates_expected_manifest(tmp_path: Path) -> None:
    evidence = _copy_evidence(tmp_path)
    manifest = manifest_from_trace(evidence / "trace.jsonl", evidence)

    assert manifest["preconditions"] == {"machine_powered_down": True}
    assert manifest["steps"] == [
        "remove_old_filter",
        "install_new_filter",
        "secure_cover",
    ]
    assert manifest["measurements"]["max_force_n"] == 31.8
    assert manifest["artifacts"]["execution_trace"] == {"path": "trace.jsonl"}
    assert manifest["final_state"] == {"system_test_passed": True}


def test_write_manifest_refuses_overwrite_without_force(tmp_path: Path) -> None:
    evidence = _copy_evidence(tmp_path)
    output = write_manifest_from_trace(evidence / "trace.jsonl", evidence)

    assert output.is_file()
    with pytest.raises(KinemicaVerifyError, match="already exists"):
        write_manifest_from_trace(evidence / "trace.jsonl", evidence)

    write_manifest_from_trace(evidence / "trace.jsonl", evidence, force=True)


def test_sequence_must_increase(tmp_path: Path) -> None:
    evidence = _copy_evidence(tmp_path)
    trace = evidence / "bad.jsonl"
    _write_events(
        trace,
        [
            {"version": 1, "sequence": 2, "kind": "step", "name": "a"},
            {"version": 1, "sequence": 2, "kind": "step", "name": "b"},
        ],
    )

    with pytest.raises(KinemicaVerifyError, match="strictly increasing"):
        load_execution_trace(trace)


def test_duplicate_semantic_key_rejected(tmp_path: Path) -> None:
    evidence = _copy_evidence(tmp_path)
    trace = evidence / "bad.jsonl"
    _write_events(
        trace,
        [
            {
                "version": 1,
                "sequence": 1,
                "kind": "measurement",
                "name": "force",
                "value": 1,
            },
            {
                "version": 1,
                "sequence": 2,
                "kind": "measurement",
                "name": "force",
                "value": 2,
            },
        ],
    )

    with pytest.raises(KinemicaVerifyError, match="duplicate measurement 'force'"):
        manifest_from_trace(trace, evidence)


def test_duplicate_json_key_rejected(tmp_path: Path) -> None:
    evidence = _copy_evidence(tmp_path)
    trace = evidence / "bad.jsonl"
    trace.write_text(
        '{"version":1,"sequence":1,"sequence":2,"kind":"step","name":"a"}\n',
        encoding="utf-8",
    )

    with pytest.raises(KinemicaVerifyError, match="duplicate key 'sequence'"):
        load_execution_trace(trace)


def test_nonfinite_json_number_rejected(tmp_path: Path) -> None:
    evidence = _copy_evidence(tmp_path)
    trace = evidence / "bad.jsonl"
    trace.write_text(
        '{"version":1,"sequence":1,"kind":"measurement",'
        '"name":"force","value":NaN}\n',
        encoding="utf-8",
    )

    with pytest.raises(KinemicaVerifyError, match="non-finite"):
        load_execution_trace(trace)


def test_artifact_escape_rejected(tmp_path: Path) -> None:
    evidence = _copy_evidence(tmp_path)
    (tmp_path / "outside.txt").write_text("x", encoding="utf-8")
    trace = evidence / "bad.jsonl"
    _write_events(
        trace,
        [
            {
                "version": 1,
                "sequence": 1,
                "kind": "artifact",
                "name": "x",
                "path": "../outside.txt",
            }
        ],
    )

    with pytest.raises(KinemicaVerifyError, match="escapes the evidence directory"):
        manifest_from_trace(trace, evidence)


def test_trace_must_be_inside_evidence_dir(tmp_path: Path) -> None:
    evidence = _copy_evidence(tmp_path)
    trace = tmp_path / "outside.jsonl"
    _write_events(
        trace,
        [{"version": 1, "sequence": 1, "kind": "step", "name": "a"}],
    )

    with pytest.raises(KinemicaVerifyError, match="must be inside"):
        manifest_from_trace(trace, evidence)


def test_trace_without_measurements(tmp_path: Path) -> None:
    trace = tmp_path / "trace-no-measurement.jsonl"
    _write_events(
        trace,
        [
            {"version": 1, "sequence": 1, "kind": "precondition", "name": "machine_powered_down", "value": True},
            {"version": 1, "sequence": 2, "kind": "step", "name": "remove_old_filter"},
            {"version": 1, "sequence": 3, "kind": "step", "name": "install_new_filter"},
            {"version": 1, "sequence": 4, "kind": "step", "name": "secure_cover"},
            {"version": 1, "sequence": 5, "kind": "final_state", "name": "system_test_passed", "value": True},
        ],
    )

    manifest = manifest_from_trace(trace, tmp_path)

    assert manifest["preconditions"] == {"machine_powered_down": True}
    assert manifest["steps"] == ["remove_old_filter", "install_new_filter", "secure_cover"]
    assert manifest["measurements"] == {}
    assert manifest["artifacts"]["execution_trace"] == {"path": "trace-no-measurement.jsonl"}
    assert manifest["final_state"] == {"system_test_passed": True}
