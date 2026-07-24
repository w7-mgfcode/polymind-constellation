# Re-ranked TODO List

Evidence date: 2026-07-23

## Ranking method

- **Priority score:** release impact 35%, security and risk reduction 25%,
  dependency value 20%, and user value 20%.
- **Complexity:** 1 is trivial and 5 is major architectural work.
- Tasks are ordered by priority, dependencies, and then complexity.

## Ranked backlog

| Rank | Task | Priority | Score | Complexity | Depends on |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | Restore the real Git repository | P0 | 100 | 2 | — |
| 2 | Confirm GitHub ownership and re-authenticate | P0 | 98 | 1 | 1 |
| 3 | Configure Gitsign release identity | P0 | 96 | 3 | 1–2 |
| 4 | Configure PyPI Trusted Publishing | P0 | 95 | 2 | 2 |
| 5 | Validate the release workflow in the real repository | P0 | 94 | 3 | 1–4 |
| 6 | Add a partial-release recovery procedure | P0 | 92 | 3 | 5 |
| 7 | Create and sign the final 0.8.1 commit and tag | P0 | 91 | 2 | 1–6 |
| 8 | Publish 0.8.1 through GitHub Actions | P0 | 90 | 2 | 7 |
| 9 | Independently verify the published release | P0 | 89 | 2 | 8 |
| 10 | Close and record the 0.8.1 release cycle | P1 | 82 | 1 | 9 |
| 11 | Harden release governance and workflow linting | P1 | 78 | 3 | 5 |
| 12 | Upgrade provenance toward SLSA Build Level 3 | P2 | 66 | 5 | 8–11 |
| 13 | Write the Phase 9 registry threat model and ADR | P2 | 61 | 3 | 10 |
| 14 | Define the OCI skill artifact contract | P2 | 59 | 3 | 13 |
| 15 | Build a disposable OCI registry fixture | P2 | 56 | 4 | 14 |
| 16 | Implement polymind registry publish | P2 | 53 | 5 | 14–15 |
| 17 | Implement digest-pinned registry downloads | P2 | 51 | 5 | 15–16 |
| 18 | Add registry authentication and RBAC tests | P2 | 49 | 5 | 16–17 |
| 19 | Integrate registry resolution into catalog.py | P3 | 43 | 5 | 17–18 |
| 20 | Complete remaining provider live-conformance gaps | P3 | 39 | 5 | 10 |

## P0 — Release-blocking work

### TODO 1: Restore a functional Git repository

**Complexity:** 2/5  
**Owner:** Repository administrator

- [ ] Locate the authoritative GitHub repository.
- [ ] Confirm the exact owner/repository identity.
- [ ] Clone it into a writable working directory.
- [ ] Transfer the current workspace changes without overwriting unrelated work.
- [ ] Confirm that .git contains valid repository metadata.
- [ ] Verify the default branch and configured remotes.
- [ ] Inspect branches, tags, release history, and outstanding remote changes.
- [ ] Confirm that v0.8.1 does not already exist locally or remotely.
- [ ] Review the complete transferred diff.
- [ ] Ensure generated release evidence remains ignored.

Acceptance criteria:

~~~sh
git status
git remote -v
git branch --show-current
git ls-remote --tags origin v0.8.1
~~~

All commands must succeed, and v0.8.1 must not conflict with an existing tag or
release.

### TODO 2: Restore GitHub authentication

**Complexity:** 1/5  
**Depends on:** TODO 1

- [ ] Select the correct GitHub account.
- [ ] Run gh auth login -h github.com.
- [ ] Confirm the account has repository administration rights.
- [ ] Confirm permission to manage Actions, environments, variables, releases,
  rules, and tags.
- [ ] Confirm artifact attestations are available for the repository and plan.
- [ ] Confirm GitHub CLI in Actions supports gh attestation verify.

Acceptance criteria:

~~~sh
gh auth status
gh repo view OWNER/REPOSITORY
gh workflow list --repo OWNER/REPOSITORY
~~~

### TODO 3: Configure Gitsign release identity

**Complexity:** 3/5  
**Depends on:** TODOs 1–2

