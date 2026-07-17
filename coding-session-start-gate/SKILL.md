---
name: coding-session-start-gate
description: Use when a coding session is about to change code, fix bugs, continue implementation after approved resume, create features, refactor, change configuration, or run scripts that may write files
---

# Coding Session Start Gate / 代码会话启动闸门

## 核心原则

每个代码会话默认只服务一个目标。准备写代码前，先确认当前会话会不会和其它会话在同一项目、同一路径、同一 branch 或同一 worktree 上互相踩踏。不需要默认主会话；每个会话自己登记、自己说明边界。

Registry 只是导航和冲突预警，不是真源；真正判断仍看 Git 状态、diff、测试和运行结果。

## 触发

使用本技能：准备改代码、修 bug、继续实现、resume handoff 后获批继续、创建功能、重构、改配置、运行可能写文件的脚本。

不使用本技能：纯只读解释、只读审查、查询命令输出、非代码闲聊。

## 统一路由入口

本技能是 coding task 的 workflow-only unified routing entry。开工前先输出一个紧凑路由结果，只选择本任务真实可能触发的 workflow；不要展开完整规则/skill catalog，也不要把路由结果当成代码、测试、Git、trace 或 live 证据的替代品。

路由结果必须是一个 machine-checkable fenced template，且只包含这 6 个 key：

```json
{
  "must_use": ["Coding Session Start Gate"],
  "conditional": [],
  "not_triggered": [],
  "first_required_action": "<placeholder: replace with one scalar first action supported by current task evidence>",
  "stop_or_ask_conditions": [],
  "workflow_state_findings": {
    "audit_exit": "<placeholder: not_run|0|1|2>",
    "evidence": ["<placeholder: replace with concrete reason/evidence before emission>"],
    "related_stop_findings": [],
    "unrelated_warnings": []
  }
}
```

Before emitting a routing result, replace every placeholder and populate only conditions/workflows/findings supported by current task evidence; never copy template placeholders or potential stop conditions as facts.

字段语义：

- `must_use`: only workflows whose canonical trigger is already satisfied.
- `conditional`: only plausible candidate workflows whose trigger still needs one named fact or evidence.
- `not_triggered`: plausible candidates actually evaluated and ruled out; not_triggered must not dump the catalog and must not list every unselected workflow/skill.
- `first_required_action`: one scalar action only, never a list, never multiple competing first steps.
- `stop_or_ask_conditions`: preserve unresolved resume approval, handoff approval gap, related active registry collision on branch/worktree/path, incomplete audit, dirty-overlap ambiguity, and missing authority as stop/ask conditions.
- `workflow_state_findings`: compact read-only audit result/evidence. audit exit 2 is incomplete, never clean. Related stop findings must not be downgraded. Unrelated warnings may be reported without activating unrelated workflows.

Workflow State Audit step: when the task is resume/continuation, long or multi-agent, touches workflow/rule/manual/skill/VOM assets, or registry/handoff/manual/POR state is materially relevant, run `scripts/audit_workflow_state.py` before finalizing the routing result if the audit asset plus explicit inputs are available. The audit uses explicit arguments only and is read-only/report-only; it never fixes, archives, closes, or copies.

If audit is not applicable or the audit asset is unavailable, `audit_exit=not_run` is allowed only when `workflow_state_findings.evidence` states the concrete reason. A low-risk fast path does not have to manufacture absent workflow assets or expand heavy checks. If audit is applicable but required explicit inputs are missing, classify this as incomplete/stop-or-ask, not clean.

Audit exits: exit 0 = no findings; exit 1 = findings to classify by relevance/actionability; exit 2 = incomplete and stop/ask. Related stop findings cannot dispatch a writer; unrelated warnings do not activate unrelated workflows.

短矩阵只引用 canonical trigger，不复制规则全文：

AGENTS.md is the canonical source for canonical trigger references; this section only names relevant AGENTS.md sections and does not copy rule bodies or add another catalog.

