---
name: resume-from-handoff
description: Use when a new session must continue unfinished work from prior handoff notes, saved plans, and the current workspace state
---

# Resume From Handoff

## Overview
新会话先承接断点，再继续执行，不要把“继续刚才工作”退化成重新分析一遍。

原则：
- 先读 handoff，再动手
- 先核对现场，再续做
- 先复述理解，再执行
- 若本轮提示末尾附带补充要求，优先并入承接约束

## Read Order
按顺序读取：
1. `docs/agent/session-log.md` 最新一节，或项目已有 handoff 文档
2. 当前任务对应的 plan
3. 当前 `chunk/task` 记录
4. `docs/agent/memory.md` 中与本任务相关的稳定约束
5. 当前分支、worktree、工作目录和未提交改动状态

若部分文件不存在，要明确指出缺口，不要假装读到了。

## First Response Contract
继续执行前，先简明说明：
- 当前总目标
- 当前方案与 `chunk/task`
- 已完成内容
- 未完成内容
- 下一步第一刀
- 文档记录与现场状态是否一致

## Conflict Handling
若 handoff 与现场不一致，先说明：
- 冲突点
- 可能原因
- 准备以什么为准收敛

在冲突未收敛前，不要直接改关键路径。

## Execution Rules
- 默认直接继续执行，不停在泛泛分析
- 不重做已完成部分，除非验证表明旧结果不可信
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

阅读最新 handoff、相关 plan、稳定约束和当前工作区状态，复述当前目标、进度断点和下一步动作后，直接承接未完成工作；若文档与现场不一致，先指出差异并收敛；完成后更新会话记录并做最小必要验证。
