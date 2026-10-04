---
date:
  created: 2026-10-04T23:10:00.000Z
  updated: 2026-10-04T23:10:00.000Z
title: Ubuntu 24 内存异常排查：定位到 GDM 图形会话
createTime: 2026/10/04 23:10:00
permalink: /blog/shmem-diag/
categories:
  - 踩坑记录
comments: true
---

之前，201server 的内存膨胀到整台机器完全卡死，只能物理重启。随后将内存从 16G 升级到了 32G(~~成本颇高~~)，也为可能的高负载容器加上了资源限制和监控。

但到了 10 月 4 日，宿主机的 Shmem 又涨到了约 18.6GiB，16GiB swap 几乎用满。

这次沿着历史采样数据重新排查，主要占用最终定位到 GDM 的登录界面会话。唤醒显示器释放了其中一部分，停止 GDM 后，剩余异常占用也随会话一起释放。下面记录这次排查的过程。

<!-- more -->

## 1. 机器卡死，重启大法+监控服务

201server 是放在实验室的一台个人 Ubuntu 机器，平时跑sub2api, 内网穿透, Hermes, m7a等服务。

9 月 15 日, 机器内存占用膨胀到 16G，swap 几乎用满，导致整台机器卡死。物理重启和内存扩容(16G -> 32G)后暂时恢复了运行。

平时的高负载应用是 m7a（March7th Assistant）的容器定时任务，排查自然先从它开始。

- 在GPT 5.6 的分析中, 仅定位到Shmem异常, 但缺少进一步的监控数据
- 初步怀疑 m7a 的内存泄露或者启动配置异常, 导致启动了GUI, 进而占用大量内存

所以为 m7a 加上资源限制，并部署了常驻监控。监控同时记录容器与宿主机的内存变化，异常时保存快照，便于后续对照。

::: note 机器具体配置如下：

| 项目 | 规格 |
| --- | --- |
| 内存 | 扩容后 32G，系统可见 31.09GiB RAM；另有 16GiB swap（`/swap.img`） |
| CPU | 12 逻辑核 |
| 系统 | Ubuntu 24.04，内核 7.0.0-31-generic |
| 图形栈 | libmutter-14-0 46.2-1ubuntu0.24.04.14、<br>gnome-shell 46.0-0ubuntu6~24.04.13、<br>Mesa 25.2.8-0ubuntu0.24.04.2 |

:::

## 2. 扩容后，内存仍在持续增长

> **扩容之后，机器仍然出现了内存不足的问题。忍不了了, 严查!**

监控留下的快照显示，GDM 会话的内存和 swap 总量仍在增长。

| 时间 | GDM 内存（GiB） | GDM swap（GiB） | 合计（GiB） |
| --- | ---: | ---: | ---: |
| 10-03 19:07 | 16.50 | 0.00 | 16.50 |
| 10-04 03:07 | 24.25 | 0.15 | 24.40 |
| 10-04 15:07 | 26.86 | 7.95 | 34.81 |
| 10-04 22:11 | 18.70 | 15.62 | 34.32 |

> 这里的“GDM 内存”取自会话 cgroup 的 `memory.current`，swap 则取自 `memory.swap.current`，后者不包含在前者里。

- 前几个时间段的总量接近线性增长，部分窗口接近 1GiB/小时。

翻看日志还发现，10 月 3 日凌晨已经发生过一次 global OOM，hermes 通知服务被内核杀掉。

### 2.1 解除对 m7a 的怀疑

先回到最初怀疑的 m7a 服务：

- 已有历史采样里，它的 cgroup shmem 一直为零；容器也没有设备映射，没有开启 privileged。
宿主机几十 GiB 的 Shmem 并没有体现在它的 cgroup 里。
- 10 月 4 日晚，m7a 因反复重启被监控自动隔离，但停止后宿主机异常内存并没有大幅释放。
- 检查图形服务的启动记录后，也没有发现 m7a 参与：GDM 由 systemd 随系统启动，异常会话属于宿主机的登录界面。

### 2.2 从 Shmem 查到 GDM 的图形对象

