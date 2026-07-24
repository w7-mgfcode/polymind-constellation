# Phase 5 portability record

Phase 5 refactors the three owner-authored workflows without modifying the
vendor source. Canonical packages remain under `skills/`; generated provider
trees remain read-only projections.

## Package changes

| Skill | Portable core | Selectable profiles | Deterministic gate |
|---|---|---|---|
| `maintaining-agent-docs` | Evidence, canonical policy, managed regions, diff and approval | Claude Code, Gemini CLI, generic pointer, network links | `validate.py --check --strict` and `polymind validate-agent-docs` |
| `starting-new-project` | One-question discovery, research, recommendation, two approvals, scaffold preview | GitHub, GitLab, local-only, no-CI, selected assistant adapters | Approved `scripts/verify` used locally and by selected CI |
| `analyzing-workflow-patterns` | Extraction, repository capability scan, 3-5 flows, normalized scoring, hard stop | Hungarian, GitHub Issues, legacy five-flow | All-higher-is-better weighted matrix plus approval checkpoint |

All profiles state prerequisites, behavior, and validation. A profile may add a
provider-specific constraint but cannot remove the core approval, rollback,
validation, or capability boundary.

## Safety changes

The agent-docs validator is read-only and supports `--check`, `--diff`, and
`--strict`. It parses YAML with `safe_load`; checks managed marker order,
nesting, and uniqueness; compares normalized semantic blocks at a configurable
threshold; rejects absolute, traversal, and symlink-escaping local links; and
reports secret matches only as redacted SHA-256 allowlist candidates. Network
link checks are opt-in and bounded by a timeout.

Project scaffolding now requires approval of the recommendation and a second
approval of the exact paths and diff. Unresolved template variables fail the
canonical package validator. Local/CI parity may be claimed only when both call
the same deterministic `scripts/verify` entrypoint.

## Research snapshot

Provider and host facts were rechecked against official sources on 2026-07-22.
The project-start skill records claim, source URL, `verified_at`, and
applicability in its volatile-fact ledger. Re-validation is required before a
profile changes generated paths or compatibility claims.

## Boundary

This work stops at the Phase 5 exit gate. Phase 6 distribution, generic
local-LLM execution harnesses, marketplaces, remote registries, and advanced
runtime features remain deferred.
