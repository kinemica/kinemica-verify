# Kinemica Verify

[![CI](https://github.com/kinemica/kinemica-verify/actions/workflows/ci.yml/badge.svg)](https://github.com/kinemica/kinemica-verify/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Open-source verification infrastructure for physical-world work performed by people, agents, and machines.

Kinemica Verify turns a machine-readable **Work Contract** and collected evidence into a deterministic pass/fail result. It can also bind that result to the exact contract, manifest, and file-backed evidence with SHA-256 and authenticate the resulting record with an Ed25519 signature.

## Quick start

Kinemica Verify requires Python 3.10 or newer.

```bash
git clone https://github.com/kinemica/kinemica-verify.git
cd kinemica-verify
python -m pip install .
kinemica verify examples/filter-replacement/work.yaml examples/filter-replacement/evidence
```

Expected result:

```text
Kinemica Verify

Preconditions               PASS
Required steps              PASS
Safety constraints          PASS
Evidence                    PASS
Final state                 PASS

VERIFIED
```

The CLI exits with `0` for a verified job, `1` for a failed verification, and `2` for invalid input or configuration. Add `--json` for machine-readable output.

## What it checks

| Check | Purpose |
| --- | --- |
| Preconditions | Required state before work starts |
| Required steps | Whether every mandated step is present in the evidence |
| Safety constraints | Numeric limits such as force, torque, temperature, or other measured values |
| Evidence | Whether required evidence exists and file-backed evidence stays inside the evidence boundary |
| Final state | Whether the resulting state matches the contract |

The same verification model can describe work performed by a person, robot, software agent, or mixed team.

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

## Signed verification records

Generate an Ed25519 key pair:

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

Authenticate the record and re-check its original inputs:

```bash
kinemica verify-record \
  verification.json \
  signer.public.pem \
  --contract examples/filter-replacement/work.yaml \
  --evidence examples/filter-replacement/evidence
```

Expected result:

```text
Kinemica Verify

Signature                   PASS
Work contract integrity     PASS
Evidence manifest integrity PASS
Artifact integrity          PASS
Verification replay         PASS

SIGNED RECORD VALID
```

A signed record binds:

- the exact Work Contract bytes
- the exact Evidence Manifest bytes
- every valid file-backed evidence artifact
- task identity
- the complete deterministic verification result
- the signer public-key fingerprint

Verification records contain no implicit timestamp or random nonce, so identical inputs signed with the same key produce the same record.

See [docs/verification-records.md](docs/verification-records.md) for the format and trust boundary.

## How it fits

```text
physical-world task
        |
        v
   Work Contract
        |
        v
person / robot / agent
        |
        v
collected evidence
        |
        v
 Kinemica Verify
        |
        +--> VERIFIED / NOT VERIFIED
        |
        +--> signed verification record
```

Adapters can later translate execution traces, telemetry, ROS 2 messages, inspection outputs, or enterprise-system events into the evidence format while leaving the core verification semantics unchanged.

## Current scope

v0.2 verifies **structured evidence** deterministically. It does not infer completion from images, video, or raw sensor streams.

`VERIFIED` means the supplied evidence satisfies the configured Work Contract. `SIGNED RECORD VALID` means the record is authentic for the supplied public key and, when source paths are provided, the bound inputs still match. These results do not prove unobserved physical reality, replace independent safety engineering, or constitute regulatory certification.

## Design principles

- **Explicit contracts**: completion criteria are machine-readable and reviewable before work starts.
- **Deterministic verification**: the same contract and evidence produce the same result.
- **Evidence first**: failures identify which requirement was not satisfied.
- **Cryptographic provenance**: signed records bind results to exact source files and artifacts.
- **Actor agnostic**: the same model works across people, robots, agents, and mixed teams.
- **Composable**: integrations can extend evidence collection without changing the verification core.
- **Local by default**: the open-source verifier does not require a hosted service.

## Repository layout

```text
src/kinemica_verify/    Reference verifier, record signing, and CLI
examples/               Complete example jobs and evidence
schemas/                Public interchange schemas
docs/                   Format and trust-boundary documentation
tests/                  Verification, integrity, signing, and CLI tests
```

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
```

CI runs installation, lint, tests, the reference example, and a full signed-record round trip on Python 3.10, 3.12, and 3.14.

## Roadmap

1. Stabilize Work Contract v1, Evidence Manifest v1, and Verification Record v1 semantics.
2. Add one production-shaped execution-trace or telemetry adapter.
3. Add a reference ROS 2 integration.
4. Build reproducible benchmarks for physical-work verification failures.
5. Add pluggable evidence attestations without weakening deterministic local verification.

Compatibility and verification semantics take priority over feature count.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues should follow [SECURITY.md](SECURITY.md).

## Maintainer

Created and maintained by [Sylvester Kaczmarek](https://github.com/sylvesterkaczmarek).

## License

Apache License 2.0. See [LICENSE](LICENSE).