- [ ] Select the authoritative release signer identity.
- [ ] Select the approved OIDC issuer.
- [ ] Document whether the identity is an email address or URI.
- [ ] Configure Gitsign locally.
- [ ] Set repository variable RELEASE_COMMIT_IDENTITY.
- [ ] Set repository variable RELEASE_COMMIT_OIDC_ISSUER.
- [ ] Ensure both values exactly match the Gitsign certificate claims.
- [ ] Sign a non-release test commit.
- [ ] Verify it with the release gate's exact identity arguments.
- [ ] Confirm Git signature, Rekor entry, and certificate-claim validation.
- [ ] Document signer rotation and emergency revocation.

Acceptance criteria:

~~~sh
gitsign verify \
  --certificate-identity="$RELEASE_COMMIT_IDENTITY" \
  --certificate-oidc-issuer="$RELEASE_COMMIT_OIDC_ISSUER" \
  HEAD
~~~

### TODO 4: Configure PyPI Trusted Publishing

**Complexity:** 2/5  
**Depends on:** TODO 2

- [ ] Confirm whether polymind-constellation already exists on PyPI.
- [ ] Create a pending publisher if this is the first publication.
- [ ] Create the GitHub environment named pypi.
- [ ] Add required reviewers where supported.
- [ ] Restrict the environment to protected version tags.
- [ ] Configure the exact Trusted Publisher mapping:

~~~text
Owner:       CONFIRMED_GITHUB_OWNER
Repository:  CONFIRMED_REPOSITORY
Workflow:    release.yml
Environment: pypi
~~~

- [ ] Confirm no PYPI_TOKEN, TWINE_PASSWORD, or long-lived credential is stored.
- [ ] Confirm the publish job has only contents: read and id-token: write.

Acceptance criterion: the PyPI mapping and GitHub environment must exactly match
the workflow configuration.

### TODO 5: Validate the workflow in the real repository

**Complexity:** 3/5  
**Depends on:** TODOs 1–4

- [ ] Add the implemented CI and release workflows to the real repository.
- [ ] Confirm every third-party action uses a 40-character commit SHA.
- [ ] Validate workflow YAML with actionlint.
- [ ] Confirm release execution is limited to version tags.
- [ ] Confirm an incorrect tag fails in polymind release-manifest.
- [ ] Confirm missing Gitsign variables fail closed.
- [ ] Confirm a missing attestation bundle fails closed.
- [ ] Confirm an unsigned release commit is rejected.
- [ ] Confirm a mismatched signer identity or issuer is rejected.
- [ ] Confirm mismatched tag, commit, repository, workflow, ref, and digest
  values are rejected.
- [ ] Confirm pull requests cannot obtain publication permissions.

Acceptance criteria: CI passes on a normal pull request, no publication occurs,
and every negative release scenario fails at its intended gate.

### TODO 6: Add partial-release recovery

**Complexity:** 3/5  
**Depends on:** TODO 5

The current workflow creates the GitHub Release after PyPI succeeds. A later
GitHub failure must not force an unsafe PyPI re-upload.

- [ ] Define recovery for “PyPI succeeded, GitHub Release failed.”
- [ ] Preserve distributions and evidence long enough for recovery.
- [ ] Add a finalize-only workflow or a documented maintainer command.
- [ ] Verify existing PyPI digests against SHA256SUMS before finalization.
- [ ] Prevent recovery from rebuilding or replacing artifacts.
- [ ] Prevent skip-existing from accepting mismatched PyPI files silently.
- [ ] Simulate a GitHub Release failure after successful publication.
- [ ] Test the complete recovery path.
- [ ] Document safe and unsafe retries.
- [ ] Document PyPI filename immutability.

Acceptance criterion: a failed GitHub Release step can be resumed without
rebuilding or republishing PyPI artifacts.

### TODO 7: Prepare the final release commit and tag

**Complexity:** 2/5  
**Depends on:** TODOs 1–6

- [ ] Apply all reviewed workspace changes to the real repository.
- [ ] Confirm version consistency across pyproject.toml, uv.lock,
  polymind.__version__, projection.lock.json, and CHANGELOG.md.
- [ ] Run projection dry-run and drift checks.
- [ ] Run the complete verification suite.
- [ ] Review the complete Git diff.
- [ ] Commit only the intended 0.8.1 changes.
- [ ] Sign the release commit with Gitsign.
- [ ] Verify its exact certificate identity and issuer.
- [ ] Ensure the tracked worktree and index are clean.
- [ ] Create the exact v0.8.1 tag.
- [ ] Verify the tag resolves to the signed release commit.

