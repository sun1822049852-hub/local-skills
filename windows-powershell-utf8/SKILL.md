---
name: windows-powershell-utf8
description: 在 Windows PowerShell 5.1 中处理中文文本、Markdown/TXT/JSON/.ps1/.cmd 文件、乱码、双击脚本红字、The string is missing the terminator 或中文输出异常时，统一检查 UTF-8、BOM、cmd 代码页和 Python/PowerShell 输出编码。
---

# Windows PowerShell UTF-8 防乱码

## 适用场景

- 用户提到“乱码”“中文显示异常”“锟斤拷”“璇婃柇”这类文本异常。
- 在 Windows 上使用 `powershell.exe`（尤其是 PowerShell 5.1）执行文件读写命令。
- 读取或写入 `*.md`、`*.txt`、`*.json`、`*.csv` 等文本文件，且包含中文。
- 双击 `.cmd` 启动 `.ps1`，出现红字、中文乱码，或 `The string is missing the terminator: "`。
- 需要在会话中长期稳定地避免编码问题，而不是一次性临时修复。

## 核心原则

1. 先统一会话编码，再做文件操作。
2. 所有文本 IO 显式指定 `UTF8`，不要依赖默认编码。
3. 先读后写，避免无意改变原文件编码。

## 执行流程

### 1) 识别环境与风险
- 优先确认是否为 Windows PowerShell 5.1：
```powershell
$PSVersionTable.PSVersion
[System.Text.Encoding]::Default.WebName
```
- 若默认编码是 `gb2312`/`gbk` 等本地代码页，则 UTF-8 无 BOM 文件存在高风险乱码。
- 如果入口是 `.cmd` 双击启动 `powershell.exe`，默认按 Windows PowerShell 5.1 风险处理；即使当前 Codex shell 是 PowerShell 7，也不能据此排除 5.1 解析问题。

### 2) 会话级修复（每次进入会话先执行）
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
```
- 说明：
- 第一、二行保证终端输出链路尽量使用 UTF-8。
- 第三行让大多数支持 `-Encoding` 的 cmdlet 默认使用 UTF-8。

### 3) 命令级强约束
- 对关键 IO 命令始终显式指定编码：
```powershell
Get-Content -Path "<path>" -Encoding UTF8
Set-Content -Path "<path>" -Value $content -Encoding UTF8
Add-Content -Path "<path>" -Value $line -Encoding UTF8
Out-File -FilePath "<path>" -Encoding UTF8
Import-Csv -Path "<path>" -Encoding UTF8
Export-Csv -Path "<path>" -NoTypeInformation -Encoding UTF8
```
- 在自动化脚本中，优先把 `-Encoding UTF8` 写死，不要依赖会话默认值。

### 3a) `.cmd` 双击启动 `.ps1` 的专门处理

若 `.ps1` 含中文并可能由 `.cmd` 调 `powershell.exe` 运行：

1. `.ps1` 保存为 UTF-8 with BOM。PowerShell 7 的 `Set-Content -Encoding UTF8` 可能写成无 BOM；需要 BOM 时用：
```powershell
$content = Get-Content -Path ".\script.ps1" -Encoding UTF8 -Raw
$encoding = New-Object System.Text.UTF8Encoding($true)
[System.IO.File]::WriteAllText((Resolve-Path ".\script.ps1"), $content, $encoding)
```
2. `.ps1` 开头仍设置输出编码：
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
```
3. `.cmd` 入口先切 UTF-8 代码页，并固定 Python 输出编码：
```bat
@echo off
setlocal
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0script.ps1"
endlocal
```
4. 验证 `.ps1` BOM：
```powershell
Format-Hex -Path ".\script.ps1" -Count 4
```
开头应为 `EF BB BF`。

### 4) 验证修复是否生效
```powershell
$p = "<path>"
"--- DEFAULT ---"; Get-Content -Path $p -TotalCount 5
"--- UTF8 ---";    Get-Content -Path $p -Encoding UTF8 -TotalCount 5
```
- 若 `UTF8` 正常、默认读取乱码，说明根因就是默认编码错配。
- 若两者都乱码，检查文件内容是否已被错误编码覆盖。

## 写回文件前的保护动作

- 先备份再覆盖，避免把乱码永久写回：
```powershell
Copy-Item "<path>" "<path>.bak" -Force
```
- 仅在确认源文本正确解码后再执行写回。
- 批量替换时分批验证，不一次性改全仓库。

## 故障模式速查

1. 现象：`Get-Content` 读中文乱码，但编辑器显示正常。  
判定：UTF-8 文件被按 GBK/ANSI 解码。  
处理：改为 `Get-Content -Encoding UTF8`，并执行会话级修复。

2. 现象：终端输出乱码，但文件本身正确。  
判定：控制台输出编码链路不一致。  
处理：执行 `[Console]::OutputEncoding` 与 `$OutputEncoding` 两行修复。

3. 现象：修复后新会话又复发。  
判定：会话初始化未固化。  
处理：在每个会话开头优先执行本技能的“会话级修复”三行命令。

4. 现象：双击 `.cmd` 后 PowerShell 红字，错误包含 `The string is missing the terminator: "`，错误行里的中文变成乱码。
判定：Windows PowerShell 5.1 很可能把 UTF-8 无 BOM 的 `.ps1` 按 ANSI/GBK 读了，导致中文字符串和引号被解析坏。
处理：先把 `.ps1` 改为 UTF-8 with BOM，再在 `.cmd` 加 `chcp 65001 >nul` 和 `PYTHONIOENCODING=utf-8`，最后复现入口验证。

## 输出要求

- 对用户报告编码问题时，先给根因判断，再给最小修复命令。
- 修改文件前必须明确“是否会改写原文件编码”。
- 默认不做批量转码，除非用户明确要求。
