## Kinemica Verify v0.2.0

Kinemica Verify is open-source verification infrastructure for physical-world work performed by people, agents, and machines.

This release adds cryptographic provenance around the deterministic verification core.

### Included

- Work Contract v1 and Evidence Manifest v1 verification
- deterministic pass/fail verification
- SHA-256 integrity binding for contracts, manifests, and file-backed artifacts
- Verification Record v1
- Ed25519 key generation and record signing
- signature authentication against a supplied trusted public key
- source integrity re-checking and verification replay
- human-readable and JSON CLI output
- Python 3.10, 3.12, and 3.14 CI coverage
- 21 automated tests at the release baseline

### Trust boundary

A valid signed record authenticates the signed payload relative to the supplied public key and can prove that re-checked source files still match their recorded digests. It does not establish who controls a key, prove unobserved physical events, replace independent safety engineering, or constitute regulatory certification.
