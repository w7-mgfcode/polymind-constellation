# Downstream installation

Polymind installs its generated skills into an existing repository without
claiming ownership of that repository's instructions or runtime configuration.
The installer writes only these per-skill directories:

```text
.agents/skills/<polymind-skill>/
.claude/skills/<polymind-skill>/
.polymind/polymind-constellation.lock.json
.polymind/polymind-constellation.rollback/
```

It does not write `AGENTS.md`, `CLAUDE.md`, `.gemini/settings.json`, OpenCode
configuration, unrelated skill directories, or application files. The target
must be an existing directory. An installed release defaults to its bundled
projection. A source checkout uses only the `dist/repo/` projection anchored to
the framework module; a `dist/repo/` beneath an unrelated working directory can
never shadow either trusted default.

## Plan, inspect, approve, and apply

From the Polymind source checkout or an installed release:

```sh
# Default: non-mutating plan
polymind install /path/to/downstream

# Optional bounded unified diff
polymind install /path/to/downstream --diff

# Explicit approval signal
polymind install /path/to/downstream --apply

# Verify installed files match this release
polymind install /path/to/downstream --check
```

Use `--source /path/to/generated/repo` when deliberately testing a separately
supplied projection. Every plan identifies the resolved source path,
projection-lock SHA-256, and framework version. Installation is offline and
never executes a skill script.

## Updates and conflicts

The target lock records every managed file digest and managed skill root. An
update proceeds only when every previously installed file still matches that
lock. The installer refuses:

- a first install over an existing directory with the same skill name;
- changed, missing, or unknown files inside a managed skill directory;
- malformed locks, source projection drift, path traversal, or symlinked source
  or target paths;
- concurrent operations, unless a diagnosed lock is older than five minutes
  and the operator explicitly passes `--break-stale-lock`.

Unrelated skills alongside Polymind skills are preserved. Resolve conflicts by
reviewing ownership and either renaming/removing the unowned target package or
restoring a managed package to its recorded digest. Never delete a conflicting
directory automatically.

## Rollback

Each successful apply retains exactly one pre-apply snapshot. Roll it back with:

```sh
polymind install /path/to/downstream --rollback
```

Rollback first verifies that the current install and snapshot still match their
locks. Rolling back an update restores the previous managed version. Rolling
back a first install removes only the six Polymind-owned skill directories. A
successful rollback consumes the snapshot. Interrupted apply and rollback
operations automatically restore the state present before the command.

The rollback snapshot is operational recovery, not a provenance or authenticity
mechanism. Review the source and release metadata before installation.