Acceptance criteria:

~~~sh
scripts/sync-adapters --dry-run
scripts/sync-adapters --check
scripts/verify
git diff --quiet
git diff --cached --quiet
gitsign verify ... HEAD
git rev-parse HEAD
git rev-parse 'refs/tags/v0.8.1^{commit}'
~~~

The final two commit values must be identical.

### TODO 8: Publish 0.8.1

**Complexity:** 2/5  
**Depends on:** TODO 7

- [ ] Push the release commit.
- [ ] Wait for required CI checks.
- [ ] Push only the v0.8.1 tag.
- [ ] Monitor the Release workflow.
- [ ] Confirm source verification passes.
- [ ] Confirm fresh wheel and sdist construction.
- [ ] Confirm SHA-256 evidence generation.
- [ ] Confirm direct Gitsign commit verification.
- [ ] Confirm GitHub/Sigstore artifact attestation generation.
- [ ] Confirm both artifacts pass gh attestation verify.
- [ ] Approve the protected pypi deployment.
- [ ] Confirm PyPI publication.
- [ ] Confirm GitHub Release creation.
- [ ] Do not manually upload locally built validation artifacts.

### TODO 9: Independently verify the public release

**Complexity:** 2/5  
**Depends on:** TODO 8

- [ ] Download the wheel and sdist from PyPI.
- [ ] Download all GitHub Release assets.
- [ ] Compare filenames, sizes, and SHA-256 values.
- [ ] Verify both Sigstore attestations independently.
- [ ] Confirm the source digest equals the release commit.
- [ ] Confirm the source ref is refs/tags/v0.8.1.
- [ ] Confirm the exact signer workflow.
- [ ] Install the downloaded PyPI wheel in a disposable environment.
- [ ] Exercise installer dry-run, apply, check, and rollback.
- [ ] Confirm the wheel contains no generated bytecode.
- [ ] Confirm PyPI and GitHub serve byte-identical distributions.

Acceptance criterion: both registries expose identical artifacts with valid
source and build provenance.

## P1 — Release closure and governance

### TODO 10: Close the release cycle

**Complexity:** 1/5  
**Depends on:** TODO 9

- [ ] Change release documentation from locally validated to published.
- [ ] Record PyPI and GitHub Release URLs.
- [ ] Record tag, commit, workflow run, filenames, sizes, and digests.
- [ ] Update HANDOFF.md.
- [ ] Update the Phase 8 release record.
- [ ] Record intentional validation skips separately from passes.
- [ ] Record Gitsign identity and issuer without credentials.
- [ ] Create follow-up issues for warnings or manual interventions.

### TODO 11: Harden release governance

**Complexity:** 3/5  
**Depends on:** TODO 5

- [ ] Add actionlint to local and CI verification.
- [ ] Add CODEOWNERS coverage for workflows, provenance code, and release docs.
- [ ] Protect the default branch.
- [ ] Restrict version-tag creation.
- [ ] Require signed commits for release preparation where feasible.
- [ ] Require CI before merge.
- [ ] Add environment reviewers for PyPI publication.
- [ ] Define Gitsign identity rotation.
- [ ] Define the Gitsign binary upgrade and checksum-review process.
- [ ] Test least-privilege permissions for every job.
- [ ] Add a scheduled provenance-verification smoke test.

## P2 — Provenance maturity and registry foundation

### TODO 12: Upgrade toward SLSA Build Level 3

**Complexity:** 5/5  
**Depends on:** TODOs 8–11

- [ ] Move build and attestation generation into a reusable workflow.
- [ ] Prevent callers from changing security-critical build steps.
- [ ] Separate untrusted caller inputs from the builder.
- [ ] Pin the reusable workflow by immutable commit SHA.
- [ ] Validate signer repository and workflow identity.
- [ ] Deny self-hosted runners where appropriate.
- [ ] Produce a formal SLSA level assessment.
- [ ] Do not claim Level 3 until all requirements are independently reviewed.

### TODO 13: Write the registry threat model and ADR

**Complexity:** 3/5  
**Depends on:** TODO 10

- [ ] Define publisher, registry, consumer, and catalog trust boundaries.
- [ ] Cover overwrite, replay, downgrade, namespace-squatting, and
  digest-confusion threats.
