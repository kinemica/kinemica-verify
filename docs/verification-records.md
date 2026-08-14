# Verification records

Kinemica Verification Record v1 is a JSON envelope containing a deterministic payload and an Ed25519 signature over that payload.

## Signed payload

The signed payload binds four classes of information:

- task ID and actor from the Work Contract
- SHA-256 digest of the exact Work Contract bytes
- SHA-256 digest of the exact Evidence Manifest bytes
- SHA-256 digest and relative path of every valid file-backed artifact
- the complete verification result

Scalar evidence remains bound through the Evidence Manifest digest.

The payload is serialized as UTF-8 JSON with keys sorted, compact separators, Unicode preserved, and non-finite numbers rejected. The signature also includes a fixed Kinemica Verify v1 domain-separation prefix.

## Signatures

Records use Ed25519. The `key_id` is the SHA-256 digest of the raw 32-byte Ed25519 public key, prefixed with `sha256:`.

The record does not embed a public key. Verification therefore requires a public key supplied through an independent trust path. This avoids treating a self-declared key inside the record as proof of signer identity.

## Source verification

`kinemica verify-record` can authenticate only the signed record, or it can additionally receive the original Work Contract and evidence directory.

When source paths are supplied it checks:

1. Work Contract SHA-256
2. Evidence Manifest SHA-256
3. every signed file-backed artifact SHA-256
4. a fresh verification replay against the current verifier

A changed file fails its corresponding integrity check even when the changed content would still satisfy the Work Contract.

## Determinism

Verification Record v1 contains no automatically generated timestamp or random nonce. Ed25519 signatures are deterministic, so identical inputs signed by the same key produce identical records.

Time, operator identity, hardware attestation, certificate chains, transparency logs, and external trust metadata can be layered around this format without changing the v1 signed payload semantics.

## Trust boundary

A valid record establishes that:

- the payload has not changed since it was signed
- the signature was produced by the private key corresponding to the supplied public key
- optional source checks match the digests recorded in the signed payload

It does not establish who controls the key, prove unobserved physical events, certify a work process as safe, or replace independent operational safeguards.
