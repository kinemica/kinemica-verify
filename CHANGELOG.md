# Changelog

All notable changes to Kinemica Verify are documented here.

## 0.3.0 - 2026-08-14

### Added

- Execution Trace v1 JSON Lines ingestion format.
- `kinemica ingest-trace` for deterministic trace-to-manifest conversion.
- Strict event ordering, duplicate-key detection, duplicate semantic-name rejection, and non-finite JSON number rejection.
- File-boundary validation for trace-declared artifacts.
- Automatic `execution_trace` provenance artifact so signed records bind the source trace bytes.
- Public Execution Trace Event v1 JSON Schema and format documentation.
- Reference filter-replacement execution trace.
- CI regeneration gate proving the checked-in manifest is reproduced exactly from the trace.

### Improved

- PyPI-first installation instructions and package badge.
- CI and package documentation for execution-trace ingestion.

Work Contract v1, Evidence Manifest v1, and Verification Record v1 semantics remain unchanged.

## 0.2.1 - 2026-08-14

### Fixed

- Raised the minimum Setuptools build dependency to 77 so the declared PEP 639 SPDX license metadata is supported by every allowed build backend version.

### Improved

- Reworked the README around a faster quick start and clearer public project explanation.
- Added wheel and source distributions to the GitHub release process.
- Added a clean-environment wheel smoke test to CI.
- Added a manual PyPI Trusted Publishing workflow with isolated OIDC permissions.
- Added project changelog and package documentation links.

No Work Contract, Evidence Manifest, or Verification Record semantics changed in this patch release.

## 0.2.0 - 2026-08-14

### Added

- SHA-256 binding for Work Contracts, Evidence Manifests, and file-backed artifacts.
- Deterministic Verification Record v1.
- Ed25519 key generation, record signing, and signature verification.
- Public-key fingerprints for signer identification.
- Source integrity re-checking and verification replay.
- `kinemica keygen` and `kinemica verify-record` CLI commands.
- Verification Record v1 JSON Schema and trust-boundary documentation.
- End-to-end signed-record round-trip validation in CI.

### Improved

- CI coverage across Python 3.10, 3.12, and 3.14.
- Security-reporting instructions and private-key handling guidance.
- CLI regression coverage for success, failed verification, and invalid input exit codes.

## 0.1.0 - 2026-08-14

### Added

- Work Contract v1 and Evidence Manifest v1 schemas.
- Deterministic verification of preconditions, required steps, numeric constraints, evidence, and final state.
- Path-boundary checks for file-backed evidence.
- Human-readable and JSON CLI output.
- Filter-replacement reference example.
