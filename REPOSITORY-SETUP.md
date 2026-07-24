# Polymind Constellation repository setup runbook

> Status: Phase A plan, authored 2026-07-24. Do not execute any mutation in
> this document until Gabor Szabo explicitly approves Phase B.

This playbook creates and hardens the new public personal-account repository
`w7-mgfcode/polymind-constellation`. It assumes the current source tree is the
authoritative tree, the existing `.git/` is an empty read-only placeholder, and
there is no remote history or tag to preserve.

Repository owner and commit author: Gabor Szabo (he/him), GitHub
`w7-mgfcode`, `shellsnake@icloud.com`. The email is used only for Git author and
committer identity; it is not inserted into public issue templates or commands
as a credential.

The commands use GitHub REST API version `2026-03-10`, which is the current
version shown in GitHub's REST examples as of this runbook's date. Stop on the
first unexpected result; do not improvise around an authorization, policy, CI,
or security failure.

## Scope and non-negotiable release hold

- This session may initialize Git, make the initial commit, create and harden
  the public GitHub repository, and verify the resulting configuration.
- It must not create or push `v0.8.1`, create a GitHub Release, publish to PyPI,
  or invoke the tag-triggered release workflow.
- Release remains blocked until the exact Gitsign identity and OIDC issuer,
  repository variables, protected `pypi` environment, PyPI Trusted Publisher,
  and tested partial-release recovery path all exist.
- Never hand-edit `dist/repo/`; it is generated. Canonical skills live in
  `skills/`, and framework implementation lives in `src/polymind/`.

Observed Phase A facts:

- `gh 2.46.0` is installed.
- `gh auth status` reports active HTTPS authentication as `w7-mgfcode`; the
  token has `repo` and `workflow` scopes. `llw7-hector` is present but inactive.
- `gh api user` reports `w7-mgfcode`, account type `User`, name `Gabor Szabo`.
- User actor ID `168316277` belongs to `w7-mgfcode`.
- `GET /repos/w7-mgfcode/polymind-constellation` returns HTTP 404, so the target
  repository does not currently exist.
- `git status` reports `fatal: not a git repository`; `.git/` is empty.
- Package metadata is `polymind-constellation` `0.8.1`, Python `>=3.11`, with
  `license = { text = "Proprietary" }` and no root `LICENSE` file.
- Existing workflows are `.github/workflows/ci.yml` and `release.yml`. Their
  third-party `uses:` references are pinned to 40-character SHAs. CI's required
  job/check context is `verify`. Release already uses least-scoped job
  permissions, OIDC, PyPI Trusted Publishing, and GitHub/Sigstore attestations.
- Existing `.github/dependabot.yml` monitors only GitHub Actions monthly.

## 1. Prerequisites and identity

Run from the repository root:

```sh
pwd
gh --version
gh auth status
gh api user --jq '{login,name,type}'
gh api repos/w7-mgfcode/polymind-constellation
git status
```

Expected:

- `pwd` ends in `/platform/w7-ghlanding`.
- `gh --version` reports `gh version 2.46.0` or a newer compatible release.
- The active account is `w7-mgfcode`; otherwise stop and run `gh auth login`
  interactively yourself.
- The repository lookup returns `Not Found (HTTP 404)` before creation.
- `git status` says this is not a Git repository before initialization.

After initialization in section 3, set repository-local identity only:

```sh
git config --local user.name "Gabor Szabo"
git config --local user.email "shellsnake@icloud.com"
git config --local user.useConfigOnly true
git config --local --get user.name
git config --local --get user.email
```

Expected output from the last two commands:

```text
Gabor Szabo
shellsnake@icloud.com
```

Rationale and source:

