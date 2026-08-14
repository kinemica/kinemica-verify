from __future__ import annotations

from pathlib import Path

from kinemica_verify.cli import main

EXAMPLE = Path(__file__).parents[1] / "examples" / "filter-replacement"


def test_cli_success(capsys) -> None:
    code = main(
        [
            "verify",
            str(EXAMPLE / "work.yaml"),
            str(EXAMPLE / "evidence"),
        ]
    )
    output = capsys.readouterr().out

    assert code == 0
    assert "VERIFIED" in output
    assert "Safety constraints  PASS" in output


def test_cli_json(capsys) -> None:
    code = main(
        [
            "verify",
            str(EXAMPLE / "work.yaml"),
            str(EXAMPLE / "evidence"),
            "--json",
        ]
    )
    output = capsys.readouterr().out

    assert code == 0
    assert '"verified": true' in output
