# No-CI profile

## Prerequisites

- The user explicitly deferred continuous integration.
- The risk level permits local-only enforcement.

## Selection

This profile is orthogonal to repository hosting. Record why CI is deferred and
the condition that should trigger reconsideration.

## Behavior

Create no CI files. Still provide a deterministic `scripts/verify` entrypoint
and document that checks are local conventions, not remotely enforced gates.

## Validation

- Run `scripts/verify` from a clean environment.
- Confirm no CI parity or protected-branch claim appears.
- Record the deferral decision in the approved project plan.
