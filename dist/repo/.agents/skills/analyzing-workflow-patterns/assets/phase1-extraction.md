# Phase 1 Extraction Table Template

Copyable starter for Phase 1. Each cell has inline guidance (replace with
actual content). See `references/output-quality.md` for good vs. bad examples.

---

## Extraction Table

| Category | Extracted from current material | How to reuse safely | What not to copy blindly | Template variable |
|---|---|---|---|---|
| **Reusable Pattern** | [The structural skeleton that survives any domain change. Describe the hierarchy, transition rules, and phase sequence in 1–3 sentences.] | [Actionable instruction: "Deploy as the standard skeleton for X. Replace Y with domain-specific terms."] | [What breaks if copied literally: "The specific names of phases, counts of tasks per epic, command strings."] | `{{WORKFLOW_TYPE}}`, `{{WORKFLOW_NAME}}` |
| **Example-Specific Details** | [Names, IDs, labels, paths that are specific to the source example and must be discarded: project names, issue numbers, label names, exact command arguments.] | [How to replace: "Map to your repo's label taxonomy and naming conventions."] | [Explicit: "Issue numbers #55–#92, label `knowrag`, command `w7 verify @lab/ll-X`."] | `{{SOURCE_MATERIAL_NAME}}`, `{{REPO_NAME}}` |
| **Template Variables** | [Which `{{VARIABLE}}` tokens are needed to make this workflow repo-agnostic. List all that apply.] | [Map each variable to its resolution source: "Resolve `{{GH_OWNER}}` from `git remote -v`."] | [Don't assume variables have the same value as in the example.] | *(all applicable)* |
| **Hard Rules** | [Non-negotiable constraints stated or implied by the workflow material. E.g., "Foundation epic must close before parallel tracks open."] | [Enforce via tooling or lint scripts. State the check method.] | [Exact character limits, exact token lists, or exact counts if your repo has different standards.] | `{{PHASE_BOUNDARY_RULE}}`, `{{REPO_CONVENTIONS}}` |
| **Approval Gates** | [Human review checkpoints: when they occur, who reviews, what must be true to pass. List each gate named in the material.] | [Keep gate positions but adapt reviewer roles to your team structure.] | [Forcing multi-person live reviews for small, internal, or low-risk changes.] | `{{APPROVAL_GATES}}` |
| **Validation Gates** | [Automated correctness checks: commands, queries, or scripts that verify state before a phase transition is allowed.] | [Ensure a pre-close or continuous compliance check runs the equivalent logic.] | [Running a specific command string that only works in the source environment.] | `{{VALIDATION_COMMANDS}}` |
| **Output Artifacts** | [Concrete outputs: files, GitHub issues/PRs, reports, tags, handoff documents, database entries. Name them with paths or formats.] | [Ensure every execution pipeline drops a verifiable handoff file.] | [Exact directory names like `dogfood-output/<utc>/` unless already in repo conventions.] | `{{OUTPUT_ARTIFACTS}}`, `{{HANDOFF_FORMAT}}` |

---

## Quick Fill Checklist

Before submitting Phase 1 output, verify every cell:

- [ ] "Extracted" column: 1–3 concrete sentences, no vague summaries
- [ ] "How to reuse" column: starts with an action verb (Deploy, Enforce, Map, Replace)
- [ ] "Not to copy" column: contains at least one specific example from the source material
- [ ] "Template variable" column: references a real `{{VARIABLE}}` from `template-variables.md`
- [ ] No cell contains only "N/A" or is left blank
- [ ] Hard Rules row: lists at least 2 distinct constraints
- [ ] Approval Gates and Validation Gates rows are NOT merged or combined

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| "How to reuse: Use this pattern in your repo." | Specify what to keep, what to replace, and how |
| "Not to copy: Example-specific details." | Name the actual examples: project name, label, command |
| Template variable column left blank | Every row maps to at least one `{{VARIABLE}}` |
| Hard Rules = one row says "Follow best practices" | Extract actual stated constraints from the material |
| Approval Gates = empty or "same as standard review" | Name each gate: T1 architectural sign-off, T2.5 phase transition, etc. |