- [ ] Define fail-closed behavior for missing provenance.
- [ ] Compare GHCR, another OCI registry, and bespoke object storage.
- [ ] Record the OCI/ORAS backend decision.
- [ ] Define retention, deprecation, and deletion policies.
- [ ] Define recovery from a compromised publisher.

### TODO 14: Define the OCI skill contract

**Complexity:** 3/5  
**Depends on:** TODO 13

- [ ] Finalize artifact and manifest media types.
- [ ] Define deterministic skill archive construction.
- [ ] Define required OCI annotations.
- [ ] Define SemVer tag behavior and overwrite rejection.
- [ ] Require digest-pinned installation.
- [ ] Define provenance and signature referrers.
- [ ] Define framework compatibility metadata.
- [ ] Define capability declarations and validation rules.
- [ ] Publish valid examples and invalid fixtures.

### TODO 15: Build a disposable registry fixture

**Complexity:** 4/5  
**Depends on:** TODO 14

- [ ] Add a local OCI Distribution registry fixture.
- [ ] Push and pull a minimal skill through ORAS.
- [ ] Test manifest and blob digest validation.
- [ ] Test immutable-version enforcement.
- [ ] Test missing and malformed provenance.
- [ ] Test unknown media types and namespace collisions.
- [ ] Ensure tests need no production credentials.

### TODO 16: Implement polymind registry publish

**Complexity:** 5/5  
**Depends on:** TODOs 14–15

- [ ] Validate the canonical package before packaging.
- [ ] Produce a deterministic archive.
- [ ] Calculate archive and manifest digests.
- [ ] Authenticate without command-line credentials.
- [ ] Refuse an existing SemVer tag with a different digest.
- [ ] Push blobs and manifests through ORAS.
- [ ] Attach provenance.
- [ ] Verify the remote digest after publication.
- [ ] Default to dry-run.
- [ ] Add comprehensive negative tests.

### TODO 17: Implement digest-pinned downloads

**Complexity:** 5/5  
**Depends on:** TODOs 15–16

- [ ] Resolve name and version to an immutable digest.
- [ ] Pull into a bounded temporary directory.
- [ ] Enforce size and file-count limits.
- [ ] Reject symlinks and path traversal.
- [ ] Verify OCI manifest and blob digests.
- [ ] Verify Sigstore provenance.
- [ ] Run the canonical package validator.
- [ ] Cache only verified content by digest.
- [ ] Reject mutable or digestless requests under strict policy.

### TODO 18: Add registry authentication and RBAC

**Complexity:** 5/5  
**Depends on:** TODOs 16–17

- [ ] Define reader, publisher, maintainer, and administrator roles.
- [ ] Test unauthorized push and pull operations.
- [ ] Test cross-namespace publication denial.
- [ ] Test publisher revocation and token expiry.
- [ ] Test credential redaction in logs.
- [ ] Document interactive and CI authentication.
- [ ] Keep provider credentials outside canonical skill packages.

## P3 — Broader integration

### TODO 19: Integrate the registry into catalog.py

**Complexity:** 5/5  
**Depends on:** TODOs 17–18

- [ ] Preserve current local, data-only catalog behavior.
- [ ] Add explicit registry configuration.
- [ ] Separate search, resolution, download, verification, and activation.
- [ ] Never execute downloaded package code.
- [ ] Expose source, version, digest, and provenance state.
- [ ] Require explicit network approval where applicable.
- [ ] Add offline and corrupted-cache behavior.
- [ ] Add deterministic catalog snapshots.

### TODO 20: Close remaining provider conformance gaps

**Complexity:** 5/5  
**Depends on:** TODO 10

- [ ] Run a real Claude live invocation.
- [ ] Validate OpenCode native local-model discovery.
- [ ] Test positive and negative triggers in every supported provider.
- [ ] Test resource loading, approval stops, and permission narrowing.
- [ ] Record unavailable runtimes as skips.
- [ ] Refresh the compatibility evidence matrix.
- [ ] Preserve distinct static, measured, partial, skipped, and passed states.

## Critical execution path

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

Related documents:

- [Development direction decision](development-directions.md)
- [Release automation and provenance](release-automation.md)
- [Phase 9 registry publication plan](phase9-registry.md)
- [Versioning and release policy](versioning.md)

