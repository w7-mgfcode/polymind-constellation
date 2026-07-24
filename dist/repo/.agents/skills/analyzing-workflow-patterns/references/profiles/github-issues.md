# GitHub issue-decomposition profile

## Prerequisites

- GitHub Issues is the selected tracker.
- Repository and issue permissions are known.
- Any remote read or mutation receives the required authorization.

## Selection

Use this profile only when the workflow maps work into GitHub issues,
sub-issues, labels, milestones, Projects, or pull requests.

## Behavior

Map generic entities to umbrella issues, child issues, dependency links, labels,
milestones, or project fields only after inspecting existing conventions. Keep
commands and API examples as proposals until approved. Separate planning object
creation from code changes.

## Validation

- Dry-run or list intended issue operations before mutation.
- Validate repository owner, issue IDs, labels, and field identifiers from live
  read-only evidence.
- Define unlink/close/reopen rollback operations before creation.
- Confirm the core hard stop remains in force.
