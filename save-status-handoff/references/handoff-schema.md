# Advanced Handoff Contract

Read this reference only for long, parallel, resumed, compact-risk, or multi-agent work.

## Metadata

Required identity fields are `handoff_id`, `parent_handoff_id`, `status`, `created_at`, `updated_at`, `project_root`, `worktree`, `branch`, and `task`. Keep one handoff file per ID and one registry file per writer session.

Registry records also contain `target`, `allowed_paths`, `forbidden_paths`, and `last_verified` or the verification gap. An active same branch, worktree, or related path collision stops writes.

## Statuses

- `initial_marker`: early anchor for resumable, parallel, long, or context-risk work; not a full progress report.
- `continuation_started`: child marker created after the user approves resuming `parent_handoff_id`.
- `partial_emergency`: minimal truthful checkpoint written before imminent context loss.
- `in_progress`: current detailed checkpoint.
- `complete`: goal and fresh verification finished.

Never treat a parent as the latest state when a child exists. Never treat `initial_marker`, `continuation_started`, or `partial_emergency` as complete progress.

## Recovery Fields

Preserve goal, done/current/next, blockers, last persisted action, possibly unpersisted action, verification, must-not-change items, dirty paths, unreviewed scope, and failed approaches. If subagent authorization exists, record its goal/path/role boundary, source handoff, expiry, and `requires_resume_approval: true`.

## Resume Rule

Reading the chain is read-only evidence recovery. Restate the breakpoint and wait for explicit user approval before creating a child, writing code, dispatching an implementation agent, starting services, or changing external state.
