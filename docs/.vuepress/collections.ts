/**
 * @see https://theme-plume.vuejs.press/guide/collection/ 查看文档了解配置详情。
 *
 * Collections 配置文件，它在 `.vuepress/plume.config.ts` 中被导入。
 *
 * 请注意，你应该先在这里配置好 Collections，然后再启动 vuepress，主题会在启动 vuepress 时，
 * 读取这里配置的 Collections，然后在与 Collection 相关的 Markdown 文件中，自动生成 permalink。
 *
 * collection 的  type 为 `post` 时，表示为 文档列表类型（即没有侧边导航栏，有文档列表页）
 * 可用于实现如 博客、专栏 等以文章列表聚合形式的文档集合 （内容相对碎片化的）
 *
 * collection 的 type 为 `doc` 时，表示为文档类型（即有侧边导航栏）
 * 可用于实现如 笔记、知识库、文档等以侧边导航栏形式的文档集合 （内容强关联、成体系的）
 * 如果发现 侧边栏没有显示，那么请检查你的配置是否正确，以及 Markdown 文件中的 permalink
 * 是否是以对应的 Collection 配置的 link 的前缀开头。 是否展示侧边栏是根据 页面链接 的前缀 与 `collection.link`
 * 的前缀是否匹配来决定。
 */

/**
 * 在受支持的 IDE 中会智能提示配置项。
 *
 * - `defineCollections` 是用于定义 collection 集合的帮助函数
 * - `defineCollection` 是用于定义单个 collection 配置的帮助函数
 *
 * 通过 `defineCollection` 定义的 collection 配置，应该填入 `defineCollections` 中
 */
import { defineCollection, defineCollections } from 'vuepress-theme-plume'

const blog = defineCollection({
  // post 类型，这里用于实现 博客功能
  type: 'post',
  // 文档集合所在目录，相对于 `docs`
  dir: 'blog/posts',
  // 文档标题，它将用于在页面的面包屑导航中显示
  title: 'Blog',
  // 文章列表页的链接，如果 `linkPrefix` 未定义，它也将作为 相关的文章的 permalink 的前缀
  link: '/blog/posts/',
  //   linkPrefix: '/article/', // 相关文章的链接前缀
  //   postList: true, // 是否启用文章列表页
  //   tags: true, // 是否启用标签页
  //   archives: true, // 是否启用归档页
  //   categories: true, // 是否启用分类页
  //   postCover: 'right', // 文章封面位置
  //   pagination: 15, // 每页显示文章数量
})

const FZUCSCourse = defineCollection({
  type: 'doc',
  dir: 'fzu_cs_course',
  linkPrefix: '/fzu_cs_course',
  title: 'FZU CS课程',
  sidebar: [
    { text: '课程总览', link: '/fzu_cs_course/README.md' },
    {
      text: '数字电路与逻辑设计', collapsed: true,
      items: 'auto',
      prefix: '/fzu_cs_course/数字电路与逻辑设计/',
    },
    { text: '离散数学', link: '/fzu_cs_course/离散数学/离散数学.md', collapsed: true },
    {
      text: '数据结构', collapsed: true,
      items: 'auto',
      prefix: '/fzu_cs_course/数据结构/',
    },
    {
      text: '计算机组成原理', collapsed: true,
      items: 'auto',
      prefix: '/fzu_cs_course/计算机组成原理/',
    },
    {
      text: '计算机网络', collapsed: true,
      items: 'auto',
      prefix: '/fzu_cs_course/计算机网络/',
    },
    {
      text: '操作系统', collapsed: true,
      items: 'auto',
      prefix: '/fzu_cs_course/操作系统/',
    },
    {
      text: '软件工程', collapsed: true,
      items: 'auto',
      prefix: '/fzu_cs_course/软件工程/',
    },
    {
      text: '数据库系统原理', collapsed: true,
      items: 'auto',
      prefix: '/fzu_cs_course/数据库系统原理/',
    },
    { text: '计算机图形学', link: '/fzu_cs_course/图形学/图形学.md' },
    {
      text: '汇编 & 接口', collapsed: true,
      items: [
        { text: '汇编 & 接口', link: '/fzu_cs_course/汇编&接口/汇编&接口.md' },
        { text: '汇编模板', link: '/fzu_cs_course/汇编&接口/汇编模板.md' },
      ],
    },
    { text: '劳动实践 (BearPi)', link: '/fzu_cs_course/劳动实践(BearPi)/劳动实践笔记.md' },
    { text: '数据挖掘', link: '/fzu_cs_course/数据挖掘/数据挖掘.md' },
    {
      text: '计算机系统结构', collapsed: true,
      link: '/fzu_cs_course/计算机系统结构/README.md',
      items: [
        { text: '课程笔记', link: '/fzu_cs_course/计算机系统结构/系统结构.md' },
        { text: '复习提纲MAP', link: '/fzu_cs_course/计算机系统结构/复习提纲MAP.md' },
        { text: '简答题', link: '/fzu_cs_course/计算机系统结构/简答题.md' },
        { text: '小测选填', link: '/fzu_cs_course/计算机系统结构/小测选填.md' },
      ],
    },
    { text: '编译原理', link: '/fzu_cs_course/编译原理/编译原理.md' },
    {
      text: '计算方法 (数值分析)', collapsed: true,
      items: 'auto',
      prefix: '/fzu_cs_course/计算方法(数值分析)/',
    },
    {
      text: '人机交互', collapsed: true,
      items: 'auto',
      prefix: '/fzu_cs_course/人机交互/',
    },
    {
      text: '毕业设计', collapsed: true,
      items: 'auto',
      prefix: '/fzu_cs_course/毕业设计/',
    },
  ],
  sidebarCollapsed: true,
})

const csdiy = defineCollection({
  type: 'doc',
  dir: 'csdiy',
  linkPrefix: '/csdiy',
  title: 'CSDIY公开课',
  sidebar: [
    {
      text: 'CMU 10-414 Deep Learning Systems', link: '/csdiy/10-414/',
      items: [
        { text: 'Homework笔记', link: '/csdiy/10-414-homework/' },
        { text: '课程笔记', link: '/csdiy/10-414-notes/' },
      ]
    },
    {
      text: 'CS224W 图机器学习', link: '/csdiy/CS224w图机器学习/',
      items: [
        { text: '课程笔记', link: '/csdiy/CS224w图机器学习/课程笔记/' },
        { text: '笔记源文件', link: '/csdiy/CS224w图机器学习/CS224w.pdf' }
      ]
    },
  ],
})

const dlLLM = defineCollection({
  type: 'doc',
  dir: 'dl_llm',
  linkPrefix: '/dl_llm',
  title: 'DL-LLM',
  sidebar: [
    { text: 'vLLM: 高吞吐量大语言模型推理系统剖析', link: '/dl_llm/vllm-anatomy/' },
    {
      text: 'CMU 10-414 Deep Learning Systems', link: '/csdiy/10-414/',
      items: [
        { text: 'Homework笔记', link: '/csdiy/10-414-homework/' },
        { text: '课程笔记', link: '/csdiy/10-414-notes/' },
      ]
    },
  ],
})

const tools = defineCollection({
  type: 'doc',
  dir: 'tools',
  linkPrefix: '/tools',
  title: '工具分享',
  sidebar: 'auto',
})

/**
 * 导出所有的 collections
 * (blog 为博客示例，如果不需要博客功能，请删除)
 * (demoDoc 为参考示例，如果不需要它，请删除)
 */
export default defineCollections([
  blog,
  FZUCSCourse,
  csdiy,
  dlLLM,
  tools,
])
