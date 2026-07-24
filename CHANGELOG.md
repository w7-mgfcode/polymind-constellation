# Changelog

All notable framework and canonical skill behavior changes are recorded here.
The framework follows Semantic Versioning; skill behavior versions remain
independent and are named explicitly.

## 0.8.1 - 2026-07-23

This hardening release was built and validated locally; it has not been
published to a package registry.

### Fixed

- Restored every managed projection destination after interruption at any
  atomic-replacement boundary.
- Rejected symlinked canonical roots, package directories and resources,
  installer roots, and existing generated projection paths, including
  digest-identical substitutions.
- Removed process-working-directory projection shadowing; installed releases
  prefer their bundled projection and source checkouts are resolved relative to
  the framework module.
- Preserved `skip`, `partial`, and `measured` conformance outcomes instead of
  summarizing every non-failure as `pass`.

### Changed

- Installer output now identifies the selected projection path, projection-lock
  digest, and framework version before reporting planned changes.
- Added a tag-triggered, commit-pinned GitHub Actions release pipeline using
  PyPI Trusted Publishing and a separate protected publication environment.
- Added deterministic SHA-256 manifests and release notes plus fail-closed
  Git/tag/artifact/Sigstore provenance verification for release mode.
- Required exact-identity Gitsign verification for the release commit; the
  workflow installs a versioned binary only after checking its SHA-256.
- Added CI workflow pinning tests, provenance fault tests, and a Phase 9
  OCI/ORAS registry architecture plan.

## 0.8.0 - 2026-07-22

This release was built and validated locally; it has not been published to a
package registry.

### Added

- Conflict-safe downstream installation with dry-run, bounded unified diff,
  explicit apply, drift check, atomic recovery, and one-generation rollback.
- A wheel-bundled generated projection for offline downstream installation.
- Contributor, installation, security, Claude-first migration, compatibility,
  and versioning/release documentation.
- A tested fourth-skill fixture proving projection and catalog extensibility.

### Changed

- Compatibility evidence now records a 90-day freshness window, per-provider
  evidence dates and scopes, and distinct tested/static-only/unsupported states.
- Generated projection locks now record framework version `0.8.0`.

### Known gaps

- Claude live invocation and OpenCode native discovery remain untested.
- Full positive, negative, resource, and approval behavior has not passed across
  every native provider.
- Raw Ollama models are measured inputs to a data-only harness, not safe
  executable agents.

## 0.7.0 - 2026-07-22

- Added cross-provider static conformance, Codex/Gemini native discovery probes,
  and two pinned Ollama structured-output measurements.

## 0.6.0 - 2026-07-22

- Added the provider-SDK-free catalog, activation, bounded resource access, and
  local-harness safety contract.

## 0.5.0 - 2026-07-22

- Refactored all three canonical skills into portable cores with opt-in legacy,
  language, host, tracker, and assistant profiles. Skill behavior versions moved
  to `2.0.0`.

## 0.4.0 - 2026-07-22

- Established provenance, canonical validation, lossless self-contained
  migration, closed capabilities, deterministic Claude and `.agents`
  projections, overlays, locks, conflict checks, and rollback tests.
