# Assistant adapter profiles

Select only adapters named by the user or proven necessary by repository
requirements. Shared policy belongs in `AGENTS.md`; provider files add discovery
or runtime configuration only.

## Shared Agent Skills profile

### Prerequisites

- At least one selected client discovers the open Agent Skills format.

### Behavior

Place canonical project guidance in `AGENTS.md`. Add `.agents/skills/` only when
the project will author or install actual skills. Do not create an empty skills
tree.

### Validation

- Validate each selected `SKILL.md` against the Agent Skills specification.
- Run the client's live skill-list command when available.

## Claude Code profile

### Prerequisites

- Claude Code is explicitly selected.

### Behavior

Create a thin `CLAUDE.md` import and `.claude/` runtime or skill paths only when
their contents are part of the approved manifest. Never copy shared policy.

### Validation

- Confirm the import resolves and live skill discovery succeeds.
- Confirm provider permissions do not broaden project capability policy.

## Gemini CLI profile

### Prerequisites

- Gemini CLI is explicitly selected.

### Behavior

Configure shared context through `.gemini/settings.json` when needed. Prefer the
interoperable `.agents/skills/` workspace alias unless a Gemini-only package is
required.

### Validation

- Parse settings as JSON and run `/skills list` or the current non-interactive
  equivalent.
- Confirm only selected skills appear.

## Generic or local harness profile

### Prerequisites

- The harness contract defines instruction loading, skill activation, tools,
  sandboxing, permission prompts, and timeouts.

### Behavior

Generate only the files its documented loader consumes. A raw model endpoint is
not an agent harness and must not be claimed to discover repository skills.

### Validation

- Test catalog discovery and activation separately.
- Attempt a denied tool action and a timeout before claiming safe execution.
