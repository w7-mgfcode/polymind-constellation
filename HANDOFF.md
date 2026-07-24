# Session Handoff

> **Date:** 2026-07-24 (updated); original session 2026-07-23
> **Session focus:** Complete the 0.8.1 hardening review, rank the next
> architectural directions, and implement release automation plus signed
> provenance.
> **Status:** Local implementation and validation are complete. Remote
> publication is blocked on Git, GitHub, PyPI, and signer configuration.
>
> **2026-07-24 update:** A newly added Hungarian translation
> (`docs/_transIT-hu/prioritized-todo_hu.md`) contained four sibling-relative
> links that turned the documentation-link check — and therefore
> `scripts/verify` — red. The four links were repointed one level up into
> `docs/` and the full gate now passes again (see the dated evidence below).

## Executive Summary

Polymind Constellation 0.8.1 is locally release-ready but is not published.
The end-to-end review first closed fail-closed projection, symlink, installer
source-selection, and conformance-state gaps. A subsequent architecture review
ranked release automation at 94/100, provenance at 89/100, and registry
publication at 47/100. Release automation and provenance were selected for
implementation; registry publication was deferred to Phase 9.

The repository now contains a tag-triggered GitHub Actions release pipeline,
PyPI Trusted Publishing, deterministic release evidence, direct Gitsign commit
verification, and GitHub/Sigstore SLSA artifact attestations. Standard
verification passes. Release-mode orchestration passes in a disposable real Git
repository with controlled verifier stubs, while genuine cryptographic
verification remains intentionally blocked until the real GitHub repository
issues the attestations.

The prioritized remaining backlog is maintained in
[prioritized-todo.md](docs/prioritized-todo.md).

## Delivered Work

### 0.8.1 hardening

- Restored the prior generated projection after interruption at every managed
  atomic-replacement boundary.
- Rejected symlinked canonical roots, package directories, resources, installer
  roots, and generated projection paths.
- Removed working-directory projection shadowing.
- Made installed releases prefer their wheel-bundled projection.
- Anchored source-checkout projection lookup to the framework module.
- Preserved pass, partial, skip, measured, and fail conformance states.
- Added projection fault-injection, symlink, installer-source, and conformance
  regression tests.
- Updated framework, lock, changelog, security, compatibility, and Phase 8
  release documentation to 0.8.1.

### Release automation

- Added .github/workflows/ci.yml for pull-request and push verification.
- Added .github/workflows/release.yml for version-tag releases.
- Added monthly GitHub Actions dependency monitoring.
- Pinned every third-party action to a 40-character commit SHA.
- Built wheel and source archives in a dedicated build job.
- Generated deterministic SHA-256 evidence and changelog-derived release notes.
- Used a protected pypi environment and PyPI Trusted Publishing.
- Kept long-lived PyPI tokens and Twine passwords out of the workflow.
- Created the GitHub Release only after successful PyPI publication.
- Added tests for workflow permissions, action pinning, publication ordering,
  and the absence of token-based publishing.

### Git and artifact provenance

- Added polymind release-manifest.
- Added scripts/verify --release.
- Required HEAD, the exact version tag, and manifest commit to match.
- Required a clean tracked index and worktree.
- Required exactly one expected wheel and source archive.
- Verified artifact names, sizes, and SHA-256 digests.
- Required direct Gitsign verification of the release commit.
- Required an exact certificate identity and exact OIDC issuer.
- Required a keyless GitHub/Sigstore attestation for both artifacts.
- Pinned attestation verification to:
  - the expected repository;
  - .github/workflows/release.yml;
  - the exact source commit;
  - refs/tags/v0.8.1;
  - the SLSA provenance v1 predicate.
- Downloaded Gitsign 0.16.1 only after checking SHA-256
  4a29a1f4b9add1f0f6d9a3e9e6ba0cffa121b971be82d62bb1496d7d1d877b0a.
- Added negative tests for missing Git provenance, artifact drift, missing
  manifests, invalid Gitsign verification, and missing or invalid attestations.

### Architecture and planning

