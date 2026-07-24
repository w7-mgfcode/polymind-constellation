---
name: starting-new-project
description: >
  Plans and initializes a new software project through one-question-at-a-time
  discovery, current primary-source research, explicit recommendations and
  trade-offs, selected host and assistant profiles, an approved file manifest,
  and deterministic verification. Use for a new project, repository plan,
  scaffold, codebase initialization, or stack-selection request. Do not use to
  repair an established project, create unselected provider folders, or write
  files before the user approves both the plan and exact file list.
license: Proprietary
metadata:
  polymind.version: "2.0.0"
  polymind.tags: "project-planning,repository-scaffolding,portable,governance"
  polymind.risk: "writes-after-two-approvals"
---

# Starting a New Project

Guide a new project across two explicit boundaries: first research and
recommendation, then optional scaffolding. Keep the user in control of both.

## Phase A: discover, research, and recommend

1. Load [discovery-questions.md](references/discovery-questions.md). Ask exactly
   one targeted question per turn, reflect the answer briefly, and skip every
   dimension the user already answered. Use the fast exit when enough context
   is available.
2. Identify the required host, CI, and assistant profiles from user choices and
   repository evidence. Never select a provider merely because support might be
   useful later.
3. Research volatile stack, host, CI, and assistant facts using current primary
   sources. Record each material fact using
   [volatile-facts.md](references/volatile-facts.md): claim, source URL,
   `verified_at`, and applicability. Do not present a current-version claim from
   memory.
4. Present one `[RECOMMENDED]` plan, at least one `[ALTERNATIVE]` when viable,
   the decisive `[TRADE-OFF]`, and every preference-only choice as
   `[USER DECIDES]`.
5. Include the repository tree, stack, verification command, selected profiles,
   governance depth, and initialization order. Ask for approval of the plan.
   Stop here until the user approves or revises it.

Read only the selected profile references:

- [github.md](references/profiles/github.md)
- [gitlab.md](references/profiles/gitlab.md)
- [local-only.md](references/profiles/local-only.md)
- [no-ci.md](references/profiles/no-ci.md)
- [assistant-adapters.md](references/assistant-adapters.md)

Use [repo-conventions.md](references/repo-conventions.md) only when the user
explicitly selects the legacy GitHub-first profile.

## Phase B: scaffold after approval

1. Confirm the target directory.
2. Derive the smallest file manifest from the approved stack and profiles. Show
   every create and modify path. Do not add dormant provider configuration.
3. Render selected assets into a staging preview. Resolve every
   `{{PLACEHOLDER}}`; fail the preview if any unresolved token remains.
4. Show the complete diff, validation commands, and rollback procedure. Ask:
   “Create these exact files?” Stop until the user explicitly approves.
5. Apply only the approved diff. Preserve unrelated and human-authored content.
6. Run the repository's deterministic `scripts/verify` contract, or create that
   contract as an approved scaffold item before making a local/CI parity claim.
   Run host-specific linting when the selected profile provides it.
7. Report created files, command results, remaining assumptions, and recovery
   steps. Do not publish, push, or create remote resources without separate
   authorization.

## Output contract

The recommendation must identify:

- project goal and constraints;
- selected host, CI, and assistant profiles with prerequisites;
- annotated repository tree;
- stack and current-source evidence;
- one deterministic verification command used both locally and in CI, when CI
  is selected;
- recommendation, alternative, trade-off, and user decisions;
- implementation order and explicit research-to-scaffolding boundary.

Available assets:

- [AGENTS.md.tmpl](assets/AGENTS.md.tmpl) for shared agent instructions.
- [CLAUDE.md.tmpl](assets/CLAUDE.md.tmpl) only for the selected Claude adapter.
- [github-ci.yml.tmpl](assets/github-ci.yml.tmpl) only for the GitHub host profile.
- [gitlab-ci.yml.tmpl](assets/gitlab-ci.yml.tmpl) only for the GitLab host profile.
