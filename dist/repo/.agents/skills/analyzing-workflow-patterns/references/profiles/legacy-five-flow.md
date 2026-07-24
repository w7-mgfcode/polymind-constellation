# Legacy five-flow profile

This profile preserves the original owner-authored workflow for teams that rely
on its exact output shape. It is opt-in, not the portable default.

## Prerequisites

- The user explicitly requests legacy behavior.
- Hungarian output, GitHub-oriented inspection, and exactly five variants are
  appropriate for the task.

## Selection

Load [../phases.md](../phases.md), [../output-quality.md](../output-quality.md),
[../template-variables.md](../template-variables.md), and all three assets.

## Behavior

Run all eleven legacy phases, in order:

| 0 | Material Pre-processing |
| 1 | Deep Workflow Analysis |
| 2 | Hungarian Explanation |
| 3 | Hungarian Examples |
| 4 | English Keyword Flows |
| 5 | Repository Reality Check |
| 6 | Fit Analysis |
| 7 | Brainstorm |
| 8 | Five Recommended Flows |
| 9 | Fit Matrix |
| 10 | Decision Checkpoint |

Generate LIGHTWEIGHT, STANDARD, STRICT, AGENTIC, and GITHUB_NATIVE variants.
Preserve classification, entity/verb extraction, template variables, flow
comparison, assumptions, validation, rollback, and the **Hard stop before
writes**. Interpret old effort fields through the normalized conversion in
[../scoring.md](../scoring.md); higher final values must always be better.

The source workflow's “Possible Additions” block is optional under Polymind.
Include it only when it materially improves the decision.

## Validation

- Confirm phases 0-10 are present and ordered.
- Confirm exactly five named variants are present.
- Confirm repository inspection precedes fit analysis.
- Confirm scoring uses the normalized model.
- Stop for explicit flow selection without mutating files or remote objects.
