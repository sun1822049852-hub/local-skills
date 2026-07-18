---
name: save-status-handoff
description: Use when unfinished work, context risk, interruption, or a later session needs a reliable written checkpoint.
---

# Save Status Handoff

Write confirmed facts to `docs/agent/handoffs/<handoff_id>.md`; never overwrite a different ID. Reuse the current session ID, or create `YYYYMMDD-HHMMSS-xxxx`. Keep the common handoff near 20 lines:

```markdown
---
handoff_id: <id>
parent_handoff_id: <id or null>
status: in_progress
worktree: <path>
branch: <branch>
updated_at: <ISO-8601>
---
Goal: <goal>
Done: <verified progress>
Current: <current state>
Next: <one first action>
Blockers: <none or exact blockers>
Verified: <commands/results or gap>
Must not change: <boundaries>
```

Use an early marker only for resumable, parallel, long, or context-risk work. A resumed session creates a child only after user approval. When compact risk is immediate, save the smallest truthful checkpoint first. Read [references/handoff-schema.md](references/handoff-schema.md) for lineage, emergency, authorization, and registry fields.

Return the `handoff_id`, saved path, short summary, and `resume from handoff <id>`. If writing is impossible, output the same shape and state that it was not persisted. Stable project knowledge belongs in `PROJECT_MAP.md`, project rules, ADR/CONTEXT, or focused wiki pages, not the handoff.
