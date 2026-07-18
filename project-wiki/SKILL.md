---
name: project-wiki
description: Use when a repository lacks a compact project orientation map, agents repeatedly rediscover modules or flows, or an existing PROJECT_MAP/wiki may be stale after code changes.
---

# Project Wiki

Build broad, shallow project orientation before deep source reading. Code, tests, contracts, and runtime evidence remain truth; when they conflict, source wins.

## Interface

- `$project-wiki init`: inspect the repository and create one root `PROJECT_MAP.md` from [assets/PROJECT_MAP.md](assets/PROJECT_MAP.md).
- `$project-wiki read [topic]`: read the root map first, then only the named linked topic and directly relevant sources.
- `$project-wiki update [base-ref]`: compare working/staged changes plus the branch merge-base when available; update or remove only invalidated claims and mark unverifiable claims stale.
- `$project-wiki add <topic>`: add one focused `docs/wiki/NN-topic.md` from [assets/wiki-topic.md](assets/wiki-topic.md) and link it from the root map.

## Mode Behavior

- `init`: inspect tracked source, manifests, tests, and existing docs. In an empty or evidence-poor repository, create only the supported skeleton and list gaps; never invent modules, commands, or flows.
- `read`: use an existing root map as the first orientation source. Open only the requested topic and directly relevant current sources; report when the map is absent or stale.
- `update`: record dirty state, validate `base-ref`, and compare tracked, staged, and working changes. If the ref is unavailable, use a proven merge-base or mark the comparison gap. If a changed path cannot be mapped, record it as an explicit gap instead of guessing or broadly rewriting the map.
- `add`: keep the topic in the root unless the expansion threshold is met. Use the next available numeric prefix without renaming unrelated pages.

## Evidence Rules

Record repository-relative paths and stable `symbol` or section anchors. Do not store fragile source line number claims. Record the verified commit or dirty state and explicit gaps. Never include secrets, reversible private URLs, payloads, or personal data.

Recheck every affected source reference. Update it when evidence moved, mark it stale when current evidence is insufficient, and remove its claim when source deletion is verified. Dirty worktrees remain dirty in the map until a commit is actually verified.

An accepted architecture baseline may seed the map, but the baseline/ADR explains a decision while `PROJECT_MAP.md` describes the current repository. Neither replaces the other.

## Progressive Expansion

Start with one map. Split a topic only when the root would exceed 8 KB, or the topic exceeds 40 lines and is read repeatedly. Do not pre-create topic files. Delete obsolete claims when source deletion is verified; do not accumulate permanent removed entries.

Create a nested module `AGENTS.md` only for local hard constraints that differ from the parent. Keep it 5-10 lines: responsibility, public entry, owned state, allowed/forbidden dependencies, verification, and local traps. Ordinary module descriptions stay in the map.

## Boundaries

Use VOM/POR instead when the work needs high-risk operation completeness, truth/projection/observation ownership, propagation, exact evidence, failure, and cleanup. A map is navigation, never authority.
