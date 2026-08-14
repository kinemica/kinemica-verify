# Kinemica Verify

[![CI](https://github.com/kinemica/kinemica-verify/actions/workflows/ci.yml/badge.svg)](https://github.com/kinemica/kinemica-verify/actions/workflows/ci.yml)

Open-source verification infrastructure for physical-world work performed by people, agents, and machines.

Kinemica Verify defines machine-readable **Work Contracts** and deterministically checks submitted evidence against the conditions that matter for safe, correct completion. v0.2 can also bind a verification result to the exact contract, evidence manifest, and file-backed evidence using SHA-256, then authenticate that record with an Ed25519 signature.

## Why

Physical work increasingly crosses human, software-agent, robot, and mixed-team boundaries. A task being reported as complete is not enough for consequential operations. Completion criteria should be explicit before execution, and the resulting evidence should be independently checkable afterward.

Kinemica Verify provides a small, auditable layer for that purpose.

## Work Contract

A Work Contract states what must be true before, during, and after a job.

```yaml
version: 1

task:
  id: replace-filter
  actor: robot

preconditions:
  machine_powered_down: true

required_steps:
  - remove_old_filter
  - install_new_filter
  - secure_cover

constraints:
  max_force_n:
    op: lte
    value: 40

evidence:
  required:
    - before_image
    - replacement_serial
    - installation_image
    - torque_reading
    - final_system_test

final_state:
  system_test_passed: true
```

The evidence directory contains a `manifest.yaml` describing observed preconditions, completed steps, measurements, final state, and evidence artifacts.

## Install

Kinemica Verify requires Python 3.10 or newer.

```bash
python -m pip install -e .
```

For development:

```bash
python -m pip install -e ".[dev]"
```

## Verify a job

```bash
kinemica verify examples/filter-replacement/work.yaml examples/filter-replacement/evidence
```

Expected output:

```text
Kinemica Verify

Preconditions               PASS
Required steps              PASS
Safety constraints          PASS
Evidence                    PASS
Final state                 PASS

VERIFIED
```

The command exits with status `0` for a verified job, `1` for a failed verification, and `2` for invalid input or configuration. Add `--json` for machine-readable output.

## Create a signed verification record

Generate an Ed25519 key pair. Private keys are written with owner-only permissions and must not be committed to source control.

```bash
kinemica keygen \
  --private-key signer.private.pem \
  --public-key signer.public.pem
```

Create a signed record while verifying a job:

```bash
kinemica verify \
  examples/filter-replacement/work.yaml \
  examples/filter-replacement/evidence \
  --signing-key signer.private.pem \
  --record verification.json
```

The signed payload contains:

- SHA-256 of the exact Work Contract file
- SHA-256 of the exact evidence manifest
- SHA-256 and relative path for every valid file-backed artifact
- task identity
- the complete deterministic verification result
- the Ed25519 signer key fingerprint

The record contains no implicit timestamp, so the same inputs and signing key produce the same signed record.

## Verify a signed record

Authenticate the record against a trusted public key:

```bash
kinemica verify-record verification.json signer.public.pem
```

Re-check the original inputs and replay the verification result:

```bash
kinemica verify-record \
  verification.json \
  signer.public.pem \
  --contract examples/filter-replacement/work.yaml \
  --evidence examples/filter-replacement/evidence
```

Expected output:

```text
Kinemica Verify

Signature                   PASS
Work contract integrity     PASS
Evidence manifest integrity PASS
Artifact integrity          PASS
Verification replay         PASS

SIGNED RECORD VALID
```

A valid signature authenticates the record relative to the public key supplied by the verifier. Trust in the person or organization controlling that key must be established separately.

See [docs/verification-records.md](docs/verification-records.md) for the record format and trust boundary.

## Scope of v0.2

The verifier still focuses on deterministic verification of **structured evidence**. It does not infer task completion from images, video, or sensor streams. v0.2 adds tamper-evident evidence binding and signed, replayable verification records around that structured verification core.

A `VERIFIED` result means that the supplied structured evidence satisfies the configured Work Contract. A `SIGNED RECORD VALID` result means that the signed record is authentic for the supplied public key and, when source paths are supplied, that the bound inputs still match. Neither result proves unobserved physical reality, replaces independent safety engineering, or constitutes regulatory certification.

## Design principles

- **Explicit contracts**: completion criteria are machine-readable and reviewable before work starts.
- **Deterministic verification**: the same contract and evidence produce the same result.
- **Evidence first**: failures identify which requirement was not satisfied.
- **Cryptographic provenance**: signed records bind results to exact source files and artifacts.
- **Actor agnostic**: the same model can describe work performed by a person, robot, agent, or mixed team.
- **Composable**: integrations can add ROS 2, MCP, computer vision, telemetry, and enterprise systems around the core.
- **Local by default**: the open-source verifier does not require a hosted service.

## Repository layout

```text
src/kinemica_verify/    Reference verifier, record signing, and CLI
examples/               Complete example jobs and evidence
schemas/                Public interchange schemas
docs/                   Format and trust-boundary documentation
tests/                  Verification, integrity, signing, and CLI tests
```

## Roadmap

The near-term roadmap is intentionally narrow:

1. Stabilize Work Contract v1, Evidence Manifest v1, and Verification Record v1 semantics.
2. Add adapters for robot and agent execution traces and telemetry.
3. Add reference integrations for ROS 2 and agent/tool protocols.
4. Build reproducible benchmarks for physical-work verification failures.
5. Add pluggable evidence attestations without weakening deterministic local verification.

Compatibility and verification semantics take priority over feature count.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues should follow [SECURITY.md](SECURITY.md).

## Maintainer

Created and maintained by [Sylvester Kaczmarek](https://github.com/sylvesterkaczmarek).

## License

Apache License 2.0. See [LICENSE](LICENSE).
