# Security policy

Polymind Constellation has no published, supported release yet. Version 0.8.1
is locally validated but remains unpublished and must not be treated as a
released package until the release blockers in `HANDOFF.md` are cleared.

Report suspected vulnerabilities through GitHub private vulnerability
reporting:

https://github.com/w7-mgfcode/polymind-constellation/security/advisories/new

Do not open a public issue for a vulnerability. Do not include credentials,
private model transcripts, or unrelated personal data. Include the affected
commit or version, impact, minimal reproduction, and suggested mitigation when
available. The maintainer will coordinate disclosure after validation and a
fix; no response-time SLA is promised.

The detailed trust boundaries, installer safety model, provider-claim limits,
and release-provenance requirements are documented in
[`docs/security.md`](docs/security.md). Generated projections under
`dist/repo/` are artifacts; report the canonical source under `skills/` or the
implementation under `src/polymind/` when one exists.
