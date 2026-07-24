# Versioning and release policy

Polymind has three independent compatibility numbers.

## Framework version

The Python package and CLI use Semantic Versioning. `0.8.1` is a pre-1.0
release: the public CLI and lock formats are documented, but complete native
provider behavioral parity remains open. During `0.y.z`, incompatible framework
changes increment the minor version; compatible fixes increment the patch
version. Version `1.0.0` is reserved for a stable public API and completed
production-readiness gates.

The authoritative runtime value is `polymind.__version__`; `pyproject.toml` and
`uv.lock` must match it. Tests enforce equality. Generated and installed locks
record the framework version.

## Skill behavior version

Each canonical skill owns `metadata.polymind.version` independently:

- major: incompatible procedure, approval, output, trigger, or capability
  behavior;
- minor: backward-compatible profile, resource, trigger, or workflow addition;
- patch: clarification or correction that preserves observable behavior.

Any behavior version change must update `CHANGELOG.md`, conformance cases when
routing or approval could change, and regenerated projections.

## Package schema version

`skill.toml`, provider overlays, compatibility manifests, conformance matrices,
and lockfiles currently use schema major `"1"`. Backward-compatible optional
fields remain within schema 1. A renamed/removed field, changed meaning, or new
required field requires schema `"2"`, a migration guide, and explicit support
for reading or rejecting older data. Schema version and skill behavior version
must never be inferred from one another.

## Release checklist

1. Update `CHANGELOG.md`, framework version, and any changed skill versions.
2. Re-verify primary provider documentation and update evidence dates/scopes.
3. Run `scripts/sync-adapters --dry-run`, review, then `--apply` and `--check`.
4. Run static conformance and every available opt-in client smoke test. Record
   skips rather than converting them into passes.
5. Run `scripts/verify`.
6. Build with `uv build`, inspect the wheel for `polymind/_projection/`, install
   it into a disposable environment, and run downstream dry-run/apply/check/
   rollback.
7. Generate and verify release evidence according to the
   [release automation contract](release-automation.md). Publish only from the
   tagged GitHub workflow through PyPI Trusted Publishing; do not use a local
   long-lived upload token.
8. Independently verify the PyPI files, GitHub Release assets, SHA-256 manifest,
   and Sigstore provenance before marking the release published.

The increment rules follow [Semantic Versioning 2.0.0](https://semver.org/).
Python distribution metadata follows the
[PyPA project metadata specification](https://packaging.python.org/specifications/declaring-project-metadata/).
