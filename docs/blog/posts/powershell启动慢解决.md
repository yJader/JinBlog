---
date:
  created: 2025-10-01T00:00:00.000Z
  updated: 2025-10-01T00:00:00.000Z
categories:
  - 踩坑记录
comments: true
title: powershell启动慢解决
createTime: 2025/12/05 15:54:53
permalink: /blog/posts/xe7h3rou/
---

# PowerShell 启动慢解决

从不知道什么时候开始, PowerShell启动速度从秒开->2s->30s???, 实在忍不了了, 该解决了

```powershell
PowerShell 7.5.3
Loading personal and system profiles took 30669ms.
```
<!-- more -->
在AI的帮助下, 我们可以通过一个脚本, 分析配置文件的加载时间来找到问题所在

```powershell
# 定义所有可能的 PowerShell 配置文件路径
$profilesToTest = @(
    $PROFILE.CurrentUserCurrentHost,
    $PROFILE.CurrentUserAllHosts,
    $PROFILE.AllUsersCurrentHost,
    $PROFILE.AllUsersAllHosts
) | Get-Unique

Write-Host "--- 开始分析 PowerShell 配置文件加载耗时 ---" -ForegroundColor Green

# 测量加载所有存在配置文件所花费的总时间
$totalMeasuredTime = Measure-Command {
    foreach ($profileFile in $profilesToTest) {
        # 检查文件是否存在
        if (Test-Path $profileFile) {
            Write-Host "正在测量: $profileFile"
            
            # 使用 Measure-Command 来精确测量加载该文件所需的时间
            $individualLoadTime = Measure-Command {
                try {
                    # 使用 . (dot-sourcing) 来在当前作用域内执行配置文件
                    . $profileFile
                } catch {
                    Write-Error "加载配置文件 $profileFile 时出错: $_"
                }
            }
            
            # 输出单个文件的加载耗时
            Write-Host " -> 加载耗时: $($individualLoadTime.TotalMilliseconds) 毫秒" -ForegroundColor Yellow
        }
    }
}

Write-Host "--- 分析完成 ---" -ForegroundColor Green
Write-Host "所有已找到配置文件的总加载耗时: $($totalMeasuredTime.TotalMilliseconds) 毫秒" -ForegroundColor Cyan
```

结果如下

```powershell
--- 开始分析 PowerShell 配置文件加载耗时 ---
正在测量: ~\Documents\PowerShell\Microsoft.PowerShell_profile.ps1
 -> 加载耗时: 677.4452 毫秒
正在测量: ~\Documents\PowerShell\profile.ps1
 -> 加载耗时: 4907.1769 毫秒
--- 分析完成 ---
所有已找到配置文件的总加载耗时: 5594.52 毫秒
```

很好 那么该看看`profile.ps1`文件的内容了

```powershell
# cat ~\Documents\PowerShell\profile.ps1

#region conda initialize
# !! Contents within this block are managed by 'conda init' !!
If (Test-Path "D:\Python\MiniConda3\Scripts\conda.exe") {
    (& "D:\Python\MiniConda3\Scripts\conda.exe" "shell.powershell" "hook") | Out-String | ?{$_} | Invoke-Expression
}
#endregion
```

呃...之前安装的conda, 或许该考虑转用mamba了

不过现在先简单优化一下配置文件, 修改为以下的配置, 避免自动启动

```ps
# 定义一个函数来手动初始化 Conda
function Start-Conda {
    #region conda initialize
    # !! Contents within this block are managed by 'conda init' !!
    If (Test-Path "D:\Python\MiniConda3\Scripts\conda.exe") {
        (& "D:\Python\MiniConda3\Scripts\conda.exe" "shell.powershell" "hook") | Out-String | ?{$_} | Invoke-Expression
    }
    #endregion

    # 初始化后移除这个函数自身，避免重复执行
    Remove-Item -Path "Function:\Start-Conda"
}

# 给这个函数设置一个更短的别名，方便调用
Set-Alias -Name cinit -Value Start-Conda
```

解决后:

```powershell
PowerShell 7.5.3
Loading personal and system profiles took 974ms.
```

但是开头的逆天30s还是不知道怎么来的, 或许是刚开机导致的? 总之现在启动速度能接受了