- Recorded the weighted ranking in
  [development-directions.md](docs/development-directions.md).
- Documented one-time setup and release operations in
  [release-automation.md](docs/release-automation.md).
- Selected OCI Distribution 1.1 plus ORAS as the initial Phase 9 registry
  architecture.
- Deferred the registry publisher and catalog integration until release
  identity and provenance are operational.
- Created a priority-, complexity-, and dependency-ranked backlog in
  [prioritized-todo.md](docs/prioritized-todo.md).

## Architecture Decisions

- **Release automation and provenance precede registry publication.** A registry
  must not distribute packages before immutable release identity and artifact
  verification are operational.
- **Use PyPI Trusted Publishing instead of a long-lived upload token.** The
  publication job receives only the job-scoped OIDC permission needed to mint a
  short-lived credential.
- **Require both source and build identities.** Gitsign proves the approved
  release-commit signer. GitHub/Sigstore attestation separately proves the
  hosted workflow and source-to-artifact relationship.
- **Pin exact signer identity.** Release verification accepts neither an
  unspecified signer nor an identity regex.
- **Target SLSA Build Level 2 honestly.** Level 3 is not claimed because the
  build and signing logic have not moved into a hardened reusable workflow.
- **Treat the manifest as metadata, not a signature.** A checksum manifest
  without valid Gitsign and Sigstore verification is insufficient.
- **Use OCI and ORAS for Phase 9.** Content-addressed generic artifacts,
  referrers, and existing registry authorization are preferred to a bespoke S3
  and DynamoDB protocol.
- **Keep canonical skills under skills/.** Generated provider projections remain
  read-only and must be regenerated through the existing synchronization
  command.

## Provenance Contract

A release must fail unless all of these statements are true:

1. The release ref is exactly refs/tags/v0.8.1.
2. HEAD, the tag commit, and the manifest commit are identical.
3. The tracked index and worktree contain no changes.
4. The manifest describes exactly the expected wheel and source archive.
5. Both artifacts match their recorded byte size and SHA-256 digest.
6. The manifest requires Gitsign and Sigstore verification.
7. The Gitsign certificate identity matches RELEASE_COMMIT_IDENTITY exactly.
8. The Gitsign issuer matches RELEASE_COMMIT_OIDC_ISSUER exactly.
9. Gitsign validates the Git signature, Rekor entry, and certificate claims.
10. Both artifacts have valid SLSA provenance attestations.
11. The attestation repository, workflow, source digest, and source ref match
    the release.
12. The attestation predicate is https://slsa.dev/provenance/v1.

Required repository variables:

~~~text
RELEASE_COMMIT_IDENTITY
RELEASE_COMMIT_OIDC_ISSUER
~~~

Required GitHub environment:

~~~text
pypi
~~~

Required PyPI Trusted Publisher mapping:

~~~text
Owner:       CONFIRMED_GITHUB_OWNER
Repository:  CONFIRMED_REPOSITORY
Workflow:    release.yml
Environment: pypi
~~~

## Validation Evidence

### Standard repository gate

The 2026-07-24 scripts/verify run passed (exit 0) after the documentation-link
fix described in the header:

- Ruff lint: pass
- Ruff format check: pass
- Strict mypy for src and tests: pass
- Pytest: 123 passed, 1 skipped
- Canonical validation: 3 packages
- Documentation links: pass
- Projection drift: none
- Static conformance: 27 checks passed
- Optional external skills-ref validator: skipped because it is not installed

Historical note: an intermediate 2026-07-24 state failed the gate (exit 1)
because `docs/_transIT-hu/prioritized-todo_hu.md` linked to
`development-directions.md`, `release-automation.md`, `phase9-registry.md`, and
`versioning.md` as siblings when those files live in `docs/`. The links were
repointed to `../` and the gate returned to green. The prior 2026-07-23 pass
remains valid for the pre-translation tree.

### Live-provider evidence currency (2026-07-24)

The recorded compatibility baseline in `adapters/providers.toml` is unchanged;
support states are not modified without successful live evidence. The following
observations qualify — but do not overturn — that baseline:

