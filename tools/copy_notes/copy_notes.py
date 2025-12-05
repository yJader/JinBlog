#!/usr/bin/env python3
"""
笔记复制脚本
将其他工作区的笔记文件夹复制到当前工作区，支持重命名和覆盖
"""

import shutil
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

# 添加父目录到路径以导入 transferMD
current_dir = Path(__file__).parent
tools_dir = current_dir.parent
sys.path.insert(0, str(tools_dir))

app = typer.Typer(help="笔记复制工具 - 在工作区间复制笔记文件夹")
console = Console()


def copy_with_progress(src: Path, dst: Path, description: str) -> None:
    """带进度显示的文件复制"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(description, total=None)

        if src.is_file():
            # 复制单个文件
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        else:
            # 复制整个目录
            shutil.copytree(src, dst, dirs_exist_ok=True)

        progress.update(task, completed=True)


def find_assets_folder(note_path: Path) -> Optional[Path]:
    """查找对应的 .assets 文件夹"""
    note_name = note_path.stem
    assets_folder_name = f"{note_name}.assets"

    # 在笔记文件的同级目录查找 assets 文件夹
    assets_path = note_path.parent / assets_folder_name

    if assets_path.exists() and assets_path.is_dir():
        return assets_path

    return None


def validate_source_path(source_path: Path) -> tuple[bool, str]:
    """验证源路径（文件或目录）"""
    if not source_path.exists():
        return False, f"源路径不存在: {source_path}"

    if source_path.is_file():
        if not source_path.suffix.lower() == ".md":
            return False, f"源文件不是 Markdown 文件: {source_path}"
    elif not source_path.is_dir():
        return False, f"源路径既不是文件也不是目录: {source_path}"

    return True, ""


def validate_target_path(target_path: Path) -> tuple[bool, str]:
    """验证目标路径"""
    # 检查目标路径的父目录是否存在
    if not target_path.exists():
        return False, f"目标目录不存在: {target_path}"

    if not target_path.is_dir():
        return False, f"目标路径不是目录: {target_path}"

    return True, ""


def find_md_files_in_directory(directory: Path) -> list[Path]:
    """查找目录中的所有 Markdown 文件"""
    md_files = []

    # 只查找直接子文件，不递归
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".md":
            md_files.append(file_path)

    return sorted(md_files)


def transfer_markdown_file(file_path: Path, verbose: bool = False) -> bool:
    """
    对单个 Markdown 文件执行格式转换
    返回是否进行了修改
    """
    try:
        # 动态导入 transfer 模块
        from transferMD.transfer import transfer_mark

        # 读取原始内容
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()

        # 执行转换
        transfer_mark(str(file_path), verbose=verbose)

        # 检查是否有修改
        with open(file_path, "r", encoding="utf-8") as f:
            new_content = f.read()

        return original_content != new_content

    except Exception as e:
        console.print(f"[yellow]警告: 转换文件 {file_path.name} 时出错: {e}[/yellow]")
        return False


@app.command()
def copy(
    source: str = typer.Argument(..., help="源笔记文件或文件夹路径"),
    target: str = typer.Argument(..., help="目标文件夹路径"),
    rename: Optional[str] = typer.Option(
        None,
        "--rename",
        "-r",
        help="重命名文件（仅当源为单个文件时有效，不包含扩展名）",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="强制覆盖已存在的文件"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="预览操作，不实际执行"),
    no_transfer: bool = typer.Option(
        False, "--no-transfer", help="跳过复制前的 Markdown 格式转换"
    ),
    transfer_verbose: bool = typer.Option(
        False, "--transfer-verbose", help="显示格式转换的详细信息"
    ),
) -> None:
    """
    复制笔记文件和对应的 assets 文件夹到目标位置

    源路径可以是：
    - 单个 Markdown 文件：复制该文件和对应的 assets 文件夹
    - 文件夹：复制文件夹内所有 Markdown 文件和对应的 assets 文件夹

    功能特性：
    - 自动修复 Markdown 格式问题（可用 --no-transfer 跳过）
    - 支持文件重命名（仅单文件模式）
    - 强制覆盖已存在文件
    - 预览模式查看操作

    示例:
        copy_notes copy "/path/to/source/note.md" "/path/to/target/folder"
        copy_notes copy "/path/to/source/note.md" "/path/to/target/folder" --rename "new_name"
        copy_notes copy "/path/to/source/folder" "/path/to/target/folder"
        copy_notes copy "/path/to/source/folder" "/path/to/target/folder" --no-transfer
    """

    # 转换为 Path 对象
    source_path = Path(source).expanduser().resolve()
    target_dir = Path(target).expanduser().resolve()

    # 验证源路径
    valid, error_msg = validate_source_path(source_path)
    if not valid:
        console.print(f"[red]错误: {error_msg}[/red]")
        raise typer.Exit(1)

    # 验证目标路径
    valid, error_msg = validate_target_path(target_dir)
    if not valid:
        console.print(f"[red]错误: {error_msg}[/red]")
        raise typer.Exit(1)

    # 确定要复制的文件列表
    if source_path.is_file():
        # 单个文件模式
        source_files = [source_path]
        if rename and len(source_files) == 1:
            # 只有单个文件时才允许重命名
            pass
        elif rename:
            console.print("[red]错误: 只有在复制单个文件时才能使用 --rename 选项[/red]")
            raise typer.Exit(1)
    else:
        # 文件夹模式
        source_files = find_md_files_in_directory(source_path)
        if not source_files:
            console.print(
                f"[yellow]在源目录中未找到任何 Markdown 文件: {source_path}[/yellow]"
            )
            return

        if rename:
            console.print("[red]错误: 复制文件夹时不能使用 --rename 选项[/red]")
            raise typer.Exit(1)

    # 准备复制操作列表
    copy_operations = []

    for source_file in source_files:
        # 确定目标文件名
        if rename and len(source_files) == 1:
            target_filename = f"{rename}.md"
        else:
            target_filename = source_file.name

        target_file_path = target_dir / target_filename

        # 查找对应的 assets 文件夹
        source_assets = find_assets_folder(source_file)
        target_assets = None
        if source_assets:
            target_note_name = target_file_path.stem
            target_assets = target_dir / f"{target_note_name}.assets"

        copy_operations.append(
            {
                "source_file": source_file,
                "target_file": target_file_path,
                "source_assets": source_assets,
                "target_assets": target_assets,
            }
        )

    # 显示操作概览
    console.print(Panel.fit("📋 操作概览", style="blue"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("序号", style="cyan", width=6)
    table.add_column("类型", style="magenta", width=8)
    table.add_column("源路径", style="green")
    table.add_column("目标路径", style="yellow")
    table.add_column("状态", style="white")

    conflicts = []  # 记录冲突的文件
    row_num = 1

    for operation in copy_operations:
        source_file = operation["source_file"]
        target_file = operation["target_file"]
        source_assets = operation["source_assets"]
        target_assets = operation["target_assets"]

        # 检查文件覆盖状态
        file_status = "新建"
        if target_file.exists():
            file_status = "覆盖" if force else "存在 (需要 --force)"
            if not force:
                conflicts.append(f"目标文件已存在: {target_file}")

        table.add_row(
            str(row_num),
            "笔记",
            str(source_file.name),
            str(target_file.name),
            file_status,
        )
        row_num += 1

        # 处理 assets 文件夹
        if source_assets:
            assets_status = "新建"
            if target_assets and target_assets.exists():
                assets_status = "覆盖" if force else "存在 (需要 --force)"
                if not force:
                    conflicts.append(f"目标 Assets 文件夹已存在: {target_assets}")

            table.add_row(
                str(row_num),
                "Assets",
                str(source_assets.name),
                str(target_assets.name) if target_assets else "无",
                assets_status,
            )
            row_num += 1

    console.print(table)
    console.print(f"\n[blue]总计: {len(copy_operations)} 个笔记文件[/blue]")

    # 检查是否有冲突
    if conflicts:
        console.print(f"\n[red]发现 {len(conflicts)} 个冲突:[/red]")
        for conflict in conflicts[:5]:  # 只显示前5个冲突
            console.print(f"  [red]• {conflict}[/red]")
        if len(conflicts) > 5:
            console.print(f"  [red]... 还有 {len(conflicts) - 5} 个冲突[/red]")
        console.print("[yellow]使用 --force 参数强制覆盖[/yellow]")
        raise typer.Exit(1)

    # 预览模式
    if dry_run:
        console.print("\n[cyan]🔍 预览模式 - 不会实际执行操作[/cyan]")
        return

    # 确认操作
    if not Confirm.ask("\n是否继续执行复制操作?"):
        console.print("[yellow]操作已取消[/yellow]")
        return

    try:
        console.print("\n[green]🚀 开始复制操作...[/green]")

        # 第一步：格式转换（如果启用）
        if not no_transfer:
            console.print("\n[cyan]📝 执行 Markdown 格式转换...[/cyan]")
            transfer_success_count = 0
            transfer_modified_count = 0

            for operation in copy_operations:
                source_file = operation["source_file"]

                try:
                    modified = transfer_markdown_file(
                        source_file, verbose=transfer_verbose
                    )
                    if modified:
                        transfer_modified_count += 1
                        if transfer_verbose:
                            console.print(
                                f"[yellow]📝 已转换: {source_file.name}[/yellow]"
                            )
                    elif transfer_verbose:
                        console.print(f"[dim]✓ 无需转换: {source_file.name}[/dim]")
                    transfer_success_count += 1

                except Exception as e:
                    console.print(
                        f"[yellow]⚠️  转换失败 {source_file.name}: {e}[/yellow]"
                    )

            if transfer_modified_count > 0:
                console.print(
                    f"[green]✅ 格式转换完成: {transfer_modified_count}/{transfer_success_count} 个文件已修复[/green]"
                )
            else:
                console.print("[green]✅ 格式检查完成: 所有文件格式正确[/green]")

        # 第二步：文件复制
        console.print("\n[blue]📁 开始文件复制...[/blue]")
        success_count = 0
        total_operations = len(copy_operations)

        for i, operation in enumerate(copy_operations, 1):
            source_file = operation["source_file"]
            target_file = operation["target_file"]
            source_assets = operation["source_assets"]
            target_assets = operation["target_assets"]

            console.print(
                f"\n[blue]处理第 {i}/{total_operations} 个文件: {source_file.name}[/blue]"
            )

            # 复制笔记文件
            copy_with_progress(
                source_file, target_file, f"复制笔记文件: {source_file.name}"
            )
            console.print(f"[green]✅ 笔记文件复制完成: {target_file.name}[/green]")

            # 复制 assets 文件夹（如果存在）
            if source_assets and target_assets:
                copy_with_progress(
                    source_assets,
                    target_assets,
                    f"复制 Assets 文件夹: {source_assets.name}",
                )
                console.print(
                    f"[green]✅ Assets 文件夹复制完成: {target_assets.name}[/green]"
                )

            success_count += 1

        console.print(
            Panel.fit(
                f"[green]🎉 所有文件复制完成! 成功复制 {success_count}/{total_operations} 个文件[/green]",
                style="green",
            )
        )

    except Exception as e:
        console.print(f"[red]❌ 复制过程中发生错误: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_notes(
    directory: str = typer.Argument(..., help="要扫描的目录路径"),
    recursive: bool = typer.Option(
        True, "--recursive/--no-recursive", "-r", help="递归扫描子目录"
    ),
) -> None:
    """
    列出指定目录下的所有笔记文件
    """

    dir_path = Path(directory).expanduser().resolve()

    if not dir_path.exists() or not dir_path.is_dir():
        console.print(f"[red]错误: 目录不存在或不是有效目录: {dir_path}[/red]")
        raise typer.Exit(1)

    console.print(f"[blue]📁 扫描目录: {dir_path}[/blue]")

    # 查找 Markdown 文件
    pattern = "**/*.md" if recursive else "*.md"
    md_files = list(dir_path.glob(pattern))

    if not md_files:
        console.print("[yellow]未找到任何 Markdown 文件[/yellow]")
        return

    # 显示结果
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("序号", style="cyan", width=6)
    table.add_column("文件名", style="green")
    table.add_column("路径", style="yellow")
    table.add_column("Assets", style="white")

    for i, md_file in enumerate(sorted(md_files), 1):
        assets_folder = find_assets_folder(md_file)
        assets_status = "✅" if assets_folder else "❌"

        # 计算相对路径
        try:
            rel_path = md_file.relative_to(dir_path)
        except ValueError:
            rel_path = md_file

        table.add_row(
            str(i),
            md_file.name,
            str(rel_path.parent) if rel_path.parent != Path(".") else ".",
            assets_status,
        )

    console.print(table)
    console.print(f"\n[green]共找到 {len(md_files)} 个 Markdown 文件[/green]")


if __name__ == "__main__":
    app()
