---
name: resume-from-handoff
description: Use when a new session must continue unfinished work from prior handoff notes, saved plans, and the current workspace state
---

# Resume From Handoff

## Overview
新会话先承接断点，但不能读完 handoff 后自动实现。先恢复事实、复述断点，再等用户批准。

原则：
- 先读 handoff，再核对现场
- 先复述理解，再等批准
- 用户批准后再续做
- 若本轮提示末尾附带补充要求，优先并入承接约束

## Read Order
按顺序读取：
1. 用户给出的 `handoff_id` 对应 handoff 文件
2. 若未给 `handoff_id`，先查找当前项目候选 handoff，并在多个候选时停下来让用户选择
3. 当前任务对应的 plan
4. 当前 `chunk/task` 记录
5. `docs/agent/memory.md` 中与本任务相关的稳定约束
6. 当前分支、worktree、工作目录和未提交改动状态

若部分文件不存在，要明确指出缺口，不要假装读到了。

## Handoff ID Lookup
恢复时优先按 `handoff_id` 精确定位，避免同一项目多个终端会话读错断点。

- 从用户消息中识别 `handoff_id`，包括 `handoff_id: <id>`、`resume from handoff <id>`、`恢复 <id>` 或 handoff 文件名里的 ID。
- 有 `handoff_id` 时，优先读取 `docs/agent/handoffs/<handoff_id>.md`；若项目有其它约定路径，也可以查对应索引或 handoff 目录。
- 读取后必须核对文件内元信息的 `handoff_id`、`project_root`、`worktree`、`branch` 和当前现场是否一致或可解释。
- 若找不到这个 ID，列出已检查路径和可用候选，停住让用户确认；不要退回“最新 handoff”继续。
- 若未给 `handoff_id`，先在当前项目的 `docs/agent/handoffs/*.md`、项目已有 handoff 索引和 `session-log.md` 汇总里找候选。
- 如果候选多于一个，列出每个候选的 `handoff_id`、更新时间、任务摘要、worktree/branch、文件路径，然后停住让用户选择。
- 只有候选唯一且元信息与当前项目/worktree匹配时，才可以读取该候选，并说明“因为候选唯一所以读取”。
- 旧项目只有 `session-log.md`、没有 `handoff_id` 时，可以按旧格式只读恢复，但必须说明这是 legacy handoff，存在多会话混淆风险。
- 如果候选包含 `parent_handoff_id`，优先按父子关系判断最新链路；子 handoff 比父 handoff 更新，父 handoff 不能代表子会话进度。

## Continuation Marker
从 handoff 恢复并获得用户批准继续后，先创建续作占位，再开始实质实现。

- 用户批准继续后，生成新的子 `handoff_id`，写入 `docs/agent/handoffs/<child_id>.md`。
- 子文件必须包含 `parent_handoff_id: <当前读取的 handoff_id>` 和 `status: continuation_started`。
- 续作占位只需要写清当前目标、父 handoff、cwd/worktree/branch、获批时间、下一步第一刀和“详细进度尚未写入”。
- 创建成功后，在对话里回显新的子 `handoff_id`；后续保存 handoff 必须更新这个子 ID。
- 如果创建失败，停止实质实现并说明原因；不要继续做一堆工作却没有任何新 handoff 文件。
- 若用户明确要求“继续写回原 handoff”，必须先说明这会覆盖父断点、降低多会话可追踪性，再等用户确认。

## Subagent Authorization Carryover
如果当前 handoff 或同一父子链上的 handoff 里有 `subagent_authorization.status: granted_for_this_goal`，可把它视为同一目标的既有用户授权上下文，但不能跳过恢复批准闸门。

恢复时必须复述：
- 授权来自哪个 handoff。
- 授权只覆盖哪个目标、路径或角色。
- 是否仍在 `expires_when` 范围内。
- 恢复后如果用户批准继续，实现阶段是否会使用子 agent。