- Gemini: `providers.toml` records `0.51.0` as the historical tested baseline.
  The currently installed CLI is `0.52.0`, which is not yet revalidated; its
  probe timed out today. The `0.51.0` `tested` state stands as historical
  evidence and must not be generalized to `0.52.0` until re-tested.
- Codex: `0.145.0` remains the historically tested version. Today's probe was
  blocked by read-only environment behavior, not a confirmed product
  regression; the recorded `tested` state is not invalidated by an
  environment-blocked run.
- Claude Code and OpenCode: unchanged. Claude live invocation stays
  intentionally out of scope without explicit external-model authorization, and
  OpenCode is not installed here.

### Repository directory facts (2026-07-24 correction)

An earlier ad hoc summary mis-described several `docs/` subdirectories. The
accurate state is:

- `docs/_runway/` contains the 1,190-line
  `polymind-constellation-runway.md`.
- `docs/provenance/` contains two JSON ledgers
  (`dynamous-community-skills.json` and `migration-map.json`).
- `docs/conformance/` is empty.

### Projection and packaging

- Projection dry-run reported no changes.
- Projection drift check reported no changes.
- The wheel contains the complete generated three-skill projection.
- The source archive contains the projection, release workflow, release code,
  and release documentation.
- Neither archive contains generated Python bytecode.
- The final wheel installed in a disposable environment.
- Installed-wheel dry-run, apply, check, and rollback all succeeded using the
  embedded projection.

### Release-mode orchestration

A disposable writable Git repository was created with:

- a real commit;
- a matching v0.8.1 tag;
- a clean tracked worktree;
- the final local wheel and source archive;
- generated release evidence.

The complete release verification command passed with controlled gh and
gitsign verifier stubs. This proves command orchestration, policy propagation,
tag and commit checks, artifact validation, and fail-closed handling. Separate
negative tests prove that invalid verifier exits are rejected.

This does not constitute genuine Gitsign or Sigstore cryptographic evidence.
Only the configured real GitHub release workflow can issue and verify that
evidence.

### Current local artifacts

Wheel:

~~~text
dist/polymind_constellation-0.8.1-py3-none-any.whl
SHA-256: 8f01bf2b3427acc198b738b1e3096d3f59bd8b413f31521eee8ede810b9518b9
~~~

The handoff is included in the source archive. Its digest is therefore not
embedded here because changing this document changes that archive. Generate the
authoritative source-archive digest after the final documentation build; the
release workflow records it in SHA256SUMS and release-manifest.json.

The locally built archives are validation artifacts. The tagged GitHub workflow
must rebuild the public release artifacts from the real signed commit.

## Current External Blockers

- The workspace .git path is a non-functional, read-only placeholder.
- No usable branch, history, tag, or remote metadata is available here.
- The configured w7-mgfcode GitHub credential is invalid.
- The configured llw7-hector GitHub credential is invalid.
- The intended GitHub owner/repository identity is unconfirmed.
- The pypi GitHub environment is not configured.
- The PyPI Trusted Publisher mapping is not configured.
- RELEASE_COMMIT_IDENTITY is not configured.
- RELEASE_COMMIT_OIDC_ISSUER is not configured.
- No genuine Gitsign-signed release commit exists in this workspace.
- No GitHub-issued artifact attestation exists.
- The 0.8.1 package and GitHub Release have not been published.

Do not work around these blockers with a local Twine upload, an unsigned tag,
an unverified identity, or manually substituted artifacts.

## Current-Session Files

~~~text
.github/dependabot.yml
.github/workflows/ci.yml
.github/workflows/release.yml
.gitignore
CHANGELOG.md
CONTRIBUTING.md
HANDOFF.md
README.md
docs/development-directions.md
docs/phase8-release.md
docs/phase9-registry.md
docs/prioritized-todo.md
docs/release-automation.md
docs/security.md
docs/versioning.md
src/polymind/cli.py
src/polymind/installer.py
src/polymind/projection.py
src/polymind/release.py
src/polymind/validation.py
src/polymind/verify.py
tests/test_conformance.py
tests/test_installer.py
tests/test_projection.py
tests/test_provenance.py
tests/test_release.py
~~~

