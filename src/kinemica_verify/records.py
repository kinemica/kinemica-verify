"""Cryptographically signed verification records."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature

from .contracts import load_evidence_manifest, load_work_contract, validate_data
from .errors import KinemicaVerifyError
from .evidence import resolve_artifact_file
from .models import CheckGroup, VerificationReport
from .signing import load_private_key, load_public_key, public_key_id
from .verifier import verify_work

_DOMAIN = b"kinemica-verify:verification-record:v1\x00"


def sha256_file(path: Path | str) -> str:
    path = Path(path)
    if not path.is_file():
        raise KinemicaVerifyError(f"Input file does not exist: {path}")

    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise KinemicaVerifyError(f"Could not hash file {path}: {exc}") from exc
    return digest.hexdigest()


def canonical_payload(payload: dict[str, Any]) -> bytes:
    """Return the stable byte representation signed by Kinemica Verify v1 records."""

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _artifact_digests(evidence_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for name in sorted(manifest["artifacts"]):
        artifact = manifest["artifacts"][name]
        file_path, failure = resolve_artifact_file(evidence_dir, name, artifact)
        if failure is not None or file_path is None:
            continue
        artifacts[name] = {
            "path": artifact["path"],
            "sha256": sha256_file(file_path),
        }
    return artifacts


def create_signed_record(
    contract_path: Path | str,
    evidence_dir: Path | str,
    private_key_path: Path | str,
    *,
    report: VerificationReport | None = None,
) -> dict[str, Any]:
    """Create a deterministic Ed25519-signed record for one verification execution."""

    contract_path = Path(contract_path)
    evidence_dir = Path(evidence_dir)
    manifest_path = evidence_dir / "manifest.yaml"

    if report is None:
        report = verify_work(contract_path, evidence_dir)

    contract = load_work_contract(contract_path)
    manifest = load_evidence_manifest(evidence_dir)
    private_key = load_private_key(private_key_path)

    payload: dict[str, Any] = {
        "task": {
            "id": contract["task"]["id"],
            "actor": contract["task"]["actor"],
        },
        "inputs": {
            "work_contract": {"sha256": sha256_file(contract_path)},
            "evidence_manifest": {"sha256": sha256_file(manifest_path)},
            "artifacts": _artifact_digests(evidence_dir, manifest),
        },
        "verification": report.to_dict(),
    }

    signed_bytes = _DOMAIN + canonical_payload(payload)
    signature = private_key.sign(signed_bytes)
    record = {
        "version": 1,
        "payload": payload,
        "signature": {
            "algorithm": "Ed25519",
            "key_id": public_key_id(private_key.public_key()),
            "value": base64.b64encode(signature).decode("ascii"),
        },
    }
    validate_data(record, "verification-record-v1.schema.json", "Verification Record")
    return record


def write_signed_record(record: dict[str, Any], path: Path | str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(
            json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise KinemicaVerifyError(f"Could not write verification record to {path}: {exc}") from exc


def load_signed_record(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise KinemicaVerifyError(f"Verification record does not exist: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise KinemicaVerifyError(f"Could not read verification record from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise KinemicaVerifyError(f"Expected an object at the root of verification record {path}")
    validate_data(data, "verification-record-v1.schema.json", "Verification Record")
    return data


def _signature_check(record: dict[str, Any], public_key_path: Path | str) -> CheckGroup:
    public_key = load_public_key(public_key_path)
    expected_key_id = public_key_id(public_key)
    recorded_key_id = record["signature"]["key_id"]
    if recorded_key_id != expected_key_id:
        return CheckGroup(
            "Signature",
            False,
            (f"record key id {recorded_key_id!r} does not match supplied public key",),
        )

    try:
        signature = base64.b64decode(record["signature"]["value"], validate=True)
    except (ValueError, base64.binascii.Error):
        return CheckGroup("Signature", False, ("record signature is not valid base64",))

    try:
        public_key.verify(signature, _DOMAIN + canonical_payload(record["payload"]))
    except InvalidSignature:
        return CheckGroup("Signature", False, ("Ed25519 signature verification failed",))
    return CheckGroup("Signature", True)


def _digest_check(name: str, expected: str, path: Path) -> CheckGroup:
    try:
        observed = sha256_file(path)
    except KinemicaVerifyError as exc:
        return CheckGroup(name, False, (str(exc),))
    if observed != expected:
        return CheckGroup(
            name,
            False,
            (f"SHA-256 mismatch: expected {expected}, observed {observed}",),
        )
    return CheckGroup(name, True)


def _artifact_integrity_check(record: dict[str, Any], evidence_dir: Path) -> CheckGroup:
    failures: list[str] = []
    for name, artifact in record["payload"]["inputs"]["artifacts"].items():
        file_path, failure = resolve_artifact_file(evidence_dir, name, artifact)
        if failure is not None or file_path is None:
            failures.append(failure or f"evidence '{name}' has no file")
            continue
        observed = sha256_file(file_path)
        if observed != artifact["sha256"]:
            failures.append(
                f"evidence '{name}' SHA-256 mismatch: expected {artifact['sha256']}, "
                f"observed {observed}"
            )
    return CheckGroup("Artifact integrity", not failures, tuple(failures))


def _replay_check(
    record: dict[str, Any],
    contract_path: Path,
    evidence_dir: Path,
) -> CheckGroup:
    try:
        replay = verify_work(contract_path, evidence_dir).to_dict()
    except KinemicaVerifyError as exc:
        return CheckGroup("Verification replay", False, (str(exc),))
    if replay != record["payload"]["verification"]:
        return CheckGroup(
            "Verification replay",
            False,
            ("current verification result does not match the signed result",),
        )
    return CheckGroup("Verification replay", True)


def verify_signed_record(
    record_path: Path | str,
    public_key_path: Path | str,
    *,
    contract_path: Path | str | None = None,
    evidence_dir: Path | str | None = None,
) -> VerificationReport:
    """Authenticate a signed record and optionally verify its bound source files."""

    record = load_signed_record(record_path)
    signature_group = _signature_check(record, public_key_path)
    if not signature_group.passed:
        return VerificationReport(groups=(signature_group,))

    groups: list[CheckGroup] = [signature_group]

    if contract_path is not None:
        groups.append(
            _digest_check(
                "Work contract integrity",
                record["payload"]["inputs"]["work_contract"]["sha256"],
                Path(contract_path),
            )
        )

    if evidence_dir is not None:
        evidence_dir = Path(evidence_dir)
        groups.append(
            _digest_check(
                "Evidence manifest integrity",
                record["payload"]["inputs"]["evidence_manifest"]["sha256"],
                evidence_dir / "manifest.yaml",
            )
        )
        groups.append(_artifact_integrity_check(record, evidence_dir))

    if contract_path is not None and evidence_dir is not None:
        groups.append(_replay_check(record, Path(contract_path), Path(evidence_dir)))

    return VerificationReport(groups=tuple(groups))
