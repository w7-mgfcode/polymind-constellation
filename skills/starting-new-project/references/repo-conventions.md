# Repository Conventions for AI-Agent Projects

Distilled from current official documentation for Claude Code, OpenAI Codex, and Gemini CLI
(research snapshot: early 2026). Use this during Phase 2 to inform recommendations.

---

## The Three-Layer Model

The most maintainable multi-agent repository structure has exactly three canonical layers:

| Layer | Canonical file(s) | Audience | Contains |
|-------|------------------|----------|----------|
| Human orientation | `README.md`, `CONTRIBUTING.md`, `SECURITY.md` | Humans first | Purpose, quickstart, contributor guide |
| Shared AI rules | `AGENTS.md` | All coding agents | Setup, verify commands, constraints, "done" definition |
| Durable reference | `docs/` | Humans + agents (deep) | Architecture, testing, security, governance |

**Enforcement** lives in a fourth layer: `.github/` (CI, rulesets, CODEOWNERS, templates).

The critical rule: each file has one primary audience and one job. Drift begins when
README starts duplicating AGENTS.md, or when tool-specific folders start holding policy.

---

## File-by-File Conventions

### README.md
- Human-first entry point. GitHub surfaces it as the repository front door.
- Should answer: what it is, why useful, quickstart, where deeper docs live.
- **Does not belong here:** agent-only rules, tool-specific prompts, full PR checklist,
  architecture detail.

### AGENTS.md
- Canonical cross-agent instruction file.
- Codex reads it natively before every task.
- Gemini CLI can be configured to read it via `context.fileName` in `.gemini/settings.json`.
- Claude Code imports it via `@AGENTS.md` at the top of `CLAUDE.md`.
- **Right content level:** short and operational. Answer what an agent needs on almost every
  task: setup commands, verify commands, high-risk paths, what "done" means, where docs live.
- **Does not belong here:** full architecture docs, copy of README, tool-specific runtime
  config, wall of style preferences.
- For larger repos, nested `AGENTS.md` files at package/module level add scoped rules.

### CLAUDE.md
- Claude Code reads this natively as its project memory surface.
- In a multi-agent repo, this should be a **thin shim**, not a second rulebook.
- Recommended content:
  ```markdown
  @AGENTS.md

  <!-- Claude-specific additions only below this line -->
  ## Claude-specific notes
  [Anything that is genuinely Claude-only: specific slash commands, skill references,
   trust settings, hook behavior. Omit this section entirely if there is nothing to add.]
  ```
- **Anti-pattern:** maintaining a full copy of repo rules here. Maintenance cost doubles
  immediately.
- A symlink `CLAUDE.md -> AGENTS.md` works when there are no Claude-only additions, but
  a plain text shim is safer cross-platform.

### GEMINI.md (optional)
- Gemini CLI defaults to `GEMINI.md` but can be configured to read `AGENTS.md` first.
- If the team uses Gemini IDE surfaces (VS Code, IntelliJ), keep a root `GEMINI.md`
  as a thin adapter.
- If CLI-only, configure `.gemini/settings.json` with `context.fileName: ["AGENTS.md",
  "GEMINI.md"]` and skip the root file.

---

## Tool-Specific Folders

Each tool folder holds **runtime and safety configuration only** — never shared policy.

### .claude/
- `settings.json` — project-wide Claude settings (trust, hooks, permissions)
- `settings.local.json` — machine-local (Claude auto-gitignores this)
- `rules/` — path-scoped and topic-scoped rules (Claude Code feature)
- `skills/` — project-specific Claude Code skills
- `agents/` — project-specific Claude subagents
- `commands/` — legacy slash commands (prefer skills/ for new work)
- **Commit:** `settings.json`, `rules/`, `skills/`, `agents/`
- **Do not commit:** `settings.local.json`, secrets, user auth tokens

