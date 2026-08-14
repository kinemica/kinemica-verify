from pathlib import Path


def test_public_and_bundled_schemas_match() -> None:
    root = Path(__file__).parents[1]
    for name in ("work-contract-v1.schema.json", "evidence-manifest-v1.schema.json"):
        assert (root / "schemas" / name).read_bytes() == (
            root / "src" / "kinemica_verify" / "schemas" / name
        ).read_bytes()
