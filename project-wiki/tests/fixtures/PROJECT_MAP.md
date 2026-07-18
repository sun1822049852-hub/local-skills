# Project Map Fixture: codex-working-rules

> Test-only fixture for the `project-wiki` RED/GREEN comparison. It is not the repository's maintained root map.

Verified commit or dirty state: `3ddb552` plus the current `workflow-knowledge-first` dirty refactor

## Purpose And Stack

- Purpose: versioned backup and review surface for personal Codex workflow rules, manuals, user-owned skills, and their validation assets.
- Users: the repository owner and coding agents that synchronize canonical assets to local runtime copies.
- Stack: Markdown instructions, YAML/JSON contracts, and Python validators/tests; PowerShell is the declared Windows shell.
- Product surfaces: no application frontend, backend service, business database, auth, payment, or sync service exists in this repository.
- External projections: `AGENTS.md` and principles copy to `C:/Users/18220/.codex`; the manual copies to the Desktop; owned skills copy to `.agents/skills/local` or `.codex/skills`.

## Start And Verify

| Task | Command or entry | Evidence/gap |
| --- | --- | --- |
| Workflow contracts | `python -B -m unittest discover -s skills-local/coding-session-start-gate/tests -p "test_*.py"` | Covers routing, audit, registry, budgets, and relocated contracts. |
| Project Wiki | `python -B -m unittest discover -s skills-local/project-wiki/tests -p "test_*.py"` | Covers package and scenario contracts. |
| VOM | `python -B -m unittest discover -s skills/verified-operation-map/tests -p "test_*.py"` | Covers schema validation and compact generation. |
| Skill package | `quick_validate.py <skill-directory>` | The validator is provided by the system `skill-creator` skill, not this repository. |

## Core Modules

| Module/path | Responsibility | Public entry/symbol | Owned data/state | Primary tests |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | Compact always-on hard contracts | `Silent Workflow Routing` | Global mandatory behavior | `skills-local/coding-session-start-gate/tests/` |
| `workflow-manual.md` | User-facing workflow invocation and procedures | `全局规则压缩后的阅读方式` | User operating guidance | Contract tests plus mirror hash checks |
| `working-principles.md` | Durable rationale and mature-practice boundaries | `Project Knowledge Entry Point` | Long-lived policy rationale | Contract tests |
| `skills-local/` | Locally executed personal workflow skills | each `SKILL.md` frontmatter | Executable workflow procedures | per-skill `tests/` |
| `skills/` | User-owned Codex skills backed up from `.codex/skills` | each `SKILL.md` frontmatter | Skill-specific procedures/assets | per-skill `tests/` |
| `skills-superpowers/` | Backed-up workflow dependency pack | named skill `SKILL.md` files | Imported workflow methods | package-specific tests where present |
| `docs/validation/workflow-validation/` | Replay evidence schemas and validators | `scripts/run_replay.py` | Validation evidence contracts | `tests/` |
| `docs/superpowers/` | Historical plans/specifications, not current runtime truth | dated plan/spec files | Decision and implementation history | none |
| `opencode-config/` | Separate OpenCode configuration and skill copies | `opencode.jsonc` | OpenCode projection | not part of Codex live sync by default |

## State Owners

| Truth/state | Sole writer | Readers/projections | Persistence | Propagation/failure |
| --- | --- | --- | --- | --- |
| Global workflow contracts | canonical root documents in this repository worktree | `.codex/AGENTS.md`, `.codex/working-principles.md`, Desktop manual | Git after separate commit authority | exact byte copy; unsynchronized mirrors must be reported |
| Local personal skill procedure | matching directory under `skills-local/` | `.agents/skills/local/<skill>/` | Git plus local runtime copy | validate before copy; runtime and repository may be independently dirty |
| Codex personal skill procedure | matching directory under `skills/` | `.codex/skills/<skill>/` | Git plus local runtime copy | validate before copy; do not overwrite unrelated live changes |
| Workflow session status | Git diff/tests/runtime evidence plus ignored handoff/registry files | audit script JSON report | worktree and `docs/agent/` local state | registry/audit is navigation, never code truth |
| POR contract | `skills/verified-operation-map/references/vom-por.schema.json` | validator and generator scripts | versioned JSON schema | validator exit state gates compact generation |

## Key Flows

| Flow | Trigger -> modules -> storage/external effect | Verification |
| --- | --- | --- |
| Global rule change | root documents -> contract tests -> exact copies to `.codex`/Desktop -> optional authorized Git commit/push | tests, hashes, `git diff --check`, status |
| Local skill change | `skills-local/<skill>/` -> scenario/contract tests -> package validation -> exact runtime copy | per-skill tests, validator, source/target hashes |
| VOM/POR use | POR JSON -> `validate_vom.py` -> `generate_vom_markdown.py` -> scoped compact Markdown | VOM unit suite and fresh commit/reference checks |
| Workflow audit | handoff DAG + active registries + optional manual/POR inputs -> `audit_workflow_state.py` -> JSON and exit code | audit unit suite; exit 2 means incomplete |

## Known Traps

- This is a backup/review repository, not the live runtime; editing it alone does not update Codex, Desktop, or local skills.
- There is no product frontend/backend/database here, so login/payment/business sync flows are not applicable.
- `docs/agent/handoffs/` and `docs/agent/worktrees/` are ignored local session state; they are not tracked project knowledge.
- Installed contract tests use different path resolution from repository-layout tests; verify both after synchronization.
- VOM schema/validator/generator are intentionally unchanged by the knowledge-first refactor; only its trigger and positioning change.
- Commit, push, mirror synchronization, and worktree cleanup are separate authority boundaries.

## Wiki Index

| Topic | When to read | Path |
| --- | --- | --- |
| None | The fixture remains under the split threshold. | N/A |

## Verification And Gaps

- Verified against: `git ls-tree`, current root documents, skill paths, tests, and synchronization rules at `3ddb552` plus this dirty refactor.
- Known stale or unverified areas: third-party skill internals and OpenCode behavior were not inspected; this fixture does not claim live mirror hashes.
- Last checked by/at: implementation forward-test fixture, 2026-07-18.