### .codex/
- `config.toml` — Codex sandbox, approval, and persistent behavior settings
- `hooks.json` — Codex lifecycle hooks (pre/post task)
- `agents/` — custom spawned Codex agents
- `rules/` — command-approval rules
- **Important:** `.codex/skills/` is NOT the right location for repo skills. Use
  `.agents/skills/` instead (Codex's official cross-tool skill location).
- Project-local `.codex/` only loads in trusted projects.

### .gemini/
- `settings.json` — project settings, context filename override, sandbox config
- `commands/` — Gemini-specific prompt shortcuts
- `skills/` — Gemini workspace skills (or use `.agents/skills/` for cross-tool)
- `sandbox.Dockerfile` — project-specific sandbox customization
- `.geminiignore` — file exclusion patterns

### .agents/ (cross-tool)
- `skills/` — **preferred location for skills reusable across Claude, Codex, and Gemini**
- Codex officially documents `.agents/skills/` as the repo-skill location.
- Gemini supports `.agents/skills/` as an alias.

---

## GitHub Governance Layer

`.github/` is the **enforcement layer** — where prose rules become deterministic gates.

| Path | Purpose |
|------|---------|
| `workflows/ci.yml` | Required checks on every PR |
| `PULL_REQUEST_TEMPLATE.md` | PR description checklist |
| `ISSUE_TEMPLATE/` | Bug report and feature request forms |
| `CODEOWNERS` | Human review requirements by path |
| `dependabot.yml` | Automated dependency update config |

**Critical rule:** The verify command in `AGENTS.md` must be identical to what CI runs.
If they diverge, CI is the truth and `AGENTS.md` is stale.

---

## Anti-Patterns

| Anti-pattern | Why it causes problems |
|-------------|----------------------|
| Full repo rules duplicated in both `AGENTS.md` and `CLAUDE.md` | Drift guaranteed; maintenance cost doubles |
| `.codex/skills/` as canonical skill location | Wrong per official Codex docs; use `.agents/skills/` |
| `README.md` containing agent-only behavior rules | Mixes human and agent audiences |
| AGENTS.md verify commands that differ from CI commands | Agents pass local checks but CI fails |
| Deep nesting of tool config files | Every extra file increases contradiction risk |
| Tool folders holding long-form policy | Policy belongs in `AGENTS.md` and `docs/` |
| Creating `.claude/`, `.codex/`, `.gemini/` "just in case" | Add only for tools the team actually uses |

---

## Recommended Baseline Directory Tree

For a new small-to-medium repository using Claude + Codex + GitHub:

```text
.
├── README.md                         # Human entry point
├── AGENTS.md                         # Canonical shared AI rules
├── CLAUDE.md                         # Thin Claude shim (@AGENTS.md import)
├── GEMINI.md                         # Optional: only if Gemini IDE surfaces in use
├── CONTRIBUTING.md                   # Contributor guide
├── SECURITY.md                       # Vulnerability reporting policy
├── .claude/
│   ├── settings.json
│   ├── rules/                        # Optional: path-scoped rules
│   └── skills/                       # Optional: Claude-specific skills
├── .codex/
│   ├── config.toml
│   └── rules/                        # Optional: Codex approval rules
├── .gemini/
│   └── settings.json                 # Includes context.fileName pointing to AGENTS.md
├── .agents/
│   └── skills/                       # Cross-tool reusable workflow skills
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   └── feature_request.yml
│   ├── workflows/
│   │   └── ci.yml
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── CODEOWNERS
├── docs/
│   ├── architecture.md
│   ├── development.md
│   ├── testing.md
│   └── ai-agent-governance.md        # Documents the source-of-truth strategy
├── scripts/
│   ├── bootstrap-dev                 # One-command local setup
│   └── verify-local                  # Matches what CI runs
├── tests/
└── src/
```

**Omit aggressively:** only add tool folders for tools the team actually uses. Only add
`docs/` files for content that exists. Start with the minimum and grow.

---

## Source-of-Truth Conflict Rule

When instructions in different files contradict each other, priority order is:

1. **Automation** — CI, tests, linters, GitHub rulesets (automation always wins)
2. **Governance docs** — `docs/ai-agent-governance.md`, `docs/security.md`
3. **AGENTS.md** — shared AI operating rules
4. **Tool shims** — `CLAUDE.md`, `GEMINI.md` (must never contradict upstream)

If `AGENTS.md` says "run `npm test`" but CI runs `pnpm test && pnpm lint`, CI is correct
and `AGENTS.md` needs updating.
