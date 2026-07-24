# Release automation and provenance

Release workflow: `.github/workflows/release.yml`

The workflow builds exactly one wheel and source archive from a version tag,
generates deterministic SHA-256 and release-note evidence, obtains a keyless
Sigstore artifact attestation from GitHub Actions, verifies the complete
tag-to-artifact chain, publishes through PyPI Trusted Publishing, and only then
creates the GitHub Release.

## One-time remote configuration

These controls must exist before pushing `v0.8.1`:

1. Establish the real GitHub repository and push the complete source history.
2. Create a protected GitHub environment named `pypi`. Add required reviewers
   if the repository's plan supports them.
3. On PyPI, configure a Trusted Publisher for the project with the exact GitHub
   owner, repository, workflow filename `release.yml`, and environment `pypi`.
   A pending publisher may be used when the project does not yet exist.
4. Protect the release branch and restrict creation of `v*` tags to release
   maintainers. Require the CI workflow before merge.
5. Confirm that the repository has access to GitHub artifact attestations and
   that the installed GitHub CLI supports `gh attestation verify`.
6. Require maintainers to sign release commits with Gitsign. Set repository
   variables `RELEASE_COMMIT_IDENTITY` and `RELEASE_COMMIT_OIDC_ISSUER` to the
   exact certificate identity and issuer allowed by release policy. Regex
   identities are not accepted.

No PyPI token or `TWINE_PASSWORD` belongs in repository secrets. Trusted
Publishing exchanges the job's GitHub OIDC identity for a short-lived PyPI
credential.

## Local and CI gates

Standard source verification remains:

```sh
scripts/verify
```

The workflow builds archives, then generates the source and digest manifest:

```sh
uv build
uv run polymind release-manifest \
  --repository OWNER/REPOSITORY \
  --commit FULL_40_CHARACTER_COMMIT_SHA \
  --ref refs/tags/v0.8.1 \
  --commit-identity EXACT_CERTIFICATE_IDENTITY \
  --commit-issuer https://EXACT-OIDC-ISSUER
```

After `actions/attest` has generated the Sigstore bundle, the mandatory release
gate is:

```sh
scripts/verify --release
```

That gate fails closed unless all of the following match:

- `HEAD`, `refs/tags/v0.8.1`, and the manifest commit;
- the release commit's Gitsign signature, transparency-log record, exact
  certificate identity, and exact OIDC issuer;
- the expected wheel and source archive names, sizes, and SHA-256 digests;
- a clean tracked index and worktree;
- the repository and exact `.github/workflows/release.yml` signer identity;
- the tag ref and source commit in the attestation certificate;
- the `https://slsa.dev/provenance/v1` predicate for both artifacts.

The manifest alone is integrity metadata and is never treated as a signature.
Gitsign proves the approved source signer identity; the separate keyless
Sigstore artifact attestation proves the build identity and source-to-artifact
relationship. This workflow targets SLSA Build Level 2. A future Level 3 claim
requires an isolated, maintainer-controlled reusable build workflow and a new
validation record.

## Release procedure

1. Complete the one-time remote configuration and verify `gh auth status`.
2. Run `scripts/verify` in the real clean Git checkout.
3. Create and push the exact version tag: `git push origin v0.8.1`.
4. Observe the `Release` workflow. Do not retry publication by hand if PyPI
   succeeded but a later job failed; PyPI filenames are immutable.
5. Verify the published files independently with their SHA-256 values and
   `gh attestation verify`, then record the final PyPI and GitHub Release URLs.

PyPI Trusted Publishing guidance is maintained in the
[PyPI documentation](https://docs.pypi.org/trusted-publishers/). GitHub documents
the attestation identity and verification model in its
[artifact attestation guide](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations).
