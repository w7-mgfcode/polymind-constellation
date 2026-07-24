# Local harness contract

Polymind's Phase 6 reference harness is a discovery and context-loading bridge,
not an executable agent runtime. It imports no model-provider SDK and exposes no
tool or script execution operation.

## Session protocol

1. Run `polymind catalog --format json|xml|markdown` at session start. Catalog
   output contains compact metadata only; it does not load skill bodies.
2. Choose one skill from its name and description.
3. Run `polymind activate <name> --format json|markdown`. Activation returns the
   selected `SKILL.md`, package digest, capabilities, fail-closed permission
   requirements, base directory, and resource manifest. It grants no permission
   and executes nothing.
4. Read at most one declared resource with
   `polymind resource <name> <path> --format json`. Resource output is bounded to
   256 KiB by default and 1 MiB absolutely. Request another resource only when
   the current task needs it.
5. Treat instructions as context. A separate, approved host tool must perform
   any filesystem, shell, network, browser, or secret operation.

The provider-SDK-free example in
[`examples/local_harness.py`](../examples/local_harness.py) implements only
these three data operations.

## Data-operation safety

- Validate the complete canonical skill set before cataloging or activation.
- Resolve packages against the canonical skills root and reject invalid names.
- Reject every symlink during activation, including a symlink that currently
  resolves inside the package, so later retargeting cannot change the boundary.
- Reject absolute resource paths, `..`, non-normalized paths, backslashes, and
  resources absent from the activation manifest.
- Hash every resource and verify its digest again when reading it.
- Return `SKILL.md` only during activation and one other resource per request.
- Bound resource output and encode binary data as base64 in JSON.
- Never import or execute a declared script during catalog, activation, or
  resource reads.

## Capability-to-permission mapping

Mappings are recommendations for the host approval layer, not grants.

| Canonical action | Default | Generic host permissions | Reason |
|---|---|---|---|
| `filesystem.read` | ask | read, glob, grep | Constrain reads to validated roots |
| `filesystem.write` | ask | edit | Require approved diff and writable roots |
| `shell.readonly` | ask | shell | Shell syntax is not reliably read-only |
| `shell.execute` | ask | shell | Requires full execution sandbox and limits |
| `network.read` | ask | web fetch/search | Restrict destinations and credentials |
| `network.write` | deny | none | No portable mutation boundary |
| `browser.read`, `browser.write` | deny | none | No portable browser sandbox |
| `secret.access` | deny | none | Secrets are excluded by default |
| unknown | deny | none | Fail closed |

Provider adapters may narrow these decisions. They must never turn a canonical
denial or undeclared capability into an implicit grant.

## Executable-host gate

Do not label a harness safe for executable skills until an implementation and
its tests demonstrate all of the following:

- default denial plus host/user approval for every tool or script;
- canonical capability validation and fail-closed provider mapping;
- resolved working-directory, readable-root, and writable-root boundaries;
- package-escape and unsafe-symlink rejection;
- network denial unless the atomic action declares it;
- an allowlisted child environment with secrets absent by default;
- bounded wall-clock and idle timeouts;
- bounded stdout and stderr;
- CPU and memory limits where supported;
- cancellation and whole-process-tree termination;
- audit records containing skill/version/digest, requested and granted
  capabilities, command or tool, working directory, timeouts, exit status, and
  redacted output metadata.

The Phase 6 reference harness intentionally cannot run the executable-host
conformance suite because it has no execution endpoint. An attempt to invoke an
`execute` subcommand is rejected by argument parsing. Adding such a command
requires a later approved phase and every gate above.

Phase 7 evaluated two installed Ollama models through structured, data-only
catalog and activation context. Routing was strong, but strict approval-stop
compliance was only `0.6667` for `gemma4-agent:latest` and `0.3333` for
`qwen3:8b`. This confirms why mutation denial must be enforced by the host and
must never depend on model prose. See the
[Phase 7 conformance record](phase7-conformance.md) for pinned digests, token
costs, latency, and the exact interpretation of these measurements.

## OpenCode local-model example

[`examples/opencode-local/opencode.json`](../examples/opencode-local/opencode.json)
uses the current OpenCode OpenAI-compatible provider shape and points to LM
Studio on loopback. It contains no API key, credential reference, external
directory, or machine-specific filesystem path. Copy it to `opencode.json` in a
writable projection, make the locally served model ID match `local-model`, and
start OpenCode from that projection.

The example defaults tool access to `ask`, requires approval to load skills, and
denies editing, shell, network, and external-directory access. OpenCode should
discover the projected `.agents/skills/` packages through its native skill
tool. Live verification remains skipped when OpenCode or a local model server is
not installed; static compatibility is not reported as a live pass.

Current primary sources, verified 2026-07-22:

- <https://opencode.ai/docs/skills>
- <https://opencode.ai/docs/providers>
- <https://opencode.ai/docs/permissions/>
