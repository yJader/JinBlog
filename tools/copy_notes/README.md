# 笔记复制工具

一个用于在不同工作区间复制笔记文件的命令行工具。支持自动复制对应的 `.assets` 文件夹，文件重命名和覆盖功能。

## 功能特性

- 🚀 复制 Markdown 笔记文件和对应的 `.assets` 文件夹
- 📝 支持文件重命名
- 🔄 支持覆盖已存在的文件
- 👀 预览模式，查看操作而不实际执行
- 📋 列出目录下的所有笔记文件
- 🎨 美观的终端界面（使用 Rich）

## 安装依赖

```bash
pip install typer rich
```

## 使用方法

### 基本复制

```bash
python copy_notes.py copy "/Users/jader/Work/MyNote/DL-LLM/CMU 10-414 Deep Learning Systems/note.md" "/Users/jader/Work/JinBlog/docs/csdiy/CMU 10-414 Deep Learning Systems"
```

### 重命名复制

```bash
python copy_notes.py copy "/path/to/source/note.md" "/path/to/target/folder" --rename "new_name"
```

### 强制覆盖

```bash
python copy_notes.py copy "/path/to/source/note.md" "/path/to/target/folder" --force
```

### 预览模式

```bash
python copy_notes.py copy "/path/to/source/note.md" "/path/to/target/folder" --dry-run
```

### 列出目录下的笔记

```bash
# 递归列出所有笔记
python copy_notes.py list-notes "/Users/jader/Work/MyNote"

# 只列出当前目录的笔记
python copy_notes.py list-notes "/Users/jader/Work/MyNote" --no-recursive
```

## 命令详解

### copy 命令

复制笔记文件和对应的 assets 文件夹。

**参数:**

- `source`: 源笔记文件路径（必需）
- `target`: 目标文件夹路径（必需）

**选项:**

- `--rename, -r`: 重命名文件（不包含扩展名）
- `--force, -f`: 强制覆盖已存在的文件
- `--dry-run, -d`: 预览操作，不实际执行

### list-notes 命令

列出指定目录下的所有笔记文件。

**参数:**

- `directory`: 要扫描的目录路径（必需）

**选项:**

- `--recursive/--no-recursive, -r`: 是否递归扫描子目录（默认：true）

## 使用示例

### 场景1：复制 CMU 课程笔记

```bash
python copy_notes.py copy \
  "/Users/jader/Work/MyNote/DL-LLM/CMU 10-414 Deep Learning Systems/10-414_深度学习系统课程笔记.md" \
  "/Users/jader/Work/JinBlog/docs/csdiy/CMU 10-414 Deep Learning Systems"
```

### 场景2：重命名并复制

```bash
python copy_notes.py copy \
  "/Users/jader/Work/MyNote/course/原始笔记.md" \
  "/Users/jader/Work/JinBlog/docs/csdiy" \
  --rename "整理后的笔记"
```

### 场景3：查看可复制的笔记

```bash
# 查看源目录下的所有笔记
python copy_notes.py list-notes "/Users/jader/Work/MyNote/DL-LLM"
```

## 功能说明

### Assets 文件夹处理

脚本会自动查找与笔记文件同名的 `.assets` 文件夹。例如：

- 笔记文件：`note.md`
- Assets 文件夹：`note.assets/`

复制时，如果指定了重命名，Assets 文件夹也会相应重命名。

### 安全检查

- 验证源文件是否存在且为 Markdown 文件
- 检查目标目录是否存在
- 覆盖前会显示警告，需要 `--force` 参数确认
- 操作前会显示详细的操作概览表格

### 错误处理

- 详细的错误信息显示
- 操作失败时的安全退出
- 路径验证和权限检查

## 注意事项

1. 确保有足够的磁盘空间
2. 复制大文件时请耐心等待
3. 使用 `--dry-run` 预览操作结果
4. 重要文件建议先备份
