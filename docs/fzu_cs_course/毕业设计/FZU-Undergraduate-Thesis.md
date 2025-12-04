---
title: FZU-Undergraduate-Thesis
createTime: 2025/05/27 21:51:12
permalink: /fzu_cs_course/7xo99t9w/
---
# 福州大学本科生毕业论文 LaTeX 模板
>
> copy from [FZU-Undergraduate-Thesis](https://github.com/yJader/FZU-Undergraduate-Thesis)
>
> ==**注意**==：本模板为非官方版本，具体格式请以当年学校发布的最新规范为准。

本项目为福州大学本科生毕业设计（论文）LaTeX 模板，旨在帮助同学们规范、高效地撰写毕业论文。模板参考了福州大学研究生毕业论文模板，并根据[本科生论文格式要求](./20.福州大学本科生毕业设计（论文）撰写规范.pdf)进行了调整和优化。

- **使用范围**: 福州大学本科生毕业设计环节中的 文献综述, 外文原文及翻译, 论文撰写等。

- **答辩后更新**: 答辩评委评价"论文格式比较规范"

  - 注: 答辩评委会检查论文格式，请确保你的论文符合学校要求。

## 模板预览

见[预览文件](./FZU-Undergraduate-Thesis-Preview.pdf)

## 目录结构（主要文件说明）

- `main.tex`：主控文件，包含各章节与模块的引用。
- `Text/pre-defined.tex`：预定义宏包、字体、字号、环境等。
- `Text/Abstract.tex`：中英文摘要模板。
- `Text/Chapter_1.tex` 等：正文各章节内容。
- `Text/Reference.tex`、`Text/reference.bib`：参考文献及其数据库。
- `Text/titlepage-define.tex`：自定义封面相关命令。
- `Text/Titlepage.tex`：封面内容与布局。(deprecated)
- `TemplateAssets/`：图片与学校相关素材。
- 字体文件（`simfang.ttf`、`simhei.ttf`、`simkai.ttf`、`simsun.ttc`）：确保跨平台一致性。

## 使用说明

1. **编译方式**: 推荐使用 XeLaTeX 进行编译，支持中文和自定义字体。或在 Overleaf 上直接编译（选择 XeLaTeX）。
2. **格式规范**
   - 模板已按福州大学本科毕业论文格式要求设置页边距、字体、字号、行距、章节编号、目录、参考文献等。
   - 公式、图表、定义等均支持自动编号与交叉引用。
3. 关于封面
   - 使用 `main.tex` 文件中定义的变量来填充封面信息。这些变量包括：
     - `\title{本科生毕业设计（论文）}`：论文的主标题，可以根据实际情况修改，例如 "本科生毕业论文（文献综述 / 外文原文及翻译...等）"。
     - `\contenttitle{福州大学本科生毕业论文}`：内容标题，通常保持不变。
     - `\contenttitleSecond{\LaTeX 模板}`：第二行内容标题，可以留空。
     - `\author{亦瑾}`：作者姓名。
     - `\institute{计算机与大数据学院}`：学院名称。
     - `\major{计算机科学与技术}`：专业名称。
     - `\date{110年3月7日}`：日期，可以修改为终稿提交日期。
   - 签名图片：由于签名图片暂时无法配置为变量，请直接在 `Text/titlepage-define.tex` 文件中修改。
   - 封面不保证与word版完全一致, 图片相对位置存在一定偏差(尽力了QAQ)
     如果担心出问题, 请直接使用学校提供的word版封面, 转为pdf后插入使用`\includepdf[pages={1}]{Text/封面文件.pdf}`插入到文档。
4. **其他**
   - 如果编译过慢, 可以尝试使用工具将图片转为pdf格式, 以加快编译速度。

## 致谢

本模板基于 [Shifan He 的福州大学研究生毕业论文模板](https://www.overleaf.com/latex/templates/fu-zhou-da-xue-yan-jiu-sheng-bi-ye-lun-wen-mo-ban/pdccsztcptxy) 修改，感谢学长的贡献。  
感谢 Xiuqi Cui 对模板样式提出的宝贵建议。

## 参与贡献

如有建议或希望参与改进，请联系 <yjader@foxmail.com>。

## 相关项目

- [FZU-SINTEF-Beamer-Template](https://github.com/yJader/FZU-SINTEF-Beamer-Template): 一个基于sintef主题的福州大学LaTeX幻灯片模板，适用于福州大学的学术报告、课程展示、毕业设计答辩等场合。
- [pdf2pptx](https://github.com/yJader/pdf2pptx): 将pdf转为pptx格式, 并将pdfnote转为pptx的备注
