# Contributing

Kinemica Verify is building a small, auditable verification core for physical-world work.

## Development

Use Python 3.10 or newer.

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
```

Before proposing a change:

1. Keep verification semantics deterministic.
2. Add tests for both passing and failing behavior.
3. Do not weaken path, schema, or evidence validation to make an example pass.
4. Keep Work Contract changes backward-compatible within v1 unless the change is explicitly versioned.
5. Update both public and bundled schema copies. The test suite checks that they remain identical.

## Pull requests

Keep changes focused. Explain the physical-work failure mode or verification requirement being addressed, and include a reproducible test.

For substantial changes to Work Contract semantics, open an issue first so the compatibility impact can be discussed.

## Code of conduct

Be precise, constructive, and respectful. Technical disagreement is expected; personal attacks and harassment are not.
