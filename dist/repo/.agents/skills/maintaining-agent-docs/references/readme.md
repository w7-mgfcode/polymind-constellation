# Reference: README.md

For **humans** (and the rendered repo landing page). Not the agent source of truth — keep agent rules in
AGENTS.md and link to it.

## Recommended structure (top to bottom)
- **Title + one-liner** — what it is in a sentence.
- **Quickstart** — the fastest path to running it (near the top).
- **Install** — prerequisites + install commands (from real manifests; cite source).
- **Usage / examples** — concrete commands or snippets.
- **Project layout** — short map; link to deeper docs.
- **Contributing** — how to develop + the verify command (link AGENTS.md, don't restate it).
- **License** — and a status line (alpha/beta/stable) if relevant.
- Optional: badges.

## Authoring rules for this skill
- Repo-verified facts only; cite commands `file:line`. No invented quickstart.
- Do **not** copy AGENTS.md policy here — link to it (`See [AGENTS.md](AGENTS.md) for agent rules.`).
- Wrap any generated section in the `<!-- BEGIN/END maintaining-agent-docs -->` markers so human edits to
  the rest of the README survive regeneration.
- If a README already exists, **augment** (insert/refresh marked sections) rather than rewrite the file.
