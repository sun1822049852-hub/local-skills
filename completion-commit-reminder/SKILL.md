---
name: completion-commit-reminder
description: Use when a coding, configuration, workflow, skill, or documentation-rule task is about to be reported complete after file writes may have occurred
---

# Completion Commit Reminder / 完成时提交提醒

## 核心原则

AI 认为任务完成时，先提醒用户是否需要提交；不要把未提交 diff 留到会话关闭后才被发现。

这不是自动提交规则。提醒归提醒，commit、push、stash、清理 worktree 都要等用户明确要求。

## 触发

使用本技能：代码、配置、工作流、skill、文档规则或其它会写文件的任务，准备向用户说“完成 / 修好 / 已收口 / 可以关闭”之前。

不使用本技能：纯只读解释、只读审查、查询命令输出、非代码闲聊。

## 收口检查

在本轮涉及的每个仓库或 worktree 里检查：

```powershell
git status --short
```

如果多个 worktree 相关，要写清检查的是哪个路径。

## 回复要求

完成说明末尾主动提醒：

- 若本轮已提交：说明 commit hash，问是否还需要 push 或 PR。
- 若本轮未提交但有改动：问用户是否要现在提交，或改为写 handoff。
- 若存在其它会话/用户改动：明确说这些不属于本轮提交范围。

## 禁止

- 不要未经用户要求就 commit、push、stash、删除、清理 worktree。
- 不要把其它会话或用户改动混进本轮提交。
- 不要把仍有未提交改动的仓库说成 clean。
