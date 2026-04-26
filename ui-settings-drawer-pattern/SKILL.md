---
name: ui-settings-drawer-pattern
description: Use when implementing icon-triggered settings drawers or popovers with checkbox options, especially when layout compression, hidden-state conflicts, or checkbox sizing regressions occur.
---

# 设置抽屉样式复用规范

## 适用场景

- 页面右上角齿轮/图标按钮触发“设置弹层”。
- 弹层内是少量开关项（checkbox）。
- 需要紧凑布局，且在窗口变窄时不出现逐字竖排。
- 需要可复用、可关闭、可维护的前端实现。

## 目标效果（强约束）

1. 每一行布局为：`文字在前，复选框在后`。
2. 文案和复选框紧贴，行内不留大空白。
3. 弹层默认隐藏，点击齿轮打开，再点齿轮或点外部可关闭。
4. 不能被全局 `input` 样式污染成大方框。
5. `.hidden` 必须可靠生效，不能被组件样式覆盖掉。

## HTML 模板

```html
<div class="settings-wrap">
  <button id="settingsBtn" class="icon-btn" type="button" aria-label="设置">⚙</button>
  <div id="settingsPanel" class="settings-panel hidden">
    <label class="inline">
      <span>使用冷却中的物品</span>
      <input id="optIncludeCooling" type="checkbox" />
    </label>
    <label class="inline">
      <span>显示种子</span>
      <input id="optShowSeed" type="checkbox" />
    </label>
    <div class="muted">冷却中可选：484件</div>
  </div>
</div>
```

## CSS 关键规则

```css
.settings-wrap {
  position: relative;
  display: inline-flex;
}

.settings-panel {
  position: absolute;
  right: 0;
  top: 36px;
  z-index: 20;
  min-width: 220px;
  width: max-content;
  max-width: min(320px, calc(100vw - 24px));
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px;
  border: 1px solid #d0d7de;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.2);
}

.settings-panel.hidden {
  display: none;
}

.settings-panel .inline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  white-space: nowrap;
  font-size: 13px;
}

input[type="checkbox"],
input[type="radio"] {
  min-width: 0;
  width: 14px;
  height: 14px;
  padding: 0;
  margin: 0;
}
```

## JS 交互规范

1. 仅维护一个布尔状态：`settingsOpen`。
2. `setSettingsOpen(open)` 只做两件事：更新状态 + 切换 `.hidden`。
3. 点击齿轮时切换；点击面板外关闭；按 `Escape` 关闭。
4. 不直接写内联 `style.display`，统一走 class 切换。

## 默认值规范

- 涉及“显示高级字段”（如显示种子）时，默认值建议为 `false`。
- 有本地存储时，版本号要可升级（如 `*_prefs_v2`），避免旧缓存污染新默认值。

## 常见坑

1. `input` 全局样式给了 `min-width: 220px`，导致 checkbox 变大方框。  
修复：单独覆盖 `input[type="checkbox"]`。

2. `.hidden {display:none}` 被 `.settings-panel {display:flex}` 覆盖。  
修复：显式写 `.settings-panel.hidden {display:none}`。

3. 文字逐字竖排。  
修复：面板设最小宽度 + 行内 `white-space: nowrap`。

## 验收清单

1. 齿轮可开可关，外部点击可关闭。
2. 设置项为“文字前、框后”。
3. 复选框尺寸正常，不是大方框。
4. 窄窗口下仍横向排版，不竖排。
5. 默认“显示种子”关闭。

