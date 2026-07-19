---
name: project-wiki
description: Use when a repository lacks a compact project orientation map, agents repeatedly rediscover modules or flows, or an existing PROJECT_MAP/wiki may be stale after code changes.
---

# Project Wiki

Build broad, shallow project orientation before deep source reading. Code, tests, contracts, and runtime evidence remain truth; when they conflict, source wins.

## Interface

- `$project-wiki init`: inspect the repository and create one root `PROJECT_MAP.md` from [assets/PROJECT_MAP.md](assets/PROJECT_MAP.md).
- `$project-wiki read [topic]`: read the root map first, then only the named linked topic and directly relevant sources.
- `$project-wiki update [base-ref]`: maintain the map from tracked, staged, and working changes.
- `$project-wiki add <topic>`: add one source-supported topic, root-first.

## Mode Behavior

- `init`: inspect tracked source, manifests, tests, and existing docs. In an empty or evidence-poor repository, create only the supported skeleton and list gaps; never invent modules, commands, or flows.
- `read`: use an existing root map as the first orientation source. Open only the requested topic and directly relevant current sources; report when the map is absent or stale.
- `update`: record dirty state and validate `base-ref`; use a proven merge-base or record the comparison gap. For added paths, add source-supported claims; for modified paths, recheck affected claims; for deleted paths, remove claims only after verified deletion. Mark unverifiable claims stale. If a changed path cannot be mapped, record an explicit gap; never guess or broadly rewrite.
- `add`: add the topic to the root first. Split it only when the root would exceed 8 KB, or the topic exceeds 40 lines and is read repeatedly. Use the next `docs/wiki/NN-topic.md` from [assets/wiki-topic.md](assets/wiki-topic.md), link it from the root, and preserve unrelated pages.

## Evidence Rules

Record repository-relative paths and stable `symbol` or section anchors. Do not store fragile source line number claims. Record the verified commit or dirty state and explicit gaps. Never include secrets, reversible private URLs, payloads, or personal data.

Recheck every affected source reference. Update it when evidence moved, mark it stale when current evidence is insufficient, and remove its claim when source deletion is verified. Dirty worktrees remain dirty in the map until a commit is actually verified.

An accepted architecture baseline may seed the map, but the baseline/ADR explains a decision while `PROJECT_MAP.md` describes the current repository. Neither replaces the other.

## Progressive Expansion

Start with one map. Do not pre-create topic files or accumulate permanent removed entries.

Create a nested module `AGENTS.md` only for local hard constraints that differ from the parent. Keep it 5-10 lines: responsibility, public entry, owned state, allowed/forbidden dependencies, verification, and local traps. Ordinary module descriptions stay in the map.

## Boundaries

Use VOM/POR instead when the work needs high-risk operation completeness, truth/projection/observation ownership, propagation, exact evidence, failure, and cleanup. A map is navigation, never authority.
