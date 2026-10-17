---
date:
  created: 2026-10-17T06:29:28.322Z
  updated: 2026-10-17T06:29:28.322Z
comments: true
title: 用 chezmoi 管理多机开发环境
createTime: 2026/10/17 14:29:28
permalink: /tools/chezmoi/
---

## 为什么开始统一管理配置

主力开发机迁到 MacOS 之后，日常使用的环境逐渐变成了 Mac、手机上的 Termux、个人 Ubuntu 服务器、个人 Windows 机器, 以及多台实验室服务器。

这带来了一些问题

1. 它们承担的工作不同，但很多配置习惯是共通的: Shell 插件、Git 别名、SSH 主机配置，以及一些自己写的小工具。

2. 配置还有各自的差异, 比如:
    - Mac 上使用本机 Clash 代理，服务器可能要通过 SSH 转发来方便的使用代理
    - 实验室机器需要跳板连接，手机上的 Termux 又有不同的路径和工具环境
    - 只把一份 `.zshrc` 复制到所有机器上，很快就会遇到需要逐台修改的地方

3. Agent 让 DIY 方便了不少, 但也增加了维护和同步的复杂性。

我希望在一台机器上改好的配置和工具，能通过同一个仓库带到其他机器；同时每台机器需要的差异，也能有明确的位置维护。

当前的解决方案是: 拓展我之前用的chezmoi, **使用 chezmoi 管理这些配置和工具脚本，Git 负责保存版本和同步仓库。**

## chezmoi 速览

chezmoi 是一个 dotfiles 管理工具。dotfiles 通常指 `.zshrc`、`.gitconfig` 这类以点开头的配置文件，不过 chezmoi 也可以管理普通文件、目录和脚本。

使用时会存在两份文件：

- **源文件**：保存在 chezmoi 源目录中，默认位置是 `~/.local/share/chezmoi`，可以用 `chezmoi source-path` 查看。
- **目标文件**：实际使用的配置文件或工具脚本，通常部署在用户主目录下。

例如，仓库中的 `dot_zshrc.tmpl` 会经过模板渲染，再生成实际使用的 `~/.zshrc`。运行 `chezmoi apply` 时，chezmoi 根据源文件和当前机器的数据计算目标内容，并应用相应改动。

```text
配置仓库中的源文件 + 当前机器的数据
                ↓ chezmoi apply
       ~/.zshrc、~/.ssh/config 等目标文件
```

我的配置仓库里主要会看到这些命名：

| 源文件或命名 | 含义 |
| --- | --- |
| `dot_zshrc` | 对应目标文件 `.zshrc`，`dot_` 表示开头的点 |
| `dot_zshrc.tmpl` | 应用前需要渲染模板 |
| `private_dot_ssh/config.tmpl` | 生成 `.ssh/config`，并限制 `.ssh` 目录的权限；`private_` 本身不加密内容 |
| `dot_local/bin/executable_netcheck` | 生成 `~/.local/bin/netcheck`，并设置可执行权限 |
| `run_once_*.sh.tmpl` | 渲染后执行脚本，已经成功执行过相同内容时跳过 |
| `modify_dot_gitconfig.sh` | 通过脚本修改现有 `.gitconfig`，由脚本决定保留和更新哪些内容 |

