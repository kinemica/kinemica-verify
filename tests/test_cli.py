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


def test_cli_failed_verification_returns_one(tmp_path: Path, capsys) -> None:
    contract = tmp_path / "work.yaml"
    source = (EXAMPLE / "work.yaml").read_text(encoding="utf-8")
    contract.write_text(
        source.replace("machine_powered_down: true", "machine_powered_down: false"),
        encoding="utf-8",
    )

    code = main(
        [
            "verify",
            str(contract),
            str(EXAMPLE / "evidence"),
        ]
    )
    output = capsys.readouterr().out

    assert code == 1
    assert "NOT VERIFIED" in output
    assert "Preconditions       FAIL" in output


def test_cli_invalid_contract_returns_two(tmp_path: Path, capsys) -> None:
    contract = tmp_path / "invalid.yaml"
    contract.write_text("version: 2\n", encoding="utf-8")

    code = main(
        [
            "verify",
            str(contract),
            str(EXAMPLE / "evidence"),
        ]
    )
    captured = capsys.readouterr()

    assert code == 2
    assert "Invalid Work Contract" in captured.err
