# Repository instructions

## Source of truth

- Hand-edit canonical packages only under `skills/`.
- Keep each package self-contained; references, assets, and scripts must remain
  inside its directory unless a future dependency model explicitly installs
  the complete closure.
- Treat `dist/repo/.agents/skills/` and `dist/repo/.claude/skills/` as generated,
  read-only artifacts. The current root provider placeholders are protected.
- Keep provider-specific permissions out of canonical `SKILL.md` files.

## Development

- Bootstrap with `scripts/bootstrap`.
- Validate packages with `uv run polymind validate skills`.
- Run the complete applicable gate with `scripts/verify`.
- Preview projections with `scripts/sync-adapters --dry-run`, generate with
  `scripts/sync-adapters --apply`, and check drift with
  `scripts/sync-adapters --check`.
- Keep shell wrappers thin; implementation belongs in `src/polymind/`.
- Add tests for every validator rule and use stable diagnostic codes.

## Safety and scope

- Preserve unrelated files and avoid destructive Git operations.
- Never embed source-machine absolute paths or credentials in committed files.
- Unknown capabilities and package escapes fail closed.
- Never overwrite non-generated projection content; conflicts and unknown files
  must fail closed.
