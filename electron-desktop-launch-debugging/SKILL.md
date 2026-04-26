---
name: electron-desktop-launch-debugging
description: Use when Windows 上的 Electron 桌面程序打不开、黑屏、报 spawn EINVAL、主进程 API 异常，或 require("electron") 行为异常，需要快速定位启动环境、运行时安装和 file:// 资源路径问题。
---

# Electron 桌面启动排错

## 适用场景

- Windows 上运行 Electron 桌面壳时，直接报 `spawn EINVAL`。
- 窗口能弹出，但全黑、不显示任何内容。
- 主进程报 `TypeError: Cannot read properties of undefined (reading 'on')` 这类 Electron API 为空的错误。
- `require("electron")` 返回的是字符串路径，而不是 `app` / `BrowserWindow` / `ipcMain`。
- `Electron failed to install correctly`、缺少 `path.txt`、缺少 `dist/electron.exe`。

## 核心原则

1. 先查启动环境，再查入口代码。
2. 先确认 Electron 运行时是否完整，再查前端黑屏。
3. 在 `ELECTRON_RUN_AS_NODE=1` 没排除前，不要被后面的 `electron/main`、`ipcMain`、`BrowserWindow` 异常带偏。

## 三步快查

### 1) 先查是不是被强制跑成 Node

```powershell
Get-ChildItem Env:ELECTRON_RUN_AS_NODE
Get-ChildItem Env: | Where-Object { $_.Name -like 'ELECTRON*' } | Sort-Object Name
```

- 如果 `ELECTRON_RUN_AS_NODE=1` 存在，这是最高优先级根因。
- 典型表现：
- `require("electron")` 返回 Electron 可执行文件路径字符串。
- `require("electron/main")` / `require("electron/renderer")` 直接 `MODULE_NOT_FOUND`。
- 主进程里的 `ipcMain`、`app`、`BrowserWindow` 变成 `undefined`。

最小修复：

- 启动 Electron 前清掉该环境变量，不要把当前终端环境原样透传：

```js
function buildElectronLaunchEnv(env = process.env) {
  return Object.fromEntries(
    Object.entries(env).filter(([key]) => key.toUpperCase() !== "ELECTRON_RUN_AS_NODE"),
  );
}
```

### 2) 再查 Electron 运行时有没有装完整

```powershell
Test-Path "app_desktop_web/node_modules/electron/path.txt"
Test-Path "app_desktop_web/node_modules/electron/dist/electron.exe"
```

- 任意一个不存在，都说明 `electron` 包只装了壳，没装完整 runtime。
- 典型报错：
- `Electron failed to install correctly`
- `Cannot find module 'electron'` / 启动直接退

最小修复：

- 直接重跑安装脚本，必要时加镜像：

```powershell
$env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
node "app_desktop_web/node_modules/electron/install.js"
```

- 对启动器做自愈时，优先跑 `install.js`，不要让用户自己猜。

### 3) 窗口黑屏时，优先查 file:// 资源路径

```powershell
Get-Content -Raw -Encoding UTF8 "app_desktop_web/dist/index.html"
```

- 如果看到：

```html
<script src="/assets/..."></script>
<link href="/assets/...">
```

- 这在 Electron `loadFile()` 下会变成 `file:///assets/...`，高概率直接黑屏。

最小修复：

```js
// vite.config.js
export default defineConfig({
  base: "./",
});
```

- 修完必须重新构建 `dist`。

## Windows 启动器约束

- 不要直接 `spawn(electron.cmd)`，在部分 Node 24 + Windows 环境会报 `EINVAL`。
- 优先改成 `process.execPath + electron/cli.js`：

```js
const command = process.execPath;
const args = [
  path.join(rootDir, "app_desktop_web", "node_modules", "electron", "cli.js"),
  path.join(rootDir, "app_desktop_web"),
];
spawn(command, args, {
  cwd: rootDir,
  env: buildElectronLaunchEnv(process.env),
  stdio: "inherit",
  windowsHide: false,
});
```

## 快速判断顺序

1. 先看 `ELECTRON_RUN_AS_NODE`。
2. 再看 `path.txt` 和 `dist/electron.exe`。
3. 再看 `dist/index.html` 里是不是 `/assets/...`。
4. 最后才去怀疑前端 React 代码、IPC 桥接或业务逻辑。

## 常见误判

1. 看到 `ipcMain` 是 `undefined`，就去改 `electron/main` / `electron/renderer` 导入。  
真实问题可能只是 `ELECTRON_RUN_AS_NODE=1`。

2. 窗口是黑的，就怀疑 preload 或 React 崩了。  
真实问题常常是 `file://` 下资源路径写成绝对路径。

3. 看到 `electron.cmd` 存在，就认为 Electron 安装完整。  
真实情况可能是只有 npm 壳文件，`dist/electron.exe` 根本没下载下来。

## 完成前验证

```powershell
npm --prefix "app_desktop_web" test
npm --prefix "app_desktop_web" run build
node --check "main_ui_account_center_desktop.js"
```

手工验证：

```powershell
node "main_ui_account_center_desktop.js"
```

- 成功标准不是“没立刻报错”，而是进程保持运行，且 `stderr` 为空。
