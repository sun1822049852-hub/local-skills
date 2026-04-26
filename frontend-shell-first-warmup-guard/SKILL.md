---
name: frontend-shell-first-warmup-guard
description: Use when implementing or debugging startup/loading behavior in an existing web or Electron frontend after the startup contract is already chosen, especially when changing bootstrap, hydration, route-entry guards, hidden-page warmup, or request deduplication.
---

# 前端首屏壳优先与预热护栏

## 核心原则

- 先让用户看到稳定、可信、可操作的 shell，不等全量数据与全量运行时完成。
- 非关键工作不得绑死首屏关键路径。
- hidden warmup 只能做预热，不能偷跑活跃副作用。
- 若还没确定 shell/full/bootstrap/warmup 边界，先停下，改用 `frontend-startup-design-review`。

## 何时必须启用

- 首屏慢、黑屏、白屏、首点卡顿、切页首次等待明显。
- 设计边界已经存在，正在改 `bootstrap`、`hydration`、`prefetch`、`keepalive`、`warmup`、路由首次加载、启动 trace。
- 正在修“hidden warmup 抢跑副作用”“warmup 重复请求”“首屏又被 full runtime 绑回去”。

## 不适用

- 还在设计“什么属于 `shell-critical`、什么必须 hidden 禁行、是否拆 shell/full bootstrap”。
- 纯静态页面，没有真实启动链、数据链或运行态副作用。
- 明确只改视觉样式，不碰首屏装配、数据时序、预热与交互节奏。

## 工作流

### 1. 先量再改

- 先打 trace：窗口出现、entry shell ready、首屏 commit、关键请求发出/返回、entry interactive。
- 先确认慢点在：
  - 首帧同步代码
  - 首屏数据请求
  - 非首屏模块误入首屏
  - hidden warmup 重复请求
- 没有新鲜证据，不要直接归因。

### 2. 先分层，再优化

- 若现场没有明确的启动 contract，先补设计，不要直接在实现层拍脑袋优化。
- `shell-critical`
  - 首屏必须阻塞的最小闭包，只保留可信可见可点所需能力。
- `page-entry-required`
  - 用户第一次真正进入该页时才需要的 full 数据或 runtime。
- `idle-or-background-warmup`
  - 只适合在 idle、intent、viewport、entry interactive 之后预热的资源。
- `forbidden-while-hidden`
  - hidden 态不得启动 polling、websocket、runtime action、会话变更、持续副作用。

### 3. 首屏默认姿势

- shell bootstrap 与 full bootstrap 分开。
- 首页只等最小闭包；重页面允许页面内 loading/guard。
- 首帧避免同步 storage、同步 IPC、重计算、非首屏模块 eager mount。
- 若真实状态尚未 ready，展示 `loading/unknown/degraded`，不要展示误导性的假真相。

### 4. 预热护栏

- warmup 只允许做：
  - 代码 chunk preload / route preload
  - 只读、幂等、可取消的首包数据获取
  - 响应缓存填充、promise memoization、in-flight dedupe
  - 下一个最可能动作的只读准备
- hidden warmup 不能跨过 `hidden -> active` 行为边界。
- hidden warmup 明确禁止：
  - hidden-mount 整页 effect 树
  - store subscription 常驻
  - SDK init / analytics 上报
  - auth refresh / token renew / session续期
  - 长生命周期 timer、listener、background job
- 多页共享 warmup 数据时，优先做 in-flight dedupe，避免同一轮并发重复请求。
- 预热若反向拖慢首页、吃掉大量 CPU/内存、或引入副作用，立刻降级。

### 5. 回归必须锁住

- 首屏能先亮壳，不等 full bootstrap。
- 首次进入重页面时显示页内 guard，而不是把等待偷回首页。
- hidden warmup 不启动 polling/websocket/runtime action。
- warmup 共享接口不会无意义重复请求。
- `hidden -> active` 转场后，真正进入该页不会重新走错路径，也不会漏掉本该只在 active 才运行的 effect。
- 用户从未进入被预热页面时，预热资源能回收或自然失效，不留下常驻后台负担。
- 预热结果真正被 active 页面消费，而不是后台白跑一次。

## 快速检查单

- 首页是否只等待“当前页最小闭包”？
- `shell bootstrap` 与 `full bootstrap` 是否已拆开？
- 首帧是否仍有同步 storage / 同步 IPC / 非首屏 eager mount？
- hidden warmup 是否只拉首包，不启动活跃副作用？
- 共享 warmup 请求是否有 in-flight dedupe？
- deep link / 恢复页签 / 非首页入口下，是否仍有正确的 entry shell 与 warmup 边界？
- `hidden -> active` 后是否验证了 effect、数据、guard、回收四件事？
- 修复前后是否有 fresh trace 和 focused regression？

## 红旗

- “先把所有页面和数据都拉完再显示。”
- “hidden 页 mount 了，顺手把 polling 也开了。”
- “prefetch 基本不要钱。”
- “不用量，肯定是后端慢。”
- “先把上次页签、筛选、状态同步恢复到首帧里。”
- “整页先 hidden mount 一下，反正我没主动触发 runtime action。”

## 交付口径

- 优先用产品行为表达：
  - 首屏先亮了什么
  - 哪些能力延后到首次进页
  - 哪些资源改成后台预热
  - 哪些副作用继续严格只在 active 态运行
- 不要把“更快可见”说成“整机已 fully ready”。
