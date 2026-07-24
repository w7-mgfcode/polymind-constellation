# Polymind Constellation Runway

> A build plan for turning the Dynamous Claude-first skill collection into a
> provider-neutral skill workbench for Claude Code, Codex, Gemini CLI, and
> local-LLM agent harnesses.

**Status:** Phase 8 implemented and hardened through release `0.8.1`; Claude/OpenCode and cross-provider behavioral parity remain explicit gaps; native plugins/extensions remain deferred  
**Architecture review:** ACCEPT with minor adjustments (7.6/10); amendments integrated below  
**Research date:** 2026-07-22  
**Target:** `w7-ghlanding` clean canvas  
**Source studied:** `dynamous-community/.claude/skills`  
**Source path-list digest:** `ea1918adf0252dbc61b9aece12387601bf57f4d79d09136b6963645ca6995b2d`

## 1. Outcome

Build a small framework that authors every skill once, validates it against the
open Agent Skills contract, and projects it into the native discovery surfaces
of each supported agent. Shared workflow and policy remain provider-neutral;
provider-specific discovery, permissions, invocation syntax, and runtime config
stay in generated adapters.

The first release will recreate and improve these three source skills:

1. `analyzing-workflow-patterns`
2. `starting-new-project`
3. `maintaining-agent-docs`

The framework will also support local models in two explicit ways:

- through a compatible harness such as OpenCode, which discovers `AGENTS.md`
  and `.agents/skills/` while routing to Ollama, llama.cpp, LM Studio, and other
  local providers;
- through a generic catalog/activation CLI for custom local harnesses that do
  not implement Agent Skills themselves.

“Supports local LLMs” must not mean that raw model servers magically discover
files. Ollama, llama.cpp, and LM Studio expose models; an agent harness must
assemble instructions, expose tools, enforce permissions, and activate skills.

### 1.1 Approved implementation boundary

The first implementation milestone is **Phases 0–4 only**: provenance and
licensing, the minimal framework skeleton, the canonical package model and
validator, lossless migration, and deterministic projections for Claude Code,
Codex, and Gemini CLI. It must deliver one complete vertical slice before the
framework expands.

Phases 5–8 are deferred until the Phase 4 exit review demonstrates that the
three migrated skills justify further abstraction. In particular, provider
marketplaces, advanced profile refactors, a generic local-agent runtime, broad
model evaluations, remote distribution, and MCP integrations are not part of
the MVP. A simple generic catalog may be emitted in Phase 4 because it falls out
of validated package metadata, but it must not execute tools or become a local
agent runtime.

The maintainer approved advancement after the Phase 4 gate. Phases 5 and 6 were
implemented on 2026-07-22. The maintainer separately approved Phases 7 and 8;
that approval does not extend to deferred marketplaces, plugins, or extensions.

The Phase 4 milestone is an **architecture MVP**, not a production-readiness
claim. Production use in a multi-agent environment still requires the minimum
live discovery, capability-boundary, interruption, and rollback evidence
defined in Sections 9, 11, and 14.

## 2. Current Repository Reality

The target is a clean canvas:

- no application files, package manifest, `README.md`, `AGENTS.md`, or CI;
- empty protected, currently read-only placeholder directories named `.git/`,
  `.agents/`, and `.codex/`;
- no usable Git metadata in the working directory;
- Claude Code `2.1.217`, Codex CLI `0.145.0`, Gemini CLI `0.51.0`, `uv`, and
  Python `3.14.4` are installed;
- OpenCode and `skills-ref` are not installed, so live tests for those two
  surfaces are future validation gates, not validations already completed.

This permits an architecture-first implementation without compatibility debt,
but it also means build, test, and release commands do not yet exist. The plan
must create them before an `AGENTS.md` can truthfully name them.

The current session cannot populate the protected `.agents/` or `.codex/`
placeholders. Before Phase 4, implementation needs either a normal writable
checkout or a staged `dist/repo/` projection that is installed into a writable
downstream checkout. This is an environment precondition, not a reason to move
canonical skills back into a provider folder.

## 3. Deep Source Inventory

Following the `maintaining-agent-docs` symlink, the requested source directory
contains 19 files, 2,370 lines, and 97,093 bytes.

| Skill | Shape | Core behavior | Reusable strength | Portability debt |
|---|---|---|---|---|
| `analyzing-workflow-patterns` | 1 `SKILL.md`, 3 references, 3 templates | Eleven ordered phases: classify material, extract reusable patterns, explain and exemplify in Hungarian, generate flow variants, inspect the repo, brainstorm, score five flows, then stop for approval | Strong gating, explicit evidence rules, rollback requirements, reusable templates, progressive disclosure | Hard-wired to Claude/GitHub/Hungarian; exactly five flows and mandatory appendices are excessively rigid; provider-specific `allowed-tools`; effort scoring contradicts its own rubric |
| `starting-new-project` | 1 `SKILL.md`, 2 references, 3 templates | One-question-at-a-time discovery, current web research, recommendation with trade-offs, approval, then scaffolding | Good adaptive discovery, explicit decision labels, separates shared rules from provider shims | GitHub is treated as universal; several early-2026 tool claims are already stale or incomplete; advice and mutation live in one large skill; no deterministic validator is bundled |
| `maintaining-agent-docs` | canonical under `.agents/skills`, symlinked into `.claude/skills`; 1 `SKILL.md`, 4 references, 1 validator | Maintains `AGENTS.md` as canonical, uses thin provider shims, preserves human content with managed regions, validates drift | Best example of the desired source-of-truth model; already demonstrates progressive disclosure and an adapter seam | The symlink is fragile on Windows; the validator uses regex rather than YAML parsing; link, secret, marker, and duplication checks are shallow; some cited provider facts have changed |

### 3.1 Source design that should be preserved

- `SKILL.md` is an entry point, not a dumping ground. Detailed phase rules,
  examples, and templates are loaded only when needed.
- Every mutating workflow has an explicit approval checkpoint.
- Repository claims must come from repository evidence.
- Generic workflows are distinct from downstream project rules.
- `AGENTS.md` is the canonical shared operating contract; provider files are
  adapters, not duplicate rulebooks.
- Deterministic verification is the definition of done.
- Templates use named variables rather than copying historical identifiers.

### 3.2 Source design that must not be copied blindly

