from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path

from kinemica_verify.records import (
    create_signed_record,
    sha256_file,
    verify_signed_record,
    write_signed_record,
)
from kinemica_verify.signing import generate_keypair

EXAMPLE = Path(__file__).parents[1] / "examples" / "filter-replacement"


def _keypair(tmp_path: Path, prefix: str = "signer") -> tuple[Path, Path]:
    private_key = tmp_path / f"{prefix}.private.pem"
    public_key = tmp_path / f"{prefix}.public.pem"
    generate_keypair(private_key, public_key)
    return private_key, public_key


def _copy_example(tmp_path: Path) -> tuple[Path, Path]:
    contract = tmp_path / "work.yaml"
    evidence = tmp_path / "evidence"
    shutil.copy(EXAMPLE / "work.yaml", contract)
    shutil.copytree(EXAMPLE / "evidence", evidence)
    return contract, evidence


def test_signed_record_round_trip(tmp_path: Path) -> None:
    private_key, public_key = _keypair(tmp_path)
    record_path = tmp_path / "record.json"

    record = create_signed_record(EXAMPLE / "work.yaml", EXAMPLE / "evidence", private_key)
    write_signed_record(record, record_path)

    report = verify_signed_record(
        record_path,
        public_key,
        contract_path=EXAMPLE / "work.yaml",
        evidence_dir=EXAMPLE / "evidence",
    )

    assert report.verified
    assert [group.name for group in report.groups] == [
        "Signature",
        "Work contract integrity",
        "Evidence manifest integrity",
        "Artifact integrity",
        "Verification replay",
    ]


def test_signed_record_is_deterministic_for_same_key_and_inputs(tmp_path: Path) -> None:
    private_key, _ = _keypair(tmp_path)

    first = create_signed_record(EXAMPLE / "work.yaml", EXAMPLE / "evidence", private_key)
    second = create_signed_record(EXAMPLE / "work.yaml", EXAMPLE / "evidence", private_key)

    assert first == second


def test_tampered_artifact_is_detected(tmp_path: Path) -> None:
    contract, evidence = _copy_example(tmp_path)
    private_key, public_key = _keypair(tmp_path)
    record_path = tmp_path / "record.json"
    write_signed_record(create_signed_record(contract, evidence, private_key), record_path)

    (evidence / "before_image.txt").write_text("tampered\n", encoding="utf-8")
    report = verify_signed_record(
        record_path,
        public_key,
        contract_path=contract,
        evidence_dir=evidence,
    )

    assert not report.verified
    group = next(group for group in report.groups if group.name == "Artifact integrity")
    assert not group.passed
    assert "before_image" in group.failures[0]


def test_tampered_record_payload_breaks_signature(tmp_path: Path) -> None:
    private_key, public_key = _keypair(tmp_path)
    record_path = tmp_path / "record.json"
    record = create_signed_record(EXAMPLE / "work.yaml", EXAMPLE / "evidence", private_key)
    record["payload"]["verification"]["verified"] = False
    write_signed_record(record, record_path)

    report = verify_signed_record(record_path, public_key)

    assert not report.verified
    assert report.groups[0].name == "Signature"
    assert not report.groups[0].passed


def test_wrong_public_key_is_rejected(tmp_path: Path) -> None:
    private_key, _ = _keypair(tmp_path, "one")
    _, wrong_public_key = _keypair(tmp_path, "two")
    record_path = tmp_path / "record.json"
    write_signed_record(
        create_signed_record(EXAMPLE / "work.yaml", EXAMPLE / "evidence", private_key),
        record_path,
    )

    report = verify_signed_record(record_path, wrong_public_key)

    assert not report.verified
    assert "does not match supplied public key" in report.groups[0].failures[0]


def test_private_key_file_is_owner_only(tmp_path: Path) -> None:
    private_key, _ = _keypair(tmp_path)
    mode = stat.S_IMODE(private_key.stat().st_mode)
    assert mode == 0o600


def test_record_contains_hashes_for_file_backed_artifacts(tmp_path: Path) -> None:
    private_key, _ = _keypair(tmp_path)
    record = create_signed_record(EXAMPLE / "work.yaml", EXAMPLE / "evidence", private_key)
    artifacts = record["payload"]["inputs"]["artifacts"]

    assert set(artifacts) == {
        "before_image",
        "execution_trace",
        "installation_image",
    }
    assert len(artifacts["before_image"]["sha256"]) == 64
    assert len(artifacts["installation_image"]["sha256"]) == 64
    assert artifacts["execution_trace"] == {
        "path": "trace.jsonl",
        "sha256": sha256_file(EXAMPLE / "evidence" / "trace.jsonl"),
    }
    json.dumps(record, allow_nan=False)
