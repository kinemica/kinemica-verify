# Execution Trace v1

Kinemica Execution Trace v1 is the ingestion boundary between an execution system and Evidence Manifest v1.

The trace format is intentionally small. A robot, software agent, workflow engine, industrial controller, or adapter can emit ordered events without implementing Kinemica Verify's manifest format directly.

## Encoding

A trace is UTF-8 JSON Lines. Each non-empty line contains exactly one JSON object satisfying `execution-trace-event-v1.schema.json`.

Every event contains:

- `version`, currently `1`
- `sequence`, a non-negative integer that must be strictly increasing across the trace
- `kind`
- `name`

`timestamp_ns` is optional. It is preserved in the source trace but is not used to order events or copied into the generated manifest. `sequence` is the authoritative order.

## Event kinds

### `precondition`

Requires `value`. Produces one entry under `preconditions`.

```json
{"version":1,"sequence":1,"kind":"precondition","name":"machine_powered_down","value":true}
```

### `step`

Carries no `value` or `path`. Step order in the generated manifest follows trace sequence.

```json
{"version":1,"sequence":2,"kind":"step","name":"remove_old_filter"}
```

### `measurement`

Requires a numeric `value`. Produces one entry under `measurements`.

```json
{"version":1,"sequence":3,"kind":"measurement","name":"max_force_n","value":31.8}
```

### `artifact`

Requires `value`, `path`, or both. File paths must remain inside the evidence directory and must resolve to an existing file at ingestion time.

```json
{"version":1,"sequence":4,"kind":"artifact","name":"before_image","path":"before_image.jpg"}
```

### `final_state`

Requires `value`. Produces one entry under `final_state`.

```json
{"version":1,"sequence":5,"kind":"final_state","name":"system_test_passed","value":true}
```

## Deterministic conversion rules

`kinemica ingest-trace` applies these rules:

1. Empty lines are ignored.
2. Every event must satisfy the public JSON Schema.
3. Duplicate JSON object keys are rejected.
4. Non-standard non-finite JSON numbers such as `NaN` and `Infinity` are rejected.
5. `sequence` values must be strictly increasing.
6. Duplicate precondition, measurement, artifact, final-state, or step names are rejected.
7. File-backed artifact paths must stay inside the evidence directory.
8. The source trace itself is added to the generated manifest as `execution_trace`.
9. `manifest.yaml` is written atomically.
10. Existing manifests are preserved unless `--force` is supplied.

These rules remove ambiguity about how one trace maps to one Evidence Manifest v1 document.

## CLI

The trace must be located inside the evidence directory:

```bash
kinemica ingest-trace evidence/trace.jsonl evidence/
```

To intentionally regenerate an existing manifest:

```bash
kinemica ingest-trace evidence/trace.jsonl evidence/ --force
```

Then verify normally:

```bash
kinemica verify work.yaml evidence/
```

## Provenance

The generated manifest contains:

```yaml
artifacts:
  execution_trace:
    path: trace.jsonl
```

When a signed Verification Record is created, Kinemica Verify hashes every valid file-backed artifact in the manifest. The exact trace bytes are therefore included in the signed provenance set automatically.

## Trust boundary

Trace ingestion establishes a deterministic relationship between the supplied event stream and the generated manifest. It does not establish that an event corresponds to an event in the physical world.

The trustworthiness of the trace still depends on how events were produced, which sensors or systems supplied them, how identities and clocks were managed, and whether the execution environment itself was trustworthy.

Future adapters can add source-specific validation before emitting Execution Trace v1 without changing the deterministic verification core.
