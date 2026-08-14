"""Command-line interface for Kinemica Verify."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .errors import KinemicaVerifyError
from .records import create_signed_record, verify_signed_record, write_signed_record
from .signing import generate_keypair
from .verifier import verify_work


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kinemica",
        description="Verify physical-world work against a machine-readable Work Contract.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify = subparsers.add_parser("verify", help="verify a Work Contract")
    verify.add_argument("contract", type=Path, help="path to the Work Contract YAML")
    verify.add_argument("evidence", type=Path, help="evidence directory containing manifest.yaml")
    verify.add_argument("--json", action="store_true", dest="as_json", help="emit JSON")
    verify.add_argument("--record", type=Path, help="write a signed verification record")
    verify.add_argument("--signing-key", type=Path, help="Ed25519 private key used with --record")

    keygen = subparsers.add_parser("keygen", help="generate an Ed25519 signing key pair")
    keygen.add_argument("--private-key", type=Path, required=True, help="private PEM output path")
    keygen.add_argument("--public-key", type=Path, required=True, help="public PEM output path")

    verify_record = subparsers.add_parser(
        "verify-record",
        help="authenticate a signed verification record",
    )
    verify_record.add_argument("record", type=Path, help="signed verification record JSON")
    verify_record.add_argument("public_key", type=Path, help="trusted Ed25519 public PEM key")
    verify_record.add_argument("--contract", type=Path, help="re-check the bound Work Contract")
    verify_record.add_argument("--evidence", type=Path, help="re-check the bound evidence directory")
    verify_record.add_argument("--json", action="store_true", dest="as_json", help="emit JSON")

    return parser


def _print_human(report: object) -> None:
    print("Kinemica Verify")
    print()

    for group in report.groups:
        status = "PASS" if group.passed else "FAIL"
        print(f"{group.name:<28}{status}")
        for failure in group.failures:
            print(f"  - {failure}")

    print()
    print("VERIFIED" if report.verified else "NOT VERIFIED")


def _print_record_human(report: object) -> None:
    print("Kinemica Verify")
    print()

    for group in report.groups:
        status = "PASS" if group.passed else "FAIL"
        print(f"{group.name:<28}{status}")
        for failure in group.failures:
            print(f"  - {failure}")

    print()
    print("SIGNED RECORD VALID" if report.verified else "SIGNED RECORD INVALID")


def _error(message: str, *, as_json: bool = False) -> int:
    if as_json:
        print(json.dumps({"error": message}, sort_keys=True))
    else:
        print(f"ERROR: {message}", file=sys.stderr)
    return 2


def _verify_command(args: argparse.Namespace) -> int:
    if (args.record is None) != (args.signing_key is None):
        return _error("--record and --signing-key must be supplied together", as_json=args.as_json)

    try:
        report = verify_work(args.contract, args.evidence)
        if args.record is not None:
            record = create_signed_record(
                args.contract,
                args.evidence,
                args.signing_key,
                report=report,
            )
            write_signed_record(record, args.record)
    except KinemicaVerifyError as exc:
        return _error(str(exc), as_json=args.as_json)

    if args.as_json:
        output = report.to_dict()
        if args.record is not None:
            output["record"] = str(args.record)
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        _print_human(report)
        if args.record is not None:
            print(f"Signed record       {args.record}")

    return 0 if report.verified else 1


def _keygen_command(args: argparse.Namespace) -> int:
    try:
        key_id = generate_keypair(args.private_key, args.public_key)
    except KinemicaVerifyError as exc:
        return _error(str(exc))

    print("Kinemica Verify")
    print()
    print(f"Private key         {args.private_key}")
    print(f"Public key          {args.public_key}")
    print(f"Key ID              {key_id}")
    return 0


def _verify_record_command(args: argparse.Namespace) -> int:
    try:
        report = verify_signed_record(
            args.record,
            args.public_key,
            contract_path=args.contract,
            evidence_dir=args.evidence,
        )
    except KinemicaVerifyError as exc:
        return _error(str(exc), as_json=args.as_json)

    if args.as_json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        _print_record_human(report)
    return 0 if report.verified else 1


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command == "verify":
        return _verify_command(args)
    if args.command == "keygen":
        return _keygen_command(args)
    if args.command == "verify-record":
        return _verify_record_command(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
