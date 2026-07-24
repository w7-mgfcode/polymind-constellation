---
name: maintaining-agent-docs
description: >
  Creates, audits, and safely updates canonical repository instructions, thin
  provider shims, human-facing README content, and optional llms.txt indexes.
  Uses repository evidence, managed regions, deterministic validation, a shown
  diff, and explicit approval before writes. Use for AGENTS.md maintenance,
  agent-ready repository setup, instruction drift, nested instruction scopes,
  or provider shim alignment. Do not overwrite human-authored content, duplicate
  shared policy into provider files, or create llms.txt without a docs site.
license: Apache-2.0
metadata:
  polymind.version: "2.0.0"
  polymind.tags: "agent-docs,repository-instructions,governance,portable"
  polymind.risk: "writes-after-approval"
---

# Maintaining Agent Docs

Keep repository guidance accurate without turning provider entrypoints into
competing rulebooks. Treat `AGENTS.md` as the shared operating contract,
provider files as selected adapters, `README.md` as human orientation, and
`llms.txt` as an optional docs-site index.

## Procedure

1. Scan the repository before proposing content. Find root and nested
   instruction files, manifests, lockfiles, build definitions, CI configuration,
   and durable docs. Record dirty target files and preserve nearest-scope rules.
2. Extract commands and constraints from repository evidence. Cite each claimed
   command or convention by file and line. Mark an unknown as `TODO: verify` in
   the proposal; never invent an executable command.
3. Select only the provider profiles the user or repository requires. Load
   [provider-shims.md](references/provider-shims.md) for current prerequisites,
   behavior, and tests. Keep provider facts out of shared policy.
4. Propose changes inside uniquely named managed regions:

   ```markdown
   <!-- BEGIN maintaining-agent-docs:root -->
   ...generated content...
   <!-- END maintaining-agent-docs:root -->
   ```

   Never nest regions, reuse an identifier in one file, or rewrite text outside
   a region. For unmanaged files, propose an insertion point instead of a full
   replacement.
5. Run the package validator in read-only mode:

   ```sh
   python skills/maintaining-agent-docs/scripts/validate.py --check --strict .
   # Equivalent framework entrypoint:
   polymind validate-agent-docs --check --strict .
   ```

   Add `--diff` to preview duplicate-block removals. Use `--check-remote` only
   after network access is selected and approved.
6. Show a unified diff and rollback method for every proposed mutation. Get
   explicit approval for the exact file list and diff.
7. Back up or otherwise make existing targets recoverable, apply only the
   approved changes, rerun the validator, and report evidence.

## Validation contract

The validator is non-mutating. It checks real YAML frontmatter, marker ordering,
nesting and uniqueness, normalized policy duplication with a configurable
threshold, local-link containment, optional remote links, redacted secret
findings with explicit allowlists, provider import rules, nested scopes, and
basic instruction completeness.

- `--check` performs the default read-only check.
- `--diff` shows advisory diffs without writing.
- `--strict` turns warnings into a failing exit code.
- `--secret-allowlist FILE` accepts SHA-256 digests of known fixture values,
  one digest per line. Never place raw secrets in an allowlist.

## Hard guardrails

- Preserve human-authored content and nested instruction scopes.
- Keep shared policy in one canonical file; adapters may add runtime-only facts.
- Reject local links that are absolute, traverse above the repository, or
  resolve outside it through a symlink.
- Redact possible secrets in every diagnostic.
- Generate `llms.txt` only for a published documentation site.
- Separate checking from writing. Never interpret validator success as approval.

Load detailed references only when their file type is in scope:

- [agents-md.md](references/agents-md.md) for canonical and nested instructions.
- [provider-shims.md](references/provider-shims.md) for selected provider adapters.
- [readme.md](references/readme.md) for human-facing documentation.
- [llms-txt.md](references/llms-txt.md) for an approved docs-site index.
