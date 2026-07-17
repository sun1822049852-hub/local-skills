---
name: save-status-handoff
description: Use when a session is ending, context is tight, or unfinished work must be handed to a later session with a reliable written checkpoint
---

# Save Status Handoff

## Overview
在会话结束前，把当前工作的真实状态落盘，并生成下个会话可直接使用的承接指令。

原则：
- 只写已确认事实，不伪造完成度
- 断点要能回答“做到哪了、别再犯什么、下一步先做什么”
- 若本轮提示末尾附带补充要求，视为本次 handoff 的额外重点

## When to Use
适用于：
- 上下文将满
- 任务未完成，需要切新会话
- 已经形成关键约束、踩坑记录或阶段性成果
- 即将暂停、切换分支、切换 worktree、切换话题

不适用于：
- 纯闲聊
- 没有任何有效进展的回合

## Output Targets
优先使用当前项目已有的 handoff 路径。

若项目未约定，默认：
- 当前会话断点写入 `docs/agent/handoffs/<handoff_id>.md`
- 可选索引或汇总写入 `docs/agent/session-log.md`
- 稳定约束写入 `docs/agent/memory.md`

若当前目录不是仓库或不适合写入文件，至少在回复里输出完整 handoff 内容和下会话启动指令，并明确“未实际落盘”。

## Handoff ID Rule
每个可恢复会话必须有一个 `handoff_id`，用来避免同一项目多个终端会话互相覆盖。

- 默认格式：`YYYYMMDD-HHMMSS-xxxx`，其中 `xxxx` 是 4-8 位小写字母数字短码。
- 新会话第一次保存 handoff 时生成新 `handoff_id`。
- 如果当前对话已经有本轮 `handoff_id`，继续更新同一个 handoff 文件；不要另起 ID，除非用户明确要求新断点。
- 如果用户指定已有 `handoff_id`，只更新对应文件；若文件不存在或元信息明显不匹配，先说明风险并停止，不要覆盖其它会话。
- 若目标文件已存在但内容里的 `handoff_id` 不一致，必须停止并要求用户确认。
- `session-log.md` 只能做索引或汇总，不能作为多个并发会话的唯一 handoff 真源。

handoff 文件开头至少写入这些元信息：

```yaml
handoff_id: <id>
parent_handoff_id: <id or null>
created_at: <ISO-8601 local time>
updated_at: <ISO-8601 local time>
project_root: <repo root or cwd>
worktree: <git worktree path or cwd>
branch: <current branch or unknown>
status: in_progress
task: <short human-readable task>
```

## Initial Marker
长任务、代码任务、多 agent 任务、可能超过一轮的任务，首轮不要等到快结束才第一次落盘。

- 一旦目标、工作区和必须不变项已经基本明确，先写一个最小 `initial_marker` handoff。
- `initial_marker` 不是完整 handoff，只证明本目标已经开始，并记录可恢复锚点。
- 如果首轮已经拿到子 agent 授权，`initial_marker` 也必须带上 `subagent_authorization`；不要把授权只留在聊天里。
- 如果后续来不及完整 handoff 或突然 auto compact，下一轮至少能按这个 ID 找到首轮目标和现场。
- 如果任务后来很快完成，可以在同一个 handoff 文件里把状态更新为 `complete` 或在最终说明里注明已被提交替代。

最小首轮占位示例：

```yaml
handoff_id: <new-id>
parent_handoff_id: null
status: initial_marker
created_at: <ISO-8601 local time>
updated_at: <ISO-8601 local time>
project_root: <repo root or cwd>
worktree: <git worktree path or cwd>
branch: <current branch or unknown>
task: <short human-readable task>
must_not_change:
  - <known boundary>
next_first_step: <next action if compact happens>
subagent_authorization:
  status: granted_for_this_goal
  granted_by_user_in_current_thread: true
  goal_summary: <same goal only>
  allowed_paths:
    - <path boundary>
  allowed_roles:
    - implementer
    - reviewer
  expires_when: goal_complete
  requires_resume_approval: true
known_incomplete:
  - initial marker only; detailed progress not written yet
```

## Subagent Authorization
如果用户在首轮或同一 handoff 链续作中明确授权“本目标允许使用子 agent / 主 agent 只审查 / 后续 handoff 接力沿用子 agent 授权”，必须把授权写进当前 handoff，避免下个会话反复要求用户重新提醒。若已有 `initial_marker`，立即更新同一个 handoff 文件；不要另起授权记录。

建议字段：

```yaml
subagent_authorization:
  status: granted_for_this_goal
  granted_by_user_in_current_thread: true
  goal_summary: <same goal only>
  allowed_paths:
    - <path boundary>
  allowed_roles:
    - implementer
    - reviewer
  expires_when: goal_complete
  requires_resume_approval: true
```

