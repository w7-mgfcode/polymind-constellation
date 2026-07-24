# GitHub host profile

## Prerequisites

- The user selected GitHub as the repository host.
- Remote repository creation or mutation has separate authorization.

## Selection

Combine this profile with CI only when GitHub Actions is selected. A GitHub
repository does not require Actions, issue templates, CODEOWNERS, or Projects.

## Behavior

Keep host governance proportional to team size. Add `.github/workflows/ci.yml`,
pull-request templates, CODEOWNERS, issue forms, or dependency automation only
when each item appears in the approved manifest. Pin third-party actions by an
accepted organizational policy and keep the local verification command equal to
the CI entrypoint.

## Validation

- Parse workflow YAML and run the selected workflow linter when available.
- Confirm CI invokes deterministic `scripts/verify`.
- Confirm repository creation, rulesets, secrets, and pushes remain unexecuted
  without separate approval.
