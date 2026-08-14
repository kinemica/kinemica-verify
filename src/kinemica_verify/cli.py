"""Command-line interface for Kinemica Verify."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .errors import KinemicaVerifyError
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

    return parser


def _print_human(report: object) -> None:
    print("Kinemica Verify")
    print()

    for group in report.groups:
        status = "PASS" if group.passed else "FAIL"
        print(f"{group.name:<20}{status}")
        for failure in group.failures:
            print(f"  - {failure}")

    print()
    print("VERIFIED" if report.verified else "NOT VERIFIED")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command != "verify":
        return 2

    try:
        report = verify_work(args.contract, args.evidence)
    except KinemicaVerifyError as exc:
        if args.as_json:
            print(json.dumps({"error": str(exc)}, sort_keys=True))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.as_json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        _print_human(report)

    return 0 if report.verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
