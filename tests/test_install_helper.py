"""Tests for InstallHelper (pre-commit hook) — Phase 4 RED."""
import pytest
import os
import tempfile
from pathlib import Path
from check_plan_impl_consistency import install_hook


class TestInstallHook:
    """install_hook 將 pre-commit hook 寫入 .git/hooks/。"""

    def test_writes_pre_commit_hook(self):
        """給專案路徑 → 寫入 .git/hooks/pre-commit。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            git_dir = project / ".git" / "hooks"
            git_dir.mkdir(parents=True)

            skill_dir = Path("/some/fake/skill")
            install_hook(project, skill_dir)

            hook_path = git_dir / "pre-commit"
            assert hook_path.exists()
            content = hook_path.read_text(encoding="utf-8")
            # Hook 包含 skill_dir 和 check_plan_impl_consistency.py
            assert "check_plan_impl_consistency.py" in content
            assert "check_plan_impl_consistency.py" in content

    def test_hook_is_executable(self):
        """hook 寫入後 → chmod 755。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            git_dir = project / ".git" / "hooks"
            git_dir.mkdir(parents=True)

            skill_dir = Path("/some/fake/skill")
            install_hook(project, skill_dir)

            hook_path = git_dir / "pre-commit"
            mode = hook_path.stat().st_mode & 0o777
            assert mode & 0o111  # at least one execute bit

    def test_hook_calls_check_script(self):
        """hook 內容包含 → 呼叫 check_plan_impl_consistency.py。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            git_dir = project / ".git" / "hooks"
            git_dir.mkdir(parents=True)

            skill_dir = Path("/some/skill/path")
            install_hook(project, skill_dir)

            hook_path = git_dir / "pre-commit"
            content = hook_path.read_text(encoding="utf-8")
            # 應該包含 skill_dir 的路徑
            assert str(skill_dir) in content
            assert "check_plan_impl_consistency.py" in content


class TestHookBehavior:
    """Hook 行為測試（shell script）。"""

    def test_hook_script_runs_python_check(self):
        """Hook script 可以執行（syntax valid）。"""
        import subprocess
        # 建立假的 skill 主程式
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            check_script = skill_dir / "check_plan_impl_consistency.py"
            check_script.write_text("import sys; sys.exit(0)", encoding="utf-8")

            project = Path(tmpdir) / "proj"
            project.mkdir()
            git_dir = project / ".git" / "hooks"
            git_dir.mkdir(parents=True)

            install_hook(project, skill_dir)

            hook_path = git_dir / "pre-commit"
            result = subprocess.run(
                ["bash", "-n", str(hook_path)],
                capture_output=True, text=True
            )
            assert result.returncode == 0, f"Bash syntax error: {result.stderr}"
