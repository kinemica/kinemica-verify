from __future__ import annotations

import json
from pathlib import Path

import kinemica_verify.cli as cli
from kinemica_verify import VerificationReport, verify_work
from kinemica_verify.verifier import verify_work as core_verify_work

EXAMPLE = Path(__file__).parents[1] / "examples" / "filter-replacement"


def test_verify_work_is_the_public_high_level_verifier() -> None:
    assert verify_work is core_verify_work

    report = verify_work(EXAMPLE / "work.yaml", EXAMPLE / "evidence")

    assert isinstance(report, VerificationReport)
    assert report.verified


def test_cli_and_library_share_verification_results(capsys) -> None:
    report = verify_work(EXAMPLE / "work.yaml", EXAMPLE / "evidence")

    code = cli.main(
        [
            "verify",
            str(EXAMPLE / "work.yaml"),
            str(EXAMPLE / "evidence"),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert code == 0
    assert payload == report.to_dict()
