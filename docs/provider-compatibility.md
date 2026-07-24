# Provider compatibility

The Phase 4 compiler emits `.agents/skills/` for Codex, Gemini CLI, and
OpenCode, plus `.claude/skills/` with narrowly mapped Claude `allowed-tools`
overlays. Gemini loads `AGENTS.md` through the generated
`context.fileName` setting. Claude loads the same rules through `CLAUDE.md`.

Compatibility evidence and dated documentation sources are generated from
`adapters/providers.toml`. `static-only`, `tested`, and `unsupported` are kept
distinct. A provider is not promoted to `tested` until its installed CLI lists
or invokes the projected skills in a disposable repository.

## Compatibility baseline

Verified 2026-07-22 with a 90-day freshness window. `tested` below means the
exact evidence scope in the final column passed; it does not imply full
behavioral or tool-safety parity.

| Provider | Baseline | Projection | Support state | Evidence scope |
|---|---:|---|---|---|
| codex | `0.145.0` | `.agents/skills` | `tested` | native discovery of all exact names and descriptions |
| claude-code | `2.1.217` | `.claude/skills` | statically compatible (`static-only`) | projection validation; no external model prompt |
| gemini-cli | `0.51.0` | `.agents/skills` | `tested` | native discovery of all exact names and descriptions |
| opencode | not installed | `.agents/skills` | statically compatible (`static-only`) | projection and local-provider configuration validation |
| ollama-raw-server | API observed; version unavailable | none | `unsupported` | raw server has no Agent Skills discovery or host permission layer |

Support-state meanings:

- `tested`: a named installed client passed the recorded live evidence scope;
- `static-only`: the emitted shape and configuration validate, but the named
  client did not pass a live probe in this environment;
- `unsupported`: no client compatibility claim is made. A separate harness may
  consume the catalog, but the named surface cannot discover or safely execute
  skills by itself.

The repository has no runtime dependency on the vendor source directory. All
skill instructions, references, assets, scripts, metadata, provider adapters,
and runtime projections are local and self-contained.

Phase 6 adds a credential-free OpenCode local-provider example and a
provider-SDK-free discovery harness. OpenCode's current documentation confirms
native `.agents/skills/` discovery, OpenAI-compatible local providers, and
`allow`/`ask`/`deny` permission rules. OpenCode is not installed in this
environment, so it remains `static-only` and no live OpenCode pass is claimed.

Phase 7 native discovery passed for Codex CLI `0.145.0` and Gemini CLI `0.51.0`
in a disposable generated repository. Claude Code `2.1.217` remains
`static-only`: it has no data-only discovery command, and this run did not send
private workspace-derived prompts to an external model. Local Ollama model
results are quality measurements of the generic data-only harness, not provider
support promotions. See the [local harness contract](local-harness-contract.md)
and [Phase 7 conformance record](phase7-conformance.md).

Current primary sources, re-verified 2026-07-22:

- [Agent Skills specification](https://agentskills.io/specification)
- [Codex skills documentation](https://developers.openai.com/codex/skills)
- [Claude Code skills](https://code.claude.com/docs/en/slash-commands)
- [Gemini CLI Agent Skills](https://geminicli.com/docs/cli/using-agent-skills/)
- [OpenCode Agent Skills](https://opencode.ai/docs/skills)
- [Ollama Chat API](https://docs.ollama.com/api/chat)

Re-run the relevant static and live checks when an adapter changes, an installed
client version differs from the baseline, an official discovery/permission fact
changes, or the evidence is older than 90 days.
