# Phase 9 registry publication plan

Status: architecture proposal; intentionally deferred behind the 0.8.1 release
and provenance gates.

## Backend decision

Use an OCI Distribution 1.1 registry through ORAS as the first backend. GHCR is
the preferred initial hosted deployment because it is adjacent to the source
repository and reuses GitHub package permissions. The protocol remains OCI, so
the client is not permanently coupled to GitHub.

This replaces a bespoke S3 and DynamoDB API in the first iteration. OCI already
provides content-addressed manifests and blobs, media types, tags, authentication
challenges, and referrers for signatures and provenance.

## Package representation

- One immutable skill archive blob with media type
  `application/vnd.polymind.skill.v1+tar+gzip`.
- One OCI artifact manifest with artifact type
  `application/vnd.polymind.skill.manifest.v1+json`.
- Annotations for canonical skill name, SemVer behavior version, framework
  compatibility, source repository, source commit, and creation time.
- A SemVer tag for discovery, but the catalog and lockfiles store and install
  the resolved `sha256:` manifest digest.
- Sigstore/SLSA attestations and signatures attached through OCI 1.1 subject and
  referrer relationships.

## API and authorization

The normative upload and retrieval API is the OCI Distribution specification,
not a parallel custom OpenAPI surface. A future discovery service may expose a
small OpenAPI 3.1 read API for full-text search and policy metadata, but package
push/pull stays OCI-native.

Interactive publishers authenticate through the selected registry's supported
OAuth/device or token flow. CI uses narrowly scoped, short-lived repository
credentials where the backend supports them. Roles are mapped to registry
permissions:

- reader: pull manifests, blobs, and referrers;
- publisher: push new versions, never overwrite an existing version digest;
- maintainer: deprecate metadata and manage publisher membership;
- administrator: registry and retention policy only.

## Planned CLI and catalog flow

`polymind registry publish PATH --registry HOST/NAMESPACE` will validate the
canonical package, build a deterministic archive, calculate its digest, refuse
an existing SemVer tag with a different digest, push with ORAS, attach
provenance, and verify the remote digest before success.

`catalog.py` will resolve a name and version to an immutable digest, download to
a bounded temporary directory, verify provenance and declared capabilities,
then pass the package through the existing canonical validator. Network access,
credentials, cache location, and trust policy will all be explicit CLI inputs;
unknown media types and missing attestations fail closed.

## Delivery sequence

1. Write threat model and OCI media-type contract.
2. Build a local disposable registry integration fixture.
3. Implement read-only resolve and pull by digest.
4. Implement publish without mutable overwrite.
5. Add Sigstore referrer verification and RBAC negative tests.
6. Pilot GHCR, then decide whether a separate discovery API is justified.

The design follows [OCI Distribution 1.1](https://opencontainers.org/posts/blog/2024-03-13-image-and-distribution-1-1/)
and the [ORAS documentation](https://oras.land/docs/).
