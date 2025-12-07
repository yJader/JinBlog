---
pageLayout: home
externalLinkIcon: false
config:
  -
    type: hero
    full: true
    # forceDark: true
    effect: tint-plate
    # 🌈 结束乐队专属配色方案 by 前端大神 Gemini
    tintPlate:
      # 浅色模式：明亮鲜艳，包含红黄蓝粉四色特征
      light:
        r: { value: 150, offset: 100 } # 波动范围 [50, 250]，覆盖深蓝到亮粉
        g: { value: 150, offset: 80 }  # 波动范围 [70, 230]，覆盖深红到亮黄
        b: { value: 140, offset: 80 }  # 波动范围 [60, 220]，覆盖深红到冷蓝
      # 深色模式：保留色相但降低亮度，营造 Livehouse 般的深邃霓虹感
      dark:
        r: { value: 80, offset: 60 }   # 暗红/暗紫为主调
        g: { value: 60, offset: 40 }   # 偶尔出现的暗金/橄榄色
        b: { value: 90, offset: 60 }   # 深邃的蓝色底蕴
    hero:
      name: Jin Blog
      tagline: 亦瑾的个人博客
      text: 走在未知的道路上，不许停也不能回头
      actions:
      # note: 已经被docs/.vuepress/styles/index.css覆盖, 始终显示为四色按钮
        -
          theme: brand
          text: 我的博客
          link: /blog/posts/
        - 
          theme: brand
          text: FZU CS课程
          link: /fzu_cs_course/
        - 
          theme: alt
          text: 工具分享
          link: /tools/
        -
          theme: alt
          text: Github →
          link: https://github.com/yJader
---

# Welcome to Jin blog

> 走在未知的道路上，不许停也不能回头

这是亦瑾的个人博客, 随缘更新中XD

## About Me

- FZU SOSD web 组成员
- Hub 主页:

  - [yJader (亦瑾) (github.com)](https://github.com/yJader)
  - [亦瑾 (yJader) (Gitee.com)](https://gitee.com/yJader)

- 常用语言: `Java`, `CPP`
- 学习方向:
  - Java 后端开发(已失忆)
  - System(Learning):
    - [CMU CS15-213 Introduction to Computer Systems (ICS)](https://www.cs.cmu.edu/~213/), 即[CSAPP](https://csapp.cs.cmu.edu/)
    - [南京大学 操作系统: 设计与实现 - 蒋炎岩](https://jyywiki.cn/OS/2024/)
    - [MIT 6.824/6.5840: Distributed Systems](https://pdos.csail.mit.edu/6.824/index.html)
    - 很长的TODOList...
  - LLM推理优化(尚未入门)

- 臭看动画的 & 中V日V 双厨(注: V-Vocaloid)

## Friend Link

- ~~[茉莉花 molihua](https://molihua.wiki/)~~ (已归档)
- [RockRockWhite's wonderland](https://www.rockrockwhite.cn/categories/distributed%20system)
