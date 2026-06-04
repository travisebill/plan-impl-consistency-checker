#!/usr/bin/env python3
"""Pre-commit hook 安裝腳本。

在目標專案根目錄執行此腳本，即可在 .git/hooks/pre-commit 寫入鉤子。

使用方式：
    python ~/.openclaw/workspace/skills/plan-impl-consistency-checker/install.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 這個腳本自己的目錄
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="安裝 plan-impl-consistency-checker pre-commit hook")
    parser.add_argument(
        "--project-path",
        type=str,
        default=".",
        help="專案根目錄路徑（默认：目前目錄）",
    )
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()

    if not (project_path / ".git").exists():
        print(f"Error: {project_path} 不是 git 專案（找不到 .git 目錄）", file=sys.stderr)
        sys.exit(1)

    # 匯入並執行 install_hook
    sys.path.insert(0, str(SKILL_DIR))
    from check_plan_impl_consistency import install_hook

    install_hook(project_path, SKILL_DIR)
    print()
    print("已安裝完成。以後每次 git commit 前會自動檢查 plan vs implementation 一致性。")


if __name__ == "__main__":
    main()
