# Kinemica Verify

Open-source verification infrastructure for physical-world work performed by people, agents, and machines.

Kinemica Verify defines machine-readable **Work Contracts** and deterministically checks submitted evidence against the conditions that matter for safe, correct completion: preconditions, required steps, operational constraints, required evidence, and final state.

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

Preconditions       PASS
Required steps      PASS
Safety constraints  PASS
Evidence            PASS
Final state         PASS

VERIFIED
```

The command exits with status `0` for a verified job, `1` for a failed verification, and `2` for invalid input or configuration. Add `--json` for machine-readable output.

## Scope of v0.1

The first release focuses on deterministic verification of **structured evidence**. It does not infer task completion from images, video, or sensor streams. Perception and telemetry adapters can be added later without changing the core Work Contract model.

A `VERIFIED` result means that the supplied structured evidence satisfies the configured Work Contract. It does not prove unobserved physical reality, replace independent safety engineering, or constitute regulatory certification.

## Design principles

- **Explicit contracts**: completion criteria are machine-readable and reviewable before work starts.
- **Deterministic verification**: the same contract and evidence produce the same result.
- **Evidence first**: failures identify which requirement was not satisfied.
- **Actor agnostic**: the same model can describe work performed by a person, robot, agent, or mixed team.
- **Composable**: integrations can add ROS 2, MCP, computer vision, telemetry, and enterprise systems around the core.
- **Local by default**: the open-source verifier does not require a hosted service.

## Repository layout

```text
src/kinemica_verify/    Reference verifier and CLI
examples/               Complete example jobs and evidence
schemas/                Work Contract and Evidence Manifest schemas
tests/                  Verification and CLI tests
```

## Roadmap

The near-term roadmap is intentionally narrow:

1. Stabilize Work Contract v1 and Evidence Manifest v1 semantics.
2. Add cryptographic evidence integrity and signed verification records.
3. Add adapters for robot/agent execution traces and telemetry.
4. Add reference integrations for ROS 2 and agent/tool protocols.
5. Build reproducible benchmarks for physical-work verification failures.

The roadmap is directional. Compatibility and verification semantics take priority over feature count.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues should follow [SECURITY.md](SECURITY.md).

## Maintainer

Created and maintained by [Sylvester Kaczmarek](https://github.com/sylvesterkaczmarek).

## License

Apache License 2.0. See [LICENSE](LICENSE).