| Signal group | Canonical trigger references |
| --- | --- |
| Resume, handoff, registry, dirty worktree, authority, parallel writer | Handoff Resume Approval Gate; Coding Session Start Gate; Subagent Dispatch And Lifecycle |
| Known changed cause for a bug | Known-Change Debugging |
| Live data, API shape, CLI/log/file format, external sample used for code | Live Evidence To Contract Gate |
| Source truth, read model, cache, event, queue, WebSocket, cross-context delivery | Consumer State Convergence Gate; Cross-Context Wakeup And Delivery Gate |
| New long-lived mechanism, project direction, workflow/rule/manual/map change | Architecture Baseline And Learning Loop; Workflow Discovery; Direction Challenge And Red-Team Review; Rule Placement Gate; Constraint Benchmarking; Workflow Manual Sync; Verified Operation Map |
| Completion after writes | Completion Commit Reminder |

Precedence: unresolved resume approval, handoff approval gap, missing authority, related active registry collision, dirty-overlap ambiguity, or related/incomplete workflow-state stop makes `first_required_action` a single stop/ask action before implementation or writer dispatch. Otherwise the first action is the existing Coding Session Start Gate read-only scope/worktree checks below.

Fast path: a low-risk, single-goal, existing-pattern coding change with no live data, state propagation, cross-context delivery, architecture/rule/map change, resume ambiguity, or registry collision stays on the light coding start path. Ordinary verbs such as add, modify, optimize, or adjust alone do not activate heavy workflows.

## 启动前只读检查

在项目根目录或候选目录先只读检查：

```powershell
git rev-parse --show-toplevel
git worktree list --porcelain
git status --short
```

同时检查项目是否有 `AGENTS.md`、项目地图、`docs/agent/worktrees/` registry。若只检查当前 `cwd`，必须明说没有检查其它 worktree。

## Registry

每个会话一个文件：`docs/agent/worktrees/<handoff_id>.md`。`INDEX.md` 可选汇总，但不是真源。

最少字段：

- `status`: `active` / `merged` / `abandoned` / `archived`
- `target`
- `handoff_id`
- `parent_handoff_id`
- `branch`
- `worktree`
- `allowed_paths`
- `forbidden_paths`
- `updated_at`
- `last_verified` 或验证缺口

## 开工规则

1. 先确认本会话唯一目标、必须不变项、允许和禁止路径。
2. 查 active registry 是否覆盖同一路径、branch 或 worktree。
3. 有冲突就停住说明冲突，不直接改代码。
4. 可能并行且当前不在独立 worktree 时，先只读侦察影响范围，再建议或创建独立 branch/worktree，并登记 registry。
5. 用户明确说只有当前会话可做 fast-path，但仍要说明检查的是哪个路径。
6. 若 `git status --short` 已有未提交改动但仍不建独立 worktree，写文件前必须说明 fast-path 判断：已有改动路径、是否与本轮允许路径重叠、不建 worktree 的理由、只暂存/提交本轮文件的做法、剩余风险。

## 脏工作区 fast-path 表达

脏工作区不是自动禁止开工，也不是自动必须建 worktree。关键是先把隔离判断说清楚。

只有同时满足以下条件，才可以不建 worktree：

- 已有未提交改动和本轮允许路径不重叠。
- active registry 没有覆盖同一路径、同一 branch 或同一 worktree。
- 本轮能用精确路径暂存、提交或验证，不需要全仓库格式化、批量生成或批量移动。
- 用户没有要求独立 worktree、主 agent 只审查、并行实现或隔离分支。

开工前必须用白话说明：已有改动是什么、本轮会改什么、为什么不建 worktree、怎样避免混提交、哪些风险仍未覆盖。说不清就建 worktree 或停住问用户。

## Handoff 配合

做不完就用 `save-status-handoff`。从 handoff 恢复并获批继续后，先创建子 handoff；占位也可以，但必须写 `parent_handoff_id`，并登记到 registry。快 compact 时先写 `status: partial_emergency` 的最小断点。

## 清理规则

不默认删除 worktree。只有同时满足 `merged` 或 `abandoned`、worktree clean、registry 已 `archived`、handoff 已收口、用户明确确认，才可以删除。
