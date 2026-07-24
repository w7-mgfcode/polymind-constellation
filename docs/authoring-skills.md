# Authoring canonical skills

Create a kebab-case directory under `skills/` containing `SKILL.md` and
`skill.toml`. The directory must have the same name as the frontmatter `name`.

Keep `SKILL.md` concise. Put detailed material in package-local `references/`,
reusable output files in `assets/`, and deterministic utilities in `scripts/`.
Every relative link must resolve inside the package. Document each declared
script's runtime, dependencies, inputs, outputs, side effects, and dry-run
behavior in `skill.toml`.

Use only interoperable frontmatter fields. Polymind-specific version, tags, and
risk values belong under the string-valued `metadata` map:

```yaml
metadata:
  polymind.version: "1.0.0"
  polymind.tags: "validation,agent-skills"
  polymind.risk: "read-only"
```

Do not put provider permission fields such as `allowed-tools` in a canonical
package. Declare closed Polymind capabilities and intentional template variables
in `skill.toml`, then validate and project:

```sh
uv run polymind validate skills
scripts/verify
scripts/sync-adapters --dry-run
```

## Add a fourth skill

The tested minimal example is
[`tests/fixtures/contributor/fourth-skill`](../tests/fixtures/contributor/fourth-skill).
Use it as a shape reference, not as production content.

1. Create `skills/<name>/SKILL.md` and `skill.toml`. Use a unique kebab-case
   directory and matching frontmatter `name`.
2. Put behavior version, discovery tags, and risk under `metadata` as shown
   above. Write a specific description that states both what the skill does and
   when it applies.
3. Record provenance, license, closed capabilities, approval policy, positive
   triggers, and negative triggers in `skill.toml`.
4. Keep every resource inside the package. Declare every executable script,
   including runtime, dependencies, inputs, outputs, side effects, and whether
   it supports dry-run.
5. Add the skill to `conformance/matrix.toml` with one explicit invocation, two
   positive paraphrases, at least one unrelated negative, an approval-bypass
   case, and two real package resources. Read-only skills still need a case that
   proves the model does not invent a mutation authorization.
6. Add `adapters/claude/overlays/<name>.toml` only when Claude needs a narrower
   `allowed-tools` mapping. A provider-neutral read-only skill needs no overlay.
7. Run the complete sequence:

   ```sh
   uv run polymind validate skills
   scripts/sync-adapters --dry-run
   scripts/sync-adapters --apply
   scripts/sync-adapters --check
   uv run polymind conformance --format markdown
   scripts/verify
   ```

The dry-run must show only the expected new package, catalog, compatibility, and
lock changes. Generated files under `dist/repo/` are review artifacts and must
not be hand-edited.

The [Agent Skills specification](https://agentskills.io/specification) is the
portable baseline. It defines `name` and `description` as required, supports
string-valued `metadata`, recommends progressive disclosure, and treats
`allowed-tools` as experimental. Polymind therefore keeps provider permission
syntax in overlays.
