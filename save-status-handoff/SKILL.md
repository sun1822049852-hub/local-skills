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
- 进度写入 `docs/agent/session-log.md`
- 稳定约束写入 `docs/agent/memory.md`

若当前目录不是仓库或不适合写入文件，至少在回复里输出完整 handoff 内容和下会话启动指令，并明确“未实际落盘”。

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
1. 已更新的文件，或未落盘原因
2. handoff 摘要
3. 下个会话启动指令
4. 补充提醒

## Next-Session Command Shape
生成的启动指令必须要求下个会话：
- 先读最新 handoff、相关 plan、当前工作区状态和稳定约束
- 先复述当前目标、进度断点、下一步动作
- 不重做已完成部分
- 若文档与现场冲突，先指出差异再收敛
- 修改后继续更新会话记录
