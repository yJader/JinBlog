# 博客脚本工具

一些在博客中使用的脚本工具，主要用于处理文本渲染, 图片转换等。

## 主入口 (main.py)

通过 `main.py` 可以方便地调用所有工具脚本，提供统一的命令行接口。

### 使用方法

```bash
# 查看所有可用工具
python main.py --help

# 查看工具集信息
python main.py info

# 查看版本信息
python main.py version
```

### 可用命令

#### 1. transfer - Markdown 格式转换工具

```bash
# 转换当前目录下所有 Markdown 文件
python main.py transfer "*.md"

# 转换指定文件，显示详细信息
python main.py transfer "docs/**/*.md" --verbose

# 安静模式（不显示详细信息）
python main.py transfer "*.md" --quiet

# 查看 transfer 命令的完整帮助
python main.py transfer --help
```

功能：

- 将 `==text==` 高亮语法转换为 `<mark>text</mark>`
- 修复 LaTeX 公式中的空格问题
- 优化 LaTeX 块的换行格式

#### 2. copy - 笔记复制工具

```bash
# 复制单个笔记文件到目标目录
python main.py copy "/path/to/source/note.md" "/path/to/target/folder"

# 复制时重命名文件
python main.py copy "/path/to/note.md" "/path/to/target/" --rename "new-name"

# 强制覆盖已存在的文件
python main.py copy "/path/to/note.md" "/path/to/target/" --force

# 预览操作（不实际执行）
python main.py copy "/path/to/note.md" "/path/to/target/" --dry-run

# 跳过格式转换
python main.py copy "/path/to/note.md" "/path/to/target/" --no-transfer

# 查看 copy 命令的完整帮助
python main.py copy --help
```

功能：

- 复制笔记文件和对应的 assets 文件夹
- 支持文件重命名（仅单文件模式）
- 支持强制覆盖已存在文件
- 预览操作查看操作
- 自动应用 Markdown 格式转换（可选）

#### 3. list - 笔记文件列表工具

```bash
# 列出目录下的所有笔记文件
python main.py list "/path/to/directory"

# 递归列出所有子目录的笔记文件
python main.py list "/path/to/directory" --recursive

# 非递归模式（仅扫描当前目录）
python main.py list "/path/to/directory" --no-recursive

# 查看 list 命令的完整帮助
python main.py list --help
```

功能：

- 列出目录下的所有笔记文件
- 支持递归扫描子目录
- 显示 assets 文件夹状态
- 美观的表格显示结果

## 环境要求

在使用前，请确保安装了所需依赖：

```bash
# 安装依赖
pip install typer rich

# 或者使用 uv（如果项目使用 uv 管理依赖）
uv sync
```

## 单独使用工具

你也可以直接使用各个工具脚本：

```bash
# 直接使用 transfer 工具
cd transferMD
python transfer.py "*.md"

# 直接使用 copy_notes 工具  
cd copy_notes
python copy_notes.py copy "/path/to/note.md" "/path/to/target/"
```
