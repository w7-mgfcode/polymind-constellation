---
name: inspecting-skill-packages
description: >-
  Inspect canonical Agent Skills packages for metadata, capability, reference,
  and package-boundary problems. Use when validating hand-authored skills under
  skills/; do not use to generate provider projections or execute skill tools.
license: Proprietary
metadata:
  polymind.version: "1.0.0"
  polymind.tags: "agent-skills,validation,package-quality"
  polymind.risk: "read-only"
---

# Inspect Skill Packages

Validate canonical packages before they enter a provider projection.

1. Discover packages only under the repository's `skills/` directory.
2. Run `uv run polymind validate skills`.
3. Separate specification, Polymind policy, and security diagnostics.
4. Correct canonical sources rather than editing generated provider trees.
5. Run `scripts/verify` before reporting completion.

Treat unknown capabilities, path escapes, and provider-specific permission
fields as failures. Report projection drift as not applicable until the
projection compiler exists.
