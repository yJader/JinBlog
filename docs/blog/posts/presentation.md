---
date:
  created: 2024-06-09
  updated: 2024-09-09
description: 使用纯文本制作演示文稿的优缺点及工具推荐
categories:
  - 杂项
comments: true 
---

# Plain Text is All You Need (for Presentations)

面对课程汇报 / 学术报告 / 组会等场景, 使用演示文稿进行Presentation是常见的方式

但是使用PowerPoint / Keynote等软件制作的演示文稿, 往往会有以下问题:

- 操作复杂, 需要学习软件的使用 (虽然大家信息课都学习过)
- 跨平台兼容差 (经常要导出为pdf)
- 富文本文稿, 不利于版本控制&同步
- **LLM支持不够好**

此时使用纯文本(Plain Text)来制作是一个不错的选择
<!-- more -->
但是同样有一定缺点

- 不易编辑:
  - 导出为PDF后, 需要重新编辑源文件才能修改内容
  - 不能像PPT那样即时&可视化地修改配图(流程图)和图片位置

## 编写

### LaTeX-Beamer

LaTeX-[Beamer包](https://zh.wikipedia.org/zh-cn/Beamer_(LaTeX))是一个基于LaTeX的演示文稿制作工具, 导出为PDF

**优点**:

- **模板丰富, 可定制**: 可以通过修改模板和样式来定制演示文稿的外观
  - [overleaf: LaTeX templates and examples — Beamer](https://www.overleaf.com/gallery/tagged/beamer)
- **版本控制**: 使用文本文件编写, 方便使用Git等版本控制工具进行管理
- **跨平台**: LaTeX-Beamer可以在任何支持LaTeX的操作系统上运行, 生成的PDF文件可以在任何PDF阅读器上查看
- **数学公式**: 支持LaTeX的数学公式, 适合需要展示复杂公式的场景

**缺点**:

- 环境配置较为复杂, 编译较慢
  - 使用overleaf等在线编辑器可以简化配置, 但是如果用的是普通版, 很容易编译超时
- 语法较为繁琐, 需要学习LaTeX语法
  - 但是不动模板, 只修改内容上手还是很快的

- 不支持动画效果, 只能通过切换幻灯片来实现

### Typst-touying

> [**touying: A powerful package for creating presentation slides in Typst.**](https://typst.app/universe/package/touying/)

typst与LaTeX相似, 都是基于纯文本的排版系统, 使用rust编写, 很好地解决的LaTeX编译慢&语法冗长且复杂的问题

**缺点**:

- 尽管简化了语法, 但是LaTeX在科研界更常用, 额外多学一个有些没必要了...
- 模板相对LaTeX较少

### Markdown-Marp

Marp是一个基于Markdown的演示文稿制作工具, 具有以下优点:

- **简单易用**: 使用Markdown语法编写, 上手快, 适合快速制作演示文稿
- **跨平台**: Marp for VS Code可以在任何支持VSCode的操作系统上运行, 生成的HTML和PDF文件可以在任何浏览器和PDF阅读器上查看
- **版本控制**: 使用文本文件编写, 方便使用Git等版本控制工具进行管理
- **便于LLM生成和编辑**: 没有在Markdown和html语法上做过多改造, LLM可以很好地理解和生成

## 放映方式

### 基于PDF的演讲者视图

1. **MacOS用户限定**：使用 [Présentation.app](http://iihm.imag.fr/blanch/software/osx-presentation)
   - 提供了演示者视图，可以显示PDF中的注释
2. 使用基于Python的 [pympress](https://github.com/Cimbali/pympress)

### 转为PowerPoint

1. 将PDF转为纯图的PowerPoint
    - 可以使用我编写的 [pdf2pptx脚本](https://github.com/yJader/pdf2pptx) 或其他类似工具
    - 将生成的PDF转换为PowerPoint格式，利用PowerPoint的演讲者模式显示备注
2. 针对Marp, 可以直接选择导出为PowerPoint格式
    - 使用`<!-- 演讲内容 -->`可以添加备注, 导出为pptx时会自动识别并添加到备注中

备注: Marp 不能直接通过VS Code放映, sad :(
> <https://github.com/marp-team/marp-vscode/issues/87>
> We understand requests for this feature, but since the Marp for VS Code extension is primary designed for previewing the appearance of slides, currently there are no plans to work on this by Marp team. We are very cautious about doing that because it could potentially cause scope creep.
