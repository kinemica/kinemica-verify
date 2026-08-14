# Kinemica Verify

[![CI](https://github.com/kinemica/kinemica-verify/actions/workflows/ci.yml/badge.svg)](https://github.com/kinemica/kinemica-verify/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/kinemica-verify.svg)](https://pypi.org/project/kinemica-verify/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Open-source verification infrastructure for physical-world work performed by people, agents, and machines.

Kinemica Verify turns a machine-readable **Work Contract** and collected evidence into a deterministic pass/fail result. It can bind that result to the exact contract, evidence manifest, and file-backed evidence with SHA-256, then authenticate the resulting record with an Ed25519 signature.

v0.3 adds a deterministic execution-trace ingestion layer so operational systems can generate verification evidence from an ordered event stream instead of hand-authoring `manifest.yaml`.

## Install

```bash
python -m pip install kinemica-verify
```

Kinemica Verify requires Python 3.10 or newer.

## Verify structured evidence

```bash
kinemica verify work.yaml evidence/
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

The CLI exits with `0` for a verified job, `1` for a failed verification, and `2` for invalid input or configuration. Add `--json` to verification commands for machine-readable output.

## Ingest an execution trace

Kinemica Execution Trace v1 is a JSON Lines event stream. Each event has a strictly increasing `sequence`, a `kind`, and a `name`. Events can represent preconditions, completed steps, measurements, artifacts, and final state.

```json
{"version":1,"sequence":1,"kind":"precondition","name":"machine_powered_down","value":true}
{"version":1,"sequence":2,"kind":"step","name":"remove_old_filter"}
{"version":1,"sequence":3,"kind":"measurement","name":"max_force_n","value":31.8}
{"version":1,"sequence":4,"kind":"artifact","name":"before_image","path":"before_image.jpg"}
{"version":1,"sequence":5,"kind":"final_state","name":"system_test_passed","value":true}
```

Put the trace and any referenced files inside the evidence directory, then generate the manifest:

```bash
kinemica ingest-trace evidence/trace.jsonl evidence/
kinemica verify work.yaml evidence/
```

If `manifest.yaml` already exists, ingestion refuses to overwrite it unless `--force` is supplied.

The generated manifest automatically includes the source trace as the `execution_trace` file-backed artifact. Signed verification records therefore bind the exact trace bytes along with other file-backed evidence.

See [docs/execution-traces.md](docs/execution-traces.md) for the event format, deterministic conversion rules, and trust boundary.

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
  work.yaml \
  evidence/ \
  --signing-key signer.private.pem \
  --record verification.json
```

Authenticate the record and re-check its original inputs:

```bash
kinemica verify-record \
  verification.json \
  signer.public.pem \
  --contract work.yaml \
  --evidence evidence/
```

A signed record binds:

- the exact Work Contract bytes
- the exact Evidence Manifest bytes
- every valid file-backed evidence artifact
- task identity
- the complete deterministic verification result
- the signer public-key fingerprint

Verification records contain no implicit timestamp or random nonce, so identical inputs signed with the same key produce the same record.

See [docs/verification-records.md](docs/verification-records.md) for the record format and trust boundary.

## Data flow

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
 execution trace / evidence
        |
        v
 Kinemica Verify
        |
        +--> VERIFIED / NOT VERIFIED
        |
        +--> signed verification record
```

Execution-system adapters can translate telemetry, robot logs, ROS 2 messages, inspection outputs, or enterprise-system events into Execution Trace v1 while leaving the verification core unchanged.

## Current scope

v0.3 verifies structured evidence and can deterministically derive Evidence Manifest v1 from a structured JSON Lines execution trace. It does not infer completion from images or video and does not yet decode ROS 2 bags or raw sensor streams directly.

`VERIFIED` means the supplied evidence satisfies the configured Work Contract. `SIGNED RECORD VALID` means the record is authentic for the supplied public key and, when source paths are provided, the bound inputs still match. These results do not prove unobserved physical reality, replace independent safety engineering, or constitute regulatory certification.

## Design principles

- **Explicit contracts**: completion criteria are machine-readable and reviewable before work starts.
- **Deterministic verification**: the same contract and evidence produce the same result.
- **Evidence first**: failures identify which requirement was not satisfied.
- **Cryptographic provenance**: signed records bind results to exact source files and artifacts.
- **Actor agnostic**: the same model works across people, robots, agents, and mixed teams.
- **Composable ingestion**: execution-system adapters can feed a stable event format.
- **Local by default**: the open-source verifier does not require a hosted service.

## Repository layout

```text
src/kinemica_verify/    Verifier, trace ingestion, signing, and CLI
examples/               Complete example jobs, traces, and evidence
schemas/                Public interchange schemas
docs/                   Format and trust-boundary documentation
tests/                  Verification, trace, integrity, signing, and CLI tests
```

## Development

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest
```

CI runs installation, lint, tests, deterministic trace-to-manifest regeneration, the reference verification, a full signed-record round trip, and a clean wheel installation on supported Python versions.

## Roadmap

1. Add a reference ROS 2 rosbag2/MCAP adapter that emits Execution Trace v1.
2. Add reproducible benchmarks for physical-work verification failures.
3. Add reference adapters for agent/tool execution logs and industrial telemetry.
4. Add pluggable evidence attestations without weakening deterministic local verification.
5. Stabilize the public interchange formats based on real integrations and external use.

Compatibility and verification semantics take priority over feature count.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues should follow [SECURITY.md](SECURITY.md).

## Maintainer

Created and maintained by [Sylvester Kaczmarek](https://github.com/sylvesterkaczmarek).

## License

Apache License 2.0. See [LICENSE](LICENSE).
