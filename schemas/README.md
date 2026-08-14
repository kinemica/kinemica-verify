# Schemas

These JSON Schemas define the public v1 interchange formats used by Kinemica Verify.

- `work-contract-v1.schema.json` defines task requirements.
- `evidence-manifest-v1.schema.json` defines structured evidence submitted for verification.

The verifier bundles identical copies under `src/kinemica_verify/schemas/` so installed packages can validate inputs offline. Tests enforce that the public and bundled copies remain byte-identical.