Git 保存的是源目录中的文件。对目标文件做的修改，需要重新纳入源目录，才能随仓库同步。完整概念和命名规则可以参考官方的 [Quick start](https://www.chezmoi.io/quick-start/) 和 [Source state attributes](https://www.chezmoi.io/reference/source-state-attributes/)。

## 我实际用它管理了什么

### Shell 环境

首先是 Zsh、Oh My Zsh、Powerlevel10k 和常用插件。`dot_zshrc.tmpl` 保存插件列表、主题选择、补全路径和模块加载入口，`dot_p10k.zsh.tmpl` 保存提示符配置。

环境相关的逻辑拆到了 `~/.config/zsh/` 下，按用途组织：

| 模块 | 主要内容 |
| --- | --- |
| `environment.zsh` | PATH、Conda、Node.js、NVM、CUDA 等环境配置 |
| `proxy.zsh` | 不同机器的默认代理策略，以及手动切换入口 |
| `tcodex.zsh` | 在 tmux 中启动或连接 Codex 会话的函数 |
| `terminal-title.zsh` | VSCode 终端标题及相关 hooks |

前两项主要是环境配置，后两项包含自用工具入口和标题处理代码。它们一起同步到各台机器，再由 `.zshrc` 加载。例如下面是现有入口中的一小段：

```zsh
if [[ -r "$HOME/.config/zsh/proxy.zsh" ]]; then
    source "$HOME/.config/zsh/proxy.zsh"
fi
if [[ -r "$HOME/.config/zsh/environment.zsh" ]]; then
    source "$HOME/.config/zsh/environment.zsh"
fi
```

拆分后，调整代理时可以集中看代理模块，修改终端标题时也不用翻找整个 `.zshrc`。入口会先检查模块是否可读，避免缺少某个模块时直接报错。

### SSH 与网络

SSH 配置中保存了常用主机别名、用户名、跳板关系和代理转发规则。这些连接规则通过模板按机器角色生成，让每台机器使用适合自己的配置。

连接时的可用性检查由辅助脚本完成，另有独立的网络检查工具：

- `check-clash-port`、`check-ssh-host`：供 SSH 配置调用。
- `netcheck`：使用当前代理环境检查几个常用站点，方便判断问题出在连接还是代理设置。

这些是自写的工具脚本，随 SSH 配置一起分发，换一台机器也能沿用相同的连接与排查方式。

代理地址和端口作为共享数据集中维护，Shell 与 SSH 模板共用，避免修改端口时还要分别调整两边。

### Git

Git 中需要同步的是用户名、邮箱、默认分支、推送方式和常用别名。这部分通过 chezmoi 的 `modify_` 合并配置。

例如我加了一个 `git ac "提交说明"` 的别名，用来暂存当前仓库的全部改动并提交。脚本只更新需要统一的 Git 设置，每台机器原有的登录凭据管理方式、代理地址和其他配置文件引用都会保留。

### Agent 工具

这里同时管理配置和自用工具，两部分用途不同：

- **Codex 配置**：统一常用默认项，同时保留本机的 provider、项目信息和运行状态。
- **provider 切换工具**：`codex-provider-switch` 是自己维护的脚本，提供查看状态、新增 provider 和切换入口。

脚本与补全通过模板共用一份 provider 信息，再按平台分发相应入口，认证文件留在本机。把配置和配套工具一起维护后，换机器也能沿用同一套操作习惯。

### 终端体验

这里也有两类内容：tmux 状态栏、Codex 的标题与通知选项属于配置定制；会话命名和标题辅助命令则由自用脚本实现。

例如 `tcodex` 可以创建 tmux 会话运行 Codex，也可以按 tmux 名称重新连接已有会话。通过 `resume` 新建会话时，会根据选中的 Codex 会话标题命名。终端标题和状态栏再显示对应的会话信息，便于区分同时打开的终端。

VSCode 的终端标题和通知还需要配合编辑器本机设置与扩展；仓库管理其中的 Shell、tmux 和 Codex 配置部分。iTerm2 Shell Integration 则通过 chezmoi 的外部文件管理下载，随其他终端配置一起维护。

## 同一个仓库，怎样适配不同机器

### 操作系统与机器角色

操作系统判断用于处理平台差异。例如 macOS 的 Homebrew 路径、Windows 的 PowerShell 入口，以及 Termux 中的工具路径。Termux 需要单独考虑，不能直接套用 Ubuntu 中的 `sudo`、systemd 和固定路径。

同一个系统下的机器也可能承担不同用途，所以仓库另外定义了 `machine_role`。目前有个人服务器的 `my_server`、实验室的 `nicelab`，以及其他服务器环境的角色。初始化时由 `.chezmoi.toml.tmpl` 提供选项，并把选择保存到本机 config 中。

例如，个人服务器的 `~/.config/chezmoi/chezmoi.toml` 中可以包含：

```toml
[data]
machine_role = "my_server"
```

角色判断会优先使用显式设置的值；为空时再通过 hostname 匹配。初始化中的 `full` 选项会把角色留空，实际生成哪些配置还会受到 hostname 判断影响。这样在容器或共享 home 的环境里，也可以通过本机 config 明确指定用途。

### 共享数据、本机数据与模板

模板读取的数据分成两部分：

- **共享数据**：保存在仓库的 `.chezmoidata.yaml` 中，例如代理端口、主机分组规则和 provider 元数据。
- **本机数据**：保存在本机 config 的 `[data]` 中，例如 `machine_role`，由每台机器分别维护。

下面用代理说明这个关系。为便于阅读，把现有实现简化为两个分支，端口只是示例值。

先在仓库的 `.chezmoidata.yaml` 中保存共通数据：

```yaml
clash:
  local_mixed_port: 7897
my_server:
  server_proxy_port: 7890
```

在代理模块模板中按系统和角色选择地址：

```sh
{{ if eq .chezmoi.os "darwin" -}}
export http_proxy="http://127.0.0.1:{{ .clash.local_mixed_port }}"
export https_proxy="$http_proxy"
{{ else if eq (get . "machine_role") "my_server" -}}
export http_proxy="http://127.0.0.1:{{ .my_server.server_proxy_port }}"
export https_proxy="$http_proxy"
{{ end -}}
```

Mac 和个人服务器使用同一个模板，各自得到适用的端口。实际配置还会判断代理是否可用，并处理 HTTP、SOCKS 代理及变量清理；这些逻辑都保留在代理模块里。

SSH 模板也会按角色选择内容。Shell 模块共用的角色判断抽到了 `.chezmoitemplates/zsh-roles.tmpl`，在渲染时读取；生成后的配置文件直接供 Zsh 使用，Shell 启动时不需要再运行 chezmoi。

模板及本机变量的完整用法见 [Manage machine-to-machine differences](https://www.chezmoi.io/user-guide/manage-machine-to-machine-differences/)，共享数据的规则见 [.chezmoidata](https://www.chezmoi.io/reference/special-files/chezmoidata-format/)。

### 选择部署范围和合并方式

有些差异适合通过 `.chezmoiignore.tmpl` 控制。例如 PowerShell 启动器只部署到 Windows；当前仓库也没有在 Windows 上直接托管 Codex 的共通 `config.toml`，由对应的切换工具处理需要的设置。

Git 和 Codex 则用前面提到的 `modify_` 脚本合并配置。它们负责保留哪些本机内容、更新哪些共享内容，不能仅凭文件有 `modify_` 前缀就认为所有本机改动都会被保留。这种目标类型的处理方式见官方 [Modify file](https://www.chezmoi.io/reference/target-types/#modify-file)。

### 配置文件之外的安装步骤

恢复配置还涉及工具本身的安装。仓库中的 `run_once_install-oh-my-zsh.sh.tmpl` 负责安装 Oh My Zsh、插件和主题，`run_once_install-codex.sh.tmpl` 则按平台选择工具安装方式。它们都会先检查相应工具或目录是否存在。

`run_once_` 按渲染后的脚本内容记录执行状态，相同内容成功执行过后会跳过；内容变化后仍可能再次执行。因此安装脚本也需要能处理工具已经存在的情况。tmux 配置变化后的 reload 则使用 `run_onchange_after_` 脚本处理。

安装与重载脚本在 `apply` 时执行，日常工具脚本则按需调用。执行条件和顺序见官方 [Use scripts to perform actions](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/)。

## 新机器接入与日常维护

### 新机器接入

先安装 chezmoi。下面是几个环境中的入口，选择当前系统对应的一条即可；更多方式见 [官方安装文档](https://www.chezmoi.io/install/)。

| 环境 | 安装命令 |
| --- | --- |
| macOS，已安装 Homebrew | `brew install chezmoi` |
| Ubuntu，已安装 curl | `sh -c "$(curl -fsLS https://get.chezmoi.io)" -- -b "$HOME/.local/bin"` |
| Termux | `pkg install chezmoi` |
| Windows，已安装 Scoop | `scoop install chezmoi` |

Ubuntu 安装到 `~/.local/bin` 后，先确保该目录在当前 Shell 的 PATH 中。下面的流程使用 macOS、Linux 或 Termux 中的 POSIX Shell；Windows 的初始化命令相同，路径和环境变量操作需要按 PowerShell 语法处理。

```bash
# 使用 ~/.local/bin 安装方式时，先让当前 Shell 能找到 chezmoi
export PATH="$HOME/.local/bin:$PATH"

# 我的配置仓库，使用时替换为自己的仓库
chezmoi init yJader/dotfiles

# 初始化时选择机器角色，再预览生成结果
chezmoi cat ~/.zshrc
chezmoi diff
chezmoi apply
```

接入前还需要准备好对应环境：

- **基础工具**：Git、Bash、Zsh 等，macOS 的 Codex 安装步骤还依赖 Homebrew。
- **仓库认证**：私有仓库需要先准备好 Git 认证。
- **平台差异**：Windows 的共享脚本使用 Git for Windows 的 Bash；Termux 中的安装步骤则需要结合它的包管理和工具环境单独检查。

`apply` 会部署配置，也可能执行仓库中的安装脚本。应用后重新打开 Shell，再检查主题、补全和相关命令是否加载。

### 修改并同步到其他机器

1. **修改并应用配置**

   已经托管的文件可以通过目标路径打开其源文件。例如修改代理模块：

   ```bash
   chezmoi edit ~/.config/zsh/proxy.zsh
   chezmoi diff
   chezmoi apply
   ```

   `chezmoi edit` 默认编辑源文件，保存后还需要 `apply` 才会更新目标文件；也可以通过 `--apply` 在编辑结束后应用。这个行为可以参考 [edit 命令说明](https://www.chezmoi.io/reference/commands/edit/)。

   新增一个普通配置文件时，用 `chezmoi add <目标路径>` 纳入管理；需要模板时使用 `chezmoi add --template <目标路径>`。如果已经托管的目标文件被直接改动，需要把改动同步回源文件；模板还需要保留其中的条件与变量。

2. **提交源目录中的改动**

   确认改动后，把源目录中的变更提交到 Git：

   ```bash
   cd "$(chezmoi source-path)"
   git diff
   git add .
   git commit -m "feat: 调整代理配置"
   git push
   ```

3. **在其他机器上更新**

   到另一台机器上，先更新仓库，再检查它将怎样改变本机配置：

   ```bash
   cd "$(chezmoi source-path)"
   git pull --rebase
   chezmoi diff
   chezmoi apply
   ```

这里把拉取和应用分开，便于查看差异。需要合并执行时可以使用 `chezmoi update`。多台机器上都有修改时，先提交本机改动，再处理 Git 合并；每台机器的 `machine_role` 仍然分别保存在本机 config 中。

### 让 Agent 协助 DIY

`tcodex` 是这种工作方式的一个例子。它涉及 Zsh 函数、tmux 中的启动脚本、会话标题辅助命令和补全文件，相关文件都放在同一个配置仓库中。

继续调整这类工具时，可以按下面的流程让 Agent 协助：

1. **读取现有配置**：从 chezmoi 源目录入手，先读已有实现和仓库维护说明。
2. **一起修改相关文件**：比如调整 `tcodex resume` 的会话命名，需要同时考虑入口参数、tmux 内部脚本和补全，而不只是给 `.zshrc` 再加一行 alias。
3. **预览并检查**：先预览渲染结果，再检查相关模块和测试。我的仓库为这些功能保留了聚焦测试，例如 Shell 配置、`tcodex` 和 provider 切换测试。
4. **应用并同步**：应用到当前机器，确认行为符合预期后提交；其他机器通过前面的更新流程取得同一份实现。

这样每次增加功能时，源文件、平台差异和验证方法都有地方维护。某台机器缺少 tmux、Codex 或某个可选模块时，也应由对应入口给出提示或跳过，避免影响无关的 Shell 功能。

### 常用命令速查

| 命令 | 用途 |
| --- | --- |
| `chezmoi source-path` | 查看配置源目录 |
| `chezmoi managed` | 查看当前机器托管的目标 |
| `chezmoi add <路径>` | 把已有文件纳入管理 |
| `chezmoi edit <路径>` | 编辑目标对应的源文件 |
| `chezmoi cat <路径>` | 预览渲染后的目标内容 |
| `chezmoi diff` | 查看将应用的差异 |
| `chezmoi apply [路径]` | 应用全部或指定目标 |
| `chezmoi update` | 拉取仓库更新并应用 |
