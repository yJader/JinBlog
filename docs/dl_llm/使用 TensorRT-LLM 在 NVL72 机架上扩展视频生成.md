---
author: NVIDIA TensorRT-LLM Team
date: 2026-07-13 00:00:00 +0800
categories:
  - TensorRT-LLM
  - Video Generation
tags:
  - TensorRT-LLM
  - Diffusion Transformer
  - Distributed Inference
  - Video Generation
title: 使用 TensorRT-LLM 在 NVL72 机架上扩展视频生成
createTime: 2026/07/13 00:00:00
permalink: /dl_llm/tensorrt-llm-scaling-video-generation-nvl72/
---

> [!NOTE]
> 本文译自 NVIDIA TensorRT-LLM 团队的 [Scaling Video Generation Across NVL72 rack with TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM/blob/main/docs/source/blogs/tech_blog/blog25_Scaling_Video_Generation_Across_NVL72_Rack_with_TensorRT-LLM.md)，原文采用 [Apache License 2.0](https://github.com/NVIDIA/TensorRT-LLM/blob/main/LICENSE) 发布。技术名称、代码、配置项与数值按原文保留。

# 使用 TensorRT-LLM 在 NVL72 机架上扩展视频生成

作者：NVIDIA TensorRT-LLM 团队

## 摘要

现代 Diffusion Transformer（DiT）视频生成模型（如 [Wan 2.2 T2V-A14B](https://huggingface.co/Wan-AI/Wan2.2-T2V-A14B-Diffusers) 和 [Cosmos3-Super](https://huggingface.co/nvidia/Cosmos3-Super)）的 compute 开销巨大：生成一段 5 秒的 720p 视频需要五分钟以上。几乎所有时间都花在 DiT denoising loop 上。该循环要执行数十次完整的 forward pass，每次处理 7 万到 15 万个 token。与 LLM decode 不同，DiT 的每个 denoising step 都相当于一次 prefill：classifier-free guidance（CFG）需要对 Transformer 求值两次，而 VAE decoder 也有独立的 compute 和 activation memory 峰值。在如此长的序列上，复杂度随序列长度平方增长的 dense bidirectional attention 主导了每步 compute。Pipeline Parallelism 无法在单步、单请求负载中摊销开销；Tensor Parallelism 虽然能有效减少节点内的逐层 compute，却会在包括 FFN 在内的每一层引入 communication。Sequence Parallelism 只在 attention operation 中进行 communication，直接针对主要开销，因此序列维度是多节点扩展最自然的轴。

本文介绍 TensorRT-LLM 的 [`VisualGen`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/visual_gen/visual_gen.py#L176) runtime 如何利用 **CFG Parallelism**、**Ulysses Parallelism**、**Ring Attention**、**Attention2D Context Parallelism** 和 **Parallel VAE**，把 DiT denoising loop 和 VAE decoder 从单张 NVIDIA B200 扩展到完整的 GB200 NVL72 机架。这些 parallelism axis 统一在一个 PyTorch `DeviceMesh` 下：前四种技术对 DiT 的 CFG stream 和 token sequence 进行 sharding，Parallel VAE 则独立扩展 decoder。所有 parallelism axis 都通过 [`ParallelConfig`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/visual_gen/args.py#L165) 声明配置；从 1 张 GPU 扩展到 72 张 GPU 无需修改模型代码。

在 Wan 2.2 T2V-A14B（5 秒 1280×720 视频，40 个 denoising step）上，从单张 NVIDIA B200 扩展到完整 GB200 NVL72 机架时，`CFG=2 × Ulysses=4 × Attention2D 3×3` 配方将 DiT denoising loop 缩短约 **53 倍**，并带来约 **41 倍的 end-to-end speedup**。end-to-end speedup 低于 denoising speedup，是因为 DiT 扩展后仍有固定的 latency tail，最终受 Amdahl's law 限制。

同一 runtime 无需修改即可用于 Cosmos3-Super。该模型采用 64B Mixture-of-Transformers 架构，生成 189 帧、1280×720 的视频；相同的 `CFG=2 × Ulysses=4 × Attention2D 3×3` 配方在完整 GB200 NVL72 机架上实现了**约 55 倍的 denoising speedup（end-to-end 约 33 倍）**。

<p align="center">
  <img src="./使用 TensorRT-LLM 在 NVL72 机架上扩展视频生成.assets/tech_blog25_nvl72_scaling.png" alt="Wan 2.2 T2V-A14B scaling from one B200 GPU to the 72-GPU GB200 NVL72 recipe: ~53x denoise, ~41x end-to-end" width="49%">
  <img src="./使用 TensorRT-LLM 在 NVL72 机架上扩展视频生成.assets/tech_blog25_cosmos3_highlight.png" alt="Cosmos3-Super scaling from one B200 GPU to the full 72-GPU GB200 NVL72 recipe: ~55x denoise, ~33x end-to-end" width="49%">
</p>

<p align="center"><sub><em>图 1.相同的 VisualGen 配方将两个模型从单个 GPU 扩展到完整的 GB200 NVL72 机架。左：Wan 2.2 T2V-A14B（5秒1280×720，40步）。右：Cosmos3-Super（189帧1280×720，35步）在相同的`CFG=2 × Ulysses=4 × Attention2D 3×3`配方下。</em></sub></p>

## 目录

- [视频生成中的扩展挑战](#视频生成中的扩展挑战)
- [CFG Parallelism](#cfg-parallelism)
- [Ulysses Parallelism](#ulysses-parallelism)
- [Toward Async Ulysses](#toward-async-ulysses-overlapping-communication-and-compute)
- [Context Parallelism](#context-parallelism)
- [Ring Attention](#_1-ring-attention)
- [Attention2D Parallelism](#_2-attention2d-parallelism)
- [Scaling the VAE Decoder](#scaling-the-vae-decoder)
- [Parallelism Mesh](#parallelism-mesh)
- [NVL72 扩展结果](#nvl72-扩展结果)
- [Cosmos3-Super](#cosmos3-super)
- [使用 trtllm-serve 提供在线服务](#使用-trtllm-serve-提供在线服务)
- [质量评估](#质量评估)
- [结论](#结论)
- [选择高性能配置](#选择高性能配置)
- [局限与未来工作](#局限与未来工作)
- [参考资料](#参考资料)
- [致谢](#致谢)

---

## 视频生成中的扩展挑战

多步 Diffusion Transformer 视频生成具有独特的 compute profile。单个请求会运行完整 Transformer 30 到 50 次，每个 denoising step 执行一次；每一步都要从头处理整个时空序列，没有 KV cache，也无法跨 step 摊销。对于生成 5 秒 1280×720 视频的 [Wan-AI/Wan 2.2 T2V-A14B](https://huggingface.co/Wan-AI/Wan2.2-T2V-A14B-Diffusers)，每个 step 的 dense bidirectional self-attention 大约处理 **72k 个 DiT token**，并重复 40 次\*。即使使用单张 NVIDIA B200 GPU，生成一段 5 秒视频也可能需要数分钟。

在每步 72k 个 token 的情况下，复杂度为 $O(N^2)$ 的 dense bidirectional self-attention 主导 compute cost；FFN、norm 和 modulation 仅随序列长度线性增长。相比之下，LLM decode 借助 KV cache，可将固定上下文下的逐步 attention cost 控制在 $O(N)$；即使是 prefill，也只需在通常远短于 72k token 的序列上支付一次 $O(N^2)$。DiT inference 没有跨 denoising step 的 cache，因此每一步都要按完整序列支付 $O(N^2)$。由此，**sequence** 成为天然的 sharding axis：attention matrix 是完整、无 mask 的 $N \times N$ block，可以在 GPU 间规整切分。另一个天然轴是 CFG；conditional 与 unconditional 两次 evaluation 不共享状态，可在互不相交的 GPU group 上并发执行。

Tensor Parallelism 很适合降低每层 memory 和 compute：它在 GPU 间划分 weight matrix，并可通过高速节点内互连高效运行。TRT-LLM VisualGen 支持 TP；随着模型增大，这一能力更加重要（Wan 2.2 A14B 有 40 个 attention head，[nvidia/Cosmos3-Super](https://huggingface.co/nvidia/Cosmos3-Super) 有 64 个）。代价是贯穿整个模型的 communication：TP 会在包括 FFN 在内的每一层增加 collective。当 attention 主导逐步 compute cost 时，Sequence Parallelism 更合适，因为它将 communication 限制在 attention operation 内，让 FFN、norm 和 modulation 在本地 sequence shard 上运行。

Pipeline Parallelism 则不适合这一 workload。PP 依靠 microbatch pipeline 隐藏 stage 间 communication，只有并发处理多个 request 时才能获益。这里的视频生成是单请求、latency-bound workload，因此任一时刻只有一个 pipeline stage 忙碌，其余 stage 都会空闲，PP 无法改善关键 latency 指标。

这篇文章重点关注序列和 CFG 轴作为主要的多节点扩展故事； TP 由所有这些组成，但由于其跨多个节点的效率相对较差，因此超出了本文的范围。

最后，denoising loop 末尾的 VAE decoder 有独立的 activation memory 峰值，而且完全位于 Transformer 之外。Parallel VAE 沿图像空间轴对 decoder 进行 sharding：每个 rank 在本地 decode $1/P$ 的 spatial shard，最后通过 all-gather 重建完整视频。

总而言之，本文采用以下 parallel strategy 扩展视频生成：
- **CFG Parallelism** 将 conditional 与 unconditional stream 分配到不同 GPU group；两次 prefill 完全并发，只在 combine step 执行一次小规模 all-gather。
- **Sequence Parallelism**（Ulysses、Ring、Attention2D）跨 GPU 对时空 sequence 进行 sharding；仅 attention layer 需要 collective，FFN、norm 和 modulation 都在本地 sequence shard 上运行。
- **Parallel VAE** 在空间维度对 decoder 进行 sharding，避免 DiT 扩展后 VAE decode 成为新的 bottleneck。

本文的其余部分首先介绍每个轴，然后展示它们如何组成一个由 `ParallelConfig` 上的声明性旋钮构建的单个 PyTorch `DeviceMesh`，以及相同的配置如何从单个 NVIDIA B200 扩展到完整的 GB200 NVL72 机架。

<sub>\* 本文关注多步 Diffusion Transformer；步数蒸馏扩散模型和自回归视频模型不在讨论范围内。参见[局限与未来工作](#局限与未来工作)。</sub>

## CFG Parallelism

Classifier-free guidance 在每个 denoising step 对 Diffusion Transformer 进行两次 evaluation：一次用 positive prompt embedding 生成 $\text{noise}_\text{cond}$，一次用 negative prompt embedding 生成 $\text{noise}_\text{uncond}$，然后将两个 prediction 组合为

$$
\text{noise} = \text{noise}_\text{uncond} + \text{guidance\_scale} \cdot (\text{noise}_\text{cond} - \text{noise}_\text{uncond})
$$

两次 evaluation 共享 weight、timestep 和 shape，因此可以在两个不相交的 GPU group 上完全并发。设置 `cfg_size = 2` 即可启用 CFG Parallelism：conditional stream 在 mesh 的一半上运行，unconditional stream 在另一半上运行。两边各自完成完整的 DiT forward pass，stream 之间无需 communication；只有两个 noise prediction tensor 会在 combine step 汇合。

`cfg` 是最外层 mesh dimension，因此每一半 GPU end-to-end 运行一个 stream，并且只加载各自的 conditional 或 unconditional prompt embedding。两边在每个 step 只汇合一次：CFG group 执行一次 all-gather 交换本地 `noise_pred`，随后每个 rank 都持有两个 prediction，并在本地执行 combine。额外的 guidance stream（如 STG 或 modality guidance）沿用同一模式，每个 stream 对应一个 collective。

**最终效果是每步 latency 几乎减半**，代价是两份 weight replica，以及每步在 2-rank group 上执行一次 all-gather。这个 collective 足够小，主要受 bandwidth 而非 latency 限制，并且几乎可以与每个 rank 上 combine 之后的 scheduler step 完全 overlap。仅启用 `cfg_size=2`、不使用其他 parallelism 时，latency 已接近减半：

| 配置 | GPU | denoising | end-to-end | speedup |
| :--- | ---: | ---: | ---: | ---: |
| `cfg1`（单流） | 1 | 342.04s | 346.16s | 1.0× |
| `cfg2`（CFG Parallelism） | 2 | 179.96s | 183.01s | **1.90× / 1.89×** |

这种近线性 scaling 使 CFG 成为成本最低、应优先于 Sequence Parallelism 扩展的 parallelism axis。在 72-GPU 机架上，把 2 倍 parallel factor 分配给 CFG（`cfg2·ulysses4·cp9`），而不是 Ulysses（`cfg1·ulysses8·cp9`），可将 denoising loop 从 7.57 秒缩短到 7.04 秒，即 **denoising latency 降低约 7.5%，end-to-end latency 降低约 6%**。CFG 还能与 Ulysses、Attention2D、Ring 和 Parallel VAE 直接组合。

## Ulysses Parallelism

Ulysses（[arXiv:2309.14509](https://arxiv.org/abs/2309.14509)）的关键在于：attention operation 之外的 activation 已沿 sequence axis 在 GPU 间完成 sharding。每个 rank 持有 $[B, S/P, H, D]$，其中 `P` 是 Sequence Parallelism degree；FFN、norm 和 modulation 都可在本地 shard 上运行，无需 communication。标准 attention 则是全局操作，位置 $i$ 的 query 必须访问完整 sequence 中的所有 key 和 value。Ulysses 只在 attention operation 内交换 sharding axis：attention 前通过 all-to-all 将 $[B, S/P, H, D]$ 转换为 $[B, S, H/P, D]$，attention 后再转换回来。这样每个 rank 都能看到完整 sequence，但只负责 $1/P$ 的 attention head。除非再组合 TP 等 FFN sharding scheme，否则 FFN 和其他模块都不需要 collective。

<p align="center">
  <img src="./使用 TensorRT-LLM 在 NVL72 机架上扩展视频生成.assets/tech_blog25_ulysses_dataflow.png" alt="Ulysses sequence parallelism data layout: a pair of all-to-alls transposes a frame-sharded layout into a head-sharded layout for attention, then back" width="1080">
</p>

<p align="center"><sub><em>图 2. Ulysses 在 attention 之外始终保持 sequence-sharded layout。每个 rank 持有一部分视频 frame 和全部 attention head，因此 QKV projection、norm 和 MLP 都在本地运行。仅在 full-sequence attention 前后，通过一对 all-to-all 转换为 head-sharded layout，再转回 MLP 所需的 layout。</em></sub></p>

**Fused 与 unfused QKV all-to-all。** 输入 all-to-all 之前，Q、K、V 已由 QKV projection 计算完成，并以三个独立的 $[B, S/P, H, D]$ tensor 存放在 memory 中。三者在同一 process group 上使用完全相同的 collective pattern，因此有两种传输方式：

- **Unfused（3 个 collective）：** 分别为 Q、K、V 执行 `all_to_all_4d`。实现简单，适用于任何 inner backend，因为结果直接落为三个独立 tensor。
- **Fused（1 个 collective）：** 将 Q、K、V 打包进单个 $[B, S/P, 3, H, D]$ buffer，并执行一次 `all_to_all_5d`。这要求 inner backend 能接收 stacked QKV input。

两条路径传输的 byte 数完全相同，因此 bandwidth cost 相同。差异在于 **launch overhead**：每个 NCCL collective 都对应独立的 kernel launch、staging 和 stream synchronization。从三个 collective 减少到一个，可消除关键路径上的两个 serialization point。DiT inference 的 per-rank tensor 和 batch 都较小，这一优化在每个 denoising step 的多层 Ulysses 中会产生可测量收益。

all-to-all 生成的 stacked QKV buffer 是一块连续 allocation；inner backend 可在 attention kernel 前执行一次 FP8 cast，而不必分别处理三个 tensor。对于 QKV 使用 BF16、attention kernel 输入使用 FP8 的 workflow，fused path 可将 quantization overhead 降低约 3 倍。生成的 FP8 QKV layout 还能直接传入 attention kernel，无需 intermediate copy，从而控制 memory footprint。

**Communication cost。** 无论 sequence length 多大，Ulysses Parallelism 每层只执行两次 all-to-all。对于长度为 $N$ 的 sequence 和 $P$ 张 GPU，每张 GPU 向其他 $P-1$ 个 rank 分别发送 $O(N/P^2)$ 的 data chunk，总 communication cost 为 $O(N/P)$。

**限制。** Ulysses Parallelism 受模型 attention head count 限制：degree $P$ 不能超过 `num_heads`，并且必须整除 `num_heads`；若要在 NVL72 上均匀使用全部 GPU，$P$ 还必须整除 72。Wan 2.2 T2V-A14B 的 $\text{num\_heads}=40$，因此 NVL72 上可用的最大 Ulysses degree 为 $P=8$。

### Toward Async Ulysses: Overlapping Communication and Compute

<p align="center">
  <img src="./使用 TensorRT-LLM 在 NVL72 机架上扩展视频生成.assets/tech_blog25_async_ulysses.png" alt="Async Ulysses V-to-Q-to-K pipeline: each tensor's all-to-all runs on the Copy Engines and overlaps the next tensor's projection compute" width="1080">
</p>

<p align="center"><sub><em>图 3. Async Ulysses 将 Q/K/V all-to-all 放到独立 stream 上的 GPU Copy Engine，并按 V→Q→K 形成 pipeline。每个 tensor 的跨 rank transfer 与下一个 tensor 的 projection compute overlap，从而用有效 compute 隐藏 collective latency。</em></sub></p>

当前实现同步执行 input all-to-all：attention kernel 启动前，compute stream 会在整个 collective 期间空闲。在 NVIDIA B200 上、WAN 规模 sequence length 且 `ulysses_size = 4` 时，每次 all-to-all 约耗时 1-2 ms；这一 idle time 在 40 个 attention layer 和 40 个 denoising step 中不断累积。Async Ulysses 在专用 side stream 上执行 V/Q/K 跨 rank exchange，同时让 default stream 计算下一组 V/Q/K，从而减少 idle time。该功能通过 `parallel_config` 中的 `async_ulysses: true` 启用，仅适用于可通过 NVLink 和 CUDA IPC 访问的 peer。

**设计**

- **使用 Copy Engine 进行 P2P communication。** P2P data movement 运行在 GPU Copy Engine（CE）上，而不是使用占用 SM 的 NCCL kernel。NCCL collective 会与后续 Q/K/V projection、normalization 和 RoPE 竞争 compute resource；CE 与 SM 是独立硬件，因此 communication 与 compute 可以真正 overlap。
- **本地 chunk 直接写入 HBM。** Fused pre-exchange kernel 完成 permute 后，直接写入 local rank 的 chunk，避免通过 CE local channel 执行 D2D copy，否则有限的 local bandwidth 会成为关键路径。
- **Communication 与 compute 使用独立 CUDA stream。** 两条 execution lane 通过轻量级 CUDA event 在每个 Q/K/V issue point 同步，避免在同一 stream 上相互阻塞。
- **V → Q → K rolling pipeline。** V 的 pre-exchange compute 最少，不需要 normalization 和 RoPE，因此最先发出；V transfer 与 Q compute overlap，Q transfer 与 K compute overlap。K 之后没有可用于隐藏 latency 的 compute，所以 default stream 必须等待 K transfer 和最终 barrier 完成，再启动 attention。
- **跨 rank exchange 使用 symmetric-memory buffer 与 barrier。** 一组由 CUDA IPC 支持的 symmetric-memory receive buffer 保存 V/Q/K slot，peer-writable pointer 只在启动时交换一次。Barrier deferred 到三次 push 全部完成后执行，使 transfer 可以在 CE 上连续流动；attention 启动前，default stream 会看到完全同步的 receive buffer。

**Speedup：**

*B200 isolated all-to-all。* 单 tensor all-to-all latency，`B=2, S_total=6144, H=32, D=128`，warmup=30，benchmark=100。

| Ulysses size | Fused QKV 5D all-to-all | Split QKV 3x 4D all-to-all | Async Ulysses pipeline |
| :---- | :---- | :---- | :---- |
| 4 | 419 微秒 (1.00×) | 483微秒（0.87×）| **339 µs (1.24×)** |
| 8 | 251 微秒 (1.00×) | 294微秒（0.85×）| **194 µs (1.29×)** |

*B200 end-to-end。* OFF 与 ON 分别表示禁用和启用 Async Ulysses。

WAN 2.2 T2V-A14B，720×1280，80帧，40步，NVFP4：

| World size | Ulysses | CFG | Async OFF E2E (s) | Async OFF denoising (s) | Async ON E2E (s) | Async ON denoising (s) | E2E latency delta | Denoising latency delta |
| ----:| ----:| ----: | ----:| ----: | ----:| ----:| ----: | ----: |
| 2 | 2 | 1 | 206.731 | 203.31 | 198.311 | 194.89 | **−4.07%** | **−4.14%** |
| 4 | 2 | 2 | 103.031 | 100.46 | 100.504 | 97.93 | **−2.45%** | **−2.55%** |
| 8 | 4 | 2 | 55.444 | 53.28 | 54.114 | 51.95 | **−2.40%** | **−2.48%** |


## Context Parallelism

### 1. Ring Attention

与 Ulysses 相同，Ring Attention 沿时空 sequence 进行 sharding，使每个 rank 持有 $[B, S/P, H, D]$；FFN、norm 和 modulation 都在本地 shard 上运行，无需 communication。差异在于如何实现 global attention：Ulysses 在 attention layer 内切换为 head sharding，因此 parallel degree 受 attention head count 限制；**Ring Attention 没有 head-count ceiling**，degree $P$ 可以超过 `num_heads`，可把 Sequence Parallelism 扩展到 Ulysses 上限之外。

**K/V block 轮转，Q 保持本地。** 每个 rank 固定持有 local query shard，并在由 $P$ 张 GPU 构成的 ring 中传递 K/V block。经过 $P$ 个 step，每个 rank 依次计算 local Q 对当前 K/V block 的 partial attention，并合并到 running output；最终每个 query position 都处理了完整 sequence 的全部 key/value：

```
Rank r holds Q_r (fixed) and K/V block for step i

  step 0:  attn(Q_r, K_r, V_r)  --isend/irecv-->  K/V from rank r+1
  step 1:  attn(Q_r, K_{r+1}, V_{r+1})  --isend/irecv-->  ...
     ...
  step P-1: attn(Q_r, K_{r-1}, V_{r-1})   (no exchange on final step)

  running output merged after each step  -->  final O_r
```

**Online softmax merge。** 每个 step 都产生 partial output 和 log-sum-exp（LSE）statistic；[`RingAttention`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/_torch/visual_gen/attention_backend/parallel.py) 使用 **fp32** streaming softmax recurrence 逐 block 合并，最终得到与一次 global attention pass 相同的结果。

**Communication-compute overlap。** 当前 block 的 FA4 kernel 启动前，runtime 会用 non-blocking P2P（`batch_isend_irecv`）提交下一 block 的 K/V exchange，使 neighbor transfer 与 attention compute overlap。偶数 rank 按 send-then-recv、奇数 rank 按 receive-then-send 执行以避免 deadlock；最后一个 ring step 不再 exchange。

**Communication cost。** Ring 每个 attention layer 需要 $P-1$ 次 neighbor exchange，communication volume 随 sequence length $N$ 按 $O(N)$ 增长。每个 ring step 还会执行一次 partial FA4 pass 和 online softmax merge，因此 attention compute 也随 degree $P$ 增长。优势是没有 head-count ceiling、topology 简单，并可在同一 mesh 上与 Ulysses 组合（$\text{cp\_size} \times \text{ulysses\_size}$）。P2P transfer 可与 compute overlap，所以小 $P$、短 sequence 时仍有竞争力；但 production video 通常更适合使用 communication cost 为 $O(N/\sqrt{P})$ 的 Attention2D。

### 2. Attention2D Parallelism

Attention2D Parallelism（[arXiv:2503.15758](https://arxiv.org/abs/2503.15758)）把 $P$ 张 Context Parallelism GPU 组织成 $\text{row\_size} \times \text{col\_size}$ 的 logical 2D mesh。Ulysses 用完满足 attention head divisibility 的 GPU 后，Attention2D 是继续扩展的首选 Context Parallelism strategy。它与 Ring 一样没有 head-count ceiling，任意 row×column mesh 都有效。`col_size=1` 时退化为 all-gather K/V 的 no-merge scheme，`row_size=1` 时退化为 all-gather Q 的 merge scheme。在对称 mesh 上，每个 axis 只 gather $S/\sqrt{P}$，communication cost 为 $O(N/\sqrt{P})$，适合 long-sequence DiT inference。runtime 将原本面向 causal LLM training 的 Attention2D 改造成 full bidirectional DiT inference。

**Gather phase：Q 沿 row，K/V 沿 column。** rank 构成 $\text{row\_size} \times \text{col\_size}$ mesh，其中 $P = \text{row\_size} \times \text{col\_size}$。每个 rank 起初各持有 Q、K、V 的 $1/P$ shard，即 $Q_i,K_i,V_i$，shape 均为 $[B,S/P,H,D]$。随后沿两个独立 mesh axis 执行 all-gather：

- **Q gather** 在 `row_process_group` 上执行：共享同一 row 的 `col_size` 个 rank concat 各自的 $Q_i$，最终每个成员持有 $[B,S/\text{row\_size},H,D]$；K/V 不变。
- **K/V gather** 在 `col_process_group` 上以 fused collective 执行：共享同一 column 的 `row_size` 个 rank concat 各自的 K/V，最终每个成员持有 $[B,S/\text{col\_size},H,D]$；Q 不变。

因此，Q 沿 `col_size` 扩展到 $S/\text{row\_size}$，K/V 沿 `row_size` 扩展到 $S/\text{col\_size}$；在对称的 $\sqrt{P}\times\sqrt{P}$ mesh 上，两者都是 $S/\sqrt{P}$。下图使用 `row_size=2, col_size=3` 的 $2\times3$ mesh（$P=6$），sequence 被划分为 shard 0 到 5：

<p align="center">
  <img src="./使用 TensorRT-LLM 在 NVL72 机架上扩展视频生成.assets/tech_blog25_attention2d.png" alt="Attention2D per-rank data flow on a 2x3 grid: gather Q over the row group, K/V over the column group, one attention pass per rank produces a partial output, then an all-to-all over the row group exchanges partials and a local flash_attn_combine reduction merges them" width="1080">
</p>

<p align="center"><sub><em>图 4. Rank 0 在 2×3 mesh 上的 Attention2D data flow。① row group all-gather Q；② column group all-gather K/V；每个 rank 执行一次 attention pass，得到 partial output 和 LSE；③ row group all-to-all 交换 partial，再由本地 `flash_attn_combine` reduction 合并为最终的 $[B,S/P,H,D]$ shard。</em></sub></p>

**行 (Q) 组**的成员最终具有相同的 Q 但**不相交** K/V shard； **列 (K/V) 组**的成员共享相同的 K/V，但持有不同的 Q 。

**Local attention。** [`Attention2DAttention`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/_torch/visual_gen/attention_backend/parallel.py) 执行 attention，并返回 $[B,S/\text{row\_size},H,D]$ 的 partial output，以及 $[B,H,S/\text{row\_size}]$ 的 LSE statistic。LSE 保存该 partial pass 的 softmax normalizer。

**Merge phase。** 共享相同 Q 的 `col_size` 个 rank 分别处理互不相交的 K/V shard。上图中 rank `0`、`1`、`2` 都持有 query `{0,1,2}`，但分别持有 key `{0,3}`、`{1,4}`、`{2,5}`。它们的 FA4 output 是同一 query position 在互补 key span 上的 partial result，必须在 row group 内 merge 才能恢复完整 softmax：

1. `row_process_group` 上的 **`all_to_all_single`** 在 `3` rank 之间交换输出和 LSE 块。
2. **`flash_attn_combine`** 将收到的 `3` 对 `(output, LSE)` 合并到一个批处理 kernel 中，生成与输入 layout 匹配的完全 reduction 的 $[B, S/P, H, D]$ sharding 。

**与 Ring 的区别：**

|  | Ring | Attention2D |
| :---- | :---- | :---- |
| **Q communication** | 无，所需 Q token 均在本地 | row group 内 `col_size` 个 rank all-gather $O(N/\sqrt{P})$ 数据 |
| **K/V communication** | $P$ 个 rank 以 P2P 交换 $O(N)$ 数据 | column group 内 `row_size` 个 rank all-gather $O(N/\sqrt{P})$ 数据 |
| **Partial** | $P$ 个 block，每个 ring step 对应一个轮转 K/V shard | row group 产生 `col_size` 个 partial，各覆盖不同 K/V shard |
| **Merge schedule** | Streaming：每个 FA4 step 后在本地 merge | Batch：一次 FA4 pass 后执行 `all_to_all` 与 `flash_attn_combine` |
| **Merge communication** | 无，全部本地完成 | row group 内执行一次 output+LSE `all_to_all` |
| **Attention pass** | $P$ 个 partial FA4 kernel | 每个 rank **1** 个 FA4 kernel |
| **Compute-communication overlap** | 支持 overlap | 当前分阶段执行，不 overlap |
| **Communication cost** | $O(N)$ | $O(N/\sqrt{P})$ |
| **Scaling** | $P$ 增大时 communication cost 不变 | $P$ 增大时 communication cost 按 $O(1/\sqrt{P})$ 降低 |

**Communication cost。** Attention2D 每层包含三个 collective phase：row 上的 Q all-gather、column 上的 K/V all-gather，以及 row 上的 output+LSE all-to-all。在对称 mesh（$\text{row\_size}\approx\text{col\_size}\approx\sqrt{P}$）上，communication volume 为 $O(N/\sqrt{P})$，相比 Ring 的 $O(N)$ scaling 更好，而且每个 rank 只执行一次 attention pass。

<p align="center">
  <img src="./使用 TensorRT-LLM 在 NVL72 机架上扩展视频生成.assets/tech_blog25_a2d_vs_ring.png" alt="Bar chart of denoise-loop latency for Attention2D vs Ring at 32 GPU (UL=8, CP=2), 64 GPU (UL=8, CP=4), and 72 GPU (UL=4, CP=9); Ring is +3%, +13%, and +83% slower respectively" width="820">
</p>

<p align="center"><sub><em>图 5. GB200 NVL72 上 Attention2D 与 Ring 的 denoising loop latency（Wan 2.2 T2V-A14B，5 秒 1280×720，40 个 step，固定 `cfg=2`）。随着 CP degree 增大，Attention2D 的 $O(N/\sqrt{P})$ communication cost 持续下降，而 Ring 的 $O(N)$ cost 保持不变；因此 Ring 在 CP=2、4、9 时分别慢 3%、13% 和 83%。72-GPU 配置中，每个 CFG replica 有 36 张 GPU，Ulysses degree 必须从 8 降到 4，更多 workload 被分配给 CP axis，进一步放大了 Ring 的 communication overhead。</em></sub></p>

## Scaling the VAE Decoder

DiT denoising loop 完成后，VAE decoder 仍需将 latent tensor 转换为 pixel。DiT 扩展到 GB200 NVL72 的 72 张 GPU 后，denoising loop runtime 已降到单 GPU 的一小部分，但 unsharded VAE decode 仍在单个 rank 上运行，因此成为 pipeline 的主要 bottleneck。Parallel VAE 用于消除这段 serial tail。

**Spatial sharding。** DiT 对 token sequence 进行 sharding，而 VAE 是运行在 `(B,C,T,H,W)` video tensor 上的 convolutional UNet-like stack，因此自然的 split axis 是 image space。`parallel_vae_split_dim` 选择 height 或 width，latent tensor（decode）或 video tensor（encode）沿该 dimension 分配到 `parallel_vae_size` 个 rank。每个 rank decode 一个 $1/P$ spatial shard，最后由 all-gather 重建完整 frame：

<p align="center">
  <img src="./使用 TensorRT-LLM 在 NVL72 机架上扩展视频生成.assets/tech_blog25_parallel_vae.png" alt="Parallel VAE: route the final latent to the parallel_vae_size VAE-group ranks while the rest idle, split image space along W into 1/P slices, decode each slice locally, all-gather into the full video, and use halo exchange so boundary convolutions stay correct" width="1080">
</p>

<p align="center"><sub><em>图 6. Parallel VAE decode。完整 latent 沿 image-space axis（此处为 `W`）切分为 `parallel_vae_size` 个 shard；各 rank 在本地 decode。Boundary convolution 仅与相邻 rank 交换宽度为 k-1 的 halo，attention block 则 gather 完整 split dimension；最终 all-gather 重建完整视频。</em></sub></p>

**Convolution 需要 neighbor：Halo Exchange。** Spatial split 会打断 block boundary 上的 convolution；$k\times k$ convolution 需要访问相邻 rank 上的 $k-1$ 行或列。每个 convolution 不必 gather 完整 activation，只需交换窄边界 halo，完成 compute 后再移除额外 output；边缘 rank 使用 zero padding。Halo size 只取决于 kernel size，因此 communication volume 很小。VAE attention block 是 global operation，需要在 attention 前 gather 完整 split dimension，之后再重新 sharding。

**VAE parallel degree 与 DiT sharding scheme 独立。** `parallel_vae_size` 单独控制 VAE width，不需要匹配 CFG、Ulysses 或 Context Parallelism degree。VAE 通常比 DiT 更早 saturation，而且 split dimension 必须整除数量较少的 latent row/column，因此不能直接使用较大的 `world_size`。

由此形成两种运行模式：

- **Single node（`world_size <= 8`）：** `parallel_vae_size == world_size`，每个 rank 都参与 decode。
- **Multi-node（`world_size > 8`，如 NVL72）：** DiT 使用全部 72 个 rank，`parallel_vae_size` 保持在 saturation point（约 8）；只有该 subset 执行 VAE decode，其余 rank 空闲。

**Measured impact。** 完整 72-GPU 配方的 denoising loop 仅为 **7.04s**，但 rank-0-only VAE decode 会增加约 **2.7s**；DiT 已扩展约 53 倍后，11.1s end-to-end latency 中约 **25%** 花在 single-rank VAE 上。随着 `parallel_vae_size` 翻倍，decode latency 最初近似减半，之后 spatial workload 不足，per-column halo 与 all-gather overhead 开始主导。`parallel_vae_size=8` 将 decode latency 降到约 **0.8s**（**3.3× speedup，降低 69%**），end-to-end latency 降到 **9.2s**（**1.2× speedup，降低 17%**），VAE 占比降至约 **9%**。degree 16 已无额外收益，因此 multi-node recipe 通常把 VAE degree 限制在 8 左右。

*Decode scaling*：仅测量 decode：

| `parallel_vae_size` | VAE decode | Decode speedup |
| :--- | ---: | ---: |
| 1（unsharded） | 2.72 秒 | 1.00× |
| 2 | 1.72 秒 | 1.58× |
| 4 | 1.04 秒 | 2.62× |
| 8 | 0.83 秒 | **3.28×** |
| 16 | 0.85 秒 | 3.20× |

*End-to-end impact*：完整 72-GPU NVL72 recipe：

| NVL72 recipe | VAE decode | VAE E2E share | End-to-end | End-to-end speedup |
| :--- | ---: | ---: | ---: | ---: |
| `parallel_vae_size=1`（unsharded） | 2.72 秒 | 24.5% | 11.08 秒 | 1.00× |
| `parallel_vae_size=8` | 0.83 秒 | 9.0% | 9.20 秒 | **1.20×** |


## Parallelism Mesh

五个 parallelism axis（CFG、TP、Ulysses、Context Parallelism、Parallel VAE）统一放在 `VisualGenMapping` 启动时构建的 PyTorch `DeviceMesh` 上。用户只需在 [`ParallelConfig`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/visual_gen/args.py#L165) 中设置各 axis size；`cfg_group`、`ulysses_group`、`cp_group`、`attn2d_row_group`、`attn2d_col_group` 和 `vae_group` 等 process group 都从 mesh 派生并缓存，因此 linear、attention 和 VAE layer 共享一致的 NCCL communicator。

World size 是各 axis size 的乘积：

```
world_size = cfg_size  x  tp_size  x  cp_size  x  ulysses_size

cp_size = ring_size                                 (Ring attention)
          OR attn2d_row_size x attn2d_col_size      (Attention2D, 2D tile)
```

无论 CP backend 如何，mesh axis order 都固定为 **`cfg - tp - cp - ulysses`**。Attention2D 中，`cp_size = attn2d_row_size × attn2d_col_size`；专用 row group 与 column group 由 Q 和 K/V gather 所需的 rank layout 派生：

```
Ring:          cp = ring_size
Attention2D:   cp = attn2d_row × attn2d_col   (+ row_group, col_group subgroups)
```

这一顺序由各 axis 的 communication pattern 对 interconnect locality 的敏感程度决定：**Ulysses 位于最内层，CFG 位于最外层**。TP 不在本文讨论范围内，因此下文省略。

- **Ulysses（innermost）** 包裹 CP，因此 all-to-all 最先执行，每个 rank 只移动约 $A/(UL\cdot CP)$ 的数据（$A=S\cdot H$）。虽然 volume 最小，但 all-to-all 对 bisection bandwidth 与 topology 最敏感：所有 rank 两两交换，最慢 link 会限制整个 blocking collective。因此 Ulysses group 必须放在高速、fully connected fabric 上。在混合 node-local NVLink 与 cross-node InfiniBand 的 topology 中尤其如此；GB200 NVL72 则是统一 NVLink domain，全部 72 张 GPU 都能以完整 bandwidth communication。
- **Context Parallelism（middle）** 的 per-rank volume 更大，但取决于 backend。Ring 移动约 $A/UL$，每个 rank 仅与两个 neighbor P2P exchange；Attention2D 移动约 $A/(UL\cdot\sqrt{CP})$，K/V all-gather 仅发生在 $\sqrt{CP}$ 规模的 row/column subgroup。两者对 topology boundary 都比 Ulysses all-to-all 更宽容。
- **CFG（outermost）** 每个 denoising step 只 combine 一次 conditional 与 unconditional branch，整个生成过程仅有数十次小规模 collective，因此可放在较慢的 cross-node 或 cross-rack fabric 上。

该顺序通过 rank layout 映射到 hardware。PyTorch 以 row-major 顺序排列 `mesh_shape`：最左 axis 变化最慢，最右 axis 变化最快。把 Ulysses 设为 fastest-varying axis，意味着共享 `(cfg,tp,cp)` 的 rank 获得连续 ID；若 launcher 也按 node 连续分配 rank，即可自动得到期望 placement，无需手工维护 rank-to-GPU mapping。

VAE axis 与 denoiser axis 独立。VAE group 不是从 denoiser mesh 中切分，而是 overlay 在现有 `cfg × tp × cp × ulysses` world 之上，因此 Parallel VAE 可独立扩展（参见 [Scaling the VAE Decoder](#scaling-the-vae-decoder)）。VAE rank 必须位于单个 CFG group 内，或者覆盖整个 world；guidance combine 后的 latent 只存在于一个 CFG branch，跨两个 branch 的 VAE group 会混合 conditional 与 unconditional replica，使 gather 和 halo collective 不一致。

有关完整的属性目录（每个 `*_group`、`*_rank`、扁平化的 `seq_mesh` 以及允许线性层重用 LLM TP 路径的 `to_llm_mapping()` 桥），请参阅 [`mapping.py`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/_torch/visual_gen/mapping.py)。

## NVL72 扩展结果

本节所有 performance data 都使用相同 benchmark workload 和公开的 distributed recipe：[`examples/visual_gen/configs/wan22_t2v_bf16_gb200_nvl72.yml`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/examples/visual_gen/configs/wan22_t2v_bf16_gb200_nvl72.yml)。

|项目 |价值|
| :--- | :--- |
|型号| [`Wan-AI/Wan2.2-T2V-A14B-Diffusers`](https://huggingface.co/Wan-AI/Wan2.2-T2V-A14B-Diffusers) |
|硬件| GB200 NVL72 |
|请求形状 | 5 秒 1280×720 视频（`num_frames=80`\* 16 fps）|
| denoising step | 40 |
| 精度 | BF16 |
| attention backend | FA4 |
| 引导系数 | 5.0 |
|基准负载| 3 个 prompt，单流 |

<sub>\* 受 Sequence Parallelism divisibility constraint 影响，benchmark 使用 80 帧而不是 Wan 原生的 81 帧。Temporal VAE 会把 81 帧映射为 21 个 latent frame，无法被 sweep 中的各个 CP degree 整除；80 帧会得到 20 个 latent frame，使 sequence length 可被不同 CP configuration 整除。这只是 benchmark convenience，并非 hard limit；framework-level padding 即可支持 81 帧。参见[局限与未来工作](#局限与未来工作)。</sub>

本节报告两个 metric。**Denoising loop** 是 parallelism axis 实际分担的 DiT workload。**End-to-end request** 是 serving endpoint 测得的完整 per-request latency，还包括不会随 DiT sharding 缩短的 fixed tail：text encoding、VAE decode、MP4 encode，以及 request/transport overhead。

文章顶部的图 1 汇总了核心结果；具体数字如下：

|指标| 1× B200 基线 | 72-GPU GB200 NVL72 |speedup|
| :--- | ---: | ---: | ---: |
|denoising loop| 370.8秒| 7.04秒| 52.7×（~53×）|
|end-to-end 请求| 373.35 秒 | 9.20 秒 | 40.6×（~41×）|

在 GB200 NVL72 上 sweep 各 GPU count 的最佳 recipe 后，DiT denoising loop 在完整 rack 上接近 linear scaling：

<p align="center">
  <img src="./使用 TensorRT-LLM 在 NVL72 机架上扩展视频生成.assets/tech_blog25_scaling_lines.png" alt="WAN 2.2 T2V-A14B DiT denoise-loop latency vs ideal linear scaling on GB200 NVL72, from 1 to 72 GPUs, with per-point parallel efficiency" width="1080">
</p>

<p align="center"><sub><em>图 7. GB200 NVL72 上的 DiT denoising-loop scaling。每个 GPU count 采用最佳 configuration，以 GB200 single-GPU 为 baseline。由于 CFG 与 Sequence Parallelism 几乎完整地划分了 Transformer workload，72 张 GPU 上达到约 49× speedup，接近 ideal linear scaling。</em></sub></p>

关键在于，完整机架上约 67% 的 parallel efficiency 只有 **Attention2D** 能够实现。Ulysses 受到 WAN attention head divisibility 限制（40 个 head 对应 `ulysses_size ≤ 8`），其余 GPU 必须分配给 Context Parallelism axis，而 Attention2D 是唯一能在 NVL72 scale 保持 efficiency 的方案。在 72 张 GPU 上，`cfg2·ul4·attn2d 3×3` 达到约 **67% efficiency**；等价的 `cfg2·ul4·ring9` 仅约 **37%**，相同 GPU 数量下慢 **83%**。Attention2D 的 $O(N/\sqrt{P})$ row/column collective 可持续扩展到整个 rack（参见[图 5](#_2-attention2d-parallelism)）。

这些数字背后的完整配方如下所示：

```yaml
attention_config:
  backend: FA4
parallel_config:
  cfg_size: 2            # CFG: conditional / unconditional streams on disjoint halves
  ulysses_size: 4        # Ulysses sharding
  attn2d_size: [3, 3]    # Attention2D context parallelism (row × col)
  parallel_vae_size: 8   # spatial VAE sharding (saturates at ~8)
compilation_config:
  resolutions:
    - [720, 1280]        # warmup at the benchmarked shape (request size 1280x720)
  num_frames:
    - 80                 # 5-second clip at 16 fps
```

### Cosmos3-Super

同一 runtime 无需修改即可扩展到结构差异很大的 Cosmos3-Super。该模型是具有 64 个 attention head 的 64B Mixture-of-Transformers，生成 189 帧视频，因此每个 denoising step 都是比 Wan 更大的 dense prefill。只有 workload 和各 GPU count 的 recipe 不同；CFG、Ulysses、Attention2D 和 Parallel VAE option 保持一致（[`examples/visual_gen/configs/cosmos3_t2v_bf16_gb200_nvl72.yml`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/examples/visual_gen/configs/cosmos3_t2v_bf16_gb200_nvl72.yml)）。

|项目 |价值|
| :--- | :--- |
|型号| [`nvidia/Cosmos3-Super`](https://huggingface.co/nvidia/Cosmos3-Super) |
|硬件| GB200 NVL72 |
|请求形状 | 189 帧 1280×720 视频，24 fps |
| denoising step | 35 |
| 精度 | BF16 |
| attention backend | FA4 |
| 引导系数 | 6.0 |
|基准负载| 3 个 prompt，单流 |

文章顶部图 1 的右侧汇总了核心结果；具体数字如下：

|指标| 1× B200 基线 | 72-GPU GB200 NVL72 |speedup|
| :--- | ---: | ---: | ---: |
|denoising loop| 373.1秒| 6.79 秒 | 54.9×（~55×）|
|end-to-end 请求| 383.1s | 11.78 秒 | 32.5×（~33×）|

各 GPU count 的最佳 recipe 得到与 Wan 相同的近线性 denoising-loop scaling：

<p align="center">
  <img src="./使用 TensorRT-LLM 在 NVL72 机架上扩展视频生成.assets/tech_blog25_cosmos3_scaling_lines.png" alt="Cosmos3-Super DiT denoise-loop latency vs ideal linear scaling on GB200 NVL72, with per-point parallel efficiency" width="1080">
</p>

<p align="center"><sub><em>图 8. GB200 NVL72 上的 Cosmos3-Super DiT denoising-loop scaling。每个 GPU count 使用最佳 configuration，以 GB200 single-GPU 为 baseline；72 张 GPU 上达到约 49× speedup。</em></sub></p>

与 Wan 相同，Cosmos3-Super 的 denoising loop 在同一 recipe 下也接近 linear scaling，说明 DiT sequence-length sharding pattern 能跨模型泛化。End-to-end efficiency 下降更快，因为它还包含更长视频带来的 MP4 encode、transport 和 persistence overhead；当 denoising loop 缩短到约 7 秒后，这些 fixed per-request cost 根据 Amdahl's law 成为主要占比。

## 使用 trtllm-serve 提供在线服务

相同的 `--visual_gen_args` YAML 驱动 `trtllm-serve` 进行在线服务。分布式多节点服务由 `examples/visual_gen/serve/` 下的 `benchmark_visual_gen_mgmn_distributed.sh` 脚本处理：

```shell
export CONTAINER_IMAGE=/path/to/tensorrt-llm.sqsh
export PROJECT_ROOT=/path/to/TensorRT-LLM
export MODEL=Wan-AI/Wan2.2-T2V-A14B-Diffusers
export SERVER_CONFIG=examples/visual_gen/configs/wan22_t2v_bf16_gb200_nvl72.yml

# Fill in <ACCOUNT_NAME> and <PARTITION> with your SLURM account and partition
sbatch -A <ACCOUNT_NAME> -p <PARTITION> -N 18 --ntasks-per-node=4 --ntasks=72 examples/visual_gen/serve/benchmark_visual_gen_mgmn_distributed.sh
```

该脚本在 background 为所有已分配 rank 启动 `trtllm-serve`，轮询 `http://${MASTER_ADDR}:8000/health` 直到返回 200，然后只在 rank 0 运行 `tensorrt_llm.serve.scripts.benchmark_visual_gen`。

## 质量评估

实现通过两类测试验证：**correctness** 检查每种 parallel configuration 是否复现 unsharded single-GPU Transformer forward；**quality** 则在多个 prompt 上比较完整 decoded video 与 single-GPU reference。

#### 分布式正确性

Single-node（4 GPU 和 8 GPU）parity harness [`test_wan_transformer_parallel.py`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tests/unittest/_torch/visual_gen/multi_gpu/test_wan_transformer_parallel.py) 在每种 parallel configuration 下执行 BF16 `WanTransformer3DModel` forward，并与使用相同 weight 和 seeded input 的 unsharded single-GPU reference 比较。

Ulysses、CFG+Ulysses、Ring×Ulysses 和 Attention2D `row×col`×Ulysses 均在 `atol=1e-2, rtol=1e-3` 内匹配 single-GPU reference。Harness 使用 random initialized、stabilized weight，并在 reduced model 上执行一次 forward，因此隔离验证了 parallelism 本身：all-gather、all-to-all 和 online softmax merge 在数值上正确，不依赖特定 checkpoint。

#### end-to-end 视频质量

使用 Wan 2.2 T2V-A14B 对 6 个 prompt 生成 832×480、9 帧、8 个 step 的短视频，固定 seed 42（BF16、FA4），再将每种 parallel configuration 的 decoded video 与 single-GPU reference 比较，并对所有 frame 的 LPIPS、PSNR、SSIM 和 cosine similarity 求平均。

FA4 attention kernel 和 compiled layer（`torch.compile`）使用 nondeterministic reduction，因此相同 prompt 与 seed 的两次 single-GPU run 也会略有差异，iterative denoiser 还会跨 step 累积这些误差。为此，先用第二次 single-GPU run 相对第一次的 score 建立 noise floor，再报告各 parallel configuration 相对该 floor 的结果。四项 metric 都在 decoded MP4 上逐 frame 计算并求平均，因此也包含 H.264 quantization 影响。

| 配置 | GPU | LPIPS↓ | 相对基线的 ΔLPIPS | PSNR↑ | SSIM↑ | 余弦相似度↑ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| _基线_（第二次单 GPU 运行） | 1 | 0.121 | — | 25.18 | 0.878 | 0.981 |
| `ulysses2` | 2 | 0.187 | +0.066 | 24.34 | 0.796 | 0.974 |
| `cfg2` | 2 | 0.200 | +0.079 | 23.83 | 0.777 | 0.970 |
| `cfg2·ulysses2` | 4 | 0.196 | +0.075 | 23.72 | 0.783 | 0.970 |
| `ulysses4` | 4 | 0.198 | +0.077 | 23.87 | 0.777 | 0.969 |
| `attn2d 2×1·ulysses2` | 4 | 0.198 | +0.077 | 24.00 | 0.777 | 0.970 |
| `attn2d 1×2·ulysses2` | 4 | 0.209 | +0.088 | 23.45 | 0.768 | 0.968 |
| `attn2d 2×2` | 4 | 0.220 | +0.099 | 23.36 | 0.759 | 0.967 |

为量化 nondeterminism 并确认 reference 合理，先在 single GPU 上隔离变量。Wan 使用 BF16，FA4 attention 与 `torch.compile` 都包含 nondeterministic reduction，因此相同 prompt 和 seed 不保证产生相同 pixel，iterative denoiser 还会累积微小差异。固定 model 与 seed 后，每次只改变一个 implementation detail：

|单 GPU 扰动，相同种子 | LPIPS↓ |
| :--- | ---: |
| PyTorch SDPA，`torch.compile` 关闭 — 重新运行 | 0.00（位精确）|
| FA4 与 PyTorch SDPA attention backend 对比 | 0.21 |
| PyTorch SDPA 、`torch.compile` 开启与关闭 | 0.24 |

Deterministic backend（PyTorch SDPA、关闭 `torch.compile`）可以 byte-for-byte 复现，说明 harness 本身准确。启用 fast kernel 后不再 deterministic：FA4 rerun 已产生 0.121 LPIPS，即表中的 noise floor；切换 attention backend 得到 0.21，切换 `torch.compile` 得到 0.24。这些差异来自 pixel-level kernel ordering，而非 algorithm change。`torch.use_deterministic_algorithms(True)` 可以把 floor 降回 0 LPIPS，但会牺牲 performance；因此 performance benchmark 保持关闭，并以实际 fast-kernel floor 作为 reference。

相对这一范围，parallelism 的 quality cost 很小。所有 parallel configuration 都落在 0.187–0.220 LPIPS（cosine ≥ 0.967，PSNR ≥ 23 dB），仅比 floor 高 0.07–0.10，处于 single-GPU kernel choice 本身造成的波动范围内。Offset 与 parallel degree 无关：2-GPU Ulysses（0.187）和 4-GPU recipe（约 0.196–0.198）同样接近 reference。Attention2D 的 LPIPS 略高（最高 0.220），原因是跨 rank online softmax merge 与 gather collective 改变了非结合 BF16 addition 的顺序。总体上，parallel run 与 single-GPU reference 的距离，和两次 single-GPU run 之间的距离相当。

## 结论

Video generation 的 Diffusion Transformer serving 与 LLM serving 是不同的 scaling problem：单个 latency-bound request、没有 KV cache，并且每个 denoising step 都要在 70-150k token 上执行 full bidirectional attention。TensorRT-LLM 的 [`VisualGen`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/visual_gen/visual_gen.py#L176) runtime 在单个 PyTorch `DeviceMesh` 下统一 CFG Parallelism、Ulysses Parallelism、Attention2D Context Parallelism 和 Parallel VAE，并通过 `ParallelConfig` 暴露为 declarative option。CFG 先拆分两个 guidance stream；Ulysses 再对 sequence sharding，直到达到 attention head count 上限；Attention2D 将 DiT 继续扩展到完整 rack，并凭借 $O(N/\sqrt{P})$ collective 在 72 张 GPU 上保持接近 linear scaling；最后由 Parallel VAE 扩展成为 bottleneck 的 decode stage。

最终 DiT denoising step 获得接近理想的 scaling。Wan 2.2 T2V-A14B 使用 `CFG=2 × Ulysses=4 × Attention2D 3×3`，从单张 B200 扩展到完整 GB200 NVL72 时取得约 53× denoising speedup 和 41× end-to-end speedup；相同 recipe 无需修改即可用于 64B Cosmos3-Super，达到约 55× denoising speedup 和 33× end-to-end speedup。这说明 sequence-length sharding pattern 能跨不同 model size 与 sequence length 泛化。原本需要五分钟以上的视频，现在可在完整 GB200 NVL72 上约 9 秒完成。

## 选择高性能配置

GPU 按各 parallelism axis 的 scaling efficiency 依次分配。首先使用 **CFG** 拆分 guidance stream，获得接近 2× speedup；随后使用 **Ulysses** sharding sequence，直到受 attention head count 限制；剩余 GPU 分配给 **Attention2D**，并尽量保持 symmetric mesh。Ulysses 与 Attention2D 的比例需要 tuning，例如从 64 张扩展到 72 张 GPU 时，Ulysses degree 从 8 降到 4，Attention2D mesh 相应扩大。VAE decode 独立 tuning，只在成为 end-to-end bottleneck 后扩展，degree 4 或 8 通常效果最好。

## 局限与未来工作

- 在当前实现中，序列长度必须能被 Sequence Parallelism 大小整除。这将在未来扩展以支持任意输入维度，例如通过填充或其他方案。

未来方向：

1. **将 Attention2D dispatch/combine 融入 FA4。** 当前 row/column gather 与 `flash_attn_combine` reduction 是 attention kernel 外的独立 step，每个 attention block 都多一次 all-gather 与 memory copy。融合进 FA4 可移除 round trip，降低 per-layer Context Parallelism overhead。
2. **Overlap Attention2D communication 与 compute。** 当前 row/column gather 和 `flash_attn_combine` reduction 都是 blocking collective；未来可通过 pipeline 与 compute overlap。
3. **将 Attention2D 组合折叠成 reduce-scatter 。** 为了合并子组中的部分 attention 输出，Attention2D 今天执行`all-to-all`，然后执行本地 LSE 合并。相反，它可以表示为单个 `reduce-scatter`，并将 LSE 合并作为自定义 reduction 操作。
4. **将 VAE 与 DiT disaggregate。** VAE decode 当前覆盖在 denoiser rank 上，使两阶段共享同一 resource pool。可将其拆成独立 scaling pool，由 denoiser 逐 frame 把 latent stream 发送给专用 VAE service，使两边按各自 throughput target provisioning。
5. **针对异构 NVLink + InfiniBand cluster tuning。** 本文数据来自单个 GB200 NVL72 NVLink domain。NVL8 + cross-node IB topology 的 trade-off 不同：Async Ulysses 只能优化 CUDA IPC 可达的 NVLink peer，最佳 mesh order、Ulysses/CP split 与 CP backend 仍需专项 benchmark。
6. **扩展到 autoregressive video model。** 本文针对 multi-step diffusion；autoregressive model 使用带 KV cache 的 causal attention，cost profile 完全不同，需要重新设计 parallel strategy。
7. **探索 step-distilled model。** 每个 step 仍是相同的 dense prefill，因此 per-step DiT sharding 与最佳 mesh 不变；但 step 数减少后，VAE decode 和 text encoding 等 fixed tail 会主导 end-to-end latency，需要重新 tuning DiT 与 VAE 的 GPU allocation。
8. **组合 TP 与 Attention2D。** 当前 Tensor Parallelism 可与 sequence 和 CFG axis 组合，但尚未支持 Attention2D；实现后即可在同一 mesh 上同时 sharding weight 与 sequence。

## 参考资料

- VisualGen runtime：[`tensorrt_llm/_torch/visual_gen/`](https://github.com/NVIDIA/TensorRT-LLM/tree/main/tensorrt_llm/_torch/visual_gen)
  - Mesh：[`mapping.py`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/_torch/visual_gen/mapping.py)
  - parallel 包装器：[`attention_backend/parallel.py`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/_torch/visual_gen/attention_backend/parallel.py)
  - Pipeline base：[`pipeline.py`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/_torch/visual_gen/pipeline.py)
  - 配置模型：[`config.py`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/_torch/visual_gen/config.py)
  - Parallel VAE：[`modules/vae/parallel_vae_interface.py`](https://github.com/NVIDIA/TensorRT-LLM/blob/main/tensorrt_llm/_torch/visual_gen/modules/vae/parallel_vae_interface.py)
- 示例：
  - 离线脚本：[`examples/visual_gen/`](https://github.com/NVIDIA/TensorRT-LLM/tree/main/examples/visual_gen)
  - 共享 YAML 配置：[`examples/visual_gen/configs/`](https://github.com/NVIDIA/TensorRT-LLM/tree/main/examples/visual_gen/configs)
  - 服务与基准测试：[`examples/visual_gen/serve/`](https://github.com/NVIDIA/TensorRT-LLM/tree/main/examples/visual_gen/serve)
- 论文：
  - DeepSpeed Ulysses：[arXiv:2309.14509](https://arxiv.org/abs/2309.14509)
  - Attention2D：[arXiv:2503.15758](https://arxiv.org/abs/2503.15758)
  - Ring Attention：[arXiv:2310.01889](https://arxiv.org/abs/2310.01889)

## 致谢

TensorRT-LLM 在 GB200 NVL72 rack 上扩展 video generation，是多个工程团队密切协作的成果。感谢所有工程师以 collective expertise 推动 TensorRT-LLM video generation performance；希望本文分享的技术与经验能帮助开发者更充分地利用 NVIDIA GPU。
