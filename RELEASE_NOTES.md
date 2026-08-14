## Kinemica Verify v0.2.1

This patch release tightens packaging and public distribution without changing verification semantics.

### Fixed

- Raised the minimum Setuptools build dependency to 77 so the PEP 639 SPDX license metadata is supported by every permitted build backend version.

### Improved

- Faster README quick start and clearer project explanation.
- Wheel and source-distribution release assets.
- Clean-environment wheel smoke testing in CI.
- Manual PyPI Trusted Publishing workflow with isolated OIDC permissions.
- Changelog and package documentation links.

Work Contract v1, Evidence Manifest v1, and Verification Record v1 remain unchanged.
