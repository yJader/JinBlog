import os
import re
import typer
import shutil
from pathlib import Path
from typing import Optional


def extract_image_references(md_content):
    """从Markdown内容中提取所有图片引用（包括Markdown语法和HTML语法）"""
    # 提取Markdown风格引用: ![alt text](path/to/image.png)
    md_pattern = r"!\[.*?\]\((.*?)\)"
    md_refs = re.findall(md_pattern, md_content)

    # 提取HTML风格引用: <img src="path/to/image.png" ... />
    html_pattern = r'<img[^>]*src=[\'"]([^\'"]*)[\'"]'
    html_refs = re.findall(html_pattern, md_content)

    # 合并所有引用
    all_refs = md_refs + html_refs

    # 提取文件名（不带路径）
    image_filenames = []
    for ref in all_refs:
        # 处理相对路径，获取文件名
        filename = os.path.basename(ref)
        if filename:
            image_filenames.append(filename)

    return image_filenames


def clean_assets_folder(md_file_path: str, dry_run: bool = False, delete: bool = False):
    """清理未被引用的图片文件"""
    md_file = Path(md_file_path)

    # 检查MD文件是否存在
    if not md_file.exists():
        typer.echo(f"错误: {md_file} 不存在")
        raise typer.Exit(code=1)

    # 构建对应的assets文件夹路径
    assets_folder = md_file.parent / f"{md_file.stem}.assets"

    # 检查assets文件夹是否存在
    if not assets_folder.exists() or not assets_folder.is_dir():
        typer.echo(f"警告: 找不到对应的资源文件夹 {assets_folder}")
        return

    # 读取MD文件内容
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    # 提取所有图片引用
    referenced_images = set(extract_image_references(md_content))
    typer.echo(f"在 {md_file.name} 中发现 {len(referenced_images)} 个图片引用")

    # 获取assets文件夹中的所有图片文件
    asset_files = []
    for file in assets_folder.iterdir():
        if file.is_file() and file.suffix.lower() in [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".svg",
            ".webp",
        ]:
            asset_files.append(file)

    typer.echo(f"在 {assets_folder} 中发现 {len(asset_files)} 个图片文件")

    # 找出未被引用的图片
    unreferenced_files = []
    for asset_file in asset_files:
        if asset_file.name not in referenced_images:
            unreferenced_files.append(asset_file)

    # 处理未引用的图片
    if unreferenced_files:
        typer.echo(f"找到 {len(unreferenced_files)} 个未被引用的图片文件:")

        # 创建备份文件夹
        backup_folder = None
        if not dry_run and not delete:
            backup_folder = assets_folder.parent / f"{assets_folder.name}_backup"
            backup_folder.mkdir(exist_ok=True)

        # 处理每个未引用的文件
        for file in unreferenced_files:
            typer.echo(f"  - {file.name}")

            if not dry_run:
                if delete:
                    # 直接删除文件
                    os.remove(file)
                    typer.echo(f"    已删除: {file.name}")
                else:
                    # 移动到备份文件夹
                    shutil.move(str(file), str(backup_folder / file.name))
                    typer.echo(f"    已移动到备份: {backup_folder / file.name}")

        if not dry_run:
            if delete:
                typer.echo(f"已删除 {len(unreferenced_files)} 个未引用的图片文件")
            else:
                typer.echo(f"已将未引用的图片文件移动到备份文件夹: {backup_folder}")
    else:
        typer.echo("没有找到未被引用的图片文件")


