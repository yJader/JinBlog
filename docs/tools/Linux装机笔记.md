---
date:
  created: 2024-05-22
  updated: 2025-08-30
comments: true 
---
# 装机note

> 以Ubuntu为例

[TOC]

## 基本环境配置

### 换源

[清华镜像](https://mirror.tuna.tsinghua.edu.cn/help/ubuntu/)

```shell
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak
sudo vim /etc/apt/sources.list

sudo apt update # 更新源
sudo apt upgrade
```

```shell
# 刚进入vim 处于命令行输入模式
# d: delete, G: 文档末尾, 即从光标位置开始, 删除到文章末尾
dG
# p: paste
p
# 保存退出, 注意需要冒号
:wq
```

### 一些不需要配置的常用包

```shell
sudo apt install vim git
```

### SSH配置

```bash
sudo apt install openssh-server
sudo systemctl enable ssh / sshd?
```

编辑`/etc/ssh/sshd_config`

```shell
vim /etc/ssh/sshd_config
```

```config
PasswordAuthentication yes
```

启动ssh服务

```bash
sudo systemctl start ssh
```

开机自启动

```bash
sudo systemctl enable ssh
```

#### ssh密钥登录

1. 生成SSH密钥对(client和server都需要)

   - client: 本地正在尝试访问远程机的这台机器
      server: 正在尝试访问的远程机(ssh意义上的server)

   - 二编: server真的需要吗?

   ```bash
   ssh-keygen
   ```

2. 将client生成的公钥(默认位于`/user/username/.ssh/id_rsa.pub`文件夹内) 拷贝到server的`/home/.ssh/authorized_keys`(也可能在`/home/your_username/.ssh/authorized_keys`)中

   ```shell
    ssh-copy-id -i ~/.ssh/id_rsa.pub {username}@{server_ip} # linux系统, 有ssh-copy-id工具
    wsl ssh-copy-id -i /mnt/c/Users/14258/.ssh/id_rsa.pub {username}@{server_ip} # 在windows环境下
   ```

   - 如果命令不顺利, 也可以手动创建这个`authorized_keys`文件, 然后粘贴client的公钥到`authorized_keys`中

### 编译工具链

```bash
sudo apt install build-essential
```

### ifconfig

```bash
sudo apt install net-tools
```

### git配置

```bash
# 自动将新分支推送到同名远程分支并设置 upstream
git config --global push.default current
# 创建新分支时自动关联上游
git config --global branch.autoSetupMerge always
```

## 用户管理

```shell
# 创建用户, 并为他设置用户主目录
sudo useradd <username>

# 设置密码
sudo passwd <username>

# 添加sudo权限
sudo usermod -aG sudo <username>
```

## 命令行工具

### ZSH

#### 安装 Zsh

```bash
# 安装 Zsh
sudo apt install zsh

# 将 Zsh 设置为默认 Shell
chsh -s "$(command -v zsh)"
```

#### 安装 Oh My Zsh框架

```bash
# 安装 Oh My Zsh
wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | sh
```

```shell
# 以上命令可能不好使，可使用如下两条命令
wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh
bash ./install.sh
```

#### 安装Powerlevel10k 主题

```shell
# 官方镜像
git clone --depth=1 https://gitee.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
vim ~/.zshrc
# ZSH_THEME="powerlevel10k/powerlevel10k"
```

- 重启终端, 根据引导进行操作
  - 想要重新配置, 删除`~/.p10k.zsh`
  - 或者 `p10k configure`

#### 抄来的插件配置

> [常用的oh-my-zsh插件 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/61447507) 选了一些个人常用的

##### zsh-autosuggestions

[官网](https://link.zhihu.com/?target=https%3A//github.com/zsh-users/zsh-autosuggestions)，非常好用的一个插件，会记录你之前输入过的所有命令，并且自动匹配你可能想要输入命令，然后按→补全

安装

```shell
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
```

##### zsh-syntax-highlighting

[官网](https://link.zhihu.com/?target=https%3A//github.com/zsh-users/zsh-syntax-highlighting)，命令太多，有时候记不住，等输入完了才知道命令输错了，这个插件直接在输入过程中就会提示你，当前命令是否正确，错误红色，正确绿色

```shell
git clone https://github.com/zsh-users/zsh-syntax-highlighting ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

# image
git clone https://gitee.com/minhanghuang/zsh-syntax-highlighting ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```

##### sudo

直接在插件列表中添加, 无需下载

##### 启用插件

```zsh
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-syntax-highlighting ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```

`vim ~/.zshrc` 查找 `plugins` 在括号中添加插件列表

```
sudo zsh-autosuggestions zsh-syntax-highlighting
```

### 备份配置 - chezmoi

> [chezmoi 官网](https://www.chezmoi.io/)
>
> `chezmoi` 是一个dotfile管理工具, 可以帮助我们在多台设备上同步我们的配置文件

#### 安装

```bash
# 二进制安装
sh -c "$(curl -fsLS get.chezmoi.io)"
# 将二进制文件移动到PATH
sudo mv ./bin/chezmoi /usr/local/bin/
```

#### 初始化

`chezmoi` 使用一个 git 仓库来存储配置文件, 我们可以先在 Github 等平台创建一个私有仓库, 用于存储我们的配置文件

```bash
# 初始化, {github-username}/{repo-name}
chezmoi init yJader/dotfiles
```

#### 使用

```bash
# 添加 zsh 配置文件
chezmoi add ~/.zshrc
# 添加 p10k 配置文件
chezmoi add ~/.p10k.zsh
```

`chezmoi` 会将文件复制到 `~/.local/share/chezmoi` 目录下, 我们需要进入该目录, 将变动推送到远程仓库。

```bash
cd $(chezmoi source-path)
git add .
git commit -m "Add zsh and p10k configs"
git push
```

在新设备上, 只需要再次执行`init`, 然后执行`apply`即可恢复配置。

```bash
chezmoi apply
```

#### 管理oh-my-zsh, 插件及主题

为了解决 `chezmoi` 中不同工具（`.chezmoiexternal.toml` 和 `run_once_*` 脚本）的执行顺序问题，最佳实践是将 `oh-my-zsh` 框架、插件和主题的安装逻辑整合到一个单一的脚本中。这样可以确保它们严格按照我们期望的顺序执行。

1. **统一安装脚本**

    我们创建一个名为 `run_once_install-zsh-stack.sh` 的脚本来处理所有与 Zsh 相关的安装。这个脚本会：
    a.  首先，安装 `oh-my-zsh` 核心框架。
    b.  然后，安装所需的插件（如 `zsh-autosuggestions` 和 `zsh-syntax-highlighting`）。
    c.  最后，安装 `Powerlevel10k` 主题。

    在 `chezmoi` 的源目录中创建此脚本：

    ```sh
    #!/bin/sh
    
    set -e # 如果任何命令失败，立即退出
    
    ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
    
    # 1. 安装 Oh My Zsh 框架
    if [ ! -f "$HOME/.oh-my-zsh/oh-my-zsh.sh" ]; then
      echo "Installing Oh My Zsh..."
      rm -rf "$HOME/.oh-my-zsh" # 清理不完整的安装
      sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
    else
      echo "Oh My Zsh is already installed."
    fi
    
    # 2. 安装插件和主题
    echo "Installing/updating plugins and theme..."
    
    # zsh-autosuggestions 插件
    if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
      echo "Installing zsh-autosuggestions..."
      git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions.git "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
    fi
    
    # zsh-syntax-highlighting 插件
    if [ ! -d "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" ]; then
      echo "Installing zsh-syntax-highlighting..."
      git clone --depth=1 https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
    fi
    
    # Powerlevel10k 主题
    if [ ! -d "$ZSH_CUSTOM/themes/powerlevel10k" ]; then
      echo "Installing Powerlevel10k theme..."
      git clone --depth=1 https://github.com/romkatv/powerlevel10k.git "$ZSH_CUSTOM/themes/powerlevel10k"
    fi
    
    echo "Zsh stack installation complete."
    ```

    > **注意**: 记得移除 `.chezmoiexternal.toml` 文件（如果存在），因为它会导致执行顺序冲突。

2. **提交更改**

    将新的脚本和删除的 `.chezmoiexternal.toml` 文件提交到你的 dotfiles 仓库。

    ```bash
    cd $(chezmoi source-path)
    git rm .chezmoiexternal.toml # 如果文件存在
    git add .
    git commit -m "Consolidate all zsh installation into a single script"
    git push
    ```

#### 使用模板管理多机差异配置

在多台设备上同步配置时, 常常会遇到某些配置需要因设备而异的情况, 例如不同设备使用不同的HTTP代理。`chezmoi` 强大的模板功能可以完美解决这个问题。

`chezmoi` 使用 Go 模板引擎, 允许我们在配置文件中嵌入逻辑判断。我们可以通过 `{{ .chezmoi.hostname }}` 来获取当前设备的主机名, 并以此为依据应用不同的配置。

1. **编辑模板文件**

    `chezmoi` 会将 `~/.zshrc` 转换为 `dot_zshrc` 这样的模板文件存放在源目录中。我们可以直接编辑这个模板文件。一个更方便的方式是使用 `chezmoi edit` 命令：

    ```bash
    chezmoi edit ~/.zshrc
    ```

2. **添加模板逻辑**

    以下是我根据主机名设置不同代理的例子。
    - `yijindeMacBook-Air` 会使用固定的代理地址
    - `xfusion` 或 `powerleader` 开头的远程服务器则会使用一个自定义的函数来设置代理

    将以下内容添加到 `dot_zshrc` 模板文件的合适位置：

   ```sh
   {{ if eq .chezmoi.hostname "yijindeMacBook-Air" -}}
   # For MacBook
   export http_proxy=http://127.0.0.1:7897
   export https_proxy=http://127.0.0.1:7897
   export all_proxy=socks5://127.0.0.1:7897
   
   {{ else if or (regexMatch "^xfusion" .chezmoi.hostname) (regexMatch "^powerleader" .chezmoi.hostname) -}} 
   # For xfusion or powerleader servers
   set_clash_proxy() {
      source /home/zhangjiangjie/clash_vpn/2.source_this.sh 
   }
   alias clashp='set_clash_proxy'
   
   {{ end -}}
   ```

3. **应用并推送更改**

    编辑完成后, 保存文件。`chezmoi edit` 会自动应用更改。最后, 将变动提交并推送到你的 dotfiles 仓库。

    ```bash
    cd $(chezmoi source-path)
    git add .
    git commit -m "Add templated proxy settings"
    git push
    ```

    现在, 当你在任何一台受 `chezmoi` 管理的设备上运行 `chezmoi apply` 时, 都会根据其主机名生成一份专属的 `.zshrc` 文件。

4. **故障排查: 文件未被当作模板处理**

    如果在应用配置后, 目标文件 (如 `.zshrc`) 中仍然包含 `{{ if ... }}` 等原始模板代码, 这通常意味着 `chezmoi` 没有将该文件识别为模板。

    可以使用 `chezmoi chattr` 命令来显式地为文件添加 `template` 属性:

    ```bash
    chezmoi chattr +template ~/.zshrc
    ```

    执行此命令后, 再次运行 `chezmoi apply`, `chezmoi` 就会正确地解析模板并生成配置了。

## Github Cli

<https://github.com/cli/cli?tab=readme-ov-file#installation>

```bash
(type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
 && sudo mkdir -p -m 755 /etc/apt/keyrings \
        && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        && cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
 && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
 && sudo apt update \
 && sudo apt install gh -y
```

## Conda

> 先放一个官方文档: [Installing Miniconda - Anaconda](https://www.anaconda.com/docs/getting-started/miniconda/install), 建议先看官方文档, 以下为偷懒用摘抄

```shell
cd ~

# 下载, shell较大, 注意网络环境配置
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

bash ~/Miniconda3-latest-Linux-x86_64.sh
```

值得注意的是这个配置项

```
Do you wish to update your shell profile to automatically initialize conda?
This will activate conda on startup and change the command prompt when activated.
If you'd prefer that conda's base environment not be activated on startup,
   run the following command when conda is activated:

conda config --set auto_activate_base false

You can undo this by running `conda init --reverse $SHELL`? [yes|no]
[no] >>> 
```

- 不是很推荐在shell启动时就激活base环境, 会严重拖慢shell启动速度
  - vscode选择需要的虚拟环境的解释器即可完成这个功能
- 默认是no, 挺不错

最后测试一下是否安装成功

```shell
conda --version
```

## Docker

> [Install Docker Engine on Ubuntu | Docker Docs](https://docs.docker.com/engine/install/ubuntu/)
>
> 快丢掉csdn

1. Set up Docker's `apt` repository.

   ```bash
   # Add Docker's official GPG key:
   sudo apt-get update
   sudo apt-get install ca-certificates curl
   sudo install -m 0755 -d /etc/apt/keyrings
   sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   sudo chmod a+r /etc/apt/keyrings/docker.asc
   
   # Add the repository to Apt sources:
   echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
     $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
     sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update
   ```

   > **Note**
   >
   > If you use an Ubuntu derivative distro, such as Linux Mint, you may need to use `UBUNTU_CODENAME` instead of `VERSION_CODENAME`.

2. Install the Docker packages.

   (Latest Specific version)

   To install the latest version, run:

   ```shell

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

   ```

3. Verify that the Docker Engine installation is successful by running the `hello-world` image.

   ```shell
   sudo docker run hello-world
   ```

   This command downloads a test image and runs it in a container. When the container runs, it prints a confirmation message and exits.

## 远程桌面

> 以下为当时提问GPT得到的回复, 似乎碰到了一些小挫折, 解决过程忘记记录了QAQ
>
> 欢迎补充(PR)

要远程连接到 Ubuntu 22.04 的 `:0` 桌面并进行远程控制，通常可以使用 VNC 或者 X11vnc 工具。以下是详细步骤：

### 使用 X11vnc 连接到当前桌面

`X11vnc` 是一种直接访问现有 X 会话的工具，可以实现连接到 `:0` 桌面。

#### 安装 X11vnc

1. 安装 X11vnc

   ```bash
   sudo apt update
   sudo apt install x11vnc -y
   ```

#### 设置 X11vnc 密码

1. 设置 VNC 密码

   ```bash
   x11vnc -storepasswd
   ```

#### 启动 X11vnc 服务

1. 启动 X11vnc 服务

   启动`x11vnc`并指定连接到当前的`:0`桌面：

   ```bash
   x11vnc -display :0 -auth guess -forever -loop -noxdamage -repeat -rfbauth ~/.vnc/passwd -rfbport 5900 -shared
   ```

#### 设置开机启动

1. **创建 Systemd 服务文件** 如果你希望 `X11vnc` 在系统启动时自动运行，可以创建一个 Systemd 服务文件：

   ```bash
   sudo vim /etc/systemd/system/x11vnc.service
   ```

   在文件中添加以下内容：

   ```ini
   [Unit]
   Description=x11vnc server for GNOME
   After=gdm.service
   
   [Service]
   Type=simple
   User=YOUR_USERNAME
   ExecStart=/usr/bin/x11vnc -many -shared -display :0 -auth /run/user/1000/gdm/Xauthority -noxdamage -rfbauth /home/YOUR_USERNAME/.vnc/passwd
   Restart=on-failure
   RestartSec=3
   
   [Install]
   WantedBy=graphical.target
   ```

   注意将 `YOUR_USERNAME` 替换为你的实际用户名。

2. **启用并启动服务**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable x11vnc.service
   sudo systemctl start x11vnc.service
   ```

3. 编辑GDM, 使用Xorg登录

   ```bash
   sudo vim /etc/gdm3/custom.conf
   ```

   在 `custom.conf` 文件中，找到以下行：

   ```ini
   #WaylandEnable=false
   ```

   取消注释（如果前面有 `#`），并将其改为：

   ```ini
   WaylandEnable=false
   ```

4. 设置自动登录 (也在custom.conf)

   ```ini
   AutomaticLoginEnable=true
   AutomaticLogin=[your_username]
   ```

5. 重启 GDM3 或者重启计算机

   为了使更改生效，您需要重启 GDM3 或者整个计算机。重启 GDM3 的命令如下：

   ```bash
   sudo systemctl restart gdm3
   ```

   或者，您也可以重启计算机：

   ```bash
   sudo reboot
   ```

### 使用 VNC Viewer 连接到桌面

现在，你可以使用 VNC Viewer 连接到你的 Ubuntu 机器。以下是使用 RealVNC Viewer 的步骤：

1. **下载并安装 RealVNC Viewer**
   - RealVNC Viewer 下载页面
2. **连接到 Ubuntu 机器**
   - 打开 RealVNC Viewer，输入你的 Ubuntu 机器的 IP 地址和端口（例如：`192.168.1.100:5900`）。
   - 使用你之前设置的 VNC 密码进行连接。

### 注意事项

- **防火墙配置** 确保防火墙允许 VNC 连接，默认端口为 5900：

  ```bash
  sudo ufw allow 5900
  ```

- **显示管理器** 如果你的 Ubuntu 使用的是 GDM3 作为显示管理器，确保其正确配置以允许 X11vnc 连接。

通过这些步骤，你应该能够实现连接到 Ubuntu 22.04 的 `:0` 桌面并进行远程控制。如果遇到问题，请检查相关日志文件或提供具体错误信息以便进一步诊断。

### TigerVNC

> 如果你需要连接到物理显示器 `:0`，建议使用 `x0vncserver` 而不是 `vncserver`。`x0vncserver` 直接连接到已有的X会话，而`vncserver`是启动一个新的虚拟桌面。

#### x0vncserver

> x0vncserver仅可本地连接, 远程连接不可用
> x11vnc均可使用, 但显示效果不好

```bash
x0vncserver -display :0 -rfbauth ~/.vnc/passwd -rfbport 5900
```

1. **后台运行 x0vncserver**

   如果希望 x0vncserver 在后台运行，可以使用 nohup：

   ```
   bash
   复制代码
   nohup x0vncserver -display :0 -rfbauth ~/.vnc/passwd -rfbport 5900 &
   ```

2. **创建 Systemd 服务文件**

   ```
   bash
   复制代码
   sudo nano /etc/systemd/system/x0vncserver.service
   ```

   添加以下内容：

   ```
   ini复制代码[Unit]
   Description=Start x0vncserver at startup
   After=multi-user.target
   
   [Service]
   Type=simple
   ExecStart=/usr/bin/x0vncserver -display :0 -rfbauth /home/YOUR_USERNAME/.vnc/passwd -rfbport 5900
   User=YOUR_USERNAME
   
   [Install]
   WantedBy=multi-user.target
   ```

   启用并启动服务：

   ```
   bash复制代码sudo systemctl daemon-reload
   sudo systemctl enable x0vncserver.service
   sudo systemctl start x0vncserver.service
   ```

## 一些问题

### 重启后没网

> [怎么解决在vmware虚拟机下ubuntu linux系统重启后不能联网的问题_Engineer-Bruce_Yang的博客-CSDN博客](https://blog.csdn.net/morixinguan/article/details/118886890)

问题情况: 重启后网络图标消失, 无法联网

原因: NetworkManager服务启动失败

解决方案: 停止网络管理服务，删除网络状态文件，再重新启动网络服务

```shell
service NetworkManager stop
sudo rm /var/lib/NetworkManager/NetworkManager.state
service NetworkManager start
```
