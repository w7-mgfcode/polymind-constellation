# Contributing

Canonical skill packages under `skills/` are the only hand-edited behavioral
source. Provider projections under `dist/repo/` are generated review artifacts.
Do not edit the original community directory or introduce a runtime dependency
on it.

## Development workflow

```sh
scripts/bootstrap
uv run polymind validate skills
scripts/sync-adapters --dry-run
scripts/sync-adapters --apply
scripts/verify
```

Preserve unrelated work. Add tests for every validator, projection, installer,
or permission-mapping rule. Provider facts require a primary source, an evidence
date, a bounded evidence scope, and a matching entry in
`adapters/providers.toml`.

For a new skill, follow the complete [authoring walkthrough](docs/authoring-skills.md#add-a-fourth-skill).
For framework or schema changes, follow the
[versioning and release policy](docs/versioning.md). For downstream behavior,
test the [installation contract](docs/installing.md) in a disposable repository.
Only a version-tagged workflow may publish distributions; see the
[release automation and provenance contract](docs/release-automation.md).

## License

The repository is licensed under the [Apache License 2.0](LICENSE). By
submitting a contribution, you represent that you have the right to provide it
under that license.

## Pull-request evidence

- Explain the canonical behavior change and its semantic-version impact.
- Include dry-run output or summarize the exact generated changes.
- State whether any capability, approval gate, script, provider overlay, or
  compatibility claim changed.
- Run `scripts/verify` and report intentional skips separately from passes.
- Never describe static validation as native discovery or behavioral testing.
