# Reference: llms.txt (OPT-IN)

Per **llmstxt.org**: a markdown link map at a site root (`/llms.txt`) that points an LLM to the most
important docs within a context budget. **Generate only when the repo publishes a docs site** — it is a
*website* convention, and current AI-crawler adoption is low (Google has called it "speculative"). Do not
ship it by default; offer it.

## Format (only the H1 is required)
```markdown
# Project Name            ← required (H1)

> One-line summary.       ← optional blockquote

Optional short prose about the project.

## Docs
- [Quickstart](https://…/quickstart): get running in 5 minutes
- [Reference](https://…/reference): full API

## Optional
- [Changelog](https://…/changelog)   ← items here MAY be skipped for a shorter context
```
- `##` sections are link lists: `[name](url): optional description`.
- A section literally named **`Optional`** has special semantics — its links may be dropped to shorten context.
- `llms-full.txt` (inlined docs) is a tool-generated expansion, not part of the core format.

## Authoring rules for this skill
- Opt-in only; confirm there is a published docs site first.
- **Every link must resolve** — the validator checks local links and flags likely-dead ones; never invent URLs.
- Don't claim the blockquote is required (only the H1 is).
- It links out; it never duplicates doc content.