1. 沿宿主机 cgroup 逐层排查后，发现异常占用主要集中在 GDM 的 Wayland 登录界面会话 session-c2.scope。该会话的 shmem 约为 18.5 GiB，swap 约为 15.6 GiB，与整机的异常内存占用基本吻合。
2. 进一步检查该会话中的 gnome-shell，其 DRM fdinfo 显示进程持有约 36 GiB 图形对象，其中约 13.8 GiB 驻留在内存中。驱动侧的 GEM 对象统计也与该会话的 unevictable 内存规模接近，多项证据均指向 GDM 会话持有的大量图形对象。
3. 机器仅连接一台 1080p 显示器，采样时显示器处于省电关闭状态。同时，帧缓冲和导出的 dma-buf 占用都很小，因此无法解释这几十 GiB 的内存占用。

### 2.3 查阅 Mutter 的上游修复

> Mutter 是 GNOME 桌面环境里的窗口管理器 + 合成器，GNOME Shell 底层大量依赖它。

顺着显示器省电状态和旧图形对象占用，查到了可能的相关修复：
[GNOME/mutter MR !5285](https://gitlab.gnome.org/GNOME/mutter/-/merge_requests/5285)

- 旧实现只在提交显示模式更新和退出时清理 `detached_onscreens`。
- 显示器省电时不走模式提交路径，若此时发生显示重建或热插拔，旧 onscreen 对象及其图形内存可能持续累积。
- 补丁在进入省电时清理旧列表，并避免省电期间继续加入对象；该修复已列入 Mutter 50.5 的 NEWS。

比对源码和 Ubuntu 发行版补丁后，本机的 Mutter 46.2 仍保留旧逻辑，没有包含这项修复。

## 3. 验证：唤醒显示器，再停止 GDM

先短暂唤醒显示器，再恢复省电状态。随后短暂停止并重启 GDM：

| 阶段 | GDM 内存 + swap | 图形对象 total | 全机 Shmem |
| --- | ---: | ---: | ---: |
| 唤醒前 | 34.32GiB | 36.34GiB | 18.59GiB |
| 唤醒后 | 28.14GiB | 30.17GiB | 15.37GiB |
| 停止 GDM 后 | 会话结束 | 原 client 消失 | 0.12GiB |

唤醒显示器后，内存与 swap 合计、图形对象均减少约 6GiB(应该是触发了清理机制)；停止 GDM 后，其余异常占用也释放，swap 降至约 0.21GiB。

::: note
  算是有了暂时的缓解手段...
:::

## 4. 处理结果与后续

这次确认了异常内存的主要归属：旧 GDM/GNOME 图形会话持有了大量图形对象，结束会话后可以释放。扩容到 32G 没有解决持续增长，重启 GDM 可以恢复正常的内存占用。

> 待确认：是否全部由上述 Mutter 省电路径缺陷导致。
>
> 唤醒显示器只释放了约 6GiB，剩余占用需要结束会话才释放；上游案例中的 dma-buf 快速增长与本机也有差异，后续还需要补丁前后的验证。

本机尚未安装对应修复，后续安排：

- 继续观察，并核对 Ubuntu 24.04 / Mutter 46 是否有适用的维护更新或补丁回补。
- 如果再次增长，先保存证据，再验证显示省电切换和会话重启后的变化。

回头看，最有用的是之前留下的历史采样。m7a 是主要高负载应用，所以最初从它查起，但最终的归属还是要看 cgroup 和图形对象证据。只盯进程 RSS、只看内存下降，或者把停止容器与后续变化直接联系起来，都容易漏掉这次问题。

## 参考

- GNOME 上游补丁：<https://github.com/GNOME/mutter/commit/af0c9808.patch>
- Mutter 46 系列源码（`meta-renderer-native.c`）：<https://raw.githubusercontent.com/GNOME/mutter/46.2/src/backends/native/meta-renderer-native.c>
- Mutter 50 系列 NEWS（含该修复）：<https://raw.githubusercontent.com/GNOME/mutter/gnome-50/NEWS>
- 内核 DRM usage-stats 文档（fdinfo 字段口径）：<https://docs.kernel.org/gpu/drm-usage-stats.html>
