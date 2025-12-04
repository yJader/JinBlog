/**
 * @see https://theme-plume.vuejs.press/config/navigation/ 查看文档了解配置详情
 *
 * Navbar 配置文件，它在 `.vuepress/plume.config.ts` 中被导入。
 */

import { defineNavbarConfig } from 'vuepress-theme-plume'

export default defineNavbarConfig([
  { text: '首页', link: '/' },
  { text: '博客', link: '/blog/posts/' },
  { text: 'FZU CS课程', link: '/fzu_cs_course/' },
  {
    text: 'DL-LLM',
    // items: [
    //   { text: '博客学习', link: '/dl_llm/Inside vLLM Anatomy of a High-Throughput LLM Inference System' },
    //   { text: 'CMU10-414/714', link: '/csdiy/CMU 10-414 Deep Learning Systems/' }
    // ]
    link: '/dl_llm/vllm-anatomy/'
  },
  {
    text: 'CSDIY公开课',
    link: '/csdiy/10-414/'
  },
  {
    text: '工具分享',
    link: '/tools/linux-install/'
  },
])
