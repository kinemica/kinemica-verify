# Changelog

All notable changes to Kinemica Verify are documented here.

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
