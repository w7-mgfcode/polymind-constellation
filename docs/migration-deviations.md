# Phase 3 migration deviations

The migration preserves the three source workflows before the Phase 5
portability refactor. All 19 source files are mapped in the machine-readable
[migration map](provenance/migration-map.json).

Intentional changes are limited to package normalization:

- Remove Claude-specific `allowed-tools` from canonical frontmatter and add
  project license plus namespaced Polymind metadata.
- Move legacy `templates/` directories to the Agent Skills `assets/` package
  location and update package-local references.
- Materialize `maintaining-agent-docs` as ordinary copied files instead of a
  cross-directory symlink.
- Add `skill.toml` sidecars containing provenance, closed capabilities,
  approval policy, parity triggers, script declarations, and explicit template
  variable allowlists.
- Apply formatting-only changes to the bundled documentation validator so it
  passes the repository lint gate. Its behavior is unchanged.

Provider, GitHub, and Hungarian rules remain where they were part of the source
workflow. Generalizing those legacy profiles is Phase 5 work and is not folded
into this parity migration.

## Phase 5 continuation

Phase 5 supersedes the portable entrypoints while preserving owner-authored
specialization in explicit legacy and provider profiles. The migration map now
labels files changed by that continuation; unchanged source resources retain
their digest-backed exact-copy status. The original vendor directory remains
untouched and the canonical packages are self-contained.