未获批准前，仍不得派实现子 agent、不得改代码。若当前请求已经偏离原目标、路径或角色边界，必须把授权标为不适用，并重新询问用户。获批继续并创建子 handoff 时，若授权仍适用，可以把授权写入子 handoff，并标明它继承自哪个父 handoff。

## Auto Compact Recovery
如果用户说“刚才让你 handoff 但触发 auto compact 了”，先把 compact 摘要当线索，不当真源。

按顺序处理：
1. 先查是否有用户给出的 `handoff_id`，或在当前项目 `docs/agent/handoffs/*.md` 中查最近的 handoff。
2. 按 `parent_handoff_id` 串起父子链；如果只找到父 handoff，但用户说明中间有过恢复会话，必须把父 handoff 标为“可能过期”，不要当最新进度。
3. 若找到 `status: initial_marker`，说明首轮已经开始但详细进度可能没有写入；用它定位目标、cwd/worktree/branch、必须不变项和可能存在的 `subagent_authorization`，不要把它当完整进度。
4. 若找到 `status: continuation_started`，说明续作会话已经开始，但详细进度可能没有写入；用它定位父 handoff 和后续现场，不要退回父 handoff 当最新。
5. 若找到 `status: partial_emergency`，说明这是紧急断点，只能证明其中已写明的事实；未写明部分都算未确认。
6. 若没有找到 initial marker、子 handoff 或紧急 handoff，明确说明“没有发现可靠落盘的续作 handoff”，再用 compact 摘要、git 状态和现场文件做只读重建。
7. 重建结果必须标注可信度：哪些来自落盘文件，哪些来自 compact 摘要，哪些来自当前现场推断。
8. 复述后停住，等待用户批准；不能因为 compact 摘要里写着“下一步”就自动实现。

## First Response Contract
继续执行前，先简明说明：
- 本次读取的 `handoff_id` 和 handoff 文件路径，或未能唯一定位的原因
- 当前总目标
- 当前方案与 `chunk/task`
- 已完成内容
- 未完成内容
- 最后落盘动作
- 可能未落盘动作
- 下一步第一刀
- 必须不变项
- 未检查范围
- 文档记录与现场状态是否一致

说明后必须停住，等待用户明确批准，除非用户同一条消息明确要求“复述后直接继续实现”或等价授权。

## Conflict Handling
若 handoff 与现场不一致，先说明：
- 冲突点
- 可能原因
- 准备以什么为准收敛

在冲突未收敛前，不要直接改关键路径。

## Execution Rules
- 默认不直接继续实现。读 handoff、读 plan、看 git 状态、核对文件是否存在属于只读恢复，可以先做；实现动作必须等批准。
- 未获批准前，不派实现子 agent、不改代码、不删除或清理文件、不跑会写入数据/启动服务/触发真实账号或网络动作的命令。
- 不重做已完成部分，除非验证表明旧结果不可信
- 获批继续后，先创建带 `parent_handoff_id` 的子 handoff；后续保存 handoff 必须沿用这个子 `handoff_id`，除非用户明确要求新断点
- 严格遵守已记录的失败路径和错误约束
- 若本次改动触及关键行为，先声明保护范围、保持不变项和验证方式
- 修改后更新 `docs/agent/session-log.md`
- 若形成新的稳定约束，再更新 `docs/agent/memory.md`

## Verification
完成本轮工作前，至少要：
- 运行与改动风险匹配的验证
- 明确验证命令或检查方式
- 读取结果后再下结论
- 若无法验证，明确说明缺口

## Default Task Interpretation
当用户只说“继续刚才的工作”时，应理解为：

先查找当前项目的 handoff 候选；如果存在多个候选，列出 `handoff_id`、更新时间、任务摘要和路径后停住让用户选择，不要默认读取最新一个。若候选唯一，则阅读该 handoff、相关 plan、稳定约束和当前工作区状态，复述当前目标、进度断点、下一步动作、必须不变项和未检查范围后停住，等待用户批准；若文档与现场不一致，先指出差异和建议以什么为准收敛。只有用户明确批准后，才承接未完成工作并做最小必要验证。
