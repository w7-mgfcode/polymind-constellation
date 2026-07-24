---
name: analyzing-workflow-patterns
description: 'Analyzes workflow documents, pasted text, URLs, or repository processes; extracts reusable entities, verbs, boundaries, gates, artifacts, failure paths, and variables; inspects actual repository capabilities; then compares three to five normalized, scored integration flows with validation and rollback before stopping for approval. Use to understand, map, compare, or integrate a workflow design. Do not modify files or external systems before the user selects a flow, and do not assume a language, tracker, provider, or fixed number of variants unless its optional profile is selected.

  '
license: Proprietary
metadata:
  polymind.version: 2.0.0
  polymind.tags: workflow-analysis,repository-planning,portable,decision-support
  polymind.risk: read-only-until-approval
allowed-tools: Read Grep Glob WebFetch WebSearch
---

# Analyzing Workflow Patterns

Turn source material into evidence-backed integration choices. Understand the
workflow before recommending changes and stop before every mutation.

## Core protocol

1. Acquire every named source. Fetch a URL before interpreting it; identify the
   primary source and report anything unavailable.
2. Classify the material and extract actors, nouns, verbs, states, transitions,
   inputs, outputs, approval gates, failure paths, and reusable variables. Keep
   the abstract pattern separate from example identifiers.
3. Explain the workflow in the user's requested language and give a small and a
   scaled example. Default to the conversation language when none is requested.
4. Normalize the source into concise keyword chains so candidate flows use the
   same vocabulary and can be compared fairly.
5. Inspect the actual repository before designing options. Scan capabilities,
   not fixed provider paths:
   - shared and scoped instruction mechanisms;
   - tracker and planning conventions;
   - build, test, CI, release, and rollback commands;
   - agent, skill, handoff, and automation surfaces;
   - existing artifacts, ownership, and clean-canvas gaps.
6. Compare source needs with repository evidence. Mark every inference as
   `[ASSUMPTION]` and distinguish present, absent, conflicting, and unknown
   capabilities.
7. Generate three flows for a bounded change, four for a cross-cutting change,
   or five for a high-risk or organization-wide change. Each flow must include
   prerequisites, exact artifacts, approval gates, validation, risk, rollback,
   and repo-evidence rationale using
   [flow-definition.md](assets/flow-definition.md).
8. Score every flow with the all-higher-is-better model in
   [scoring.md](references/scoring.md) and render
   [fit-matrix.md](assets/fit-matrix.md). State sensitivity or uncertainty when
   close scores depend on assumptions.
9. Recommend a flow or an explicit combination, explain the decisive trade-off,
   and stop. Do not create files, tracker objects, branches, commits, or remote
   resources until the user chooses a flow and separately approves its mutation
   plan.

## Optional profiles

Load a profile only when the user requests it or repository evidence requires
it. Profiles may add constraints but may not remove the core evidence, approval,
validation, rollback, or hard-stop rules.

- [hungarian.md](references/profiles/hungarian.md) changes the explanation layer.
- [github-issues.md](references/profiles/github-issues.md) adds issue-decomposition output.
- [legacy-five-flow.md](references/profiles/legacy-five-flow.md) preserves the
  source collection's exact eleven-phase, five-variant workflow.

Use [template-variables.md](references/template-variables.md) to resolve generic
tokens. Load [output-quality.md](references/output-quality.md) for difficult
reviews. The legacy [phases.md](references/phases.md) is loaded only by the
legacy-five profile.

## Optional iteration contract

After the decision checkpoint, offer additions or questions only when they can
materially change fit, safety, cost, or validation. Keep them specific and make
clear that answering is optional. Do not append a fixed boilerplate list.
