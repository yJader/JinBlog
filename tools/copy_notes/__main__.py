#!/usr/bin/env python3

"""
笔记复制工具的可执行入口
"""

import sys
from pathlib import Path

# 将脚本目录添加到 Python 路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

# 导入必须在路径设置之后
from copy_notes import app  # noqa: E402

if __name__ == "__main__":
    app()