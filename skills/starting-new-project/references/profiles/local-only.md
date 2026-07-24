# Local-only repository profile

## Prerequisites

- The user selected a repository with no remote host.

## Selection

Use this profile for private experiments, air-gapped work, or projects whose
host decision is intentionally deferred.

## Behavior

Do not create host namespaces, remote URLs, CI configuration, issue templates,
or CODEOWNERS. Keep verification runnable locally and make future host adoption
an explicit later decision.

## Validation

- Confirm the manifest contains no host-only paths.
- Run `scripts/verify` locally.
- Confirm docs do not claim remote enforcement or review gates exist.
