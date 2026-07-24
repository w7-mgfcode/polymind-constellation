# Architecture

Polymind uses a neutral canonical source plus deterministic provider
projections. Only `skills/` is hand-edited. The compiler stages copied runtime
trees, applies allowlisted provider overlays, validates them independently, and
records drift hashes.

Each canonical package contains `SKILL.md` and `skill.toml`. `SKILL.md` follows
the interoperable Agent Skills contract. The sidecar records Polymind package
schema, provenance, capabilities, approval policy, scripts, dependencies, and
trigger cases. A package must be self-contained.

Capabilities are descriptive and never grant permission. The vocabulary is
closed and expands compound declarations into atomic actions. Future overlays
may disable or require approval for declared actions, but cannot add actions.

The validator reports three independent diagnostic categories:

- `spec` for Agent Skills contract violations;
- `polymind-policy` for repository quality and packaging requirements;
- `security` for escapes, unsafe paths, or capability-boundary failures.

The current environment cannot write its protected root `.agents/` placeholder,
so the repository projection lives under `dist/repo/`. It is a complete staged
repository containing shared instructions, Codex/Gemini/OpenCode skills,
Claude skills, Gemini context settings, a data-only catalog, compatibility
evidence, and a drift lock. `polymind sync` defaults to dry-run and requires
`--apply` for writes.

Phase 6 adds a discovery-only local bridge. `polymind catalog` returns compact
metadata, `polymind activate` returns exactly one `SKILL.md` and its resource
manifest, and `polymind resource` reads one bounded manifested resource. These
operations never execute scripts or grant permissions. The generic host mapping
defaults known actions to `ask` or `deny` and denies unknown actions. An
executable local runtime remains outside the implemented architecture.

Phase 8 adds a distribution boundary. Release wheels bundle the synchronized
projection as package data. `polymind install` copies only the named skill
directories into a downstream repository; it never installs this framework's
repository instructions or provider settings. A separate target lock proves
managed-file continuity, preserves unrelated skills, and retains one pre-apply
rollback snapshot. See [downstream installation](installing.md) and the
[security model](security.md).
