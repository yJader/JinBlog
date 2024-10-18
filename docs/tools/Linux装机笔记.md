---
date:
  created: 2024-05-22
  updated: 2024-10-18
comments: true 
---


# 装机note

> 以Ubuntu为例

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
   sudo ssh-keygen
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



## ZSH终端

### 安装 Zsh

```bash
# 安装 Zsh
sudo apt install zsh

# 将 Zsh 设置为默认 Shell
chsh -s /bin/zsh
```

### 安装 Oh My Zsh框架

```bash
# 安装 Oh My Zsh
wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | sh
```

```shell
# 以上命令可能不好使，可使用如下两条命令
wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh
bash ./install.sh
```



### 安装Powerlevel10k 主题

```shell
git clone --depth=1 https://gitee.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
vim ~/.zshrc
# ZSH_THEME="powerlevel10k/powerlevel10k"
```

- 重启终端, 根据引导进行操作
  - 想要重新配置, 删除`~/.p10k.zsh`
  - 或者 `p10k configure`

### 抄来的插件配置

> [常用的oh-my-zsh插件 - 知乎 (zhihu.com)](https://zhuanlan.zhihu.com/p/61447507) 选了一些个人常用的

#### zsh-autosuggestions

[官网](https://link.zhihu.com/?target=https%3A//github.com/zsh-users/zsh-autosuggestions)，非常好用的一个插件，会记录你之前输入过的所有命令，并且自动匹配你可能想要输入命令，然后按→补全

安装

```shell
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
```

#### zsh-syntax-highlighting

[官网](https://link.zhihu.com/?target=https%3A//github.com/zsh-users/zsh-syntax-highlighting)，命令太多，有时候记不住，等输入完了才知道命令输错了，这个插件直接在输入过程中就会提示你，当前命令是否正确，错误红色，正确绿色

```shell
git clone https://github.com/zsh-users/zsh-syntax-highlighting ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```

#### sudo

直接在插件列表中添加, 无需下载

#### 启用

`vim ~/.zshrc` 查找 `plugins` 在括号中添加插件列表

```
sudo zsh-autosuggestions zsh-syntax-highlighting
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

>  [怎么解决在vmware虚拟机下ubuntu linux系统重启后不能联网的问题_Engineer-Bruce_Yang的博客-CSDN博客](https://blog.csdn.net/morixinguan/article/details/118886890)

问题情况: 重启后网络图标消失, 无法联网

原因: NetworkManager服务启动失败

解决方案: 停止网络管理服务，删除网络状态文件，再重新启动网络服务

```shell
service NetworkManager stop
sudo rm /var/lib/NetworkManager/NetworkManager.state
service NetworkManager start
```



