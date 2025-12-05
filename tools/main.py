#!/usr/bin/env python3
"""
JinBlog 工具集主入口
整合所有工具脚本，提供统一的命令行接口
"""

import sys
from pathlib import Path

import typer
from rich.console import Console

# 添加子模块到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入子模块的具体命令函数 (需要在路径设置后导入)
try:
    from copy_notes.copy_notes import copy as copy_notes_copy
    from copy_notes.copy_notes import list_notes
    from transferMD.transfer import transfer
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在 tools 目录下运行此脚本")
    sys.exit(1)

# 创建主应用
app = typer.Typer(
    help="JinBlog 工具集 - 便捷的笔记管理和处理工具",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()

# 添加第一级命令
app.command("transfer", help="转换 Markdown 文件格式")(transfer)
app.command("copy", help="复制笔记文件和资源")(copy_notes_copy)
app.command("list-notes", help="列出目录下的笔记文件")(list_notes)


@app.command()
def info():
    """
    显示工具集信息
    """
    console.print("""
[bold blue]🛠️  JinBlog 工具集[/bold blue]

[green]可用命令:[/green]
  [cyan]transfer[/cyan]     - Markdown 格式转换工具
                 • 转换 ==text== 高亮语法为 <mark>text</mark>
                 • 修复 LaTeX 公式空格问题
                 • 优化 LaTeX 块换行格式
                 
  [cyan]copy[/cyan]        - 笔记复制工具
                 • 复制笔记文件和对应的 assets 文件夹
                 • 支持文件重命名和强制覆盖
                 • 自动应用格式转换
                 
  [cyan]list[/cyan]        - 笔记文件列表工具
                 • 列出目录下的所有笔记文件
                 • 支持递归扫描子目录
                 • 显示 assets 文件夹状态

[yellow]使用示例:[/yellow]
  [dim]# 转换当前目录下所有 Markdown 文件[/dim]
  python main.py transfer "*.md"
  
  [dim]# 复制笔记文件[/dim]
  python main.py copy "/path/to/note.md" "/path/to/target/"
  
  [dim]# 列出目录下的笔记文件[/dim]
  python main.py list "/path/to/directory"

[yellow]获取更多帮助:[/yellow]
  python main.py transfer --help
  python main.py copy --help
  python main.py list --help
""")

if __name__ == "__main__":
    app()
