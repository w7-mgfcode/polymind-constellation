# Development direction decision

Evidence date: 2026-07-23

## Scoring model

The three proposals were scored on a 100-point scale. Each criterion is rated
from 1 to 5 and multiplied by its weight.

| Criterion | Weight | Release automation | Provenance | Registry |
| --- | ---: | ---: | ---: | ---: |
| Urgency and risk reduction | 25 | 5 | 5 | 3 |
| Immediate user and release value | 25 | 5 | 4 | 3 |
| Architectural dependency value | 20 | 5 | 5 | 2 |
| Implementability in the current repository | 15 | 3 | 3 | 1 |
| Operational sustainability | 15 | 5 | 5 | 2 |
| **Weighted score** | **100** | **94** | **89** | **47** |

## Decision

1. **0.8.1 release automation — 94/100.** This closes the current release
   cycle and replaces long-lived upload credentials with PyPI Trusted
   Publishing.
2. **Git and artifact provenance — 89/100.** This is a prerequisite for a
   defensible public release and is implemented in the same pipeline.
3. **Registry publication — 47/100.** This has strategic value, but publishing
   into a new registry before release identity, artifact integrity, and
   operational ownership are established would invert the dependency order.

The selected implementation is directions 1 and 2. Direction 3 is retained as
the [Phase 9 registry plan](phase9-registry.md), with no premature publisher CLI
or backend commitment in the 0.8.1 release.

## Research conclusions

- PyPI recommends Trusted Publishing with short-lived OIDC credentials and a
  dedicated GitHub environment. The publish job is separated from the build
  job and contains no API token.
- GitHub artifact attestations use Sigstore and bind the artifact to repository,
  workflow, commit, and ref identity. Verification additionally pins the signer
  workflow, source digest, source ref, and SLSA provenance predicate.
- Release commits additionally require Gitsign verification against an exact
  certificate identity and OIDC issuer; no long-lived signing key is stored.
- A GitHub-hosted build with signed provenance is designed to satisfy SLSA
  Build Level 2. Build Level 3 requires moving build and signing into an
  appropriately hardened reusable workflow; this repository does not claim
  Level 3.
- OCI Distribution 1.1 and ORAS provide content-addressed generic artifacts,
  subject relationships, and referrers. They are a better Phase 9 foundation
  than inventing a bespoke S3 and DynamoDB protocol first.

Primary references:

- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [PyPI Trusted Publisher security model](https://docs.pypi.org/trusted-publishers/security-model/)
- [GitHub artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [GitHub attestation verification](https://cli.github.com/manual/gh_attestation_verify)
- [Sigstore Gitsign](https://github.com/sigstore/gitsign)
- [SLSA build track basics](https://slsa.dev/spec/v1.2/build-track-basics)
- [OCI Image and Distribution 1.1](https://opencontainers.org/posts/blog/2024-03-13-image-and-distribution-1-1/)
- [ORAS documentation](https://oras.land/docs/)