- Verify the CLI's active account before an irreversible public-repository
  creation; GitHub documents `gh auth status` and account switching in the
  [GitHub CLI manual](https://cli.github.com/manual/gh_auth_status).
- Keep the supplied author identity local to this repository rather than
  changing unrelated repositories; Git documents local configuration and
  author identity in [git-config](https://git-scm.com/docs/git-config).

## 2. Pre-publication review and repository health files

### 2.1 Validate the authoritative tree

Do not proceed if any command fails:

```sh
test -d .git
test -z "$(find .git -mindepth 1 -print -quit)"
test -f README.md
test -f CONTRIBUTING.md
test -f CHANGELOG.md
test -f pyproject.toml
test -f .gitignore
test -f .github/workflows/ci.yml
test -f .github/workflows/release.yml
test -f uv.lock
test ! -e LICENSE
rg -n '^license = \{ text = "Proprietary" \}$' pyproject.toml
if rg -n --pcre2 '^[[:space:]]*uses:[[:space:]]+[^ ]+@(?![0-9a-f]{40}([[:space:]]|$))' .github/workflows; then
  echo "un-pinned GitHub Action reference detected" >&2
  exit 1
fi
scripts/sync-adapters --check
scripts/verify
```

Expected:

- The empty-placeholder checks exit 0 and print nothing.
- The license check prints the proprietary metadata line.
- The unpinned-action check prints nothing and exits 0.
- Projection drift is absent and the full verification gate passes. The last
  recorded full gate was 123 passed and 1 intentional skip; the actual Phase B
  result is authoritative.

Do not print suspected credentials while checking for accidental disclosure.
Review filenames and common secret-bearing file types only:

```sh
rg --files --hidden \
  -g '!dist/repo/**' \
  -g '!*.example' \
  -g '*.pem' -g '*.key' -g '*.p12' -g '*.pfx' \
  -g '.env' -g '.env.*' -g '*credentials*' -g '*secret*'
```

Expected: no unexplained sensitive file. If anything is listed, inspect it
locally without echoing secret values and stop until it is removed or proven to
be a safe fixture.

Rationale and source:

- Public visibility makes code, history, Actions logs, and forks broadly
  visible; inspect before the first push because later deletion does not erase
  copied data. See GitHub's [repository visibility guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility).
- A public repository is not automatically open source. Without a license,
  default copyright applies, although GitHub users may view and fork public
  code under the Terms of Service. Preserve the declared `Proprietary` status
  until the owner makes a deliberate legal choice. See [Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

### 2.2 Add governance files before the first commit

Apply this exact patch. It never touches `dist/repo/`.

```diff
*** Begin Patch
*** Add File: .github/CODEOWNERS
+* @w7-mgfcode
+/.github/ @w7-mgfcode
+/skills/ @w7-mgfcode
+/src/ @w7-mgfcode
+/scripts/ @w7-mgfcode
*** Add File: .github/ISSUE_TEMPLATE/config.yml
+blank_issues_enabled: false
+contact_links:
+  - name: Report a security vulnerability privately
+    url: https://github.com/w7-mgfcode/polymind-constellation/security/advisories/new
+    about: Do not disclose vulnerabilities, credentials, or private transcripts publicly.
*** Add File: .github/ISSUE_TEMPLATE/bug_report.yml
+name: Bug report
+description: Report a reproducible defect in Polymind Constellation.
+title: "[Bug]: "
+labels:
+  - bug
+body:
+  - type: markdown
+    attributes:
+      value: Do not report security vulnerabilities here. Use the private security link.
+  - type: input
+    id: version
+    attributes:
+      label: Polymind version or commit
+      placeholder: 0.8.1 or a full commit SHA
+    validations:
+      required: true
+  - type: dropdown
+    id: operation
+    attributes:
+      label: Operation
+      options:
+        - validate
+        - projection sync
+        - catalog or activation
+        - conformance
+        - downstream install
+        - release verification
+        - other
+    validations:
+      required: true
+  - type: textarea
+    id: reproduction
+    attributes:
+      label: Minimal reproduction
+      description: Include commands, sanitized inputs, and the smallest reproducible case.
+    validations:
+      required: true
+  - type: textarea
+    id: expected
+    attributes:
+      label: Expected behavior
+    validations:
+      required: true
+  - type: textarea
+    id: actual
+    attributes:
+      label: Actual behavior and diagnostics
+      description: Remove credentials, absolute source-machine paths, and private transcripts.
+    validations:
+      required: true
+  - type: checkboxes
+    id: checks
+    attributes:
+      label: Verification
+      options:
+        - label: I searched for an existing issue and ran the applicable validation command.
+          required: true
*** Add File: .github/ISSUE_TEMPLATE/feature_request.yml
+name: Feature request
+description: Propose a bounded, provider-neutral improvement.
+title: "[Feature]: "
+labels:
+  - enhancement
+body:
+  - type: textarea
+    id: problem
+    attributes:
+      label: Problem or use case
+    validations:
+      required: true
+  - type: textarea
+    id: proposal
+    attributes:
+      label: Proposed behavior
+    validations:
+      required: true
+  - type: textarea
+    id: alternatives
+    attributes:
+      label: Alternatives considered
+    validations:
+      required: true
+  - type: textarea
+    id: safety
+    attributes:
+      label: Capability, permission, compatibility, and migration impact
+      description: State whether the proposal changes any approval or trust boundary.
+    validations:
+      required: true
*** Add File: .github/PULL_REQUEST_TEMPLATE.md
+## Summary
+
+Describe the problem and the smallest coherent change.
+
+## Safety and compatibility
+
+- Canonical behavior or capability change:
+- Provider compatibility evidence changed:
+- Semantic-version impact:
+- Generated projection impact:
+
+## Verification
+
+- [ ] I edited canonical skills only under `skills/`.
+- [ ] I did not hand-edit generated content under `dist/repo/`.
+- [ ] I ran `scripts/sync-adapters --dry-run` when projections could change.
+- [ ] I ran `scripts/verify` and reported intentional skips separately.
+- [ ] I added tests for validator or behavior changes and preserved diagnostic codes.
+- [ ] I removed credentials, source-machine paths, and private transcripts.
*** Add File: SECURITY.md
+# Security policy
+
+Polymind Constellation has no published, supported release yet. Version 0.8.1
+is locally validated but remains unpublished and must not be treated as a
+released package until the release blockers in `HANDOFF.md` are cleared.
+
+Report suspected vulnerabilities through GitHub private vulnerability
+reporting:
+
+https://github.com/w7-mgfcode/polymind-constellation/security/advisories/new
+
+Do not open a public issue for a vulnerability. Do not include credentials,
+private model transcripts, or unrelated personal data. Include the affected
+commit or version, impact, minimal reproduction, and suggested mitigation when
+available. The maintainer will coordinate disclosure after validation and a
+fix; no response-time SLA is promised.
+
+The detailed trust boundaries, installer safety model, provider-claim limits,
+and release-provenance requirements are documented in
+[`docs/security.md`](docs/security.md). Generated projections under
+`dist/repo/` are artifacts; report the canonical source under `skills/` or the
+implementation under `src/polymind/` when one exists.
*** Add File: .github/rulesets/main.json
+{
+  "name": "main-protection",
+  "target": "branch",
+  "enforcement": "active",
+  "bypass_actors": [
+    {
+      "actor_id": 168316277,
+      "actor_type": "User",
+      "bypass_mode": "pull_request"
+    }
+  ],
+  "conditions": {
+    "ref_name": {
+      "include": ["~DEFAULT_BRANCH"],
+      "exclude": []
+    }
+  },
+  "rules": [
+    {"type": "deletion"},
+    {"type": "non_fast_forward"},
+    {"type": "required_linear_history"},
+    {
+      "type": "pull_request",
+      "parameters": {
+        "allowed_merge_methods": ["squash"],
+        "dismiss_stale_reviews_on_push": true,
+        "require_code_owner_review": true,
+        "require_last_push_approval": true,
+        "required_approving_review_count": 1,
+        "required_review_thread_resolution": true
+      }
+    },
+    {
+      "type": "required_status_checks",
+      "parameters": {
+        "do_not_enforce_on_create": false,
+        "required_status_checks": [
+          {"context": "verify"}
+        ],
+        "strict_required_status_checks_policy": true
+      }
+    }
+  ]
+}
*** Update File: .gitignore
@@
 .venv/
+.env
+.env.*
+!.env.example
 .mypy_cache/
*** Update File: .github/workflows/ci.yml
@@
 on:
   pull_request:
-  push:
+  push:
+    branches:
+      - main
*** Update File: .github/dependabot.yml
@@
 version: 2
 updates:
+  - package-ecosystem: uv
+    directory: "/"
+    schedule:
+      interval: weekly
+    open-pull-requests-limit: 5
   - package-ecosystem: github-actions
     directory: "/"
     schedule:
       interval: monthly
*** Update File: docs/security.md
@@
-This self-contained owner-authored repository has no public security contact or
-remote release channel configured. Until one is established, report findings to
-the repository owner through the private channel used to distribute the source.
-Do not include secrets, credentials, or private model transcripts in a report.
+Report findings through GitHub private vulnerability reporting as described in
+the repository [`SECURITY.md`](../SECURITY.md). Do not open a public issue or
+include secrets, credentials, or private model transcripts in a report.
*** End Patch
```

Expected: the patch applies cleanly; `git diff --check` later prints nothing.

Re-run the complete repository gate after applying the governance patch:

```sh
scripts/verify
```

Expected: exit 0. Stop if the CI-trigger, Dependabot, security documentation,
or any other repository test rejects the proposed state.

Policy notes:

- `CODEOWNERS` is placed in `.github/`, assigns the owner to the whole tree, and
  explicitly protects `.github/` itself. Code owners must have write access.
  Source: [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners).
- Structured issue forms and a PR template elicit reproducible evidence and
  route security reports away from public issues. Sources: [issue and pull
  request templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates)
  and [issue-form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms).
- `SECURITY.md` gives a public disclosure policy while reusing the existing
  detailed security model. Source: [Adding a security policy](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/add-security-policy).
- Local environment files are ignored while an intentionally sanitized
  `.env.example` may be committed; ignore rules reduce accidental staging but
  never replace secret scanning. Source: [Ignoring files](https://docs.github.com/en/get-started/getting-started-with-git/ignoring-files).
- CI runs on pull requests and pushes to `main`, avoiding duplicate same-named
  `verify` jobs for ordinary same-repository PR branches while retaining a
  post-merge/default-branch signal. GitHub warns that job names used as required
  checks should be unique. Source: [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
- Dependabot now supports `package-ecosystem: uv`; retain the existing Actions
  monitoring and add weekly Python lock/manifest updates. Sources: [Dependabot
  configuration](https://docs.github.com/en/code-security/concepts/supply-chain-security/about-the-dependabot-yml-file)
  and GitHub's [uv support announcement](https://github.blog/changelog/2025-03-13-dependabot-version-updates-now-support-uv-in-general-availability/).

Licensing decision: do not add a `LICENSE` during this run. The project is
explicitly proprietary, and choosing Apache-2.0, MIT, GPL, or another license is
a legal/product decision outside an infrastructure setup. The GitHub community
profile will therefore correctly show the license item as incomplete. If the
owner chooses a license later, update `pyproject.toml`, add the exact license
text, and review contribution terms together.

## 3. Initialize Git and make the first commit

The placeholder removal is destructive but narrowly scoped and preflighted in
section 2. It must be empty before removal.

```sh
rmdir .git
git init -b main
git config --local user.name "Gabor Szabo"
git config --local user.email "shellsnake@icloud.com"
git config --local user.useConfigOnly true
git status --short
git add --all
git add -f dist/.gitignore dist/repo
git diff --cached --check -- \
  .github .gitignore SECURITY.md REPOSITORY-SETUP.md docs/security.md
git status --short
git -c commit.gpgsign=false commit \
  --author="Gabor Szabo <shellsnake@icloud.com>" \
  -m "chore: establish Polymind Constellation repository"
git branch --show-current
git log -1 --format='%H%n%an <%ae>%n%cn <%ce>%n%s'
git status --short
```

Expected:

- `rmdir` prints nothing and removes only the verified-empty placeholder.
- `git init` reports an empty Git repository initialized on `main`.
- Before `git add`, all project files are untracked; after it, the normal source
  tree is staged. The nested `dist/.gitignore` (`*`) intentionally leaves
  `dist/` ignored.
- `git add -f dist/.gitignore dist/repo` explicitly stages the validated
  projection required by the package build and verification gate.
- The scoped `git diff --cached --check` prints nothing for the governance files
  authored during repository setup.
- The commit is created on `main`; author and committer are both
  `Gabor Szabo <shellsnake@icloud.com>`.
- Final `git status --short` is empty.

`git diff --check` is a generic Git hygiene heuristic, not this project's
validation contract. The initial import contains intentional Markdown hard line
breaks, deliberately malformed validator fixtures, projection-locked byte
copies, and harmless inherited end-of-file blank lines. Do not normalize those
bytes: doing so can invalidate fixtures or cause projection drift. The
authoritative, stronger project gate is `scripts/verify`; the scoped Git check
above governs only the repository-governance files authored in this setup.

The one-command signing override is intentional only for this bootstrap commit:
the exact Gitsign identity and issuer are still unknown. Do not enable the
`required_signatures` ruleset rule until a real signed non-release commit has
been pushed and verified. GitHub's signed-commit rule checks verified
signatures, and enabling it prematurely would turn an unresolved release
identity into a repository availability problem. Source: [ruleset signed
commits](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#require-signed-commits).

## 4. Create the public GitHub repository and push `main`

Reconfirm the irreversible target immediately before creation:

```sh
gh api user --jq .login
gh api repos/w7-mgfcode/polymind-constellation
```

Expected: `w7-mgfcode`, followed by HTTP 404. Any other result is a stop.

Create the public repository without a server-generated README, license, or
`.gitignore`, then push separately so failures remain attributable:

```sh
gh repo create w7-mgfcode/polymind-constellation \
  --public \
  --source=. \
  --remote=origin \
  --description="Provider-neutral Agent Skills compiler, validator, projection generator, and safe downstream installer." \
  --disable-wiki
git remote -v
git push --set-upstream origin main
```

Expected:

- `gh repo create` prints
  `https://github.com/w7-mgfcode/polymind-constellation`.
- `git remote -v` shows HTTPS fetch and push URLs for that exact repository.
- Push creates `main`, uploads the initial commit, and sets upstream tracking.
- The push triggers CI only. It does not match release.yml's `v*.*.*` tag
  trigger.

Rationale and source:

- Separate creation from push to preserve a clear stop boundary around the
  public exposure and upload. CLI syntax is documented by
  [`gh repo create`](https://cli.github.com/manual/gh_repo_create).
- Do not ask GitHub to generate bootstrap files because the authoritative local
  tree already contains README, ignore rules, workflows, and proprietary
  package metadata.

Wait for the initial CI result before requiring the check:

```sh
gh run list \
  --repo w7-mgfcode/polymind-constellation \
  --workflow CI \
  --branch main \
  --limit 1 \
  --json databaseId,status,conclusion,headSha,url
CI_RUN_ID="$(gh run list --repo w7-mgfcode/polymind-constellation --workflow CI --branch main --limit 1 --json databaseId --jq '.[0].databaseId')"
test -n "$CI_RUN_ID"
gh run watch "$CI_RUN_ID" --repo w7-mgfcode/polymind-constellation --exit-status
gh run view "$CI_RUN_ID" --repo w7-mgfcode/polymind-constellation --json jobs --jq '.jobs[] | {name,conclusion}'
```

Expected: the run concludes `success`, and the jobs output contains
`{"name":"verify","conclusion":"success"}`. GitHub requires a status check to
have completed successfully in the repository during the previous seven days
before it can be selected reliably as required. Source: [Troubleshooting
required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks).

## 5. About metadata

There is no independent project website or published PyPI page yet. Point the
About website field at the maintained architecture document rather than a dead
or speculative URL.

```sh
gh repo edit w7-mgfcode/polymind-constellation \
  --description="Provider-neutral Agent Skills compiler, validator, projection generator, and safe downstream installer." \
  --homepage="https://github.com/w7-mgfcode/polymind-constellation/blob/main/docs/architecture.md"
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/topics \
  -f 'names[]=python' \
  -f 'names[]=agent-skills' \
  -f 'names[]=ai-agents' \
  -f 'names[]=developer-tools' \
  -f 'names[]=cli' \
  -f 'names[]=security' \
  -f 'names[]=supply-chain' \
  -f 'names[]=sigstore' \
  -f 'names[]=slsa' \
  -f 'names[]=github-actions'
```

Expected:

- `gh repo edit` is silent on success.
- The topics request returns a `names` array containing exactly the ten topics.

Rationale and source:

- A concise description, valid website, and bounded discoverability topics make
  the repository understandable without overstating publication status.
  GitHub topics are public, lower-case, limited to 20, and limited to 50
  characters each. Source: [Classifying a repository with topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics).

## 6. Repository settings and merge policy

Use squash-only merging and delete merged branches. Keep Issues and pull
requests enabled; keep Discussions, wiki, Projects, and auto-merge disabled at
bootstrap so policy and support information have one maintained home.

```sh
gh repo edit w7-mgfcode/polymind-constellation \
  --enable-issues=true \
  --enable-discussions=false \
  --enable-projects=false \
  --enable-wiki=false \
  --enable-squash-merge=true \
  --enable-merge-commit=false \
  --enable-rebase-merge=false \
  --enable-auto-merge=false \
  --delete-branch-on-merge=true \
  --allow-update-branch=true
gh api --method PATCH \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation \
  -F has_pull_requests=true \
  -f squash_merge_commit_title=PR_TITLE \
  -f squash_merge_commit_message=PR_BODY
```

Expected: the CLI is silent; the API returns the repository object with Issues
and pull requests enabled, disabled Discussions/wiki/Projects, squash enabled,
merge/rebase disabled, and `delete_branch_on_merge: true`.

Rationale and source:

- Squash-only merging plus the ruleset's linear-history rule produces one
  reviewable commit per PR and prevents merge commits. Linear history requires
  squash or rebase to remain enabled. Sources: [About merge methods](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github)
  and [available rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets#require-linear-history).
- Automatic branch deletion reduces stale branches after successful review.
  Source: [Managing automatic deletion of branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches).
- Issues remain the single public work/support channel; other collaboration
  surfaces can be enabled later when there is an owner and moderation policy.
  Repository feature fields are documented by the [Repositories REST API](https://docs.github.com/en/rest/repos/repos?apiVersion=2026-03-10).

## 7. Actions security

Allow only GitHub-owned actions and the two third-party action publishers used
by the checked-in workflows. Require every action reference to be a full SHA,
make the repository default `GITHUB_TOKEN` read-only, prevent Actions from
approving PRs, and require approval before workflows from any external fork run.

```sh
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/actions/permissions \
  -F enabled=true \
  -f allowed_actions=selected \
  -F sha_pinning_required=true
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/actions/permissions/selected-actions \
  -F github_owned_allowed=true \
  -F verified_allowed=false \
  -f 'patterns_allowed[]=astral-sh/setup-uv@*' \
  -f 'patterns_allowed[]=pypa/gh-action-pypi-publish@*'
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/actions/permissions/workflow \
  -f default_workflow_permissions=read \
  -F can_approve_pull_request_reviews=false
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/actions/permissions/fork-pr-contributor-approval \
  -f approval_policy=all_external_contributors
```

Expected: each PUT returns HTTP 204 and no response body.

Rationale and source:

- A read-only default token and explicit job-level escalation implement least
  privilege. CI already declares only `contents: read`; release grants OIDC,
  attestation, and release-write permissions only to the jobs that need them.
  Source: [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use#use-credentials-that-are-minimally-scoped).
- A full commit SHA is the only immutable action reference. The checked-in
  workflows already comply, and the platform setting makes regressions fail
  closed. Source: [Secure use reference—pin actions](https://docs.github.com/en/actions/reference/security/secure-use#using-third-party-actions).
- The allowlist permits `actions/*` (including checkout, setup-python,
  artifacts, and attest), `astral-sh/setup-uv`, and
  `pypa/gh-action-pypi-publish`; it does not trust all Marketplace-verified
  publishers. API behavior and public-repository patterns are documented in
  [Actions permissions REST API](https://docs.github.com/en/rest/actions/permissions?apiVersion=2026-03-10).
- External fork workflows require maintainer approval and receive no default
  write permission. Source: [Managing Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).
- OIDC avoids a long-lived PyPI credential, but the workflow itself remains
  trusted code and must be protected. Sources: [OIDC in PyPI](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-pypi)
  and [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/).

Recommended follow-up: integrate
[`actionlint`](https://github.com/rhysd/actionlint) into `scripts/verify` and CI
after selecting a version and verifying its release checksum. It detects
workflow schema/expression errors and common script-injection mistakes. Do not
add a floating action tag or unverified binary merely to satisfy this
recommendation.

## 8. Security and quality controls

### 8.1 Dependency graph and Dependabot

```sh
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/vulnerability-alerts
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/automated-security-fixes
```

Expected: each command returns HTTP 204 with no body.

Rationale and source:

- The dependency graph is enabled by default and cannot be disabled for public
  repositories; Dependabot alerts and security updates are not enabled by
  default and should be turned on. Source: [Supply chain security—feature
  availability](https://docs.github.com/en/code-security/concepts/supply-chain-security/supply-chain-security#feature-availability).
- Version updates from `.github/dependabot.yml` and vulnerability-triggered
  security updates are distinct controls; enable both. Source: [Dependabot
  security updates](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-security-updates).

After the first dependency scan, inspect Insights > Dependency graph. If
`uv.lock` is not represented, treat that as an assumption failure and add a
reviewed dependency-submission workflow; do not claim full transitive alert
coverage merely because uv version-update PRs work. GitHub documents supported
graph manifests and its dependency-submission API separately: [dependency
graph ecosystems](https://docs.github.com/en/code-security/reference/supply-chain-security/dependency-graph-supported-package-ecosystems)
and [dependency submission](https://docs.github.com/en/rest/dependency-graph/dependency-submission?apiVersion=2026-03-10).

### 8.2 Secret scanning and push protection

```sh
gh api --method PATCH \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation \
  -f 'security_and_analysis[secret_scanning][status]=enabled' \
  -f 'security_and_analysis[secret_scanning_push_protection][status]=enabled'
```

Expected: the returned `security_and_analysis` object reports both statuses as
`enabled`. If GitHub rejects repository-level push protection for the current
personal-account plan, stop and report the response; do not call user-level
push protection equivalent. User push protection remains useful but does not
create the same repository alerts on bypass.

Rationale and source:

- Secret scanning runs automatically for public repositories for free; enable
  repository alerts explicitly and verify them. Source: [Enabling secret
  scanning](https://docs.github.com/en/code-security/how-tos/secure-your-secrets/detect-secret-leaks/enable-secret-scanning).
- Repository push protection blocks supported credentials before they enter
  history and records bypasses; user push protection is on by default for
  public pushes but has different alert behavior. Availability can vary with
  Secret Protection and plan, so the API result is authoritative. Source:
  [Push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection).

### 8.3 Private vulnerability reporting and Security tab

```sh
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/private-vulnerability-reporting
```

Expected: HTTP 204 with no body. The Security tab then exposes private
reporting alongside `SECURITY.md`.

Rationale and source:

- Private reporting lets researchers disclose a public repository's
  vulnerabilities without a public issue. Source: [Configuring private
  vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configuring-private-vulnerability-reporting-for-a-repository).

### 8.4 CodeQL default setup

Use GitHub-managed default setup with the extended query suite for Python and
Actions. The local-source threat model is currently relevant only to supported
Java/C# analysis, so retain `remote` here.

```sh
gh api --method PATCH \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/code-scanning/default-setup \
  -f state=configured \
  -f runner_type=standard \
  -f query_suite=extended \
  -f threat_model=remote \
  -f 'languages[]=python' \
  -f 'languages[]=actions'
```

Expected: HTTP 200 or 202. A 202 response includes `run_id` and `run_url`.
Wait for the initial CodeQL analysis and require it to succeed before later
adding a ruleset `code_scanning` merge gate.

Rationale and source:

- Code scanning is available for public GitHub.com repositories without a paid
  Code Security license; private organization repositories require an
  applicable plan/license. GitHub recommends starting with default setup.
  Source: [Configure code scanning](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/configure-code-scanning).
- Default setup tracks supported languages and runs on default/protected-branch
  pushes, pull requests, and a weekly schedule. Source: [Code scanning setup
  types](https://docs.github.com/en/code-security/concepts/code-scanning/setup-types).
- The exact supported API values are documented by [Code scanning REST API](https://docs.github.com/en/rest/code-scanning/code-scanning?apiVersion=2026-03-10).

Public-repository distinction: CodeQL/code scanning, public secret scanning,
dependency review, and artifact attestations are available for public
repositories. Equivalent controls for private/internal repositories may need
GitHub Code Security, Secret Protection, Advanced Security, Team, or Enterprise
entitlements. Public Sigstore/SLSA attestations are recorded through the public
Sigstore transparency infrastructure, so provenance identities and artifact
metadata are public. Source: [Artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations).

## 9. Protect `main` with a repository ruleset

Use a ruleset rather than also creating classic branch protection. Rulesets are
available for public personal repositories on GitHub Free, can layer multiple
policies, expose status/audit information to readers, and coexist with classic
rules. Adding both here would create two policy sources whose most restrictive
combination wins.

Only apply the ruleset after the initial `verify` check succeeded:

```sh
gh api --method POST \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/rulesets \
  --input .github/rulesets/main.json \
  --jq '{id,name,enforcement,target,bypass_actors,rules}'
```

Expected: HTTP 201 and an object named `main-protection`, target `branch`,
enforcement `active`, with the PR-only `w7-mgfcode` bypass and five rules.

Effective policy:

- all changes enter `main` through a PR;
- one approval and a code-owner approval are required;
- stale approvals are dismissed and the last push needs another approver;
- review threads must be resolved;
- `verify` must pass on a branch up to date with `main`;
- only squash is accepted and history must stay linear;
- branch deletion and force pushes are blocked;
- no blanket administrator/repository-role bypass exists.

Solo-maintainer exception: pull-request authors cannot approve their own PRs.
Because `w7-mgfcode` is currently the only maintainer, the ruleset grants that
specific user a `pull_request`-only bypass. This does not permit direct pushes;
it permits a deliberate ruleset bypass while merging a PR, which GitHub records
in rule insights. Once a second trusted write collaborator can provide real
review, add that collaborator to the relevant `CODEOWNERS` patterns and then
remove `bypass_actors` entirely. This is weaker than true two-person control and
must not be described otherwise.

Rationale and source:

- Rulesets offer layering, enforcement status, public visibility, and audit
  insight not provided as cleanly by classic protection. Source: [About
  rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets).
- PR reviews, code owners, current status checks, linear history, deletion
  protection, and force-push blocking prevent unreviewed or history-rewriting
  changes. Source: [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).
- The REST schema permits `User` bypass actors on personal repositories and a
  `pull_request` bypass mode for branch rulesets. Source: [Rules REST API](https://docs.github.com/en/rest/repos/rules?apiVersion=2026-03-10).
- GitHub explicitly states that PR authors cannot approve their own PRs.
  Source: [Approving a pull request with required reviews](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews).

Signed commits are deferred, not rejected. After configuring Gitsign, push a
non-release test commit through a PR, verify the exact identity and issuer with
`gitsign verify`, and confirm GitHub itself marks that signature `Verified`.
Whether GitHub's `required_signatures` rule accepts the chosen Gitsign signature
format is an assumption to confirm, not a fact established by local Gitsign
verification. Only after that live test should the maintainer add
`{"type":"required_signatures"}` to the stored ruleset JSON and PUT the complete
ruleset to `/repos/w7-mgfcode/polymind-constellation/rulesets/ID`.

## 10. Insights and community standards

The initial commit supplies README, CONTRIBUTING, SECURITY, CODEOWNERS, issue
forms, and a PR template. Verify how GitHub parsed them:

```sh
gh api \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/community/profile
gh api \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation/codeowners/errors
```

Expected:

- Community profile reports README, CONTRIBUTING, SECURITY, issue template,
  and pull request template URLs.
- License remains absent by deliberate proprietary-policy decision, so do not
  expect a 100% health score.
- CODEOWNERS `errors` is empty.

The community checklist also recommends a code of conduct and a license. Do not
insert either boilerplate blindly: moderation/enforcement capacity must back a
code of conduct, and a license must match the intended proprietary or
open-source distribution model. Source: [Community profiles for public
repositories](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories).

## 11. Releases and semantic version tags

GitHub Releases are based on Git tags. Framework tags must be exact SemVer tags
of the form `vMAJOR.MINOR.PATCH` and must correspond to the version in
`pyproject.toml`, `polymind.__version__`, `uv.lock`, generated locks, and the
changelog. Sources: [About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
and [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

The checked-in `release.yml` triggers only on pushed tags matching `v*.*.*`.
It verifies source, builds one wheel and one sdist, generates evidence, creates
GitHub/Sigstore SLSA attestations, publishes with PyPI OIDC, and creates the
GitHub Release only after PyPI succeeds.

> **WARNING — OUT OF SCOPE:** Do not run `git tag v0.8.1`, do not push any
> version tag, do not run `gh release create`, and do not publish to PyPI in
> this repository-setup session.

Before any future release:

1. Implement and test recovery when PyPI publication succeeds but a later job
   fails; PyPI artifacts are immutable.
2. Configure and verify exact `RELEASE_COMMIT_IDENTITY` and
   `RELEASE_COMMIT_OIDC_ISSUER` repository variables.
3. Create the protected `pypi` environment and exact PyPI Trusted Publisher
   mapping for owner `w7-mgfcode`, repository `polymind-constellation`, workflow
   `release.yml`, environment `pypi`.
4. Produce and verify a genuine Gitsign-signed release commit.
5. Adapt the GitHub Release job to create a draft, attach every asset, and then
   publish it; only then enable immutable releases:

   ```sh
   gh api --method PUT \
     -H "Accept: application/vnd.github+json" \
     -H "X-GitHub-Api-Version: 2026-03-10" \
     repos/w7-mgfcode/polymind-constellation/immutable-releases
   ```

Immutable releases lock the release tag/assets and generate a release
attestation; GitHub recommends draft → attach all assets → publish. This is a
future hardening step, not a Phase B command, because the current direct-create
workflow and partial-release recovery need to be reconciled first. Source:
[Immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases).

Public-repository attestations use the Sigstore Public Good Instance and public
transparency log; the resulting repository/workflow identities are public.
Attestation proves build provenance, not that an artifact is vulnerability-free.
Source: [Using artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations).

## 12. Final verification checklist

All commands below are GET/read-only. Run every item after Phase B mutations.

### Identity, repository, remote, and branch

```sh
gh api user --jq '{login,name,type}'
git remote -v
git branch --show-current
git status --short
git log -1 --format='%H%n%an <%ae>%n%cn <%ce>%n%s'
gh api \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  repos/w7-mgfcode/polymind-constellation \
  --jq '{full_name,visibility,default_branch,description,homepage,has_issues,has_discussions,has_projects,has_wiki,has_pull_requests,allow_squash_merge,allow_merge_commit,allow_rebase_merge,allow_auto_merge,delete_branch_on_merge,security_and_analysis}'
```

Expected: correct identity; clean `main`; exact public repository; squash only;
intended feature toggles; security statuses enabled.

### Topics, rules, CODEOWNERS, and community profile

```sh
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/topics
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/rulesets
RULESET_ID="$(gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/rulesets --jq '.[] | select(.name == "main-protection") | .id')"
test -n "$RULESET_ID"
gh api -H "X-GitHub-Api-Version: 2026-03-10" "repos/w7-mgfcode/polymind-constellation/rulesets/$RULESET_ID"
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/codeowners/errors
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/community/profile
```

Expected: exact topics; one active `main-protection` branch ruleset; no
CODEOWNERS errors; intended community files recognized.

### Actions permissions

```sh
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/actions/permissions
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/actions/permissions/selected-actions
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/actions/permissions/workflow
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/actions/permissions/fork-pr-contributor-approval
```

Expected: Actions enabled; `allowed_actions: selected`; SHA pinning true;
GitHub-owned plus the two named patterns only; default token `read`; workflow
PR approval false; fork approval `all_external_contributors`.

### Dependency, vulnerability, secret, and code scanning controls

```sh
gh api --include -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/vulnerability-alerts
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/automated-security-fixes
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/private-vulnerability-reporting
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/code-scanning/default-setup
gh api -H "X-GitHub-Api-Version: 2026-03-10" 'repos/w7-mgfcode/polymind-constellation/code-scanning/analyses?per_page=5'
gh api -H "X-GitHub-Api-Version: 2026-03-10" 'repos/w7-mgfcode/polymind-constellation/secret-scanning/alerts?state=open&per_page=100'
```

Expected: vulnerability-alert GET returns HTTP 204; security updates and
private reporting are enabled; CodeQL state is configured for Python and
Actions and has a successful analysis; no unexplained open secret alert.

### CI and release hold

```sh
gh run list --repo w7-mgfcode/polymind-constellation --workflow CI --branch main --limit 5
gh api -H "X-GitHub-Api-Version: 2026-03-10" repos/w7-mgfcode/polymind-constellation/tags
gh release list --repo w7-mgfcode/polymind-constellation
git tag --list
```

Expected: initial CI is green; GitHub tags, GitHub Releases, and local tags are
all empty. This confirms the `v0.8.1` release hold remains intact.

## Appendix A. Source index

Primary sources used for this runbook:

- GitHub CLI: [`gh auth status`](https://cli.github.com/manual/gh_auth_status),
  [`gh repo create`](https://cli.github.com/manual/gh_repo_create)
- Repository administration: [Repositories REST API](https://docs.github.com/en/rest/repos/repos?apiVersion=2026-03-10),
  [visibility](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility),
  [topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics),
  [licensing](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository),
  [ignoring files](https://docs.github.com/en/get-started/getting-started-with-git/ignoring-files)
- Merge and branch policy: [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets),
  [available rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets),
  [Rules REST API](https://docs.github.com/en/rest/repos/rules?apiVersion=2026-03-10),
  [classic protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches),
  [required-check troubleshooting](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks),
  [required reviews](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews),
  [merge methods](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github),
  [automatic branch deletion](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-the-automatic-deletion-of-branches)
- Ownership and community: [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners),
  [community profiles](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories),
  [issue and PR templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates),
  [issue form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms),
  [security policy](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/add-security-policy),
  [private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configuring-private-vulnerability-reporting-for-a-repository)
- Actions hardening: [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use),
  [repository Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository),
  [Actions permissions REST API](https://docs.github.com/en/rest/actions/permissions?apiVersion=2026-03-10),
  [OIDC in PyPI](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-pypi),
  [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/),
  [PyPI Trusted Publisher security model](https://docs.pypi.org/trusted-publishers/security-model/),
  [actionlint](https://github.com/rhysd/actionlint)
- Dependency security: [supply chain security](https://docs.github.com/en/code-security/concepts/supply-chain-security/supply-chain-security),
  [dependency graph](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph),
  [dependency graph ecosystems](https://docs.github.com/en/code-security/reference/supply-chain-security/dependency-graph-supported-package-ecosystems),
  [dependency submission API](https://docs.github.com/en/rest/dependency-graph/dependency-submission?apiVersion=2026-03-10),
  [Dependabot configuration](https://docs.github.com/en/code-security/concepts/supply-chain-security/about-the-dependabot-yml-file),
  [Dependabot security updates](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-security-updates),
  [Dependabot uv support](https://github.blog/changelog/2025-03-13-dependabot-version-updates-now-support-uv-in-general-availability/)
- Secret and code scanning: [secret scanning](https://docs.github.com/en/code-security/how-tos/secure-your-secrets/detect-secret-leaks/enable-secret-scanning),
  [push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection),
  [configure code scanning](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/configure-code-scanning),
  [setup types](https://docs.github.com/en/code-security/concepts/code-scanning/setup-types),
  [Code scanning REST API](https://docs.github.com/en/rest/code-scanning/code-scanning?apiVersion=2026-03-10)
- Releases and provenance: [About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases),
  [immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases),
  [artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations),
  [using attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations),
  [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html)
- Git identity: [git-config](https://git-scm.com/docs/git-config)

## Appendix B. Phase B stop conditions

Stop immediately and report the command and its exact output if any of these
occurs:

- active GitHub login is not `w7-mgfcode`;
- the target repository exists before creation;
- `.git/` is not empty before `rmdir`;
- the source validation or `scripts/verify` fails;
- any suspicious secret-bearing file is unresolved;
- initial CI or CodeQL fails;
- an API mutation returns anything other than its documented success status;
- GitHub rejects a feature because of account/plan availability;
- ruleset payload, owner actor ID, or check context differs from the verified
  values in this runbook;
- any command would create a tag, release, publication, token, or secret.