Generated projections under dist/repo were validated but remain generated,
read-only artifacts.

## Dead Ends and Resolutions

- **Repository inspection failed:** Git commands against the workspace failed
  because .git is only a protected placeholder. Resolution requires a real
  clone; no synthetic history was created in the workspace.
- **GitHub operations failed:** Both configured GitHub credentials are invalid.
  Resolution requires interactive re-authentication by the repository owner.
- **Initial isolated build failed:** The sandbox could not resolve the Hatchling
  build backend. The authorized build was rerun with external dependency access
  and succeeded.
- **Genuine provenance could not be produced locally:** GitHub OIDC, Sigstore
  attestation issuance, and the real signer identity are unavailable.
  Disposable stubs were used only to validate orchestration; this limitation is
  explicitly recorded.
- **Direct manual publication was rejected as a workaround:** It would bypass
  the selected Trusted Publishing and provenance controls.

## Open Questions

- What is the authoritative GitHub owner/repository?
- Which GitHub account owns and administers the release?
- What exact Gitsign certificate identity is authorized?
- What exact OIDC issuer is authorized?
- Does the repository plan support all required artifact-attestation features?
- Should writing-session-handoffs become a canonical Polymind package or remain
  external?
- After publication, which live conformance gap should be addressed first:
  Claude invocation, OpenCode discovery, or cross-provider approval parity?

## Prioritized Next Steps

The full dependency-ranked checklist and acceptance criteria are in
[prioritized-todo.md](docs/prioritized-todo.md). The critical path is:

~~~text
RESTORE_GIT
→ AUTHENTICATE_GITHUB
→ CONFIGURE_GITSIGN
→ CONFIGURE_PYPI_OIDC
→ VALIDATE_REAL_WORKFLOW
→ ADD_RELEASE_RECOVERY
→ SIGN_AND_TAG_0.8.1
→ PUBLISH
→ INDEPENDENTLY_VERIFY
→ CLOSE_RELEASE
~~~

Immediate actions:

1. Restore a writable clone of the authoritative GitHub repository.
2. Preserve and transfer the complete current workspace state.
3. Confirm the owner/repository and default branch.
4. Re-authenticate the correct GitHub account.
5. Configure the Gitsign identity and issuer repository variables.
6. Create the protected pypi environment and PyPI Trusted Publisher mapping.
7. Validate the workflows in a pull request without publishing.
8. Implement and test the partial-release recovery path.
9. Sign the final release commit, verify it, and create v0.8.1.
10. Push the tag and let the workflow build, attest, publish, and release.
11. Independently download and verify the published artifacts.
12. Update the release record from locally validated to published.

## Commands for the Next Session

After restoring the real repository:

~~~sh
gh auth status
git status
git remote -v
git branch --show-current
git ls-remote --tags origin v0.8.1

scripts/sync-adapters --dry-run
scripts/sync-adapters --check
scripts/verify

gitsign verify \
  --certificate-identity="$RELEASE_COMMIT_IDENTITY" \
  --certificate-oidc-issuer="$RELEASE_COMMIT_OIDC_ISSUER" \
  HEAD

git diff --quiet
git diff --cached --quiet
git rev-parse HEAD
git rev-parse 'refs/tags/v0.8.1^{commit}'
~~~

Do not push v0.8.1 until GitHub authentication, the Gitsign variables, the pypi
environment, the PyPI Trusted Publisher, and partial-release recovery have all
been validated.

## Repository Rules to Preserve

- Hand-edit canonical packages only under skills/.
- Treat dist/repo/.agents/skills and dist/repo/.claude/skills as generated and
  read-only.
- Keep packages self-contained.
- Keep provider permissions out of canonical SKILL.md files.
- Keep shell wrappers thin; implementation belongs in src/polymind/.
- Add tests for every new validation rule and keep diagnostic codes stable.
- Unknown capabilities, path escapes, symlinks, and projection conflicts fail
  closed.
- Never overwrite unrelated or non-generated downstream content.

