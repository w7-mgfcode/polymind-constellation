# GitLab host profile

## Prerequisites

- The user selected GitLab as the repository host.
- Remote project creation or mutation has separate authorization.

## Selection

Combine this profile with CI only when GitLab CI/CD is selected. Self-managed
instances may impose runner, include, and security policies that override the
generic template.

## Behavior

Add `.gitlab-ci.yml`, CODEOWNERS, merge-request templates, or issue templates
only when approved. Make the pipeline call deterministic `scripts/verify` and
avoid remote includes unless their integrity and update policy are explicit.

## Validation

- Parse YAML and validate the pipeline with the selected instance's CI Lint when
  network access is approved.
- Confirm the local and pipeline entrypoints are identical.
- Confirm project creation, variables, protected branches, and pushes remain
  unexecuted without separate approval.
