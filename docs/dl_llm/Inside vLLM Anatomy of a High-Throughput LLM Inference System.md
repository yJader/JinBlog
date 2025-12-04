---
author: Aleksa Gordic
date: 2025-09-05 00:00:00 +0000
categories:
  - vLLM
  - Systems
tags:
  - LLM
  - Inference
  - Systems
title: Inside vLLM Anatomy of a High-Throughput LLM Inference System
createTime: 2025/10/18 21:45:21
permalink: /dl_llm/p6wie8rz/
---

# vLLM 深入研究：一个高吞吐量 LLM 推理系统的剖析

> [!NOTE]
> 最初发布于 [Aleksa Gordic 的网站](https://www.aleksagordic.com/blog/vllm "null")
>
> 引用自[Inside vLLM: Anatomy of a High-Throughput LLM Inference System | vLLM Blog](https://blog.vllm.ai/2025/09/05/anatomy-of-vllm.html)
> 我在AI的协助下进行了全文翻译

### 从 Paged Attention、Continuous Batching、Prefix Caching、Speculative Decoding 等到多 GPU、多节点大规模动态服务

在这篇文章中，我将逐步介绍构成现代高吞吐量 LLM 推理系统的所有核心系统组件和高级功能。我将特别详细分析 vLLM [1] 的工作原理。

这篇文章是一个系列的第一篇。它从宏观入手，然后层层深入细节（遵循倒金字塔方法），这样你可以在不陷入细枝末节的情况下，形成一个对整个系统准确的高层次心智模型。

后续的文章将深入探讨特定的子系统。

本文分为五个部分：

1. **LLM Engine & Engine Core**：vLLM 的基础知识（调度、Paged Attention、Continuous Batching 等）
2. **高级功能**：扩展核心引擎逻辑（Chunked Prefill、Prefix Caching、Guided & Speculative Decoding、Disaggregated P/D）
3. **扩展**：从单 GPU 到多 GPU 执行
4. **服务层**：分布式/并发 Web 服务架构
5. **基准测试和自动调优**：衡量延迟和吞吐量

> [!NOTE]
>
> - 分析基于 [commit 42172ad](https://github.com/vllm-project/vllm/tree/42172ad "null")（2025 年 8 月 9 日）。
> - 目标读者：对最先进的 LLM 引擎工作原理感到好奇的任何人，以及有兴趣为 vLLM、SGLang 等做出贡献的人。
> - 我将重点关注 [V1 引擎](https://docs.vllm.ai/en/latest/usage/v1_guide.html "null")。我也研究了 V0（现已[弃用](https://github.com/vllm-project/vllm/issues/18571 "null")），这对于理解项目的演变很有价值，许多概念仍然适用。
> - 关于 LLM Engine / Engine Core 的第一部分可能有点让人不知所措/枯燥——但博客的其余部分有大量的例子和图示。:)

## LLM Engine & Engine Core

LLM 引擎是 vLLM 的基本构建块。它本身就已经可以实现高吞吐量推理——但仅限于离线设置。你还不能通过网络向客户提供服务。

我们将使用以下离线推理代码片段作为我们的运行示例（改编自 [basic.py](https://github.com/vllm-project/vllm/blob/main/examples/offline_inference/basic/basic.py "null")）。

```python
from vllm import LLM, SamplingParams

prompts = [
    "Hello, my name is",
    "The president of the United States is",
]

sampling_params = SamplingParams(temperature=0.8, top_p=0.95)

def main():
    llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    outputs = llm.generate(prompts, sampling_params)

if __name__ == "__main__":
    main()
```

> [!NOTE]
> 环境变量：
>
> - VLLM_USE_V1=”1” # 我们使用的是 V1 引擎
> - VLLM_ENABLE_V1_MULTIPROCESSING=”0” # 我们在单个进程中运行

此配置为：

- 离线（没有 Web/分布式系统架构）
- 同步（所有执行都在单个阻塞进程中进行）
- 单 GPU（没有数据/模型/流水线/专家并行；DP/TP/PP/EP = 1）
- 使用标准 Transformer [2]（支持像 Jamba 这样的混合模型需要更复杂的混合 KV-cache 内存分配器）

从这里开始，我们将逐步构建一个在线、异步、多 GPU、多节点的推理系统——但仍然服务于一个标准的 Transformer。

在这个例子中，我们做了两件事：

1. 实例化一个引擎
2. 调用它的 `generate` 方法，根据给定的prompts进行采样

让我们从分析构造函数开始。

### LLM 引擎构造函数

引擎的主要组件是：

- **vLLM 配置**（包含配置模型、缓存、并行性等的所有选项）
- **处理器**（通过验证、分词和处理将原始输入转换为 `EngineCoreRequests`）
- **Engine Core 客户端**（在我们的运行示例中，我们使用的是 `InprocClient`，它基本上等同于 `EngineCore`；我们将逐步升级到 `DPLBAsyncMPClient`，它允许大规模服务）
- **输出处理器**（将原始的 `EngineCoreOutputs` 转换为用户看到的 `RequestOutput`）

> [!NOTE]
> 随着 V0 引擎被弃用，类名和细节可能会发生变化。我将强调核心思想而不是确切的签名。我会抽象掉一些但不是所有的细节。

Engine Core 本身由几个子组件组成：

- **Model Executor**（驱动模型的前向传播，我们目前处理的是 `UniProcExecutor`，它在单个 GPU 上有一个 `Worker` 进程）。我们将逐步升级到支持多个 GPU 的 `MultiProcExecutor`。
- **Structured Output Manager**（用于 Guided Decoding - 我们稍后会介绍）
- **Scheduler**（决定哪些请求进入下一个引擎步骤）- 它进一步包含：
  - 策略设置 - 可以是 **FCFS**（先到先得）或 **priority**（高优先级的请求先被服务）
  - `waiting` 和 `running` 队列
  - **KV Cache Manager** - Paged Attention [3] 的核心

KV-cache 管理器维护一个 `free_block_queue` - 一个可用的 KV-cache 块池（通常有几十万个，取决于 VRAM 大小和块大小）。在 Paged Attention 期间，这些块作为索引结构，将 token 映射到其计算出的 KV cache 块。

![图 1：本节描述的核心组件及其关系](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/engine_constructor.png)

> [!NOTE]对于一个标准的 Transformer 层（非 MLA [4]），块大小计算如下： 2 (key/value) *`block_size` (默认=16)* `num_kv_heads` *`head_size`* `dtype_num_bytes` (例如 bf16 为 2)

在 Model Executor 构建期间，会创建一个 `Worker` 对象，并执行三个关键过程。（稍后，使用 `MultiProcExecutor` 时，这些相同的过程会在不同 GPU 上的每个 worker 进程中独立运行。）

1. **初始化设备**：
    - 将 CUDA 设备（例如 "cuda:0"）分配给 worker 并检查模型数据类型是否受支持（例如 bf16）
    - 验证在给定的 `gpu_memory_utilization`（例如 0.8 -> 80% 的总 VRAM）下是否有足够的 VRAM
    - 设置分布式设置（DP / TP / PP / EP 等）
    - 实例化一个 `model_runner`（包含采样器、KV cache 和前向传播缓冲区，如 `input_ids`、`positions` 等）
    - 实例化一个 `InputBatch` 对象（包含 CPU 端的前向传播缓冲区、用于 KV-cache 索引的块表、采样元数据等）

2. **加载模型**：
    - 实例化模型架构
    - 加载模型权重
    - 调用 model.eval()（PyTorch 的推理模式）
    - 可选：在模型上调用 torch.compile()

3. **初始化 KV cache**
    - 获取每层的 KV-cache 规范。以前这总是 `FullAttentionSpec`（同构 Transformer），但随着混合模型（滑动窗口、像 Jamba 这样的 Transformer/SSM）的出现，它变得更加复杂（参见 Jenga [5]）
    - 运行一个虚拟/性能分析的前向传播，并获取 GPU 内存快照，以计算可用 VRAM 中可以容纳多少 KV cache 块
    - 分配、重塑并将 KV cache 张量绑定到注意力层
    - 准备注意力元数据（例如将后端设置为 FlashAttention），稍后在 fwd pass 期间由 kernel 消耗
    - 除非提供了 `--enforce-eager`，否则对于每个预热批次大小，进行一次**虚拟运行**并捕获 CUDA graphs。CUDA graphs 将整个 GPU 工作序列记录到一个 DAG 中。稍后在 fwd pass 期间，我们启动/重放预先准备好的 graphs，从而减少 kernel 启动开销，进而提高延迟。

我在这里抽象掉了许多底层细节——但这些是我现在要介绍的核心部分，因为我将在接下来的部分中反复引用它们。

现在我们已经初始化了引擎，让我们继续看 `generate` 函数。

### `generate` 函数

第一步是验证请求并将其输入引擎。对于每个prompt，我们：

1. 创建一个唯一的请求 ID 并捕获其到达时间
2. 调用一个输入预处理器，对prompts进行分词并返回一个包含 `prompt`、`prompt_token_ids` 和 `type`（文本、token、嵌入等）的字典
3. 将这些信息打包成一个 `EngineCoreRequest`，并添加优先级、采样参数和其他元数据
4. 将请求传递到 Engine Core，Engine Core 将其包装在一个 `Request` 对象中，并将其状态设置为 `WAITING`。然后将此请求添加到调度程序的 `waiting` 队列中（如果是 FCFS 则追加，如果是优先级则push到堆中）

此时，引擎已经接收了输入，可以开始执行。在同步引擎示例中，这些初始prompts是我们唯一要处理的——没有机制可以在运行中注入新的请求。相比之下，异步引擎支持这一点（也称为 **continuous batching** [6]）：在每个步骤之后，都会同时考虑新旧请求。

> [!NOTE]
> 因为前向传播将批次展平为单个序列，并且自定义 kernel 可以高效地处理它，所以即使在同步引擎中，continuous batching 也从根本上得到了支持。

接下来，只要有请求需要处理，引擎就会重复调用其 `step()` 函数。每个步骤有三个阶段：

1. **调度**：选择在此步骤中运行的请求（decode 和/或 (chunked) prefill）
2. **前向传播**：运行模型并采样 token
3. **后处理**：将采样到的 token ID 附加到每个 `Request` 中，去分词，并检查停止条件。如果一个请求完成了，就进行清理（例如将其 KV-cache 块返回到 `free_block_queue`）并提前返回输出

> [!NOTE]
> 停止条件是：
>
> - 请求超出了其长度限制（`max_model_length` 或其自身的 `max_tokens`）
> - 采样到的 token 是 EOS ID（除非启用了 `ignore_eos` -> 这在基准测试中很有用，当我们想要强制生成一定数量的输出 token 时）
> - 采样到的 token 与采样参数中指定的任何 `stop_token_ids` 匹配
> - 输出中存在停止字符串 - 我们将输出截断到第一个停止字符串出现的位置，并在引擎中中止该请求（注意 `stop_token_ids` 会出现在输出中，但停止字符串不会）。
>

![图 2：引擎循环](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/engine_loop.png)

> [!NOTE]
> 在流式模式下，我们会在生成 token 时发送中间 token，但我们现在先忽略这一点。

接下来，我们将更详细地研究调度。

### 调度器

推理引擎处理两种主要类型的工作负载：

1. **Prefill** 请求 — 对所有prompt token 进行一次前向传播。这些通常是**计算密集型**的（阈值取决于硬件和prompt长度）。最后，我们从最后一个 token 位置的概率分布中采样一个 token。
2. **Decode** 请求 — 仅对最新的一个 token 进行一次前向传播。所有早期的 KV 向量都已经被缓存。这些是**内存带宽密集型**的，因为我们仍然需要加载所有 LLM 权重（和 KV caches）才能计算一个 token。

> [!NOTE]
> 在[基准测试部分](#基准测试和自动调优-延迟vs吞吐量)，我们将分析所谓的 GPU 性能的 roofline 模型。这将更详细地探讨 prefill/decode 的性能概况。

V1 调度器可以在同一步骤中混合这两种类型的请求，这要归功于更智能的设计选择。相比之下，V0 引擎一次只能处理 prefill 或 decode。

调度器优先处理 decode 请求——即那些已经在 `running` 队列中的请求。对于每个这样的请求，它：

1. 计算要生成的新 token 的数量（由于 speculative decoding 和异步调度，不总是 1——稍后会详细介绍）。
2. 调用 KV-cache 管理器的 `allocate_slots` 函数（详见下文）。
3. 通过从第 1 步的 token 数量中减去来更新 token 预算。

之后，它处理来自 `waiting` 队列的 prefill 请求，它：

1. 检索已计算块的数量（如果禁用了 prefix caching，则返回 0——我们稍后会介绍）。
2. 调用 KV-cache 管理器的 `allocate_slots` 函数。
3. 从 waiting 队列中弹出请求并将其移动到 running 队列，将其状态设置为 `RUNNING`。
4. 更新 token 预算。

现在让我们看看 `allocate_slots` 做了什么，它：

1. **计算块数** — 确定必须分配多少个新的 KV-cache 块 (`n`)。每个块默认存储 16 个 token。例如，如果一个 prefill 请求有 17 个新 token，我们需要 `ceil(17/16) = 2` 个块。
2. **检查可用性** — 如果管理器池中没有足够的块，则**提前退出**。根据是 decode 还是 prefill 请求，引擎可能会尝试重新计算抢占（V0 中支持交换抢占），方法是驱逐低优先级请求（调用 `kv_cache_manager.free` 将 KV 块返回到块池），或者它可能会跳过调度并继续执行。
3. **分配块** — 通过 KV-cache 管理器的协调器，从块池（前面提到的 `free_block_queue` 双向链表）中获取前 `n` 个块。存储到 `req_to_blocks`，这是一个将每个 `request_id` 映射到其 KV-cache 块列表的字典。

![图 3：KV cache 块列表](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/kv_cache_blocks.png)

我们终于准备好进行一次前向传播了！

### 运行前向传播

我们调用 Model Executor 的 `execute_model`，它委托给 `Worker`，而 `Worker` 又委托给model runner。

以下是主要步骤：

1. **更新状态** — 从 `input_batch` 中修剪已完成的请求；更新与 fwd pass 相关的杂项元数据（例如，每个请求的 KV cache 块，将用于索引到 paged KV cache 内存中）。
2. **准备输入** — 将缓冲区从 CPU 复制到 GPU；计算位置；构建 `slot_mapping`（示例中会详细介绍）；构造注意力元数据。
3. **前向传播** — 使用自定义的 paged attn kernel 运行模型。所有序列都被展平并连接成一个长的“超级序列”。位置索引和注意力掩码确保每个序列只关注自己的 token，这使得 continuous batching 无需右填充。
4. **收集最后一个 token 的状态** — 提取每个序列最后一个位置的隐藏状态并计算 logits。
5. **采样** — 根据采样配置（贪婪、温度、top-p、top-k 等）从计算出的 logits 中采样 token。

前向传播步骤本身有两种执行模式：

1. **Eager 模式** — 启用 eager execution 时运行标准的 PyTorch 前向传播。
2. **“捕获”模式** — 当不强制执行 eager 时，执行/重放预先捕获的 CUDA Graph（请记住，我们在引擎构建期间的初始化 KV cache 过程中捕获了这些）。

这里有一个具体的例子，应该可以清楚地说明 continuous batching 和 paged attention：
![图 4：前向传播：continuous batching 和 paged attention](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/fwd_pass.png)
slot_mapping: 将逻辑的token id映射到实际的KVCache的物理槽位(slot)位置

## 高级功能 — 扩展核心引擎逻辑

掌握了基本的引擎流程后，我们现在可以看看高级功能。

我们已经讨论了抢占、Paged Attention 和 Continuous Batching。

接下来，我们将深入探讨：

1. Chunked Prefill
2. Prefix Caching
3. Guided Decoding（通过基于语法的有限状态机）
4. Speculative Decoding
5. Disaggregated P/D (prefill/decoding)

### Chunked Prefill

Chunked Prefill 是一种通过将其 prefill 步骤拆分成更小的块来处理长prompt的技术。如果没有它，我们可能会遇到单个非常长的请求独占一个引擎步骤，从而阻止其他 prefill 请求运行的情况。这会推迟所有其他请求并增加它们的延迟。

例如，让每个块包含 `n` (=8) 个 token，用小写字母标记，并用“-”分隔。一个长prompt `P` 可能看起来像 `x-y-z`，其中 `z` 是一个不完整的块（例如 2 个 token）。执行 `P` 的完整 prefill 将需要 ≥ 3 个引擎步骤（如果它在其中一个步骤中没有被调度执行，则可能 > 3），并且只有在最后一个 chunked prefill 步骤中我们才会采样一个新的 token。

这是同一个例子的图示：

![图 5：Chunked Prefill](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/chunked_pt1.png)

实现很简单：限制每个步骤的新 token 数量。如果请求的数量超过 `long_prefill_token_threshold`，则将其重置为该确切值。底层的索引逻辑（前面描述的）会处理剩下的事情。

在 vLLM V1 中，您可以通过将 `long_prefill_token_threshold` 设置为正整数来启用 chunked prefill。（技术上讲，无论如何都可能发生，如果prompt长度超过了 token 预算，我们会截断它并运行 chunked prefill。）

### Prefix Caching

为了解释 prefix caching 的工作原理，让我们对原始代码示例稍作调整：

```python
from vllm import LLM, SamplingParams

long_prefix = "<a piece of text that is encoded into more than block_size tokens>"

prompts = [
    "Hello, my name is",
    "The president of the United States is",
]

sampling_params = SamplingParams(temperature=0.8, top_p=0.95)

def main():
    llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")

    outputs = llm.generate(long_prefix + prompts[0], sampling_params)
    outputs = llm.generate(long_prefix + prompts[1], sampling_params)

if __name__ == "__main__":
    main()
```

Prefix caching 避免了重新计算多个prompt在开头共享的 token——因此得名 **prefix**。

关键部分是 `long_prefix`：它被定义为任何长于一个 KV-cache 块（默认为 16 个 token）的前缀。为了简化我们的示例，我们假设 `long_prefix` 的长度正好是 `n x block_size`（其中 `n ≥ 1`）。

> [!NOTE]
> 即它与块边界完美对齐——否则我们将不得不重新计算 `long_prefix_len % block_size` 个 token，因为我们无法缓存不完整的块。
>
> Q: 那如果没有对齐, 是选择空出block, 还是每次拼接后都重算呢?

如果没有 prefix caching，每次我们处理一个具有相同 `long_prefix` 的新请求时，我们都会重新计算所有 `n x block_size` 个 token。

有了 prefix caching，这些 token 只计算一次（它们的 KV 存储在 KV cache paged memory 中），然后被重用，所以只需要处理新的prompt token。这加快了 prefill 请求的速度（尽管对 decode 没有帮助）。

这在 vLLM 中是如何工作的？

在第一次 `generate` 调用期间，在调度阶段，在 `kv_cache_manager.get_computed_blocks` 内部，引擎调用 `hash_request_tokens`：

1. 此函数将 `long_prefix + prompts[0]` 拆分成 16 个 token 的块。

2. 对于每个完整的块，它计算一个哈希（使用内置哈希或 SHA-256，后者较慢但冲突较少）。该哈希结合了**前一个块的哈希**、**当前 token** 和可选的**元数据**。

> [!NOTE]
> 可选的元数据包括：
>
> - MM hash: **Multi-Model Hash 多模态Hash**, 组合图片和文本进行特征编码, 得到总体的Hash
> - LoRA ID: **Low-Rank Adapter**, 使用不同的低秩矩阵进行参数微调, 实现模型定制和任务迁移
> - cache salt: 注入到**第一个块**的哈希中，确保只有具有此缓存盐的请求才能重用块

3. 每个结果都存储为一个 `BlockHash` 对象，包含哈希及其 token ID。我们返回一个块哈希列表。

该列表存储在 `self.req_to_block_hashes[request_id]` 中。

接下来，引擎调用 `find_longest_cache_hit` 来检查这些block hash中是否有任何一个已经存在于 `cached_block_hash_to_block` 中。在此处的第一个请求上，没有找到命中。

![图 6：Prefix caching - 哈希函数](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/prefix_pt1.png)

然后我们调用 `allocate_slots`，它调用 `coordinator.cache_blocks`，将新的 `BlockHash` 条目与分配的 KV 块关联起来，并将它们记录在 `cached_block_hash_to_block` 中。

之后，前向传播将在 paged KV cache 内存中填充与我们上面分配的 KV cache 块相对应的 KV。

> [!NOTE]
> 经过许多引擎步骤后，它会分配更多的 KV cache 块，但这对于我们的示例来说无关紧要，因为前缀在 `long_prefix` 之后立即分叉了。

![图 7：Prefix caching - 在 paged memory 中填充 KV](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/prefix_pt2.png)

在第二次使用相同前缀的 `generate` 调用中，重复步骤 1-3，但现在 `find_longest_cache_hit` 为所有 `n` 个块找到匹配项（通过线性搜索）。引擎可以直接重用这些 KV 块。

![图 8：Prefix caching - 重用 KV](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/prefix_pt3.png)

如果原始请求仍然存在，这些块的引用计数将增加（例如增加到 2）。在这个例子中，第一个请求已经完成，所以这些块被释放回池中，它们的引用计数被重置为 0。因为我们能够从 `cached_block_hash_to_block` 中检索到它们，我们知道它们是有效的（KV cache 管理器的逻辑是这样设置的），所以我们只是再次将它们从 `free_block_queue` 中移除。

> [!NOTE] Advanced note:
> KV-cache 块只有在它们即将从 `free_block_queue`（从左侧弹出）重新分配时才会失效，并且我们发现该块仍然具有关联的哈希并且存在于 `cached_block_hash_to_block` 中。在那一刻，我们清除该块的哈希并将其条目从 `cached_block_hash_to_block` 中移除，确保它不能通过 prefix caching 重用（至少不能用于那个旧前缀）。

这就是 prefix caching 的要点：不要重新计算你已经见过的 prefixes——只需重用它们的 KV cache！

如果你理解了这个例子，你也就理解了 paged attention 的工作原理。

Prefix caching 默认启用。要禁用它：`enable_prefix_caching = False`。

### Guided Decoding (FSM)

Guided decoding 是一种技术，在每个 decoding 步骤中，logits 都受到基于语法的有限状态机的约束。**这确保了只有语法允许的 token 才能被采样。**

这是一个强大的设置：你可以强制执行从正则语法（Chomsky type-3，例如任意正则表达式模式）到上下文无关语法（type-2，涵盖大多数编程语言）的任何内容。

为了让这不那么抽象，让我们从最简单的例子开始，在我们早期的代码上构建：

```python
from vllm import LLM, SamplingParams
from vllm.sampling_params import GuidedDecodingParams

prompts = [
    "This sucks",
    "The weather is beautiful",
]

guided_decoding_params = GuidedDecodingParams(choice=["Positive", "Negative"])
sampling_params = SamplingParams(guided_decoding=guided_decoding_params)

def main():
    llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")

    outputs = llm.generate(prompts, sampling_params)

if __name__ == "__main__":
    main()
```

在我给出的玩具示例中（假设是字符级分词）：在 prefill 时，FSM 会屏蔽 logits，因此只有“P”或“N”是可行的。如果采样到“P”，FSM 会移动到“Positive”分支；下一步只允许“o”，依此类推。

![图 9：玩具示例 FSM](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/fsm.png)

这在 vLLM 中是如何工作的：

1. 在 LLM 引擎构建时，会创建一个 `StructuredOutputManager`；它可以访问 tokenizer 并维护一个 `_grammar_bitmask` 张量。
2. 添加请求时，其状态设置为 `WAITING_FOR_FSM`，`grammar_init` 选择后端编译器（例如，`xgrammar` [7]；注意后端是第三方代码）。
3. 此请求的语法是异步编译的。
4. 在调度期间，如果异步编译已完成，状态将切换到 `WAITING`，并将 `request_id` 添加到 `structured_output_request_ids`；否则将其放入 `skipped_waiting_requests` 以在下一个引擎步骤中重试。
5. 在调度循环之后（仍在调度内部），如果有 FSM 请求，`StructuredOutputManager` 会要求后端准备/更新 `_grammar_bitmask`。
6. 在前向传播产生 logits 之后，xgr_torch_compile 的函数将位掩码扩展到词汇表大小（使用 32 位整数时扩展比为 32x）并将不允许的 logits 屏蔽为 –∞。
7. 采样下一个 token 后，通过 `accept_tokens` 推进请求的 FSM。在 FSM 图上，我们视觉上移动到下一个状态。

第 6 步值得进一步说明。

如果 `vocab_size = 32`，`_grammar_bitmask` 是一个整数；其二进制表示编码了哪些 token 是允许的（“1”）与不允许的（“0”）。例如，“101…001”扩展为一个长度为 32 的数组 `[1, 0, 1, ..., 0, 0, 1]`；位置为 0 的 logits 被设置为 –∞。对于更大的词汇表，使用多个 32 位字并相应地扩展/连接。后端（例如，`xgrammar`）负责使用当前的 FSM 状态生成这些位模式。

> [!NOTE]
> 这里的大部分复杂性都隐藏在像 xgrammar 这样的第三方库中。

这是一个更简单的例子，词汇表大小为 8，使用 8 位整数（对于那些喜欢我的图示的人）：

![图 10：玩具示例](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/fsm2.png)

您可以在 vLLM 中通过传入所需的 `guided_decoding` 配置来启用此功能。

### Speculative Decoding

在自回归生成中，每个新 token 都需要对大型 LM 进行一次前向传播。这很昂贵——每一步都要重新加载和应用所有模型权重，只为了计算一个 token！（假设 batch size == 1，通常是 `B`）

Speculative decoding(投机解码) [8] 通过引入一个较小的 draft LM 来加速这一过程。draft LM 可以廉价地提出 *(未来连续的)* `k` 个 token。但我们最终不想从较小的模型中采样——它只是用来猜测候选的延续。大型模型仍然决定什么是有效的。

以下是步骤：

1. **Draft**：在当前上下文中运行小型模型并提出 `k` 个 token
2. **Verify**：在上下文 + `k` 个 draft token 上运行一次大型模型。这将为这 `k` 个位置加上一个额外的位置产生概率（所以我们得到 `k+1` 个候选）
3. **Accept/reject**：从左到右遍历 `k` 个 draft token：
    - 如果大型模型对 draft token 的概率 ≥ draft 模型的概率，则接受它
    - 否则，以 `p_large(token)/p_draft(token)` 的概率接受它
    - 在第一次拒绝时停止，或接受所有 `k` 个 draft token
        - 如果所有 `k` 个 draft token 都被接受，也从大型模型中“免费”采样额外的第 `(k+1)` 个 token（我们已经计算了该分布）
        - 如果发生拒绝，则在该位置创建一个新的重新平衡的分布（`p_large - p_draft`，将最小值钳位在 0，归一化以使总和为 1）并从中采样最后一个 token
        - 注:
         - 发生reject意味着Draft LM已经占据了概率质量, 需要在剩余的概率空间(`p_large - p_draft`)中采样
         - 每个p都是vocab size维的概率向量

**为什么这行得通**：虽然我们使用小型模型来提出候选，但接受/拒绝规则保证了序列在期望上与我们逐个 token 从大型模型中采样完全相同。这意味着 speculative decoding 在统计上等同于标准的自回归 decoding——但可能快得多，因为一次大型模型的前向传播最多可以产生 `k+1` 个 token。

> [!NOTE]
> 我建议查看 [gpt-fast](https://github.com/meta-pytorch/gpt-fast "null") 以获取简单的实现，以及[原始论文](https://arxiv.org/abs/2302.01318 "null")以了解数学细节和与从完整模型采样等效的证明。

vLLM V1 不支持 LLM draft model 方法，而是实现了更快但不太准确的提议方案：n-gram、EAGLE [9] 和 Medusa [10]。

每个方案的一句话总结：

- **n-gram**：取最后 `prompt_lookup_max` 个 token；在序列中找到一个先前的匹配项；如果找到，则提出该匹配项后面的 `k` 个 token；否则减少窗口并重试直到 `prompt_lookup_min`

> [!NOTE]
> 当前的实现返回第一个匹配项后的 `k` 个 token。引入一个近因偏见并反转搜索方向似乎更自然？（即最后一个匹配项）

- **Eagle**：对大型 LM 进行“模型手术”——保留 embeddings 和 LM head，用一个轻量级的 MLP 替换 Transformer 堆栈；将其微调为一个廉价的 draft
- **Medusa**：在大型模型的顶部（LM head 之前的 embeddings）训练辅助线性头，以并行预测接下来的 `k` 个 token；使用这些头比运行一个单独的小型 LM 更有效地提出 token

以下是如何在 vLLM 中使用 `ngram` 作为 draft 方法来调用 speculative decoding：

```python
from vllm import LLM, SamplingParams

prompts = [
    "Hello, my name is",
    "The president of the United States is",
]

sampling_params = SamplingParams(temperature=0.8, top_p=0.95)

speculative_config={
    "method": "ngram",
    "prompt_lookup_max": 5,
    "prompt_lookup_min": 3,
    "num_speculative_tokens": 3,
}

def main():
    llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", speculative_config=speculative_config)

    outputs = llm.generate(prompts, sampling_params)

if __name__ == "__main__":
    main()
```

这在 vLLM 中是如何工作的？

**设置（在引擎构建期间）：**

1. 初始化设备：创建一个 `drafter`（draft model，例如，`NgramProposer`）和一个 `rejection_sampler`（其部分是用 Triton 编写的）。
2. 加载模型：加载 draft model 权重（对于 n-gram 是无操作）。

**之后在 `generate` 函数中**（假设我们得到一个全新的请求）：

1. 使用大型模型运行常规的 prefill 步骤。
2. 在前向传播和标准采样之后，调用 `propose_draft_token_ids(k)` 从 draft model 中采样 `k` 个 draft token。
3. 将这些存储在 `request.spec_token_ids` 中（更新请求元数据）。
4. 在下一个引擎步骤中，当请求在 running 队列中时，将 `len(request.spec_token_ids)` 添加到“新 token”计数中，以便 `allocate_slots` 为 fwd pass 保留足够的 KV 块。
5. 将 `spec_token_ids` 复制到 `input_batch.token_ids_cpu` 中以形成（上下文 + draft）token。
6. 通过 `_calc_spec_decode_metadata` 计算元数据（这将从 `input_batch.token_ids_cpu` 复制 token，准备 logits 等），然后在 draft token 上运行大型模型的前向传播。
7. 不从 logits 进行常规采样，而是使用 `rejection_sampler` 从左到右接受/拒绝并产生 `output_token_ids`。
8. 重复步骤 2-7 直到满足停止条件。

内化这一点的最佳方法是启动调试器并单步执行代码库，但希望本节能让您对此有所了解。这个也是：

![图 11：Speculative Decoding](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/specdec_pt1.png)

### Disaggregated P/D

我之前已经暗示了 disaggregated P/D (prefill/decode) 背后的动机。

Prefill 和 decode 具有非常不同的性能概况（计算密集型 vs. 内存带宽密集型），因此将它们的执行分开是一种明智的设计。它对延迟提供了更严格的控制——包括 `TFTT`（首个 token 时间）和 `ITL`（token 间延迟）——更多内容将在[基准测试](#基准测试和自动调优-延迟vs吞吐量)部分讨论。

在实践中，我们运行 `N` 个 vLLM prefill 实例和 `M` 个 vLLM decode 实例，并根据实时请求组合自动扩展它们。Prefill worker 将 KV 写入专用的 KV-cache 服务；decode worker 从中读取。这将长的、突发性的 prefill 与稳定的、对延迟敏感的 decode 隔离开来。

这在 vLLM 中是如何工作的？

为清楚起见，下面的示例依赖于 `SharedStorageConnector`，这是一个用于说明机制的调试连接器实现。

> [!NOTE]
> Connector 是 vLLM 用于处理实例之间 KV 交换的抽象。Connector 接口尚不稳定，计划在近期进行一些改进，其中将涉及一些更改，其中一些可能是破坏性的。

我们启动 2 个 vLLM 实例（GPU 0 用于 prefill，GPU 1 用于 decode），然后在它们之间传输 KV cache：

```python
import os
import time
from multiprocessing import Event, Process
import multiprocessing as mp

from vllm import LLM, SamplingParams
from vllm.config import KVTransferConfig

prompts = [
    "Hello, my name is",
    "The president of the United States is",
]

def run_prefill(prefill_done):
  os.environ["CUDA_VISIBLE_DEVICES"] = "0"

  sampling_params = SamplingParams(temperature=0, top_p=0.95, max_tokens=1)

  ktc=KVTransferConfig(
      kv_connector="SharedStorageConnector",
      kv_role="kv_both",
      kv_connector_extra_config={"shared_storage_path": "local_storage"},
  )

  llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", kv_transfer_config=ktc)
  llm.generate(prompts, sampling_params)

  prefill_done.set()  # notify decode instance that KV cache is ready

  # To keep the prefill node running in case the decode node is not done;
  # otherwise, the script might exit prematurely, causing incomplete decoding.
  try:
      while True:
          time.sleep(1)
  except KeyboardInterrupt:
      print("Script stopped by user.")

def run_decode(prefill_done):
  os.environ["CUDA_VISIBLE_DEVICES"] = "1"

  sampling_params = SamplingParams(temperature=0, top_p=0.95)

  ktc=KVTransferConfig(
      kv_connector="SharedStorageConnector",
      kv_role="kv_both",
      kv_connector_extra_config={"shared_storage_path": "local_storage"},
  )

  llm = LLM(model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", kv_transfer_config=ktc)

  prefill_done.wait()  # block waiting for KV cache from prefill instance

  # Internally it'll first fetch KV cache before starting the decoding loop
  outputs = llm.generate(prompts, sampling_params)

if __name__ == "__main__":
  prefill_done = Event()
  prefill_process = Process(target=run_prefill, args=(prefill_done,))
  decode_process = Process(target=run_decode, args=(prefill_done,))

  prefill_process.start()
  decode_process.start()

  decode_process.join()
  prefill_process.terminate()
```

> [!NOTE]
> 我也尝试过 `LMCache` [11]，它是最快的生产级的连接器（使用 NVIDIA 的 NIXL 作为后端），但它仍处于前沿，我遇到了一些错误。由于其大部分复杂性存在于外部仓库中，因此 `SharedStorageConnector` 是一个更好的解释选择。

以下是 vLLM 中的步骤：

1. **实例化** — 在引擎构建期间，在两个地方创建连接器：
    - 在 worker 的 init device 过程中（在 init worker 分布式环境函数下），角色为“worker”。
    - 在调度器构造函数中，角色为“scheduler”。

2. **缓存查找** — 当调度器处理来自 `waiting` 队列的 prefill 请求时（在本地 prefix-cache 检查之后），它会调用连接器的 `get_num_new_matched_tokens`。这会在 KV-cache 服务器中检查外部缓存的 token。Prefill 在这里总是看到 0；decode 可能会有缓存命中。在调用 `allocate_slots` 之前，将结果添加到本地计数中。

3. **状态更新** — 调度器然后调用 `connector.update_state_after_alloc`，它记录了有缓存的请求（对 prefill 是无操作）。

4. **构建元数据对象** — 在调度结束时，调度器调用 `meta = connector.build_connector_meta`：
    - Prefill 添加所有 `is_store=True` 的请求（以上传 KV）。
    - Decode 添加 `is_store=False` 的请求（以获取 KV）。

5. **上下文管理器** — 在前向传播之前，引擎进入一个 KV-connector 上下文管理器：
    - 进入时：调用 `kv_connector.start_load_kv`。对于 decode，这将从外部服务器加载 KV 并将其注入到 paged memory 中。对于 prefill，这是一个无操作。
    - 退出时：调用 `kv_connector.wait_for_save`。对于 prefill，这将阻塞直到 KV 上传到外部服务器。对于 decode，这是一个无操作。

这是一个图示示例：

![图 12：disaggregated P/D](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/pd.png)

> [!NOTE] **附加说明：**
>
> - 对于 `SharedStorageConnector`，“外部服务器”只是一个本地文件系统。
> - 根据配置，KV 传输也可以逐层进行（在每个注意力层之前/之后）。
> - Decode 只在其请求的第一步加载一次外部 KV；之后它在本地计算/存储。
>

## 从 UniprocExecutor 到 MultiProcExecutor

掌握了核心技术后，我们现在可以讨论扩展了。

假设您的模型权重不再适合单个 GPU 的 VRAM。

第一个选项是使用 tensor parallelism（例如，`TP=8`）将模型分片到同一节点上的多个 GPU。如果模型仍然不适合，下一步是跨节点的 pipeline parallelism。

> [!NOTE] **注意：**
>
> - 节点内带宽明显高于节点间带宽，这就是为什么 tensor parallelism (TP) 通常优于 pipeline parallelism (PP)。（PP 传输的数据比 TP 少也是事实。）
> - 我没有涵盖 expert parallelism (EP)，因为我们专注于标准的 Transformer 而不是 MoE，也没有涵盖 sequence parallelism，因为 TP 和 PP 在实践中是最常用的。

在这个阶段，我们需要多个 GPU 进程（worker）和一个协调它们的编排层。这正是 `MultiProcExecutor` 所提供的。

![图 13：TP=8 设置中的 MultiProcExecutor（驱动 worker 为 rank 0）](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/multiprocexecutor.png)

这在 vLLM 中是如何工作的：

1. `MultiProcExecutor` 初始化一个 `rpc_broadcast_mq` 消息队列（在底层使用共享内存实现）。
2. 构造函数遍历 `world_size`（例如 `TP=8 ⇒ world_size=8`）并通过 `WorkerProc.make_worker_process` 为每个 rank 派生一个守护进程。

- **rank**: 分布式进程组中, 每个进程的唯一编号

3. 对于每个 worker，父进程首先创建一个读写管道。
4. 新进程运行 `WorkerProc.worker_main`，它实例化一个 worker（经历与 `UniprocExecutor` 中相同的“初始化设备”、“加载模型”等过程）。
5. 每个 worker 确定它是否是驱动程序（TP 组中的 rank 0）或普通 worker。每个 worker 设置两个队列：
    - `rpc_broadcast_mq`（与父进程共享）用于接收工作。
    - `worker_response_mq` 用于发回响应。
6. 在初始化期间，每个子进程通过管道将其 `worker_response_mq` 句柄发送给父进程。一旦全部收到，父进程就会解除阻塞——这完成了协调。
7. Worker 然后进入一个忙碌循环，在 `rpc_broadcast_mq.dequeue` 上阻塞。当一个work item到达时，它们执行它（就像在 `UniprocExecutor` 中一样，但现在使用 TP/PP 特定的分区工作）。结果通过 `worker_response_mq.enqueue` 发回。

- 每个`rpc_broadcast_mq`的work item都被

8. 在运行时，当一个请求到达时，`MultiProcExecutor` 将其排入所有子 worker 的 `rpc_broadcast_mq`（非阻塞）。然后它在指定的输出 rank 的 `worker_response_mq.dequeue` 上等待以收集最终结果。

从引擎的角度来看，没有任何改变——所有这些多进程复杂性都通过调用 Model Executor 的 `execute_model` 抽象掉了。

- 在 `UniProcExecutor` 的情况下：execute_model 直接导致在 worker 上调用 execute_model
- 在 `MultiProcExecutor` 的情况下：execute_model 间接导致通过 `rpc_broadcast_mq` 在每个 worker 上调用 execute_model

此时，我们可以使用相同的引擎接口运行资源允许的任何大小的模型。

下一步是横向扩展：启用 data parallelism (`DP > 1`)，跨节点复制模型，添加一个轻量级的 DP 协调层，在副本之间引入负载均衡，并在前面放置一个或多个 API 服务器来处理传入流量。

## 分布式系统服务 vLLM

> [!IMPORTANT] 记录:
> 这一段在没有上手代码的情况下有点难理解, 未来考虑重新阅读

设置服务基础设施有很多方法，但为了保持具体，这里有一个例子：假设我们有两个 H100 节点，并希望在它们上面运行四个 vLLM 引擎。

如果模型需要 `TP=4`，我们可以这样配置节点。

![图 14：具有 2 个 8xH100 节点的服务器配置（1 个无头，1 个 api 服务器）](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/server_setup.png)

在第一个节点上，以无头模式运行引擎（无 API 服务器），并使用以下参数：

```bash
vllm serve <model-name> \
  --tensor-parallel-size 4 \
  --data-parallel-size 4 \
  --data-parallel-size-local 2 \
  --data-parallel-start-rank 0 \
  --data-parallel-address <master-ip> \
  --data-parallel-rpc-port 13345 \
  --headless
```

并在另一个节点上运行相同的命令，但稍作调整：

- 无 `--headless`
- 修改 DP 起始 rank

```bash
vllm serve <model-name> \
  --tensor-parallel-size 4 \
  --data-parallel-size 4 \
  --data-parallel-size-local 2 \
  --data-parallel-start-rank 2 \
  --data-parallel-address <master-ip> \
  --data-parallel-rpc-port 13345
```

> [!NOTE]
> 这假设网络已配置，以便所有节点都可以访问指定的 IP 和端口。

这在 VLLM 中是如何工作的？

### 在无头服务器节点上

在无头节点上，一个 `CoreEngineProcManager` 启动 2 个进程（根据 `--data-parallel-size-local`），每个进程运行 `EngineCoreProc.run_engine_core`。这些函数中的每一个都创建一个 `DPEngineCoreProc`（引擎核心），然后进入其忙碌循环。

`DPEngineCoreProc` 初始化其父 `EngineCoreProc`（`EngineCore` 的子类），它：

1. 创建一个 `input_queue` 和 `output_queue` (`queue.Queue`)。
2. 使用 `DEALER` ZMQ 套接字（异步消息库）与另一节点上的前端进行初始握手，并接收协调地址信息。
3. 初始化 DP 组（例如使用 NCCL 后端）。
4. 使用 `MultiProcExecutor` (`TP=4` on 4 GPUs，如前所述）初始化 `EngineCore`。
5. 创建一个 `ready_event` (`threading.Event`)。
6. 启动一个运行 `process_input_sockets(…, ready_event)` 的输入守护线程 (`threading.Thread`)。类似地启动一个输出线程。
7. 仍在主线程中，等待 `ready_event`，直到跨越 2 个节点的所有 4 个进程中的所有输入线程都完成了协调握手，最终执行 `ready_event.set()`。
8. 一旦解除阻塞，就向前端发送一个“就绪”消息，其中包含元数据（例如，paged KV cache 内存中可用的 `num_gpu_blocks`）。
9. 然后，主、输入和输出线程进入各自的忙碌循环。

TL;DR: 我们最终得到 4 个子进程（每个 DP 副本一个），每个进程运行一个主、输入和输出线程。它们与 DP 协调器和前端完成协调握手，然后每个进程的三个线程都在稳态忙碌循环中运行。

![图 15：具有 4 个 DP 副本运行 4 个 DPEngineCoreProc 的分布式系统](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/dpenginecoreproc.png)

**当前稳态**：

- **输入线程** — 在输入套接字上阻塞，直到从 API 服务器路由一个请求；收到后，它解码有效负载，通过 `input_queue.put_nowait(...)` 将一个工作项排队，然后返回到在套接字上阻塞。
- **主线程** — 在 `input_queue.get(...)` 上唤醒，将请求馈送到引擎；`MultiProcExecutor` 运行前向传播并将结果排队到 `output_queue`。
- **输出线程** — 在 `output_queue.get(...)` 上唤醒，将结果发回 API 服务器，然后恢复阻塞。

**附加机制**：

- **DP wave counter** — 系统跟踪“wave”；当所有引擎都变为空闲时，它们会静止下来，当新工作到达时，计数器会增加（对协调/指标有用）。
- **控制消息** — API 服务器可以发送的不仅仅是推理请求（例如，中止和实用程序/控制 RPC）。
- **用于lockstep的虚拟步骤** — 如果任何 DP 副本有工作，所有副本都执行一个前向步骤；没有请求的副本执行一个虚拟步骤以参与所需的同步点（避免阻塞活动副本）。

> [!NOTE]
> Lockstep说明：这实际上只对 MoE 模型是必需的，其中 expert 层形成一个 EP 或 TP 组，而 attention 层仍然是 DP。目前总是与 DP 一起完成——这只是因为“内置”非 MoE DP 的用途有限，因为您可以只运行多个独立的 vLLM，并以正常方式在它们之间进行负载均衡。

现在是第二部分，API 服务器节点上发生了什么？

### 在 API 服务器节点上

我们实例化一个 `AsyncLLM` 对象（LLM 引擎的 asyncio 包装器）。在内部，这会创建一个 `DPLBAsyncMPClient`（data-parallel、load-balancing、asynchronous、multiprocessing client）。

在 `MPClient` 的父类中，`launch_core_engines` 函数运行并：

1. 创建用于启动握手的 ZMQ 地址（如在无头节点上所见）。
2. 派生一个 `DPCoordinator` 进程。
3. 创建一个 `CoreEngineProcManager`（与无头节点上相同）。

在 `AsyncMPClient` (`MPClient` 的子类) 中，我们：

1. 创建一个 `outputs_queue` (`asyncio.Queue`)。
2. 我们创建一个 asyncio 任务 `process_outputs_socket`，它（通过输出套接字）与所有 4 个 `DPEngineCoreProc` 的输出线程通信，并写入 `outputs_queue`。
3. 随后，`AsyncLLM` 的另一个 asyncio 任务 `output_handler` 从此队列中读取，并最终将信息发送到 `create_completion` 函数。

在 `DPAsyncMPClient` 中，我们创建一个 asyncio 任务 `run_engine_stats_update_task`，它与 DP 协调器通信。

DP 协调器在前端（API 服务器）和后端（引擎核心）之间进行协调。它：

- 定期向前端的 `run_engine_stats_update_task` 发送负载均衡信息（队列大小、等待/运行中的请求）。
- 通过动态更改引擎数量来处理来自前端的 `SCALE_ELASTIC_EP` 命令（仅适用于 Ray 后端）。
- 向后端发送 `START_DP_WAVE` 事件（由前端触发）并报告 wave-state 更新。

总而言之，前端 (`AsyncLLM`) 运行多个 asyncio 任务（请记住：并发，非并行）：

- 一类任务通过 `generate` 路径处理输入请求（每个新的客户端请求都会派生一个新的 asyncio 任务）。
- 两个任务（`process_outputs_socket`、`output_handler`）处理来自底层引擎的输出消息。
- 一个任务（`run_engine_stats_update_task`）维护与 DP 协调器的通信：发送 wave 触发器、轮询 LB 状态以及处理动态扩展请求。

最后，主服务器进程创建一个 FastAPI 应用程序并挂载诸如 `OpenAIServingCompletion` 和 `OpenAIServingChat` 之类的端点，这些端点公开 `/completion`、`/chat/completion` 等。然后通过 Uvicorn 提供堆栈服务。

那么，把所有东西放在一起，这就是完整的请求生命周期！

您从终端发送：

```bash
curl -X POST http://localhost:8000/v1/completions -H "Content-Type: application/json" -d '{
  "model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  "prompt": "The capital of France is",
  "max_tokens": 50,
  "temperature": 0.7
}'
```

接下来会发生什么：

1. 请求到达 API 服务器上 `OpenAIServingCompletion` 的 `create_completion` 路由。
2. 该函数异步地对prompt进行分词，并准备元数据（请求 ID、采样参数、时间戳等）。
3. 然后它调用 `AsyncLLM.generate`，其流程与同步引擎相同，最终调用 `DPAsyncMPClient.add_request_async`。
4. 这反过来又调用 `get_core_engine_for_request`，它根据 DP 协调器的状态在引擎之间进行负载均衡（选择得分最低/负载最低的那个：`score = len(waiting) * 4 + len(running)`）。
5. `ADD` 请求被发送到所选引擎的 `input_socket`。
6. 在该引擎处：
    - 输入线程 — 解除阻塞，从输入套接字解码数据，并将一个工作项放入主线程的 `input_queue` 中。
    - 主线程 — 在 `input_queue` 上解除阻塞，将请求添加到引擎，并重复调用 `engine_core.step()`，将中间结果排队到 `output_queue`，直到满足停止条件。
    - 输出线程 — 在 `output_queue` 上解除阻塞，并通过输出套接字发回结果。

> [!NOTE]
> 提醒：`step()` 调用调度器、Model Executor（它本身可以是 `MultiProcExecutor`！）等。我们已经看到过这个了！

7. 这些结果触发了 `AsyncLLM` 输出 asyncio 任务（`process_outputs_socket` 和 `output_handler`），这些任务将 token 传播回 FastAPI 的 `create_completion` 路由。
8. FastAPI 附加元数据（完成原因、logprobs、使用信息等）并通过 Uvicorn 向您的终端返回一个 `JSONResponse`！

就这样，您的补全回来了——整个分布式机制隐藏在一个简单的 `curl` 命令后面！:) 太有趣了！！！

> **附加说明：**
>
> - 当添加更多 API 服务器时，负载均衡在 OS/套接字级别处理。从应用程序的角度来看，没有重大变化——复杂性是隐藏的。
> - 使用 Ray 作为 DP 后端，您可以公开一个 URL 端点（`/scale_elastic_ep`），该端点可以自动扩展引擎副本的数量。

## 基准测试和自动调优-延迟vs吞吐量

到目前为止，我们一直在分析“气体颗粒”——请求如何在引擎/系统中流动的内部原理。现在是时候放大并从整体上看待系统，并问：我们如何衡量一个推理系统的性能？

在最高层次上，有两个相互竞争的指标：

1. **延迟** — 从提交请求到返回 token 的时间
2. **吞吐量** — 系统每秒可以生成/处理的 token/请求数

**延迟**对于交互式应用程序最重要，用户在这些应用程序中等待响应。

**吞吐量**在离线工作负载中很重要，例如用于预/后训练运行的合成数据生成、数据清理/处理，以及通常——任何类型的离线批处理推理作业。

在解释为什么延迟和吞吐量相互竞争之前，让我们定义一些常见的推理指标：

| 指标                      | 定义                                                                     |
| ----------------------- | ---------------------------------------------------------------------- |
| `TTFT` (首个 token 时间)    | 从提交请求到收到第一个输出 token 的时间                                                |
| `ITL` (token 间延迟)       | 两个连续 token 之间的时间（例如，从 token i-1 到 token i）                             |
| `TPOT` (每个输出 token 的时间) | 请求中所有输出 token 的**平均 ITL**                                              |
| `Latency / E2E` (端到端延迟) | 处理请求的总时间，即 TTFT + 所有 ITL 的总和，或者等效地，提交请求和接收最后一个输出 token 之间的时间           |
| `Throughput`            | 每秒处理的总 token 数（输入、输出或两者），或者每秒请求数                                       |
| `Goodput`               | 满足服务级别目标 (SLO) 的吞吐量，例如最大 TTFT、TPOT 或 e2e 延迟。例如，只计算满足这些 SLO 的请求中的 token |

![图 16：ttft, itl, e2e 延迟](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/latency_diagram.png)

这是一个解释这两个指标竞争性质的简化模型。

> **假设：** 权重 I/O 而不是 KV cache I/O 占主导地位；即我们处理的是短序列。

当观察批处理大小 `B` 如何影响单个 decode 步骤时，这种权衡变得清晰。当 `B ↓` 趋向于 1 时，ITL 下降：每一步的工作量减少，token 不会与其他 token “竞争”。当 `B ↑` 趋向于无穷大时，ITL 上升，因为我们每一步做更多的 FLOPs——但吞吐量提高了（直到我们达到峰值性能），因为权重 I/O 在更多的 token 上被摊销了。

一个 roofline 模型有助于理解这一点：在饱和批次 `B_sat` 以下，步骤时间由 HBM 带宽主导（逐层将权重流式传输到片上内存），因此步骤延迟几乎是平坦的——计算 1 个 vs 10 个 token 可能需要相似的时间。超过 `B_sat`，kernel 变得受计算限制，步骤时间大致随 `B` 增长；每个额外的 token 都会增加 ITL。

![图 17：roofline 性能模型](Inside%20vLLM%20Anatomy%20of%20a%20High-Throughput%20LLM%20Inference%20System.assets/roofline.png)

> **注意：** 为了更严谨地处理，我们必须考虑 kernel 自动调优：随着 `B` 的增长，运行时可能会切换到对该形状更有效的 kernel，从而改变实现的性能 `P_kernel`。步骤延迟为 `t = FLOPs_step / P_kernel`，其中 `FLOPs_step` 是该步骤中的工作量。您可以看到，当 `P_kernel` 达到 `P_peak` 时，每一步更多的计算将直接导致延迟增加。

### 如何在 vLLM 中进行基准测试

vLLM 提供了一个 `vllm bench {serve,latency,throughput}` CLI，它包装了 vllm / benchmarks / {server,latency,throughput}.py。

以下是这些脚本的作用：

- **latency** — 使用短输入（默认为 32 个 token）并以小批量（默认为 8）采样 128 个输出 token。它运行几次迭代并报告该批次的 e2e 延迟。
- **throughput** — 一次性提交一组固定的prompt（默认：1000 个 ShareGPT 样本）（也称为 `QPS=Inf` 模式），并报告整个运行过程中的输入/输出/总 token 数和每秒请求数。
- **serve** — 启动一个 vLLM 服务器，并通过从泊松（或更一般的，伽马）分布中采样请求的到达间隔时间来模拟真实世界的工作负载。它在一个时间窗口内发送请求，测量我们讨论过的所有指标，并且可以选择性地强制执行服务器端最大并发数（通过一个信号量，例如将服务器限制为 64 个并发请求）。

以下是如何运行延迟脚本的示例：

```bash
vllm bench latency \
  --model <model-name> \
  --input-tokens 32 \
  --output-tokens 128 \
  --batch-size 8
```

> [!NOTE]
> CI 中使用的基准测试配置位于 `.buildkite/nightly-benchmarks/tests` 下。

还有一个自动调优脚本，它驱动 serve 基准测试来找到满足目标 SLO（例如，“在保持 p99 e2e < 500 ms 的同时最大化吞吐量”）的参数设置，并返回一个建议的配置。

## 结语

我们从基本的引擎核心 (`UniprocExecutor`) 开始，添加了像 speculative decoding 和 prefix caching 这样的高级功能，扩展到 `MultiProcExecutor` (具有 `TP/PP > 1`)，最后横向扩展，将所有东西包装在异步引擎和分布式服务堆栈中——最后讨论了如何衡量系统性能。

vLLM 还包括我跳过的专门处理。例如：

- **多样化的硬件后端**：TPU、AWS Neuron (Trainium/Inferentia) 等。
- **架构/技术**：`MLA`、`MoE`、encoder-decoder (例如 Whisper)、pooling/embedding 模型、`EPLB`、`m-RoPE`、`LoRA`、`ALiBi`、无注意力变体、滑动窗口注意力、多模态 LM 和状态空间模型 (例如 Mamba/Mamba-2, Jamba)
- **TP/PP/SP**
- **混合 KV-cache 逻辑** (Jenga)，更复杂的采样方法如 beam sampling 等
- **实验性**：异步调度

好处是，这些中的大多数都与上面描述的主流程正交——你几乎可以将它们视为“插件”（当然，在实践中存在一些耦合）。

我喜欢理解系统。话虽如此，在这个高度上，分辨率肯定会受到影响。在接下来的文章中，我将放大到特定的子系统并深入探讨细节。

> **联系我：** 如果您在帖子中发现任何错误，请私信我 - 欢迎在 [X](https://x.com/gordic_aleksa "null") 或 [LinkedIn](https://www.linkedin.com/in/aleksagordic/ "null") 上给我留言，或通过[匿名反馈](https://docs.google.com/forms/d/1z1fEirrN2xtGxAsJvptpM7yV4ByT5SF25S-XiMPrXNA "null")留言。

### 致谢

非常感谢 [Hyperstack](https://www.hyperstack.cloud/ "null") 在过去一年中为我的实验提供了 H100！

感谢 [Nick Hill](https://www.linkedin.com/in/nickhillprofile/ "null") (vLLM 核心贡献者, RedHat), [Kaichao You](https://github.com/youkaichao "null") (vLLM 核心贡献者), [Mark Saroufim](https://x.com/marksaroufim "null") (PyTorch), [Kyle Krannen](https://www.linkedin.com/in/kyle-kranen/ "null") (NVIDIA, Dynamo), 和 [Ashish Vaswani](https://www.linkedin.com/in/ashish-vaswani-99892181/ "null") 阅读了这篇博文的预发布版本并提供了反馈！

### 参考文献

1. vLLM [https://github.com/vllm-project/vllm](https://github.com/vllm-project/vllm "null")
2. “Attention Is All You Need” [https://arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762 "null")
3. “Efficient Memory Management for Large Language Model Serving with PagedAttention” [https://arxiv.org/abs/2309.06180](https://arxiv.org/abs/2309.06180 "null")
4. “DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model” [https://arxiv.org/abs/2405.04434](https://arxiv.org/abs/2405.04434 "null")
5. “Jenga: Effective Memory Management for Serving LLM with Heterogeneity” [https://arxiv.org/abs/2503.18292](https://arxiv.org/abs/2503.18292 "null")
6. “Orca: A Distributed Serving System for Transformer-Based Generative Models” [https://www.usenix.org/conference/osdi22/presentation/yu](https://www.usenix.org/conference/osdi22/presentation/yu "null")
7. “XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models” [https://arxiv.org/abs/2411.15100](https://arxiv.org/abs/2411.15100 "null")
8. “Accelerating Large Language Model Decoding with Speculative Sampling” [https://arxiv.org/abs/2302.01318](https://arxiv.org/abs/2302.01318 "null")
9. “EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty” [https://arxiv.org/abs/2401.15077](https://arxiv.org/abs/2401.15077 "null")
10. “Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads” [https://arxiv.org/abs/2401.10774](https://arxiv.org/abs/2401.10774 "null")
11. LMCache [https://github.com/LMCache/LMCache](https://github.com/LMCache/LMCache "null")
