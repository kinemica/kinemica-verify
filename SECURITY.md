# Security

Kinemica Verify handles paths, manifests, verification records, signatures, and policy-like verification inputs. Security issues may therefore affect systems that consume verification results.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability.

Email **hello@kinemica.com** with the subject `Kinemica Verify security report`. Include:

- affected version or commit
- reproduction steps
- expected and observed behavior
- likely impact
- any suggested mitigation

We will acknowledge valid reports and coordinate disclosure after a fix is available.

## Signing keys

`kinemica keygen` writes an unencrypted Ed25519 private key and applies owner-only file permissions where the operating system supports them. Keep private keys outside source control, restrict filesystem access, and use a separate key-management system when operational requirements demand stronger key custody.

A public key must reach the verifier through an independent trusted channel. A valid signature proves possession of the corresponding private key; signer identity depends on how that public key is distributed and trusted.

## Security boundary

A successful work verification means the supplied evidence satisfies the configured Work Contract under the verifier's rules. A valid signed record also establishes integrity relative to the supplied public key and any source files that were re-checked. These results do not establish that unobserved physical events occurred, certify a robot or work process as safe, or replace independent operational safeguards.
