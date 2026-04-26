---
name: frontend-startup-design-review
description: Use when planning a new web or Electron frontend page, app shell, bootstrap flow, route architecture, or startup/loading behavior before implementation, especially if first paint, first interaction, entry routing, prefetch, keepalive, or warmup choices could affect perceived speed.
---

# 前端启动设计前置审查

## 核心原则

- 在写代码前，先把“什么必须挡在首屏前、什么必须后置、什么允许预热、什么绝不能 hidden 偷跑”设计清楚。
- 目标不是“最早把系统全跑完”，而是“最早给用户可信、可操作、不会误导的第一屏”。
- 若设计阶段没有分清关键路径，后面大概率会靠一轮轮返工把非关键工作从首屏里挖出来。
- 设计审查结束前，必须产出可执行 contract，而不是只停留在分层口号。

## 何时必须启用

- 正在设计新页面、新桌面壳、新路由层、新 bootstrap / hydration 方案。
- 正在决定是否做 prefetch、keepalive、后台 warmup、shell/full bootstrap 分层。
- 用户要求“首屏更快”“第一次点开别卡”“不要再后期返工启动性能”。

## 不适用

- 明确只是小样式改动，不涉及启动顺序、数据装配、页面进入时机、运行态副作用。
- 纯静态页且首绘关键路径也不需要设计取舍，例如没有字体、首屏图片、chunk、CSS 装配或入口切换问题。

## 设计前必须回答的 10 个问题

1. 用户最先必须看到什么，才能认为“程序已经响应”？
2. 用户第一屏必须能点什么，哪些操作可以延后？
3. 哪些数据属于 `shell-critical`，哪些只是 `page-entry-required`？
4. 哪些静态资产属于首绘关键路径，哪些字体、图片、CSS、icon pack、route chunk 可以延后？
5. 应用有哪些启动入口：默认首页、deep link、恢复页签、reopen window、登录回调、错误恢复页？
6. 对每个入口，哪个是 `entry shell`，哪些数据/模块允许阻塞，哪些绝不能阻塞？
7. 哪些能力可以在 `idle / intent / viewport / entry-interactive` 后预热？
8. 哪些副作用只能在 `active` 页面或用户显式动作后运行？
9. hidden 态如果 mount 页面壳，哪些 effect 必须继续禁止？
10. 多页共享同一份 warmup 数据时，如何避免并发重复请求？

## 必须写清的异常态 contract

- `auth pending` 时首屏显示什么，哪些操作仍可点。
- `permission denied` / `feature locked` 时首屏显示什么。
- `config fetch failed` / `bootstrap partial` 时是否进入 `unknown/degraded`。
- `stale data` / `cached data only` 时哪些字段允许展示，哪些必须降级。
- 网络失败、超时、重试中时，首屏和重页面 guard 分别如何表现。

没有这组 contract，不算设计完成。

## 必须产出的设计分层

### 1. `shell-critical`

- 首屏可见、可信、可操作所需的最小闭包。
- 只包含“不等它就无法进入第一屏”的东西。

### 2. `page-entry-required`

- 只有用户第一次真正进入该页面时才需要的 full 数据、runtime、重模块。
- 允许页面内 loading/guard，不得反向绑回首页。

### 3. `idle-or-background-warmup`

- 只在当前入口稳定后、空闲时、hover/intention 明确后再做的代码或首包数据预热。
- 预热应能被取消、降级，不能压过首页关键路径。

### 4. `forbidden-while-hidden`

- hidden 态不得启动的行为：
- polling
- websocket
- runtime action
- 会话刷新/续期
- 持续性副作用

## 必须产出的对象级映射

- 至少把下列对象逐项归属到某一层：
  - `route`
  - `layout`
  - `provider`
  - `store`
  - `effect`
  - `request`
  - `route chunk`
  - `font / image / CSS / icon pack`
  - `SDK / analytics / auth refresh`
- 每一项都必须写：
  - 所属层
  - 触发时机
  - 取消/回收条件
  - `hidden -> active` 边界

## 默认设计姿势

- shell bootstrap 与 full bootstrap 分开。
- 首屏只显示最小真实状态，不伪装成“全系统已 ready”。
- 非首屏模块默认不要进入首帧同步路径。
- storage 恢复、筛选恢复、重弹层、历史页签恢复，都先假设应延后，除非证明确实属于 `shell-critical`。
- warmup 默认只预热代码和首包数据，不预热持续运行态。
- 静态资产默认也要过关键路径分层，不要只审数据链。
- 默认要先列入口矩阵，不要假设“首页”就是唯一启动入口。

## 评审红旗

- “先把所有页面和数据都初始化，后面体验就会稳。”
- “反正 hidden 了，看不见，先把 polling/websocket 开起来。”
- “prefetch 基本免费，先全开再说。”
- “首页就顺手把 full runtime 也拉了，省得后面再等。”
- “历史 UI 状态恢复一定要放首帧，不然用户会不习惯。”
- “四层 bucket 已经写了，具体对象实现时再说。”
- “异常态先不管，等实现时自然会补。”

## 设计交付模板

- 启动入口矩阵：
- 首屏目标：
- 首屏成功标准：
- `auth pending / permission / config failure / stale-data` contract：
- 每个入口的 `entry shell`：
- `shell-critical`：
- `page-entry-required`：
- `idle-or-background-warmup`：
- `forbidden-while-hidden`：
- 对象级映射：
- 首次进入重页面的 guard 方案：
- warmup 触发时机：
- 请求去重策略：
- 允许保留的页内 loading 边界：
- feature flag / kill switch：
- focused regression 计划：
- 回退策略：

## 实施前移交

- 若交付物里没有异常态 contract、对象级映射、成功标准、kill switch，不得进入实现。
- 设计确认后，再使用 `frontend-shell-first-warmup-guard` 进入实现与验证。
- 若现场已经慢了、卡了、黑了，不要继续停在设计讨论，直接转入该 skill 的“先量再改”流程。