1. **Mixed canonical locations.** Two skills live only under `.claude/skills/`;
   one lives under `.agents/skills/` and is symlinked back. This is a migration
   state, not a finished architecture.
2. **Provider fields in portable frontmatter.** `allowed-tools` is experimental
   in the open specification and provider behavior varies. Claude-specific tool
   names cannot be the portable permission model.
3. **Broken package boundaries.** The adjacent vendor
   `plan-execute-review` skill refers to root-level `assets/prompts/*` and
   `docs/safe-execution.md`, but the installer copies only the skill directory.
   Those links break downstream. The same pattern must be prohibited here.
4. **Destructive installation.** The vendor installer deletes an existing
   destination skill with `shutil.rmtree` before copying. It has no conflict
   detection, backup, managed merge, or content digest despite the documentation
   promising careful reconciliation.
5. **Weak asset validation.** The vendor framework checks only whether top-level
   frontmatter keys named `name` and `description` exist. It does not validate
   YAML, directory/name equality, field limits, reference closure, duplicate
   names, script safety, or trigger quality.
6. **Stale provider research embedded as timeless truth.** Examples include an
   outdated Claude import depth, uncertainty about Gemini imports, and obsolete
   Codex configuration shapes. Provider facts require dated evidence and
   compatibility tests.
7. **Conflicting scoring semantics.** The workflow analyzer defines effort `10`
   as easiest, but its example gives the lightweight option an effort score of
   `2`. Scores are unusable unless direction and weighting are machine-checked.
8. **Over-specialization.** Hungarian output, GitHub sub-issues, `.claude/`
   integration, and exactly five flow categories are valuable profiles, not
   universal core requirements.
9. **Validator false confidence.** The current docs validator counts markers
   without checking order or nesting, compares duplicated lines instead of
   semantic blocks, uses regex frontmatter parsing, and flags broad absolute-path
   patterns. Passing it does not prove safe or portable behavior.

## 4. Current External Evidence

The architecture is based on current primary or official documentation, not on
the source repository’s early-2026 snapshot.

