# Provider shim profiles

Select a profile only when the user requests that provider or repository
evidence shows it is used. Re-verify volatile behavior against official docs
before changing a profile. Evidence below was verified on 2026-07-22.

## Claude Code profile

### Prerequisites

- Claude Code is an intended repository client.
- A root or appropriately scoped `AGENTS.md` exists or is part of the approved
  proposal.

### Behavior

Create a thin `CLAUDE.md` whose first instruction is `@AGENTS.md`. Add only
Claude-specific runtime notes below it. Claude Code discovers project skills in
`.claude/skills/`; permission and hook settings belong in Claude configuration,
not in shared repository policy.

Do not use a symlink as the portable default. Do not copy shared policy into the
shim. Claude imports may chain up to five hops according to the current project
memory documentation.

### Validation

- Confirm `CLAUDE.md` contains the exact `@AGENTS.md` import.
- Confirm normalized policy blocks are not repeated.
- Run the validator with `--strict`.

Source: <https://code.claude.com/docs/en/memory>

## Gemini CLI profile

### Prerequisites

- Gemini CLI is an intended repository client.
- The user chooses either configured shared context or a thin `GEMINI.md`
  pointer.

### Behavior

Prefer `.gemini/settings.json` with `context.fileName` containing `AGENTS.md`.
When a `GEMINI.md` compatibility pointer is needed, keep it short and do not
assume another provider's import syntax works. Gemini CLI currently discovers
workspace skills from `.gemini/skills/` and the `.agents/skills/` alias.

### Validation

- Confirm `.gemini/settings.json` is valid JSON and `context.fileName` includes
  `AGENTS.md`, or confirm `GEMINI.md` points to `AGENTS.md`.
- Confirm normalized policy blocks are not repeated.
- Run the validator with `--strict`.

Source: <https://geminicli.com/docs/cli/using-agent-skills/>

## Generic pointer profile

### Prerequisites

- A selected client has no documented import mechanism but accepts a repository
  instruction file.

### Behavior

Create the smallest supported provider file containing a prose pointer to
`AGENTS.md` and provider-only runtime notes. If the client cannot follow the
pointer, configure it to load `AGENTS.md`; do not duplicate policy as a fallback.

### Validation

- Confirm the provider's documented context mechanism loads the canonical file.
- Run an actual discovery check when the client is available.
- Record the provider version and test date.

## Network-link profile

### Prerequisites

- Network access is available and explicitly approved.
- Remote documentation links are in scope.

### Behavior

Run `validate.py --check-remote` with a bounded timeout. Treat authentication
failures and rate limits as warnings unless the link is release-critical.

### Validation

- No remote request may mutate state or send repository credentials.
- Re-run the normal offline check so network availability is not required for
  the baseline validation gate.