def move_external_assets(md_file_path: str, dry_run: bool = False):
    """将引用到的外部assets文件夹中的图片移动到对应的assets文件夹"""
    md_file = Path(md_file_path)

    # 检查MD文件是否存在
    if not md_file.exists():
        typer.echo(f"错误: {md_file} 不存在")
        raise typer.Exit(code=1)

    # 构建对应的assets文件夹路径
    own_assets_folder = md_file.parent / f"{md_file.stem}.assets"

    # 确保assets文件夹存在
    if not own_assets_folder.exists():
        if not dry_run:
            own_assets_folder.mkdir(exist_ok=True)
            typer.echo(f"创建资源文件夹: {own_assets_folder}")
        else:
            typer.echo(f"将创建资源文件夹: {own_assets_folder}")

    # 读取MD文件内容
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    # 提取所有图片引用（带完整路径）
    md_pattern = r"!\[.*?\]\((.*?)\)"
    md_refs = re.findall(md_pattern, md_content)

    html_pattern = r'<img[^>]*src=[\'"]([^\'"]*)[\'"]'
    html_refs = re.findall(html_pattern, md_content)

    all_refs = md_refs + html_refs

    # 识别外部assets文件夹中的图片
    external_assets = []

    for ref in all_refs:
        # 跳过以"./"开头的引用路径
        if ref.startswith(f"./{md_file.stem}.assets"):
            print(f"跳过引用: {ref}")
            continue

        # 如果是外部assets文件夹中的图片
        if ".assets/" in ref and not ref.startswith(f"{md_file.stem}.assets/"):
            # 确保路径是相对于Markdown文件的
            ref_path = Path(ref)
            if not ref_path.is_absolute():
                ref_path = md_file.parent / ref_path

            external_assets.append((ref, ref_path))

    if not external_assets:
        typer.echo(f"在{md_file.name}中没有找到需要移动的外部assets图片引用")
        return

    typer.echo(
        f"在{md_file.name}中找到{len(external_assets)}个外部assets文件夹中的图片引用:"
    )

    # 处理每个外部资源
    updated_content = md_content
    for original_ref, ref_path in external_assets:
        if ref_path.exists():
            # 生成新的文件名和路径
            new_filename = ref_path.name
            new_path = own_assets_folder / new_filename
            relative_new_path = f"{md_file.stem}.assets/{new_filename}"

            typer.echo(f"  - {original_ref} -> {relative_new_path}")

            # 复制文件并更新引用
            if not dry_run:
                # 处理命名冲突
                if new_path.exists():
                    base = new_path.stem
                    suffix = new_path.suffix
                    i = 1
                    while new_path.exists():
                        new_filename = f"{base}_{i}{suffix}"
                        new_path = own_assets_folder / new_filename
                        relative_new_path = f"{md_file.stem}.assets/{new_filename}"
                        i += 1

                # 复制文件
                shutil.copy2(ref_path, new_path)
                typer.echo(f"    已复制: {ref_path.name} -> {new_path}")

                # 精确替换引用路径，确保只替换图片引用中的路径部分
                # 针对Markdown语法
                md_pattern = f"!\\[.*?\\]\\({re.escape(original_ref)}\\)"
                updated_content = re.sub(
                    md_pattern,
                    lambda m: m.group().replace(original_ref, relative_new_path),
                    updated_content,
                )

                # 针对HTML语法
                html_pattern = f"<img[^>]*src=['\"]({re.escape(original_ref)})['\"]"
                updated_content = re.sub(
                    html_pattern,
                    lambda m: m.group().replace(original_ref, relative_new_path),
                    updated_content,
                )
        else:
            typer.echo(f"  - 警告: {ref_path} 不存在")

    # 保存更新后的内容
    if not dry_run and md_content != updated_content:
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(updated_content)
        typer.echo(f"已更新 {md_file.name} 中的图片引用")


app = typer.Typer(help="清理Markdown文件中未引用的图片资源")


@app.command()
def clean(
    md_file: str = typer.Argument(..., help="Markdown文件路径"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="仅显示将要处理的文件，不实际操作"
    ),
    delete: bool = typer.Option(
        False, "--delete", "-D", help="直接删除未引用的文件，而不是移动到备份文件夹"
    ),
):
    """清理Markdown文件中未引用的图片资源, 并移动到备份文件夹"""
    clean_assets_folder(md_file, dry_run, delete)


@app.command()
def move(
    md_file: str = typer.Argument(..., help="Markdown文件路径"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="仅显示将要处理的文件，不实际操作"
    ),
):
    """将Markdown引用的外部assets文件夹中的图片移动到对应的assets文件夹"""
    move_external_assets(md_file, dry_run)


# 保持向后兼容的main命令
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Markdown图片资源管理工具"""
    if ctx.invoked_subcommand is None:
        typer.echo("请使用子命令: clean 或 move")
        typer.echo("使用 --help 查看更多信息")


if __name__ == "__main__":
    app()
