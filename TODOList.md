# 博客搭建 TODOList

## 格式显示bug
- [ ] 配置到action中
### 高亮
- 编写一个脚本, 将`==text==`语法修改为 html`<mark>text</mark>`, 并配置 github action
  - 原因: 高亮语法(`==text==`)在 PyMdown 中存在 bug

### LaTeX显示
- 修复类似`$ ax+b $`中因为`$`前后有空格导致的 latex 渲染出错
- 修复方式: `\$(.*?)\$`匹配 latex, 用`${$1}$`替换
  - mark: $$会被上面的匹配, 记得排除掉
- note: 问题发现: latex框格渲染有些问题
  ```
    # 渲染错误
    text
    $$
      \LaTeX
    $$
    text

    # 渲染正确, 需要换行来间隔
    text

    $$
      \LaTeX
    $$

    text
  ```
- note: 暂时还不能处理 text$$text$$text 中有换行符的情况, 但是这种不应该出现, 手动修复吧