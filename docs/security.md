# Security model

Agent Skills are instructions and resources that can influence tool use. Schema
validity does not make a skill trustworthy, and a digest does not prove its
origin. Review provenance, instructions, scripts, capabilities, overlays, and
release evidence before enabling a package.

## Trust boundaries

- Canonical packages are hand-edited only under a non-symlinked `skills/` root;
  package directories and resources are non-symlinked, self-contained, and
  contain no dependency on the original vendor directory.
- `skill.toml` capabilities describe possible actions but grant nothing.
  Unknown actions fail validation, and provider overlays may narrow but never
  broaden the canonical set.
- Generated trees are read-only, non-symlinked artifacts. Their locks detect
  drift but are not signatures.
- Catalog, activation, resource reads, conformance routing, and downstream
  installation execute no skill scripts.
- Executable local hosts remain unsupported until they satisfy every sandbox,
  timeout, environment, network, cleanup, audit, and permission requirement in
  the [local harness contract](local-harness-contract.md).

## Installer safety

The downstream installer resolves its target, rejects symlinked path segments,
validates the source projection and its digests, and manages only named skill
directories recorded in its own lock. Installed releases prefer their bundled
projection; source checkouts use a module-anchored projection rather than a
working-directory candidate. Dry-run is the default; `--apply` is the explicit
approval boundary. Updates require a clean prior lock state.

Application uses temporary staging and backup directories beside the target,
atomic replacements, post-apply digest verification, and restoration after any
failure. One pre-apply snapshot supports an explicit rollback. Repository-owned
instruction files, provider settings, secrets, and unrelated skills are outside
the installer's write set.

## Provider and model claims

Compatibility states are evidence-scoped. Native discovery does not establish
correct routing, safe tool execution, or approval adherence. Static validation
does not establish that a client loaded the skill. Raw model servers do not
discover Agent Skills without a harness.

The Phase 7 Ollama measurements exposed approval contradictions even when
routing was strong. Hosts must enforce mutation denial independently of model
prose. See the [conformance record](phase7-conformance.md).

## Reporting and release

Report findings through GitHub private vulnerability reporting as described in
the repository [`SECURITY.md`](../SECURITY.md). Do not open a public issue or
include secrets, credentials, or private model transcripts in a report.

Before release, follow the [release automation and provenance](release-automation.md)
contract. `scripts/verify --release` requires a matching Git tag and commit,
an exact-identity Gitsign commit signature, exact artifact digests, and a
Sigstore/SLSA attestation bound to the expected repository, workflow, source
ref, and source digest. A checksum manifest without those verified identities
is not provenance.
