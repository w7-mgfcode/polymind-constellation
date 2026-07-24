# Migrating a Claude-first skill

Migration creates a self-contained canonical package; it does not edit or
depend on the original `.claude/skills` source.

1. Inventory the complete source package, following symlinks for analysis while
   recording both the link and resolved content. Record provenance, license,
   file digests, and intentional exclusions.
2. Copy the package into `skills/<name>/`. Materialize symlinked resources as
   ordinary files and move detailed content into package-local `references/`,
   `assets/`, and `scripts/` without breaking links.
3. Keep portable Agent Skills fields in `SKILL.md`. Move Claude-only
   `allowed-tools` into `adapters/claude/overlays/<name>.toml` and map every tool
   to a declared canonical capability.
4. Add `skill.toml` with schema version, behavior provenance, approval policy,
   capabilities, triggers, dependencies, placeholders, and complete script
   declarations.
5. Replace provider, tracker, language, or hosting assumptions with opt-in
   profiles where doing so preserves the owner-authored behavior. Record every
   deviation in `docs/provenance/migration-map.json` and the migration record.
6. Add conformance cases and run validation, dry-run projection, apply,
   projection check, and `scripts/verify`.

Do not copy a provider permission grant into the neutral source. Do not leave a
resource outside the package or preserve a cross-directory symlink. Do not
delete an existing target skill during migration; downstream ownership is
handled by the conflict-safe installer.

The three current migrations and their source digests are documented in
[migration-deviations.md](migration-deviations.md) and
[`docs/provenance/migration-map.json`](provenance/migration-map.json). The
original community directory remains unchanged.
