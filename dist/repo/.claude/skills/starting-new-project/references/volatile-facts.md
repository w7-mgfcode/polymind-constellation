# Volatile fact ledger

Use this schema for facts that can change between tool releases:

| claim | source_url | verified_at | applicability |
|---|---|---|---|
| concise factual statement | primary-source URL | YYYY-MM-DD | selected profile and version range |

Re-verify a row when it affects generated files and either the source changed or
the verification date is outside the project's accepted freshness window.

## Baseline snapshot

| claim | source_url | verified_at | applicability |
|---|---|---|---|
| GitHub Actions workflow files use `.github/workflows/*.yml` or `*.yaml`. | https://docs.github.com/actions/writing-workflows/workflow-syntax-for-github-actions | 2026-07-22 | GitHub host with Actions selected |
| GitLab pipelines are defined by `.gitlab-ci.yml` and can be checked with CI Lint. | https://docs.gitlab.com/ci/yaml/ | 2026-07-22 | GitLab host with CI selected |
| Claude Code project skills are discovered from `.claude/skills/`. | https://code.claude.com/docs/en/slash-commands | 2026-07-22 | Claude Code adapter selected |
| Gemini CLI discovers workspace skills from `.gemini/skills/` or `.agents/skills/`. | https://geminicli.com/docs/cli/using-agent-skills/ | 2026-07-22 | Gemini CLI adapter selected |
| Agent Skills packages use `SKILL.md` plus optional `scripts/`, `references/`, and `assets/`. | https://agentskills.io/specification | 2026-07-22 | Any Agent Skills adapter |

These rows are research inputs, not timeless guarantees. Record newly selected
framework versions and platform constraints in the same form.
