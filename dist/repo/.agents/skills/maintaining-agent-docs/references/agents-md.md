# Reference: AGENTS.md

**Canonical** agent operating rules. A **convention, not a formal spec** (agents.md) — use any headings;
do not validate against a rigid schema. Read by 20+ tools (Codex, Cursor, Copilot, Gemini CLI, Aider,
Jules, Zed…). Nested `AGENTS.md` files are supported; agents read the **nearest** file (closest wins).

## Recommended sections (checklist, not schema)

- **Purpose** — one or two lines: what the project is.
- **Setup** — install/bootstrap commands (from real manifests).
- **Build / run** — how to run the app/server/CLI.
- **Test & verification** — the explicit **definition of done** (the verify command).
- **Code style / conventions** — language, formatter/linter, naming.
- **Project structure** — the directory map and what lives where.
- **Commit / PR conventions** — message style, branch rules.
- **Safety / security boundaries** — do/don't; secrets handling; network rules.
- **High-risk paths** — files where a careless change propagates.

Keep it operational and scannable; put long-form prose in `docs/` and link to it.

## Authoring rules for this skill

- Every command/path must come from a real repo source and be cited `file:line`. No invented commands.
- This file is the **single source of truth** — policy text appears here and nowhere else.
- Wrap generated content in `<!-- BEGIN maintaining-agent-docs (generated) -->` / `<!-- END … -->`.
- Discover and preserve nested `**/AGENTS.md`; never collapse directory-scoped rules into the root.

## Completeness signals the validator looks for
Headings (case-insensitive) covering: setup/install, build/run, test/verify, structure/layout, and
safety/conventions. Missing ones are reported as advisory gaps.
