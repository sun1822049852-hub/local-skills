---
name: resume-from-handoff
description: Use when a session must recover unfinished work from a handoff, saved plan, session log, or compacted context.
---

# Resume From Handoff

Resume is evidence recovery, not approval to implement.

1. Prefer the user-provided `handoff_id`. Otherwise search project handoffs; if multiple candidates exist, list ID, task, timestamp, branch/worktree, and path, then ask the user to choose.
2. Read the selected handoff, its parent/child chain, relevant plan, project rules, `PROJECT_MAP.md`, and current Git/worktree/dirty state. A child is newer than its parent; an emergency or initial marker is incomplete evidence.
3. Restate: goal, done/current work, last persisted action, possibly unpersisted action, next action, blockers, verification, must-not-change items, dirty paths, and unreviewed scope. Separate persisted facts, chat/compact summary, and inference.
4. Stop and wait for explicit approval. Before approval, do not write files, dispatch implementation agents, start services, mutate external state, or clean anything.
5. After approval, create a new `continuation_started` child with `parent_handoff_id`, then continue in that child. Do not overwrite the parent unless the user explicitly accepts that loss of lineage.

If sources conflict, show the conflict and proposed source of truth before implementation. Existing subagent authorization remains limited to its recorded goal/path/role and never bypasses resume approval. Missing handoff files must be reported as missing, not reconstructed as if persisted.
