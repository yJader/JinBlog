# Repository Guidelines

## 博客定位

这是亦瑾的个人博客，主要记录课程学习、计算机基础、开发实践与工具使用。站点使用 VuePress 2 和 `vuepress-theme-plume` 构建，正文以中文 Markdown 为主。维护时优先保证内容分类清楚、链接有效、图片可正常显示。

## `docs/` 目录结构

- `docs/index.md`：站点首页。
- `docs/blog/posts/`：相对独立的博客文章，按“踩坑记录”“杂项”等主题分组。
- `docs/fzu_cs_course/`：福州大学计算机课程笔记，每门课程使用独立子目录。
- `docs/csdiy/`：公开课学习记录，如 CMU 10-414、CS224W。
- `docs/dl_llm/`：深度学习与大模型相关内容。
- `docs/tools/`：系统安装、软件配置和实用工具笔记。
- `docs/.vuepress/`：站点配置。`collections.ts` 管理内容集合与侧边栏，`navbar.ts` 管理顶部导航，`plume.config.ts` 管理主题，`public/` 存放全站静态资源。

`docs/backend/` 当前被 `config.ts` 的 `pagePatterns` 排除，不会进入 VuePress 构建结果。不要把计划发布的新文章放入该目录。

## 内容与资源约定

文章使用 `.md` 文件，标题和目录名应准确表达主题，可保留课程编号及中文名称。文章专用图片放在同级 `<文章名>.assets/` 目录，引用时使用相对路径，例如 `![示意图](./课程笔记.assets/image.png)`。全站共用的图标、头像等放入 `docs/.vuepress/public/`，并使用根路径引用。移动或重命名文章时，同步检查图片路径、集合链接和导航配置。

## 本地运行与检查

项目要求 Node.js `^20.6.0` 或 `>=22`，并使用 pnpm 10：

```sh
pnpm install          # 安装依赖
pnpm docs:dev         # 启动本地开发服务
pnpm docs:build       # 清理缓存并生成生产站点
pnpm docs:preview     # 预览已生成的站点
```

仓库没有独立测试套件；提交前至少运行 `pnpm docs:build`。修改导航、侧边栏、公式或图片后，还应在开发服务中打开相关页面检查渲染和跳转。

## 配置与提交

TypeScript 配置沿用现有风格：两空格缩进、单引号、无分号。不要在 `config.ts` 与 `plume.config.ts` 重复设置同一主题选项。提交信息沿用仓库历史中的类型前缀，如 `feat: 添加课程笔记`、`fix(docs): 修复图片路径`、`refactor: 调整博客目录结构`。一次提交聚焦一类内容，并避免提交 `.cache/`、`.temp/` 或构建产物。
