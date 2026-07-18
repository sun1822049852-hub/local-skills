---
name: coding-session-start-gate
description: Use when a session is about to write code, config, workflow rules, skills, or files through write-capable commands.
---

# Coding Session Start Gate

Confirm one goal, must-not-change items, `allowed_paths`, and `forbidden_paths`. Then run:

```powershell
git rev-parse --show-toplevel
git worktree list --porcelain
git status --short
```

Read the nearest project `AGENTS.md` and existing `PROJECT_MAP.md`. Scan `docs/agent/worktrees/` for an active registry. Stop for same branch/worktree/path collision, missing authority, resume approval, or dirty overlap that cannot be isolated. Registry metadata is navigation; Git diff, tests, and runtime evidence remain truth.

When no stop or escalation exists, continue silently: do not emit routing JSON or a workflow catalog. Report only a blocking finding, a material risk escalation, or a user decision.

Keep one registry per writer session with branch, worktree, `allowed_paths`, `forbidden_paths`, status, and last verification. Never revert other changes or stage unrelated paths.

Do not run `scripts/audit_workflow_state.py` by default. Run it only for multiple active registries, a resume lineage conflict, an explicit audit request, or release/final full audit. Exit 2 is incomplete and blocks writes.

Do not commit, push, stash, reset, clean, merge, or delete without explicit user authority.
