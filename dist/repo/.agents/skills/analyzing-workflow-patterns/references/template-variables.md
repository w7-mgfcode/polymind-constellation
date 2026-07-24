# Template Variables Reference

All `{{VARIABLE}}` tokens used across the 11 phases. Resolve each variable
from the current repo and workflow material before using in output.

---

## Workflow Identity Variables

| Variable | Description | Example value |
|----------|-------------|---------------|
| `{{WORKFLOW_NAME}}` | Short human-readable name | `Issue Decomposition Pipeline` |
| `{{WORKFLOW_TYPE}}` | Category from Phase 0 type list | `issue-decomposition` |
| `{{SOURCE_MATERIAL_NAME}}` | What the material is called | `decomp-spec.md`, `attached PDF` |
| `{{PRIMARY_GOAL}}` | One sentence: ultimate outcome | `Break epics into executable sub-issues` |
| `{{TARGET_USER}}` | Who runs or benefits | `platform engineer`, `all devs` |

---

## Repository Context Variables

| Variable | Description | How to resolve |
|----------|-------------|----------------|
| `{{REPO_NAME}}` | Repository name | `git remote -v` or `package.json .name` |
| `{{REPO_CONVENTIONS}}` | Key conventions summary | Derived from Phase 5 inspection |
| `{{CLAUDE_RULES_PATHS}}` | Claude instruction file paths | `find . -name "CLAUDE.md" -o -name "AGENTS.md"` |
| `{{GITHUB_WORKFLOW_PATHS}}` | GitHub Actions file paths | `ls .github/workflows/` |
| `{{ISSUE_SYSTEM}}` | Issue tracker in use | `GitHub Issues`, `JIRA`, `Linear` |
| `{{PROJECT_BOARD_SYSTEM}}` | Sprint/project tracking tool | `GitHub Projects V2`, `JIRA Board` |
| `{{COMMIT_FORMAT}}` | Commit message convention | `conventional commits`, `free-form` |
| `{{BRANCH_NAMING}}` | Branch naming pattern | `feature/<name>`, `fix/<ticket>` |
| `{{LABEL_TAXONOMY}}` | Existing label set | Derived from `gh label list` |

---

## Workflow Execution Variables

| Variable | Description | Resolution source |
|----------|-------------|-------------------|
| `{{VALIDATION_COMMANDS}}` | Commands that verify correctness | Phase 5 inspection |
| `{{APPROVAL_GATES}}` | Human review checkpoints | Extracted from material in Phase 1 |
| `{{OUTPUT_ARTIFACTS}}` | Concrete workflow outputs | Phase 1 extraction table |
| `{{ROLLBACK_STRATEGY}}` | How to undo if something fails | Phase 8 flow definition |
| `{{HANDOFF_FORMAT}}` | How context passes between phases | Phase 5 handoff conventions |
| `{{PHASE_BOUNDARY_RULE}}` | What must be true to advance a phase | Phase 1 hard rules |
| `{{CLEAN_CANVAS}}` | Whether repo has zero structural config | Phase 5 detection |

---

## API / Tool Variables (GitHub-specific)

| Variable | Description | Example |
|----------|-------------|---------|
| `{{GH_OWNER}}` | GitHub org or user | `world-of-books` |
| `{{GH_REPO}}` | GitHub repo slug | `wob-platform` |
| `{{GH_PROJECT_ID}}` | GitHub Projects V2 ID | `PVT_kwHOA...` |
| `{{SUB_ISSUES_ENDPOINT}}` | Sub-issues REST path | `POST /repos/{{GH_OWNER}}/{{GH_REPO}}/issues/{id}/sub_issues` |
| `{{GRAPHQL_ROLLUP_QUERY}}` | Query to check child issue states | Derived from workflow material |

---

## Substitution Rules

1. **Repo first.** If a variable can be read from the repo (e.g. `{{REPO_NAME}}`
   from `package.json`), read it — do not guess.

2. **Material second.** If the workflow material explicitly states a value,
   use it verbatim.

3. **Mark unresolved.** If a variable cannot be resolved, write:
   ```
   {{VARIABLE_NAME}} [UNRESOLVED — ask user]
   ```
   Never invent values. Never silently omit.

4. **Never reuse historical values.** Variables from previous sessions must
   not appear in a new analysis unless actually found in the current repo.

---

## Resolution Command Patterns

```bash
# {{REPO_NAME}}
cat package.json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('name',''))" 2>/dev/null
git remote get-url origin 2>/dev/null | sed 's/.*\///' | sed 's/\.git//'

# {{COMMIT_FORMAT}}
git log --oneline -10 2>/dev/null

# {{BRANCH_NAMING}}
git branch -a 2>/dev/null | head -20

# {{VALIDATION_COMMANDS}} — check all common runners
grep -E "^[a-z][a-z-]+:" Makefile 2>/dev/null | head -20
cat package.json 2>/dev/null | python3 -c "import sys,json; [print(k) for k in json.load(sys.stdin).get('scripts',{}).keys()]" 2>/dev/null
cat Taskfile.yml 2>/dev/null | grep -E "^\s+[a-z]"

# {{CLAUDE_RULES_PATHS}}
find . -maxdepth 3 \( -name "CLAUDE.md" -o -name "AGENTS.md" \) 2>/dev/null
ls .claude/ 2>/dev/null

# {{GITHUB_WORKFLOW_PATHS}}
ls .github/workflows/ 2>/dev/null
ls .github/ISSUE_TEMPLATE/ 2>/dev/null

# {{LABEL_TAXONOMY}}
gh label list 2>/dev/null | head -30

# {{GH_PROJECT_ID}}
gh project list --owner "{{GH_OWNER}}" 2>/dev/null
```

---

## Variable Dependency Map

Some variables depend on others being resolved first:

```
{{REPO_NAME}} ──┐
{{GH_OWNER}}    ├──> {{SUB_ISSUES_ENDPOINT}}
                └──> {{GRAPHQL_ROLLUP_QUERY}}

{{ISSUE_SYSTEM}} ──> {{PROJECT_BOARD_SYSTEM}}
{{COMMIT_FORMAT}} ──> {{PHASE_BOUNDARY_RULE}}
{{CLAUDE_RULES_PATHS}} ──> {{VALIDATION_COMMANDS}}
```

Resolve variables in the order they appear in this dependency map.