- The [Agent Skills specification](https://agentskills.io/specification)
  defines a skill as a directory containing `SKILL.md`, with optional
  `scripts/`, `references/`, and `assets/`. It requires `name` and
  `description`, recommends a `SKILL.md` below 500 lines / 5,000 tokens, and
  describes metadata → instructions → resources progressive disclosure.
- [Codex skills documentation](https://developers.openai.com/codex/skills)
  states that repo skills are discovered from `.agents/skills/`, that Codex
  supports symlinked skill directories, and that skills use progressive
  disclosure. [Codex `AGENTS.md` guidance](https://developers.openai.com/codex/guides/agents-md)
  makes durable repo instructions hierarchical and scoped.
- [Claude Code skills documentation](https://code.claude.com/docs/en/slash-commands)
  follows the Agent Skills standard but discovers project skills from
  `.claude/skills/` and adds Claude-only frontmatter and execution features.
  [Claude project-memory documentation](https://code.claude.com/docs/en/memory)
  explicitly says Claude reads `CLAUDE.md`, not `AGENTS.md`, and recommends a
  `CLAUDE.md` import of `@AGENTS.md`; it documents five import hops and warns
  that symlinks are awkward on Windows.
- [Gemini CLI Agent Skills documentation](https://geminicli.com/docs/cli/skills/)
  natively treats `.agents/skills/` as an interoperable workspace alias and
  gives it precedence over `.gemini/skills/`. Its
  [context-file documentation](https://geminicli.com/docs/cli/gemini-md/)
  supports imports and configurable `context.fileName` lists.
- [OpenCode skills documentation](https://opencode.ai/docs/skills) discovers
  `.agents/skills/`, `.claude/skills/`, and its own skill path. Its
  [provider documentation](https://opencode.ai/docs/providers) supports local
  providers including llama.cpp, LM Studio, and Ollama. This makes OpenCode a
  concrete local-model conformance harness, not the canonical architecture.

### 4.1 Consequence

There is no single native project directory discovered by all required tools:

| Surface | Shared instructions | Native project skills | Required adapter |
|---|---|---|---|
| Codex | `AGENTS.md` | `.agents/skills/` | None for standard skills; optional `.codex/config.toml` only for Codex runtime settings |
| Gemini CLI | configure `AGENTS.md`, optional `GEMINI.md` | `.agents/skills/` or `.gemini/skills/` | `.gemini/settings.json` for context filenames and Gemini runtime settings |
| Claude Code | `CLAUDE.md` imports `AGENTS.md` | `.claude/skills/` | `CLAUDE.md` plus a `.claude/skills/` projection |
| OpenCode + local model | `AGENTS.md` | `.agents/skills/` | `opencode.jsonc` only for local provider/model/permission settings |
| Custom local harness | explicit prompt assembly | none unless implemented | catalog + activation/render CLI |

## 5. Brainstormed Architecture Options

### Option A — Canonical `.agents/skills/` plus Claude symlinks

Author directly in `.agents/skills/`; symlink every directory into
`.claude/skills/`.

**Advantages:** smallest implementation, immediate Codex/Gemini/OpenCode
discovery, proven in part by the source repository.

**Problems:** Windows symlinks require special configuration; provider-specific
frontmatter cannot be added safely; authoring and runtime distribution remain
coupled; the symlink tree is not a clear build artifact.

**Verdict:** suitable for a personal POSIX repo, not for the requested portable
architecture.

### Option B — Neutral source plus deterministic projections

Author under `skills/`. A compiler validates each package and emits runtime
trees under `.agents/skills/` and `.claude/skills/`; provider overlays may add
only documented provider fields. Generated files are reproducible and checked
for drift.

**Advantages:** real single source of truth, cross-platform, provider extensions
remain isolated, generated outputs can be tested exactly as clients see them,
and custom local-harness catalogs are easy to produce.

**Problems:** generated copies consume space and contributors may accidentally
edit them; the compiler becomes a critical component; the release must decide
whether projections are committed or built at install time.

**Verdict:** recommended. The duplication is mechanical and verifiable rather
than semantic and drifting.

### Option C — Separate native packages/plugins for every provider

Build Claude plugins, Codex plugins, Gemini extensions, and an OpenCode package
from the start.

**Advantages:** maximum use of each provider’s native distribution and UI.

**Problems:** four release surfaces before core behavior is stable, repeated
manifests, high drift risk, no neutral local-harness contract, and needless
complexity for three small skills.

**Verdict:** a later distribution layer, not the authoring architecture.

### Option D — MCP server as the entire abstraction

Expose skill discovery and execution as MCP tools.

**Advantages:** broad client interoperability and dynamic capabilities.

**Problems:** MCP is appropriate for tools and external context, while Agent
Skills are appropriate for reusable instructions and local resources. Making
all instructions remote adds startup, trust, and availability failure modes.

**Verdict:** optional for remote actions later; not a replacement for skills.

## 6. Decision

Choose **Option B: neutral canonical sources with deterministic provider
projections**, paired with a lowest-common-denominator Agent Skills contract.

The architecture follows five rules:

1. `skills/` is the only hand-edited skill source.
2. `.agents/skills/` and `.claude/skills/` are generated runtime projections.
3. Canonical frontmatter uses only stable standard fields. Provider-only fields
   come from adapter overlays and appear only in that provider’s projection.
4. A skill must be self-contained after projection. Every relative reference
   must resolve inside the skill package unless a dependency is explicitly
   declared and installed with it.
5. Instructions describe intent; deterministic scripts enforce schema,
   generation, drift, and safety boundaries.

### 6.1 Independent review resolution

The accepted review scored the proposed design as follows:

| Dimension | Score | Resolution incorporated by this revision |
|---|---:|---|
| Portability | 8.5/10 | Keep neutral sources and copied projections; require live discovery evidence before production claims. |
| Spec alignment | 8.5/10 | Keep version/tags inside namespaced `metadata`, not unknown top-level fields; separate spec errors from policy warnings. |
| Safety | 8.0/10 | Formalize capability subsets, overlay allowlists, lock semantics, concurrency, path containment, and crash recovery. |
| Complexity vs payoff | 6.0/10 | Make Phases 0–4 the only approved MVP and defer advanced distribution/local-runtime work. |
| Local-LLM readiness | 6.0/10 | Define the sandbox contract now, but defer implementation until after the MVP. |
| Provider drift resilience | 8.5/10 | Add a machine-readable compatibility manifest and release-time revalidation gate. |

The unweighted review score is **7.6/10: ACCEPT with minor adjustments**.
This is acceptance of the architecture direction, not evidence that the empty
target repository is production-ready.

## 7. Proposed Repository Architecture

```text
.
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── GEMINI.md
├── pyproject.toml
├── uv.lock
├── skills/                              # only canonical, hand-edited skills
│   ├── analyzing-workflow-patterns/
│   │   ├── SKILL.md
│   │   ├── skill.toml                   # portable capabilities and package metadata
│   │   ├── references/
│   │   │   ├── protocol.md
│   │   │   ├── quality.md
│   │   │   ├── variables.md
│   │   │   └── profiles/
│   │   │       ├── github.md
│   │   │       └── hungarian.md
│   │   ├── assets/
│   │   │   ├── fit-matrix.md
│   │   │   ├── flow-definition.md
│   │   │   └── extraction-table.md
│   │   └── tests/cases.toml
│   ├── starting-new-project/
│   │   ├── SKILL.md
│   │   ├── skill.toml
│   │   ├── references/
│   │   ├── assets/
│   │   └── tests/cases.toml
│   └── maintaining-agent-docs/
│       ├── SKILL.md
│       ├── skill.toml
│       ├── references/
│       ├── assets/
│       ├── scripts/validate_agent_docs.py
│       └── tests/cases.toml
├── adapters/
│   ├── claude/
│   │   ├── overlays/                    # optional Claude-only frontmatter/config
│   │   └── settings.json.tmpl
│   ├── codex/
│   │   └── config.toml.tmpl             # runtime only; no shared policy
│   ├── gemini/
│   │   └── settings.json.tmpl
│   └── local/
│       ├── opencode.jsonc.tmpl
│       └── generic-catalog.schema.json
├── compatibility/
│   └── providers.toml                  # tested versions, sources, paths, freshness
├── .agents/skills/                      # generated Codex/Gemini/OpenCode projection
├── .claude/skills/                      # generated Claude projection
├── .gemini/settings.json                # generated/managed provider config
├── src/polymind/
│   ├── cli.py
│   ├── model.py
│   ├── capabilities.py
│   ├── discovery.py
│   ├── validation.py
│   ├── projection.py
│   ├── overlays.py
│   ├── compatibility.py
│   ├── catalog.py
│   └── diffing.py
├── scripts/
│   ├── bootstrap
│   ├── sync-adapters
│   └── verify
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── fixtures/
│   └── e2e/
└── docs/
    ├── architecture.md
    ├── authoring-skills.md
    ├── provider-compatibility.md
    ├── local-models.md
    ├── security.md
    └── _runway/
        └── polymind-constellation-runway.md
```

### 7.1 Canonical skill contract

`SKILL.md` uses only fields with cross-client meaning:

```yaml
---
name: maintaining-agent-docs
description: >-
  Create, audit, and reconcile repository agent documentation. Use when the
  user asks to manage AGENTS.md, CLAUDE.md, GEMINI.md, README.md, or llms.txt.
license: Apache-2.0
compatibility: Requires filesystem read access; writes require explicit approval.
metadata:
  polymind.version: "1.0.0"
  polymind.tags: "agent-docs,governance,repository-instructions"
  polymind.risk: "writes-after-approval"
---
```

Rules:

- directory name equals `name`;
- kebab-case, 1–64 characters, no consecutive hyphens;
- description is 1–1,024 characters and states both positive and negative
  trigger boundaries;
- `SKILL.md` target is under 500 lines and 5,000 tokens;
- canonical `allowed-tools` is omitted because implementations differ;
- every referenced file is relative to the skill root and normally one level
  deep;
- every script documents runtime, dependencies, inputs, outputs, side effects,
  and dry-run behavior;
- no skill may require a file outside its package unless `skill.toml` declares a
  dependency and projection proves the installed closure.

The current Agent Skills specification does **not** define top-level `version`
or `tags` fields. When Polymind needs them, it stores string values under the
standard `metadata` map using namespaced keys, as above. `polymind.version` is
the authoritative skill behavior version; `polymind.tags` supports Polymind
catalog search but does not replace a precise `description`, which remains the
native discovery and activation signal for provider clients. A strict
specification validator must reject unknown top-level fields rather than
silently promoting them to portable contract fields.

The 500-line / 5,000-token guidance is a progressive-disclosure quality target,
not a required Agent Skills schema field. Validation must report spec
conformance separately from Polymind policy conformance so a policy warning is
never misrepresented as a specification failure.

### 7.2 `skill.toml` responsibility

Agent clients may ignore this sidecar; the framework consumes it. It records:

- package schema version; the semantic behavior version remains canonical in
  `SKILL.md` metadata and must not be duplicated here;
- source provenance and license;
- capability vocabulary such as `filesystem.read`, `filesystem.write`,
  `shell.readonly`, `network.read`, and `browser.read`;
- whether mutation requires explicit approval;
- script entry points and runtime requirements;
- declared skill dependencies;
- adapter overlays to apply;
- positive and negative trigger-evaluation cases;
- source compatibility profile and deprecation aliases.

Capabilities are descriptive and validated. They do not grant permissions.
Each provider adapter maps them to the provider’s real permission system, and a
projection may narrow but never silently broaden capabilities.

#### 7.2.1 Capability and overlay enforcement

Capabilities form a closed, versioned vocabulary of atomic actions rather than
free-form labels. The first vocabulary must distinguish at least filesystem
read/write, shell read-only/execute, network read/write, browser read/write,
and secret access. The package validator expands compound capabilities into
their atomic action set and rejects unknown actions.

For every projection:

```text
effective_actions(provider_overlay) ⊆ declared_actions(canonical_skill)
```

An overlay may disable an action, change a declared action from automatic to
`ask`, or translate it into a provider’s narrower native permission. It may not
add actions, change the skill body, replace scripts, add executable resources,
or alter the resource dependency graph. Unknown provider mappings fail closed.
If a provider cannot express the requested boundary exactly, the generated
permission must be `ask` or `deny`, never an approximate broader `allow`.

Provider overlay schemas use explicit field allowlists. Projection validation
must compare canonical and emitted package manifests, calculate both action
sets, and fail when the emitted set is not a subset. Script declarations are
included in this comparison so an apparently harmless frontmatter overlay
cannot smuggle in a more powerful executable path.

### 7.3 Generated projections

`polymind sync` performs an atomic staged build:

1. validate canonical packages;
2. copy each package to a temporary projection root;
3. apply allowlisted provider overlays;
4. remove internal-only files such as `skill.toml` and test cases if the client
   does not need them;
5. validate the projected package independently;
6. generate `projection.lock.json` containing per-file SHA-256 digests;
7. show a diff;
8. replace the runtime tree only after all checks pass.

The MVP writes generated copies for Windows portability. A possible `--link`
developer mode is deferred until copied projections prove too costly; release
artifacts and CI always use and test copied projections.

Generated trees begin with a conspicuous `GENERATED.md` and are never edited by
hand. `polymind verify` fails when regenerating into a temporary directory does
not exactly match the committed runtime trees.

Generated projections are committed for immediate, cross-platform provider
discovery, but they are read-only build artifacts. `polymind sync` is their only
writer; contributor documentation, review checks, and CI must reject manual
changes even when the edited projection remains syntactically valid.

`projection.lock.json` proves reproducibility and detects drift; it does not
prove origin, authorship, or trust. Trust comes from source review, provenance,
repository controls, and release policy. The documentation and CLI must never
describe an unsigned digest lock as a signature or supply-chain authenticity
mechanism.

Sync uses an exclusive project lock, stages on the same filesystem as the
destination, validates resolved paths after following permitted links, and
rejects links or paths escaping the package root. The test matrix must cover
concurrent sync attempts, interruption before and during replacement,
same-volume atomic replacement semantics on POSIX and Windows, stale locks,
unknown destination files, and recovery after post-apply verification fails.

### 7.4 Shared instructions and provider shims

- `AGENTS.md` is created only after real setup and verification commands exist.
  It contains concise, repo-wide, provider-neutral rules.
- `CLAUDE.md` imports `@AGENTS.md` and adds only Claude runtime notes. It does
  not copy project policy.
- `.gemini/settings.json` configures `context.fileName` to load `AGENTS.md` and,
  only if Gemini-specific notes exist, `GEMINI.md`. `GEMINI.md` must not import
  `AGENTS.md` when the settings already load both, or the policy is duplicated.
- `.codex/config.toml` is optional and contains only trusted-project Codex
  runtime settings. Codex reads `AGENTS.md` and `.agents/skills/` without a
  shim.
- `opencode.jsonc` is an example local-model adapter, not a required shared
  policy file. It selects a provider/model and skill permissions without
  hard-coding credentials.

## 8. Skill Migration Design

Migration is parity-first, refactor-second. Each skill receives a frozen source
fixture and behavioral cases before its behavior changes.

### 8.1 `analyzing-workflow-patterns`

Preserve:

- material classification and entity/verb extraction;
- understand-before-recommend and repo reality-check ordering;
- assumption labels, approval gates, rollback, and validation requirements;
- template variables and structured flow comparison;
- the final hard stop before repository mutation.

Refactor:

- make the language layer a profile; English is core and Hungarian is the first
  bundled localization profile;
- make GitHub issue decomposition a profile rather than a universal model;
- replace `.claude` and `.github` inspection with a provider/tracker capability
  scan;
- permit 3–5 recommendation variants based on material complexity while
  retaining a `legacy-five-flow` compatibility profile;
- define every score as either benefit or cost and normalize all displayed
  scores so “higher is better”; add a formula and validation test;
- move exact output schemas into assets and keep the core `SKILL.md` procedural;
- replace the mandatory generic “Possible Additions” appendix with an optional
  iteration contract driven by unresolved decisions.

### 8.2 `starting-new-project`

Preserve:

- one targeted question per turn;
- adaptive fast-exit when the user supplied enough context;
- current web research for fast-moving choices;
- explicit recommendation, alternative, trade-off, and user-decision labels;
- plan approval and file-list approval before writes.

Refactor:

- split research/recommendation from scaffolding through an explicit phase
  boundary, while keeping one skill entry point;
- make GitHub, GitLab, local-only, and no-CI repository hosts profiles;
- derive assistant adapters from the actual chosen stack;
- never create provider folders “just in case”;
- use canonical templates under `assets/` and validate that no placeholders
  remain before projection or scaffolding;
- attach `verified_at`, source URL, and applicability notes to volatile provider
  facts;
- require an existing or newly created deterministic `scripts/verify` before
  claiming that local and CI verification match.

### 8.3 `maintaining-agent-docs`

Preserve:

- canonical `AGENTS.md`, thin shims, managed regions, diff-before-write, and
  preservation of nested instruction scopes;
- repository-evidenced commands only;
- optional `llms.txt` only for a published documentation site;
- secret checks and link validation.

Refactor:

- replace regex frontmatter parsing with real YAML parsing;
- check marker ordering, nesting, and uniqueness, not just counts;
- detect semantic duplication using normalized blocks and configurable
  thresholds;
- resolve local links safely, reject package escapes, and optionally check
  remote links only in a network-enabled validation profile;
- use secret scanning with allowlisted fixtures and redacted diagnostics;
- model Claude and Gemini imports according to current docs;
- make the validator path package-relative and expose it through the framework
  CLI, avoiding the currently ambiguous `python scripts/validate.py` command;
- add `--check`, `--diff`, and `--strict` modes; writes remain separate and
  approval-gated.

## 9. Implementation Runway

### Phase 0 — Provenance and legal gate

**Work**

1. Record the exact 19 source paths, sizes, hashes, symlink target, and source
   commit if available.
2. Determine license/permission for copying and modifying every source file.
3. Save pristine copies only in test fixtures if the license permits it;
   otherwise store hashes and behavioral summaries.

**Acceptance**

- provenance manifest is machine-readable;
- every migrated file has a license decision;
- no implementation proceeds with unresolved redistribution rights.

**Rollback:** delete only the new provenance fixture/manifest before any runtime
projection exists.

### Phase 1 — Minimal framework skeleton

**Work**

1. Create `pyproject.toml` for Python 3.11+ using `uv`.
2. Add `src/polymind`, pytest, Ruff, mypy, and a real YAML parser.
3. Add thin `scripts/bootstrap`, `scripts/sync-adapters`, and `scripts/verify`
   wrappers; business logic stays in Python.
4. Add a single `polymind verify` command that CI will later call unchanged.
5. Only now create a truthful root `AGENTS.md`, `CLAUDE.md`, and provider docs.

**Acceptance**

- clean checkout bootstrap works;
- `scripts/verify` runs lint, format check, typing, tests, canonical skill
  validation, projection drift checks, and doc checks;
- shell wrappers contain no business logic.

**Rollback:** remove the new skeleton; no source skills are changed yet.

### Phase 2 — Canonical package model and validator

**Work**

1. Implement typed `SkillPackage`, `SkillMetadata`, `Capability`, `Overlay`,
   and `Projection` models.
2. Implement discovery under canonical `skills/` only.
3. Validate Agent Skills names, YAML, field types/limits, name-directory
   equality, duplicate names, `SKILL.md` size, reference closure, script
   declarations, unresolved placeholders, and package escapes.
4. Add an optional invocation of the reference `skills-ref validate` tool when
   installed, with the internal validator remaining deterministic offline.
5. Add fixtures for malformed YAML, folded descriptions, broken links,
   traversal attempts, duplicate names, unknown top-level `version`/`tags`,
   non-string metadata values, and forbidden provider fields.
6. Emit separate `spec`, `polymind-policy`, and `security` diagnostic classes;
   only actual specification violations may be labeled spec failures.
7. Parse and normalize the closed capability vocabulary, including compound to
   atomic action expansion and fail-closed handling for unknown actions.

**Acceptance**

- every known weakness in the vendor validator has a failing fixture and a
  passing corrected case;
- validation is non-mutating and produces stable machine-readable diagnostics;
- offline validation requires no network;
- the validator distinguishes mandatory spec failures from progressive-
  disclosure policy warnings;
- capability normalization is deterministic and unknown actions fail closed.

**Rollback:** validator code is isolated; no runtime projection is enabled.

### Phase 3 — Lossless migration

**Work**

1. Import the three source skills into canonical `skills/` without behavioral
   refactoring.
2. Normalize only package layout and standard frontmatter.
3. Bring every required reference/template/script inside its owning package.
4. Write parity cases that cover positive triggers, negative triggers, required
   phases, approval stops, and expected artifact shapes.
5. Document every intentional deviation from source.

**Acceptance**

- all 19 source files are mapped or explicitly retired;
- there are no unresolved internal links;
- golden parity cases pass;
- provider names do not appear in canonical rules unless the skill is
  intentionally discussing that provider.

**Rollback:** remove canonical imports; frozen provenance remains.

### Phase 4 — Projection compiler and adapters

**Work**

1. Generate `.agents/skills/` from canonical packages without provider-only
   fields.
2. Generate `.claude/skills/` with allowlisted Claude overlays only.
3. Generate the Gemini context setting and thin provider notes using owned-key
   merge semantics; preserve unrelated human settings and refuse conflicting
   values rather than overwriting the file wholesale.
4. Generate a data-only JSON catalog containing name, description, package
   path, version, tags, capabilities, and risk. It has no execution endpoint in
   the MVP.
5. Implement atomic staging, dry-run, diff, conflict detection, lock hashes,
   and `--check` drift validation.
6. Refuse to overwrite non-generated content at a projection destination.
7. Enforce overlay field allowlists and prove emitted effective actions are a
   subset of canonical declared actions.
8. Generate `compatibility/providers.toml` with client name, tested version,
   discovery path, relevant config fields, source URL, verification date,
   support status, and smoke-test identifier.
9. Commit copied projections as read-only artifacts and make CI regenerate them
   into a temporary tree for exact comparison.

**Acceptance**

- repeated generation is byte-for-byte idempotent;
- interruption before atomic replace leaves the previous projection intact;
- hand edits and unknown files cause a conflict rather than deletion;
- existing provider configuration outside Polymind-owned keys is preserved;
- Windows-safe copied projections pass tests and no symlink mode is required;
- unknown or broadened overlay capabilities fail projection;
- lockfiles detect drift without being described as authenticity evidence;
- concurrent sync, stale-lock, path-escape, and post-apply rollback tests pass;
- installed Claude Code, Codex, and Gemini CLI versions discover the three
  projected skill names in a disposable fixture, or the milestone is explicitly
  reported as incomplete rather than “statically compatible”.

**Rollback:** remove generated runtime trees; canonical skills remain intact.

**Phase 4 decision gate:** stop and review measured maintenance cost, projection
drift incidents, provider discovery evidence, skill demand, and unresolved
safety findings. Advancing to Phase 5 requires an explicit maintainer decision;
completion of Phase 4 does not automatically authorize the deferred roadmap.

### Phase 5 — Portability refactor

**Implementation status (2026-07-22): complete.** The three canonical skills
now use portable cores with opt-in profiles, retain the owner-authored legacy
behavior, and project deterministically. The Phase 5 suite covers every profile
contract, two-stage write approvals, normalized higher-is-better scoring, the
volatile-fact ledger, and the agent-docs safety validator. The full repository
gate passes with 53 tests; `skills-ref` remains an explicitly skipped optional
validator because it is not installed.

**Work**

Apply the changes in Section 8 one skill at a time. Each refactor must preserve
the prior parity profile while adding the portable default profile.

Order:

1. `maintaining-agent-docs` establishes trustworthy shared instructions and
   validation.
2. `starting-new-project` consumes that model when scaffolding repositories.
3. `analyzing-workflow-patterns` consumes the provider/tracker capability model
   for repository-fit planning.

**Acceptance**

- no canonical skill assumes Claude, GitHub, Hungarian, or cloud APIs unless a
  selected profile requires them;
- approval gates are preserved for all writes;
- every profile has tests and documented prerequisites;
- scoring direction is consistent and tested.

**Rollback:** revert one skill/profile at a time; projection hashes identify the
last good generated state.

### Phase 6 — Local-LLM bridge

**Implementation status (2026-07-22): code complete, environment gate
pending.** Catalog output is available as JSON, XML, and Markdown; activation
returns one `SKILL.md`, a resource manifest, capabilities, permission
requirements, digest, and base directory; bounded resource reads return one
manifested file at a time. The provider-SDK-free reference harness exposes no
execution command. Static and security checks pass with 68 tests; the opt-in
OpenCode/LM Studio discovery test is skipped because neither runtime is
installed. OpenCode remains `static-only`, not live-tested.

**Work**

1. Add an OpenCode example that points to a local provider without credentials
   or machine-specific absolute paths.
2. Implement `polymind catalog --format json|xml|markdown` for tier-one skill
   discovery.
3. Implement `polymind activate <name> --format json|markdown` to return the
   selected `SKILL.md`, resource manifest, capabilities, and base directory.
4. Keep script execution outside activation. The host must approve and execute
   tools through its own sandbox.
5. Publish a minimal host contract: catalog at session start, explicit skill
   activation, resource reads on demand, capability-to-permission mapping,
   and no implicit code execution.

**Normative host safety contract (defined now, implemented after MVP):**

- catalog and activation are data-returning operations only; activation never
  executes a script or grants a permission;
- tool and script execution default to deny and require a validated capability
  mapping plus host/user approval appropriate to the risk;
- the host constrains working directory and readable/writable roots, resolves
  paths before access, blocks package escapes and unsafe symlinks, and denies
  network access unless the declared atomic action explicitly requires it;
- child processes receive an allowlisted environment with secrets excluded by
  default, bounded wall-clock and idle timeouts, bounded stdout/stderr, CPU and
  memory limits where the platform supports them, and whole-process-tree
  termination on timeout or cancellation;
- provider mappings are fail-closed: an unknown capability, unavailable
  sandbox, or unrepresentable permission becomes `ask` or `deny`;
- every execution records skill/version, content digest, requested and granted
  capabilities, command/tool, working directory, timeout, exit status, and
  redacted output metadata in an audit record;
- local-harness behavior must be compared with the same canonical capability
  actions used by Codex, Claude, Gemini, and OpenCode adapters, even when native
  permission syntax differs.

**Acceptance**

- OpenCode discovers projected skills with a local model;
- a tiny reference harness can list and activate a skill without importing
  provider SDKs;
- activation cannot read outside the package through symlinks or `..` paths;
- smaller local models receive compact instructions and one resource at a time;
- sandbox denial, timeout, cancellation, output-limit, environment-filtering,
  network-denial, and process-tree cleanup cases pass before any harness is
  labeled safe for executable skills.

**Rollback:** local adapters are additive; remove them without affecting native
providers.

### Phase 7 — Cross-provider conformance

**Implementation status (2026-07-22): implemented with live gaps recorded.**
The versioned matrix covers explicit invocation, two implicit positives, one
negative, an approval-bypass attempt, and two resources for each canonical
skill. Twenty-seven static checks run in the normal verification gate. Native
data-only discovery passed for Codex CLI `0.145.0` and Gemini CLI `0.51.0` in a
disposable generated repository. Claude Code is an explicit policy skip because
it has no data-only discovery command, and OpenCode is an explicit environment
skip because it is not installed. Structured Ollama evaluation measured
`1.0000` explicit selection for both models, `0.8333`/`1.0000` implicit
selection, and zero false activations, but only `0.6667`/`0.3333` strict
approval-stop compliance; none of these measurements is a claim of safe
executable-agent parity. See
[`docs/phase7-conformance.md`](../phase7-conformance.md).

**Work**

Create a disposable fixture repository and run the matrix in Section 11 against
pinned supported CLI versions. Static tests run on every commit; network/model
tests run in an explicitly enabled environment with credentials.

**Acceptance**

- all installed supported clients discover the same three skill names and
  descriptions;
- positive prompts activate the intended skill; negative prompts do not;
- each client respects the same approval stop before mutation;
- provider overlay behavior is confined to its projection;
- unsupported/missing clients are reported as skipped, never silently passed.

**Rollback:** conformance fixtures contain no product state and can be recreated.

### Phase 8 — Documentation and release

**Implementation status:** completed in `0.8.0` and fail-closed boundary hardened in `0.8.1` on 2026-07-23.
Authoring, fourth-skill contribution, projection, provider compatibility,
security, local harness, Claude-first migration, downstream installation,
changelog, and versioning contracts are published. The generated projection is
bundled in release wheels. The downstream installer defaults to dry-run,
supports bounded diff, requires explicit apply, rejects ownership/drift/symlink
conflicts, performs atomic recovery, and retains one verified rollback snapshot.
Compatibility evidence now has a 90-day freshness window and explicit evidence
scope. Provider-native plugin/extension packaging remains deferred because the
Phase 7 behavioral gaps are still open.

**Work**

1. Document authoring, projection, provider compatibility, local harnesses,
   security, and migration from `.claude/skills`.
2. Publish a support matrix with “tested”, “statically compatible”, and
   “unsupported” as distinct states.
3. Pin a compatibility baseline and record research timestamps.
4. Add changelog and semantic versioning for skill behavior and package schema.
5. Package provider-native plugins/extensions only after the repo-scoped
   architecture is stable.

**Acceptance**

- a new contributor can add a fourth canonical skill and generate all
  projections from the docs alone;
- a downstream repo can install with dry-run, diff, conflict safety, and
  rollback;
- no documentation claims a live provider validation that CI did not run.

## 10. Installation Model

The installer follows plan → diff → approval → atomic apply:

```text
DISCOVER_SOURCE
  -> VALIDATE_CANONICAL
  -> RESOLVE_DEPENDENCY_CLOSURE
  -> BUILD_PROJECTIONS_IN_TEMP
  -> VALIDATE_PROJECTIONS
  -> DETECT_TARGET_CONFLICTS
  -> SHOW_DIFF
  -> APPROVAL_GATE
  -> ATOMIC_APPLY
  -> POST_INSTALL_VERIFY
  -> WRITE_LOCKFILE
```

Required behaviors:

- `--dry-run` is the default recommendation for an unfamiliar target;
- existing non-managed files are never deleted or overwritten;
- managed files update only when their prior digest matches the lockfile;
- divergence produces a three-way conflict report;
- backups are stored inside a task-specific temporary/staging area until
  post-install verification passes;
- rollback restores the pre-apply snapshot;
- one exclusive project lock serializes sync/install operations, with explicit
  stale-lock diagnosis and recovery;
- all containment decisions use resolved paths and reject symlink or traversal
  escapes before staging and immediately before apply;
- absolute source-machine paths never enter generated artifacts;
- installation has no network requirement when source packages are local;
- digest lockfiles are drift/integrity evidence only and never substitute for
  provenance review, signed releases, or repository trust controls.

## 11. Validation Strategy

### 11.1 Layered validation matrix

| Layer | Proves | Required checks |
|---|---|---|
| L0 — repository | framework is internally coherent | Ruff, format, mypy, pytest, docs links, no placeholders, no secrets |
| L1 — canonical skill | source conforms to the open contract | YAML schema, names, lengths, directory match, spec-vs-policy diagnostics, progressive-disclosure budgets, reference closure, safe paths |
| L2 — projection | adapters reproduce valid client packages without privilege expansion | independent validation of `.agents` and `.claude`, overlay allowlist, action-subset proof, hash lock, reproducibility, manual-edit rejection |
| L3 — semantic policy | critical workflow invariants survive | approval-before-write, assumption labels, dry-run for mutation, scoring direction, rollback and validation sections |
| L4 — trigger eval | descriptions route correctly | positive, paraphrase, ambiguous, overlap, and negative prompt cases per skill |
| L5 — client discovery | clients see the package | Claude `/skills`, Codex skill list/explicit invocation, Gemini `/skills list`, OpenCode skill listing |
| L6 — end to end | behavior works in a real fixture | run a read-only scenario per skill, assert artifacts and hard stops, capture versions and evidence |
| L7 — install/rollback | downstream writes are safe | clean install, update, drift conflict, concurrent sync, stale lock, path/symlink escape, interruption, rollback, POSIX/Windows replacement behavior |

### 11.2 Provider conformance cases

For each client and skill:

1. **Discovery:** exact name and non-truncated key trigger terms are visible.
2. **Explicit invocation:** provider syntax loads the correct full skill.
3. **Implicit positive trigger:** two realistic paraphrases activate it.
4. **Negative trigger:** a nearby but out-of-scope request does not activate it.
5. **Resource access:** one reference and one asset resolve relative to the
   projected root.
6. **Permission behavior:** no provider overlay grants more than `skill.toml`
   declares.
7. **Approval gate:** a mutation request stops at the documented checkpoint.
8. **Context budget:** catalog and skill bodies remain within configured limits.

### 11.3 Local-model quality cases

Local models vary more in tool use and instruction adherence. Test at least one
small and one strong local code model through the same harness and record:

- correct skill selection rate;
- false activation rate;
- required-step completion;
- approval-stop compliance;
- tool-call validity;
- resource-loading discipline;
- context and latency cost.

No architecture can promise behavioral parity across arbitrary local models.
The release claim is format and harness compatibility; model-quality claims
must be tied to measured model/version combinations.

### 11.4 Provider drift gate

`compatibility/providers.toml` is the source of truth for compatibility claims.
Each release must re-run every required static and live smoke test whose adapter
or provider documentation changed, whose recorded client version differs from
the supported baseline, or whose evidence is older than the project’s declared
freshness threshold. The release fails closed when required evidence is stale
or missing.

Compatibility status uses distinct values:

- `tested` — the pinned client version passed live discovery/invocation tests;
- `static-only` — generated files validate but no live client test ran;
- `experimental` — the adapter or provider feature is unstable;
- `unsupported` — no compatibility claim is made.

Documentation generation reads this manifest so prose cannot claim `tested`
when CI recorded `static-only`. Source URLs and verification dates are evidence
metadata, not substitutes for running the client conformance case.

## 12. Critic Pass

### Criticism 1 — Generated projections duplicate content

**Risk:** repository size and accidental edits grow.

**Response:** three skills total less than 100 KB, and generated duplication is
cheaper than cross-platform symlink failure. Hash locks, generated markers, and
CI drift checks make the copies mechanical. Revisit artifact-only projections
when distribution scale makes duplication material.

### Criticism 2 — The compiler becomes a single point of failure

**Risk:** bad projection logic can corrupt every provider tree.

**Response:** canonical packages remain untouched; generation occurs in a temp
tree; projected output is validated independently; atomic apply and rollback
are required. Golden projection fixtures pin behavior.

### Criticism 3 — Lowest-common-denominator metadata wastes provider features

**Risk:** skills feel weaker in Claude or future clients.

**Response:** stable shared semantics remain canonical, while allowlisted
overlays add provider-only fields. The overlay is explicit, testable, and cannot
silently broaden declared capabilities.

### Criticism 4 — `AGENTS.md` is not universally native

**Risk:** claiming it as canonical may hide provider gaps.

**Response:** canonical means governance source, not native support. Claude gets
the documented `CLAUDE.md` import; Gemini gets configured context filenames;
Codex and OpenCode read it natively. Validation inspects the effective provider
context, not just file existence.

### Criticism 5 — Local-LLM support is underspecified

**Risk:** users may expect raw Ollama/llama.cpp servers to run skills.

**Response:** documentation explicitly separates model server from agent
harness. OpenCode is the intended first turnkey route, but it cannot be labeled
`tested` until Phase 6 runs against an installed version and named local model.
The generic catalog/activation contract is the later integration route for
custom harnesses.

### Criticism 6 — The migrated workflows are too prescriptive

**Risk:** exact phases and formats can reduce model judgment and waste context.

**Response:** retain strict legacy profiles for repeatability, but make portable
defaults outcome-driven with configurable profiles. Trigger evals and task
quality tests decide whether detail helps; instruction length alone does not.

### Criticism 7 — Provider docs will drift again

**Risk:** today’s correct paths and features become tomorrow’s stale advice.

**Response:** isolate provider claims in compatibility docs/adapters, attach a
verification date and CLI baseline, and run scheduled or release-time docs and
CLI conformance reviews. Core skill semantics avoid provider details.

### Criticism 8 — Automated validators can create false assurance

**Risk:** schema validity is mistaken for workflow correctness or safety.

**Response:** report validation layers separately. A package can be
schema-valid, statically compatible, live-discovered, and behaviorally tested;
these are not collapsed into one “pass”. Human review remains required for
permission overlays and mutating workflows.

### Criticism 9 — License provenance may block recreation

**Risk:** copying vendor content without a clear license creates legal debt.

**Response:** Phase 0 is a hard gate. If redistribution rights are unresolved,
reimplement behavior from analysis and tests without copying protected text.

### Criticism 10 — The plan may overbuild a three-skill repository

**Risk:** a framework, compiler, and adapters cost more than simple copies.

**Response:** implement vertically. The first milestone needs only validation,
two projections, and three migrated packages. Plugins, remote distribution,
MCP, UI, and advanced local harnesses are explicitly deferred. Stop after Phase
4 if the simple repo-scoped product satisfies real use.

### Criticism 11 — Capability labels can look safer than they are

**Risk:** a provider maps a vague capability to an overly broad native
permission while still claiming the overlay “did not broaden” access.

**Response:** capabilities are atomic, versioned actions; mappings fail closed;
and projection proves emitted actions are a subset. Any provider permission that
cannot represent the boundary becomes `ask` or `deny`.

### Criticism 12 — Digest locks can be mistaken for supply-chain trust

**Risk:** a reproducible malicious projection has valid hashes.

**Response:** lockfiles are used only for drift and managed-update conflict
detection. Provenance review, repository controls, license gates, and any future
signed-release mechanism remain separate trust layers.

## 13. Validation of This Plan

This plan has been checked against the following gates:

- **Source coverage:** all three requested skills, every reference/template,
  and the symlinked validator were read; the surrounding vendor installer,
  asset validator, architecture docs, and prompts were inspected where they
  materially affect portability.
- **Repo grounding:** target absence and installed CLI availability were
  checked directly; unavailable live harnesses are labeled rather than assumed.
- **Current standards:** storage, discovery, imports, and progressive disclosure
  were compared with current Agent Skills, Claude, Codex, Gemini, and OpenCode
  documentation.
- **Single source of truth:** hand-edited canonical skills are separated from
  generated projections and provider runtime config.
- **Cross-platform behavior:** the release path does not require symlinks.
- **Package closure:** downstream skill packages cannot rely on undeployed
  root-level assets.
- **Safety:** writes require dry-run/diff/approval, conflict detection, atomic
  apply, post-verify, and rollback.
- **Local-model honesty:** compatibility is defined at the harness interface,
  not attributed to a raw model server.
- **Testability:** every implementation phase has concrete acceptance and
  rollback criteria.
- **Scope control:** implementation status is recorded per phase. Static and
  live claims name their exact evidence; remaining provider and behavioral gaps
  stay explicit rather than being inferred from architecture or file shape.

## 14. Definition of Done for the Architecture

The architecture is complete when:

1. all three canonical skills pass internal and reference schema validation;
2. every package is self-contained and all references resolve;
3. `.agents/skills/` and `.claude/skills/` regenerate reproducibly from one
   source and have no drift;
4. capability normalization is deterministic, overlays are field-allowlisted,
   and every emitted action set is proven to be a subset of the canonical set;
5. Claude Code, Codex, and Gemini CLI discover and explicitly invoke all three
   skills in a fixture repo;
6. OpenCode with a local model discovers the `.agents` projection, and a generic
   reference harness can catalog and activate the same packages;
7. positive/negative trigger tests and approval-stop tests pass at the agreed
   thresholds;
8. the installer survives clean install, managed update, concurrent invocation,
   stale locks, path/symlink attacks, interruption, and rollback without data
   loss;
9. any executable local harness passes the normative sandbox, timeout,
   environment, network, resource, cleanup, and audit cases;
10. root instructions and provider shims contain no duplicated policy;
11. `scripts/verify` passes and is the exact command used by CI;
12. `compatibility/providers.toml` drives documentation and contains current
    tested client versions, evidence dates, sources, and honest support states.

## 15. Explicit Deferrals

- provider marketplaces/plugins/extensions;
- MCP servers and remote action integrations;
- a hosted skill registry;
- GUI management;
- automatic execution of skill scripts by the generic local harness;
- developer symlink projection mode;
- support claims for every local model;
- GitHub-specific CI/governance until a real remote and hosting decision exist;
- knowledge-graph generation as a mandatory requirement.

## 16. First Safe Implementation Slice

The initial approved slice was only Phases 0–2 plus one tiny fixture skill. It
proves provenance, schema validation, projection boundaries, and the canonical
source model before migrating the 97 KB source collection. Provider plugins and
a wholesale copy were intentionally excluded.

After that checkpoint passed, separately approved slices implemented Phases
3–8. The original gate remains documented here as execution history; it is no
longer the current phase boundary. The deferrals in Section 15 still apply.

The first review checkpoint should show:

- the proposed file list;
- the canonical fixture skill;
- dry-run output for `.agents` and `.claude` projections;
- validation diagnostics for deliberately broken fixtures;
- no changes outside this repository.
