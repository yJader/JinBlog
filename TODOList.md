# 博客搭建 TODOList

- [ ] 编写一个脚本, 将`==text==`语法修改为 html`<mark>text</mark>`, 并配置 github action
  - 原因: 高亮语法(`==text==`)在 PyMdown 中存在 bug
- [ ] 修复类似`$ ax+b $`中因为`$`前后有空格导致的 latex 渲染出错
  - 修复方式: `\$(.*?)\$`匹配 latex, 用`${$1}$`替换
