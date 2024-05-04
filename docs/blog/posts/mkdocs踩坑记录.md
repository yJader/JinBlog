---
date:
  created: 2024-04-04
  updated: 2024-04-04
categories:
  - 踩坑记录
comments: true 
---

## Latex

[MathJax(数学) - Material for MkDocs (wdk-docs.github.io)](https://wdk-docs.github.io/mkdocs-material-docs/reference/mathjax/)

添加脚本到`docs/javascripts/mathjax.js`

<!-- more -->

```js
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true,
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex",
  },
};

document$.subscribe(() => {
  MathJax.typesetPromise();
});
```

添加配置

```yaml
markdown_extensions:
  - pymdownx.arithmatex:
      generic: true

extra_javascript:
  - javascripts/mathjax.js
  - https://polyfill.io/v3/polyfill.min.js?features=es6
  - https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js
```

## 多层次列表

多层次列表(`- ` `1. `)无法正确显示

需要添加

```yml
markdown_extensions:
  - mdx_truly_sane_lists # 多级列表
```

## 不支持````c`格式的代码块

> [Code blocks - Material for MkDocs (squidfunk.github.io)](https://squidfunk.github.io/mkdocs-material/reference/code-blocks/)

添加

```yaml
markdown_extensions:
  - pymdownx.highlight: # 代码块语法高亮
      anchor_linenums: true # 启用行号
      line_spans: __span # 自定义行范围
      pygments_lang_class: true # 使用语言类名
  - pymdownx.inlinehilite # 行内代码高亮
  - pymdownx.tilde #删除线
  - pymdownx.snippets #代码片段, 没用过, 抄的配置
  - pymdownx.superfences #代码块增强
```

## `<img>`格式图片引用出错

在平时写 markdown 时, 添加的截图经常会使用 typora 的右键进行缩放, 实际上是使用`<img>`标签来引用图片

这在 typora 和 vscode 中一切正常, 但是在用 mkdocs 部署时无法正确地引用到该图片

### 测试

#### 测试文本

```text
## 测试
### 绝对路径

<img src="/test/test.assets/image-20240403162141023.png" alt="image-20231104201701127" style="zoom: 50%;" />

### 相对路径
#### `![]()`

![image](image.png)
![image](./image.png)
![7408](./test.assets/image-20240403162141023.png)

#### img 空
- <img src="test.assets/image-20240403162141023.png" alt="image-20220907225416746" style="zoom:33%;" />

#### img `./`
- <img src="./test.assets/image-20240403162141023.png" alt="image-20220907225416746" style="zoom:33%;" />

```

```shell
test
├── image.png
├── test.assets
│   ├── image-20231104201701127.png
│   └── image-20240403162141023.png
└── testBlog.md
```

#### 测试结果

> [markdown - configuring image filepaths correctly in mkdocs - Stack Overflow](https://stackoverflow.com/questions/71074662/configuring-image-filepaths-correctly-in-mkdocs/71083184#71083184)
>
> [配置文件 - MkDocs 中文文档 (hellowac.github.io)](https://hellowac.github.io/mkdocs-docs-zh/user-guide/configuration/#use_directory_urls)

1. 在浏览器中访问图片路径(`/test/test.assets/image-20240403162141023.png`)可以正常显示, 所以是引用出现问题

2. 通过查看报错信息可知

   - ```shell
     WARNING -  [16:49:47] "GET /test/testBlog/test.assets/image-20240403162141023.png HTTP/1.1"  code 404
     ```

   - 图片路径被错误地加上了`/testBlog`

### 错误分析

> 参考[StackOverflow 的回答](https://stackoverflow.com/questions/71074662/configuring-image-filepaths-correctly-in-mkdocs/71083184#71083184)

> [官方文档](https://www.mkdocs.org/user-guide/writing-your-docs/#linking-from-raw-html):
>
> Markdown 允许文档作者在 Markdown 语法无法满足作者需求时，回退到原始 HTML。MkDocs 在这方面并不限制 Markdown。然而，由于所有原始 HTML 都被 Markdown 解析器忽略，MkDocs**无法验证或转换包含在原始 HTML 中的链接(在这里就是我们图片链接)**。当你在原始 HTML 中包含内部链接时，你需要手动将链接适当地格式化以适应渲染后的文档。

对于我上面的 testBlog, 生成的 url 为`https://.../test/testBlog/` 这时, 这个 md 文件被视为一个目录

对于文档中`<img src="test.assets/image-20240403162141023.png" alt="image-20220907225416746" style="zoom:33%;" />`这一标签, 浏览器会去访问同一目录(`test/testBlog/`)下的图片(`test/testBlog/test.assets/image-20240403162141023.png`)

然而, 这个图片的实际路径并没有`/testBlog`

### 解决方案

> 同样参考[StackOverflow 的回答](https://stackoverflow.com/questions/71074662/configuring-image-filepaths-correctly-in-mkdocs/71083184#71083184)

因为`testBlog.md`被转换为了一个目录, 这时候只需要让它不被转换

大佬给了一个配置项: [use_directory_urls](https://hellowac.github.io/mkdocs-docs-zh/user-guide/configuration/#use_directory_urls) 该配置项会让`testBlog.md`展示为`/testBlog.html`文件而非`/testBlog`

### 后记

1. 不要熬夜改 bug, 会变得神志不清
2. 早该上 StackoverFlow 搜的 QAQ

## Blog 配置

[Mkdocs Material 使用记录 - shafish.cn](https://shafish.cn/blog/mkdocs/#14-blog)
