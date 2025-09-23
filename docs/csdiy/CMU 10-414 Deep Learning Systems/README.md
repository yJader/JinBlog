# CMU 10-414/714: Deep Learning Systems

[CMU 10-414/714: Deep Learning Systems - CS自学指南](https://csdiy.wiki/%E6%9C%BA%E5%99%A8%E5%AD%A6%E4%B9%A0%E7%B3%BB%E7%BB%9F/CMU10-414/)

[【深度学习系统：算法与实现 10-714 2022】卡耐基梅隆—ai中英字幕](https://www.bilibili.com/video/BV1ny411b7dJ)

[Deep Learning Systems 课程官网](https://dlsyscourse.org/)

一门相似的课程 [智能计算系统官方网站](https://novel.ict.ac.cn/aics/)

- [智能计算系统 - CS自学指南](https://csdiy.wiki/%E6%9C%BA%E5%99%A8%E5%AD%A6%E4%B9%A0%E7%B3%BB%E7%BB%9F/AICS/#_2)
- 学哪个待定, 先看看introduction
**TODO**:
- [CMU 11-868: Large Language Model System - CS自学指南](https://csdiy.wiki/%E6%B7%B1%E5%BA%A6%E7%94%9F%E6%88%90%E6%A8%A1%E5%9E%8B/%E5%A4%A7%E8%AF%AD%E8%A8%80%E6%A8%A1%E5%9E%8B/CMU11-868/#_1)

## prompt

```markdown
我有一份英文课程 PPT。请根据 PPT 内容，翻译出一份完整的中文笔记，要求如下：

- 用 `markdown` 代码块输出
- 公式使用 LaTeX 语法（用 `$` 包裹, `$`符号和公式之间不要有空格）
- 笔记需要涵盖 PPT 的**所有**内容，包括概念、定理、例子、图表信息等, 如果需要插入截图, 请标注
- 每行末尾不需要加上`。`
- 结构清晰，适当使用标题（`#`）、代码块、内嵌latex公式等 Markdown 语法, 其中标题为# Lec6 xxx, ## 6.1, ## 6.2...
```

## Schedule

### Homework Details

|          Homework           | Released |   Due    |                                                 Colab Link                                                  |                         GitHub Repo                          |
| :-------------------------: | :------: | :------: | :---------------------------------------------------------------------------------------------------------: | :----------------------------------------------------------: |
|         Homework 0          | 8/29/24  | 9/12/24  |          [hw0 colab](https://colab.research.google.com/github/dlsyscourse/hw0/blob/main/hw0.ipynb)          |       [hw0 github](https://github.com/dlsyscourse/hw0)       |
|         Homework 1          | 9/10/24  | 9/24/24  |          [hw1 colab](https://colab.research.google.com/github/dlsyscourse/hw1/blob/main/hw1.ipynb)          |       [hw1 github](https://github.com/dlsyscourse/hw1)       |
|         Homework 2          | 9/24/24  | 10/10/24 |          [hw2 colab](https://colab.research.google.com/github/dlsyscourse/hw2/blob/main/hw2.ipynb)          |       [hw2 github](https://github.com/dlsyscourse/hw2)       |
|         Homework 3          | 10/10/24 | 10/31/24 |          [hw3 colab](https://colab.research.google.com/github/dlsyscourse/hw3/blob/main/hw3.ipynb)          |       [hw3 github](https://github.com/dlsyscourse/hw3)       |
|         Homework 4          | 10/31/24 | 11/16/24 |          [hw4 colab](https://colab.research.google.com/github/dlsyscourse/hw4/blob/main/hw4.ipynb)          |       [hw4 github](https://github.com/dlsyscourse/hw4)       |
| Homework 4 Extra (714 only) | 10/31/24 | 11/16/24 | [hw4 extra colab](https://colab.research.google.com/github/dlsyscourse/hw4_extra/blob/main/hw4_extra.ipynb) | [hw4 extra github](https://github.com/dlsyscourse/hw4_extra) |

### Lecture&Homework Schedule

| Date (CMU) | Lecture                                                         | Instructor | Slides                                                                                                                             | Video (2022 version)                                                                                                                                                                                                                    | Homework                                                                       |
| ---------- | --------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| 8/27       | 1 - Introduction / Logistics                                    | Kolter     | [pdf](https://dlsyscourse.org/slides/intro.pdf)                                                                                    | [YouTube](https://youtu.be/ftP5HeOvsI0) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=2)                                                                                                                                  |                                                                                |
| 8/29       | 2 - ML Refresher / Softmax Regression                           | Kolter     | [pdf](https://dlsyscourse.org/slides/2-softmax_regression.pdf)                                                                     | [YouTube](https://youtu.be/MlivXhZFbNA) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=3)                                                                                                                                  | **Homework 0 Released**                                                        |
| 9/3        | 3 - Manual Neural Networks / Backprop                           | Kolter     | [pdf](https://dlsyscourse.org/slides/manual_neural_nets.pdf)                                                                       | [YouTube (pt 1)](https://youtu.be/OyrqSYJs7NQ) [YouTube (pt 2)](https://youtu.be/JLg1HkzDsKI) / [Bilibili (pt 1)](https://www.bilibili.com/video/BV1ny411b7dJ/?p=4) [Bilibili (pt 2)](https://www.bilibili.com/video/BV1ny411b7dJ/?p=5) |                                                                                |
| 9/5        | 4 - Automatic Differentiation                                   | Chen       | [pdf](https://dlsyscourse.org/slides/4-automatic-differentiation.pdf)                                                              | [YouTube](https://youtu.be/56WUlMEeAuA) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=6)                                                                                                                                  |                                                                                |
| 9/10       | 5 - Automatic Differentiation Implementation                    | Chen       | [ipynb](https://github.com/dlsyscourse/lecture5/blob/main/5_automatic_differentiation_implementation.ipynb)                        | [YouTube](https://youtu.be/cNADlHfHQHg) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=7)                                                                                                                                  | **Homework 1 Released**                                                        |
| 9/12       | 6 - Optimization                                                | Kolter     | [pdf](https://dlsyscourse.org/slides/fc_init_opt.pdf)                                                                              | [YouTube](https://youtu.be/CukpVt-1PA4) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=8)                                                                                                                                  | **Homework 0 Due**                                                             |
| 9/17       | 7 - Neural Network Library Abstractions                         | Chen       | [pdf](https://dlsyscourse.org/slides/7-nn-framework.pdf)                                                                           | [YouTube](https://youtu.be/fzKNkS_5E6U) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=9)                                                                                                                                  |                                                                                |
| 9/19       | 9 - Normalization, Dropout, + Implementation                    | Kolter     | [pdf](https://dlsyscourse.org/slides/norm_reg.pdf)                                                                                 | [YouTube](https://youtu.be/ky7qiKyZmnE) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=10)                                                                                                                                 |                                                                                |
| 9/24       | 8 - NN Library Implementation                                   | Chen       | [ipynb](https://github.com/dlsyscourse/lecture8/blob/main/8_nn_library_implementation.ipynb)                                       | [YouTube](https://youtu.be/uB81vGRrH0c) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=11)                                                                                                                                 | **Homework 1 Due, <br />Homework 2 Released**                                  |
| 9/26       | 10 - Convolutional Networks                                     | Kolter     | [pdf](https://dlsyscourse.org/slides/conv_nets.pdf)                                                                                | [YouTube](https://youtu.be/-5RPPjn0hPg) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=12)                                                                                                                                 |                                                                                |
| 10/1       | 11 - Hardware Acceleration for Linear Algebra                   | Chen       | [pdf](https://dlsyscourse.org/slides/11-hardware-acceleration.pdf)                                                                 | [YouTube](https://youtu.be/es6s6T1bTtI) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=13)                                                                                                                                 |                                                                                |
| 10/3       | 12 - Hardware Acceleration + GPUs                               | Chen       | [pdf](https://dlsyscourse.org/slides/12-gpu-acceleration.pdf)                                                                      | [YouTube](https://youtu.be/jYCxVirq4d0) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=14)                                                                                                                                 |                                                                                |
| 10/8       | 13 - Hardware Acceleration Implementation                       | Chen       | [ipynb](https://github.com/dlsyscourse/lecture13/blob/main/13_hardware_acceleration_architecture_overview.ipynb)                   | [YouTube](https://youtu.be/XdhUZRXA7fg) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=15)                                                                                                                                 |                                                                                |
| 10/10      | 14 - Convoluations Network Implementation                       | Kolter     | [ipynb](https://github.com/dlsyscourse/public_notebooks/blob/main/convolution_implementation.ipynb)                                | [YouTube](https://youtu.be/7kclgMIcMq0) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=16)                                                                                                                                 | **Homework 2 Due, <br />Homework 3 Released**                                  |
| 10/15      | *No class - Fall Break*                                         |            |                                                                                                                                    |                                                                                                                                                                                                                                         |                                                                                |
| 10/17      | *No class - Fall Break*                                         |            |                                                                                                                                    |                                                                                                                                                                                                                                         |                                                                                |
| 10/22      | 15 - Sequence Modeling + RNNs                                   | Kolter     | [pdf](https://dlsyscourse.org/slides/rnns.pdf)                                                                                     | [YouTube](https://youtu.be/aI47BqLYahc) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=17)                                                                                                                                 |                                                                                |
| 10/24      | 16 - Sequence Modeling Implementation                           | Kolter     | [ipynb](https://github.com/dlsyscourse/public_notebooks/blob/main/rnn_implementation.ipynb)                                        | [YouTube](https://youtu.be/q12VPh-bK7k) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=18)                                                                                                                                 |                                                                                |
| 10/29      | 17 - Transformers and Autoregressive Models                     | Kolter     | [pdf](https://dlsyscourse.org/slides/transformers.pdf)                                                                             | [Youtube](https://youtu.be/IFKRf-BAqZo) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=19)                                                                                                                                 |                                                                                |
| 10/31      | 18 - Transformers Implementation                                | Kolter     | [ipynb](https://github.com/dlsyscourse/public_notebooks/blob/main/transformer_implementation.ipynb)                                | [Youtube](https://youtu.be/OzFmKdAHJn0) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=20)                                                                                                                                 | **Homework 3 Due, <br />Homework 4 Released, <br />Homework 4 Extra Released** |
| 11/5       | *No class - Democracy Day*                                      |            |                                                                                                                                    |                                                                                                                                                                                                                                         |                                                                                |
| 11/7       | 19 - Training Large Models                                      | Chen       | [pdf](https://dlsyscourse.org/slides/15-training-large-models.pdf)                                                                 | [YouTube](https://youtu.be/HSzVogM5IPo) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=21)                                                                                                                                 |                                                                                |
| 11/12      | 20 - Generative Models                                          | Chen       | [pdf](https://dlsyscourse.org/slides/16-generative-models.pdf)                                                                     | [YouTube](https://youtu.be/iIx_8_pxzhs) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=22)                                                                                                                                 |                                                                                |
| 11/14      | 21 - Generative Models Implementation                           | Chen       | [ipynb](https://github.com/dlsyscourse/public_notebooks/blob/main/21_generative_adversarial_networks_implementation.ipynb)         | [YouTube](https://youtu.be/DmBw8SEeAc0) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=23)                                                                                                                                 |                                                                                |
| 11/16      |                                                                 |            |                                                                                                                                    |                                                                                                                                                                                                                                         | **Homework 4 Due, Homework 4 Extra Due**                                       |
| 11/19      | 22 - Customize Pretrained Models                                | Chen       | [pdf](https://dlsyscourse.org/slides/22-augment-pretrained-models.pdf)                                                             |                                                                                                                                                                                                                                         |                                                                                |
| 11/21      | 23 - Model Deployment                                           | Chen       | [pdf](https://dlsyscourse.org/slides/23-model-deployment.pdf)                                                                      | [Youtube](https://youtu.be/jCBrUisBQ0A) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=24)                                                                                                                                 |                                                                                |
| 11/26      | 24 - Machine Learning Compilation and Deployment Implementation | Chen       | [ipynb](https://github.com/dlsyscourse/public_notebooks/blob/main/24_machine_learning_compilation_deployment_implementation.ipynb) | [Youtube](https://youtu.be/HIwsCzdW_pw) / [Bilibili](https://www.bilibili.com/video/BV1ny411b7dJ/?p=25)                                                                                                                                 |                                                                                |
| 11/28      | *No class - Thanksgiving*                                       |            |                                                                                                                                    |                                                                                                                                                                                                                                         |                                                                                |
| 12/3       | 25 - Future Directions / Q&A                                    | Both       |                                                                                                                                    |                                                                                                                                                                                                                                         |                                                                                |
| 12/5       | 26 - Student project presentations                              | Students   |                                                                                                                                    |                                                                                                                                                                                                                                         |                                                                                |

## Slides下载

AI真是太好用了XD

```shell
#!/bin/bash

# 创建一个目录来存放下载的幻灯片
OUTPUT_DIR="dlsys_course_slides"
mkdir -p "$OUTPUT_DIR"
echo "将在 '$OUTPUT_DIR/' 目录中保存所有文件"
echo "-----------------------------------------"

# 定义一个辅助函数来处理单个文件的下载，避免代码重复
download_file() {
    local filename="$1"
    local url="$2"
    
    echo "正在下载: $filename"
    # 使用 wget 命令
    # -O 指定输出文件名 (包括目录)
    # -q 使其静默运行，--show-progress 显示一个简洁的进度条
    wget -q --show-progress -O "$OUTPUT_DIR/$filename" "$url"
    
    if [ $? -eq 0 ]; then
        echo "下载完成."
    else
        echo "下载失败: $filename"
    fi
    echo "" # 添加一个空行以提高可读性
}

# --- 所有 PDF 链接和对应的文件名都硬编码在此 ---

download_file "1 - Introduction - Logistics.pdf" "https://dlsyscourse.org/slides/intro.pdf"
download_file "2 - ML Refresher - Softmax Regression.pdf" "https://dlsyscourse.org/slides/2-softmax_regression.pdf"
download_file "3 - Manual Neural Networks - Backprop.pdf" "https://dlsyscourse.org/slides/manual_neural_nets.pdf"
download_file "4 - Automatic Differentiation.pdf" "https://dlsyscourse.org/slides/4-automatic-differentiation.pdf"
download_file "6 - Optimization.pdf" "https://dlsyscourse.org/slides/fc_init_opt.pdf"
download_file "7 - Neural Network Library Abstractions.pdf" "https://dlsyscourse.org/slides/7-nn-framework.pdf"
download_file "9 - Normalization Dropout Implementation.pdf" "https://dlsyscourse.org/slides/norm_reg.pdf"
download_file "10 - Convolutional Networks.pdf" "https://dlsyscourse.org/slides/conv_nets.pdf"
download_file "11 - Hardware Acceleration for Linear Algebra.pdf" "https://dlsyscourse.org/slides/11-hardware-acceleration.pdf"
download_file "12 - Hardware Acceleration + GPUs.pdf" "https://dlsyscourse.org/slides/12-gpu-acceleration.pdf"
download_file "15 - Sequence Modeling + RNNs.pdf" "https://dlsyscourse.org/slides/rnns.pdf"
download_file "17 - Transformers and Autoregressive Models.pdf" "https://dlsyscourse.org/slides/transformers.pdf"
download_file "19 - Training Large Models.pdf" "https://dlsyscourse.org/slides/15-training-large-models.pdf"
download_file "20 - Generative Models.pdf" "https://dlsyscourse.org/slides/16-generative-models.pdf"
download_file "22 - Customize Pretrained Models.pdf" "https://dlsyscourse.org/slides/22-augment-pretrained-models.pdf"
download_file "23 - Model Deployment.pdf" "https://dlsyscourse.org/slides/23-model-deployment.pdf"

# --- 下载列表结束 ---

echo "-----------------------------------------"
echo "所有预设的 PDF 均已下载完毕"
```
