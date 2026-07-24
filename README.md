# Polymind Constellation

Polymind is a provider-neutral workbench for authoring Agent Skills once under
`skills/`. It contains three migrated workflow skills, offline validation,
closed capability declarations, and deterministic provider projections.

Phase 5 adds portable core workflows with selectable language, host, tracker,
assistant, and legacy profiles. Provider assumptions are no longer defaults;
each selected profile declares prerequisites and validation. The bundled
agent-docs validator enforces safe links, managed regions, redacted secret
findings, semantic duplication thresholds, and real YAML parsing.

Phase 6 adds a provider-SDK-free, data-only bridge for local harnesses. Catalog,
activation, and bounded single-resource reads execute no package code and grant
no permissions. A fail-closed OpenCode example targets a loopback LM Studio
endpoint without credentials.

Phase 7 adds a versioned conformance matrix, disposable projection and native
client fixtures, and opt-in structured-output evaluation through Ollama. Static
conformance runs in the default verification gate; provider and model probes
remain explicit because their runtimes and trust boundaries are environment
dependent.

Phase 8 packages the synchronized projection, hardened in framework release `0.8.1`,
adds a conflict-safe downstream installer, and publishes explicit compatibility,
security, migration, contribution, changelog, versioning, and signed-release
contracts. Native provider plugins and marketplaces remain deferred.

The current checkout has protected root `.agents/` and `.codex/` placeholders,
so generated runtime trees are materialized as a self-contained staged repository
under `dist/repo/`. Canonical packages remain the only hand-edited skill source.

## Setup and verification

```sh
scripts/bootstrap
scripts/verify
```

Validate canonical packages directly:

```sh
uv run polymind validate skills
uv run polymind validate skills --format json
scripts/sync-adapters --dry-run
scripts/sync-adapters --apply
scripts/sync-adapters --check
uv run polymind validate-agent-docs --check --strict .
uv run polymind catalog --format json
uv run polymind activate analyzing-workflow-patterns --format markdown
uv run polymind resource analyzing-workflow-patterns references/scoring.md --format json
uv run polymind conformance --format markdown
# Opt-in installed-client and local-model evidence:
uv run polymind conformance --probe-installed \
  --ollama-model gemma4-agent:latest --ollama-model qwen3:8b --format markdown
uv run polymind install /path/to/downstream --diff
uv run polymind install /path/to/downstream --apply
uv run polymind install /path/to/downstream --check
# One-generation recovery:
uv run polymind install /path/to/downstream --rollback
```

See [architecture](docs/architecture.md),
[skill authoring](docs/authoring-skills.md), and
[provider compatibility](docs/provider-compatibility.md), plus the
[Phase 5 portability record](docs/phase5-portability.md) and
[local harness contract](docs/local-harness-contract.md), and the
[Phase 7 conformance record](docs/phase7-conformance.md). Release and
contribution guidance lives in [CONTRIBUTING.md](CONTRIBUTING.md),
[downstream installation](docs/installing.md), the [security model](docs/security.md),
[Claude-first migration](docs/migrating-from-claude.md), and the
[versioning policy](docs/versioning.md). The exact artifact and acceptance
evidence is recorded in the [Phase 8 release record](docs/phase8-release.md).
The selected development priorities, automated release contract, and deferred
registry design are documented in [development directions](docs/development-directions.md),
[release automation](docs/release-automation.md), and the
[Phase 9 registry plan](docs/phase9-registry.md).

## License

Polymind Constellation is licensed under the
[Apache License 2.0](LICENSE).
