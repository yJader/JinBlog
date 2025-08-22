import re
import glob
import typer


def transfer_mark(filename, verbose=True):
    with open(filename, "r", encoding="utf-8") as file:
        if file is None:
            print(f"File {filename} is empty or does not exist.")
            return
        content = file.read()

    original_content = content

    # 分类统计不同类型的修改
    changes = {
        "mark_syntax": 0,  # ==text== 高亮语法转换
        "latex_space": 0,  # LaTeX公式空格修复（真正的错误修复）
        "latex_newline": 0,  # LaTeX块之间的换行添加（格式优化）
        "latex_surrounding": 0,  # LaTeX块前后的换行规范化（格式优化）
        "latex_internal": 0,  # LaTeX块内部连续换行规范化（格式优化）
    }

    # 高亮语法: ==text== -> <mark>text</mark>
    new_content, count = re.subn(r"==(.*?)==", r"<mark>\1</mark>", content)
    if new_content != content:
        changes["mark_syntax"] += count
    content = new_content

    # LaTeX公式空格修复: $ text $ -> $text$
    # 暂时还不能处理如text$$LaTeX$$text, LaTeX中有换行符的情况
    # 但是这种不应该出现, 手动修复吧
    temp_content, count = re.subn(r"\$?\$\ ?(.*?)\ ?\$\$?", r"$\1$", content)
    if temp_content != content:
        changes["latex_space"] += count
    content = temp_content

    # LaTeX块间换行优化: $$\n\n$$ -> $$\n\n\n$$
    temp_content, count = re.subn(r"\$\$\n\n\$\$", r"$$\n\n\n$$", content)
    if temp_content != content:
        changes["latex_newline"] += count
    content = temp_content

    # LaTeX块前后换行规范化(在文字和换行后的$$之间再加一个换行符)
    temp_content, count = re.subn(
        r"(\n\n?)(\$\$([\s\S]*?)\$\$)(\n\n?)", r"\n\n\2\n\n", content
    )
    if temp_content != content:
        changes["latex_surrounding"] += count
    content = temp_content

    # LaTeX块内部连续换行规范化
    pattern = r"(\n\n\$\$)([\s\S]*?)(\$\$\n\n)"
    matches = re.finditer(pattern, content)

    changed_content = content
    for match in matches:
        old_text = match.group(0)
        new_text = (
            match.group(1) + re.sub(r"\n+", r"\n", match.group(2)) + match.group(3)
        )
        if old_text != new_text:
            changes["latex_internal"] += 1
            changed_content = changed_content.replace(old_text, new_text, 1)

    content = changed_content

    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

    # 总结修改情况
    if original_content != content:
        if verbose:
            print(f"Transferred file: {filename}")

            # 分类报告
            true_errors = changes["latex_space"]  # 真正的语法错误
            format_optimizations = (
                changes["mark_syntax"]
                + changes["latex_newline"]
                + changes["latex_surrounding"]
                + changes["latex_internal"]
            )  # 格式优化

            print(f"修复了 {true_errors} 处语法错误")
            print(f"进行了 {format_optimizations} 处格式优化")

            # 详细报告
            print("详细修改统计:")
            if changes["mark_syntax"] > 0:
                print(f"  - 高亮语法转换: {changes['mark_syntax']} 处")
            if changes["latex_space"] > 0:
                print(f"  - LaTeX公式空格修复: {changes['latex_space']} 处")
            if changes["latex_newline"] > 0:
                print(f"  - LaTeX块间换行优化: {changes['latex_newline']} 处")
            if changes["latex_surrounding"] > 0:
                print(f"  - LaTeX块前后换行规范化: {changes['latex_surrounding']} 处")
            if changes["latex_internal"] > 0:
                print(f"  - LaTeX块内部换行规范化: {changes['latex_internal']} 处")
        else:
            print(f"✓ {filename}")
    else:
        if verbose:
            print(f"文件 {filename} 没有需要修改的内容")
        else:
            print(f"- {filename}")


def main(
    pattern: str = typer.Argument(
        ..., help="文件名模式，支持 glob 通配符 (例如: '*.md' 或 'docs/*.md')"
    ),
    verbose: bool = typer.Option(
        True, "--verbose/--quiet", "-v/-q", help="是否显示详细输出信息"
    ),
):
    """
    转换 Markdown 文件的格式：\n
    - 将 ==text== 高亮语法转换为 <mark>text</mark> \n
    - 修复 LaTeX 公式中的空格问题 \n
    - 优化 LaTeX 块的换行格式 \n
    """
    filenames = glob.glob(pattern)

    if not filenames:
        typer.echo(f"没有找到匹配模式 '{pattern}' 的文件", err=True)
        raise typer.Exit(1)

    for filename in filenames:
        transfer_mark(filename, verbose=verbose)


if __name__ == "__main__":
    typer.run(main)