写入时必须保证：
- `goal_summary`、`allowed_paths`、`allowed_roles` 写清当前目标、路径和角色边界，不能写成“所有后续任务”或其它永久全局授权。
- 授权只对同一个目标和同一条 handoff 链有效；目标、路径或角色变了就要重新确认。
- `requires_resume_approval: true` 必须保留。恢复会话仍必须先复述断点并等待用户批准继续实现，未获批准前不得派实现子 agent。

## Continuation Lineage
从已有 handoff 恢复并继续工作的会话，必须写成新的子 handoff，不能静默覆盖父 handoff。

- 如果本会话是从 `parent_handoff_id` 恢复而来，第一次获批继续后，先创建新的 `handoff_id` 文件，并写入 `parent_handoff_id: <parent>`.
- 这个子文件可以先是最小占位，状态用 `continuation_started`；它的目的就是证明“父 handoff 之后已经有过续作会话”。
- 后续本会话所有 handoff 更新都写入子 `handoff_id` 文件，不再写回父文件，除非用户明确要求更新父文件。
- 如果子会话刚开始就遇到 auto compact，至少应该已经有 `continuation_started` 或 `partial_emergency` 子文件可供下个会话定位。
- 如果无法创建子 handoff 文件，必须在对话里明确说“续作 handoff 未落盘”；后续恢复不能把父 handoff 当成最新进度。

最小续作占位示例：

```yaml
handoff_id: <new-child-id>
parent_handoff_id: <parent-id>
status: continuation_started
created_at: <ISO-8601 local time>
updated_at: <ISO-8601 local time>
project_root: <repo root or cwd>
worktree: <git worktree path or cwd>
branch: <current branch or unknown>
task: <short human-readable task>
known_incomplete:
  - continuation marker only; detailed progress not written yet
```

## Emergency Partial Handoff
当用户要求 handoff 时上下文已经接近红线，先抢救最小可恢复断点，再补完整细节。

触发条件：
- 用户明确要求 handoff / 冻结断点，但当前上下文可能马上触发 auto compact。
- 任务很长，完整整理会有来不及落盘的风险。
- 已经出现疑似 compact 前兆，或者用户明确担心“handoff 还没写完就 compact”。

执行顺序：
1. 先生成或沿用 `handoff_id`。
2. 立刻写入 `docs/agent/handoffs/<handoff_id>.md`，状态标记为 `partial_emergency`。
3. 最小内容只写已确认事实：当前目标、最后确认进度、最后落盘动作、可能未落盘动作、下一步第一刀、必须不变项、未验证缺口、当前 cwd/worktree/branch。
4. 立刻在对话里回显 `handoff_id` 和 `resume from handoff <handoff_id>`。
5. 如果还有上下文余量，再回到同一个文件补全 Required Content，并把状态改为 `in_progress` 或保留 `partial_emergency` 加说明。

紧急 handoff 不追求完整，但必须诚实标注：

```yaml
status: partial_emergency
compact_risk: true
parent_handoff_id: <id or null>
known_incomplete:
  - <what was not checked or not fully written>
```

如果来不及落盘，只能在对话里输出最小 handoff 内容，必须明确写“未实际落盘”；下个会话不能把它当成已保存文件。

## Required Content
handoff 至少覆盖以下内容：

### 当前目标
- 本次总目标
- 当前方案或 plan 名称

### 进度断点
- 当前 `chunk`
- 当前 `task`
- 已完成内容
- 正在进行内容

### 现场状态
- 正在改动的文件或模块
- 当前分支、worktree、工作目录
- 是否存在未提交改动

### 错误与约束
- 已尝试但失败的路径
- 失败原因
- 后续不要再犯的约束
- 必须保持不变的关键行为

### 验证状态
- 已执行的验证
- 验证结果
- 尚未覆盖的验证缺口

### 下一步第一刀
- 下个会话先做什么
- 做完后立刻验证什么

## Memory Rule
只有稳定信息才写入 `memory.md`：
- 长期偏好
- 环境事实
- 已定案决策
- 反复出现的坑
- 后续仍然生效的限制

不要把短期进度和一次性待办写进 `memory.md`。

## Response Contract
完成时按这个顺序输出：
1. `handoff_id` 和已更新的文件，或未落盘原因
2. handoff 摘要
3. 下个会话启动指令，必须直接包含这个 `handoff_id`
4. 补充提醒

回复里必须把编码放在用户容易复制的位置，例如：

```text
handoff_id: 20260705-143012-a8f3
下个会话启动指令：resume from handoff 20260705-143012-a8f3
```

## Next-Session Command Shape
生成的启动指令必须要求下个会话：
- 先按 `handoff_id` 读取对应 handoff 文件、相关 plan、当前工作区状态和稳定约束
- 先复述当前目标、进度断点、下一步动作
- 不重做已完成部分
- 若文档与现场冲突，先指出差异再收敛
- 修改后继续更新会话记录
