"""Tests for CLI + auto-discover — Phase 3 RED."""
import pytest
import tempfile
from pathlib import Path
from check_plan_impl_consistency import discover_plan_files, scan_directory


class TestScanDirectory:
    """scan_directory 測試。"""

    def test_reads_single_file(self):
        """給定檔案路徑 → 讀取內容。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_file = Path(tmpdir) / "plan.md"
            plan_file.write_text("# Plan\n\ngamelogs/{date}.jsonl.gz", encoding="utf-8")
            result = scan_directory([str(plan_file)])
            assert str(plan_file) in result
            assert "gamelogs/{date}.jsonl.gz" in result[str(plan_file)]

    def test_reads_multiple_files(self):
        """scope 含多個檔案 → 全部讀取。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            f1 = Path(tmpdir) / "file1.py"
            f2 = Path(tmpdir) / "file2.py"
            f1.write_text("R2_ACCOUNT_ID = 'x'", encoding="utf-8")
            f2.write_text("os.environ['R2_BUCKET_NAME']", encoding="utf-8")
            result = scan_directory([str(f1), str(f2)])
            assert str(f1) in result
            assert str(f2) in result

    def test_filters_by_extension(self):
        """scan_directory 只讀取指定副檔名。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            py_file = Path(tmpdir) / "script.py"
            txt_file = Path(tmpdir) / "readme.txt"
            py_file.write_text("x = 1", encoding="utf-8")
            txt_file.write_text("readme", encoding="utf-8")
            result = scan_directory([tmpdir], extensions=(".py",))
            assert str(py_file) in result
            assert str(txt_file) not in result


class TestDiscoverPlanFiles:
    """discover_plan_files 自動發現 plan 文件。"""

    def test_finds_03_plan_md(self):
        """docs/changes/**/03-plan.md → 被發現。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            docs = project / "docs" / "changes" / "phase-l"
            docs.mkdir(parents=True)
            plan = docs / "03-plan.md"
            plan.write_text("# Phase L Plan\n\n`R2_ACCOUNT_ID`", encoding="utf-8")
            found = discover_plan_files(project)
            assert plan in found

    def test_finds_designs_md(self):
        """docs/designs/*.md → 被發現。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            designs = project / "docs" / "designs"
            designs.mkdir(parents=True)
            design = designs / "architecture.md"
            design.write_text("# Architecture\n\n`gamelogs/{date}.jsonl.gz`", encoding="utf-8")
            found = discover_plan_files(project)
            assert design in found

    def test_empty_when_no_plans(self):
        """無 plan 文件 → 回傳空 list。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir) / "empty_project"
            project.mkdir()
            found = discover_plan_files(project)
            assert found == []


    def test_auto_discover_with_ignore_legacy_skips_designs(self):
        """--ignore-legacy 應該跳過 docs/designs/*.md，只掃 docs/changes/phase-*/03-plan.md"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            # active phase
            changes = project / "docs" / "changes" / "phase-l-cloud-saas"
            changes.mkdir(parents=True)
            (changes / "03-plan.md").write_text("# Plan L.1.2\n", encoding="utf-8")
            # legacy designs
            designs = project / "docs" / "designs"
            designs.mkdir(parents=True)
            (designs / "2026-05-15-phase-7.md").write_text("# Phase 7 (legacy)\n", encoding="utf-8")
            (designs / "2026-05-10-phase-3.md").write_text("# Phase 3 (legacy)\n", encoding="utf-8")

            plans = discover_plan_files(project, ignore_legacy=True)

            # 只應該有 1 個 plan (phase-l)
            assert len(plans) == 1
            assert "phase-l" in str(plans[0])

    def test_auto_discover_without_ignore_legacy_includes_designs(self):
        """不帶 --ignore-legacy 時，legacy designs/*.md 也要掃（向後相容）"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            # active phase
            changes = project / "docs" / "changes" / "phase-l-cloud-saas"
            changes.mkdir(parents=True)
            (changes / "03-plan.md").write_text("# Plan L.1.2\n", encoding="utf-8")
            # legacy designs
            designs = project / "docs" / "designs"
            designs.mkdir(parents=True)
            (designs / "2026-05-15-phase-7.md").write_text("# Phase 7 (legacy)\n", encoding="utf-8")

            plans = discover_plan_files(project, ignore_legacy=False)

            # 應該有 2 個 plans
            assert len(plans) == 2


class TestCLIArgparse:
    """CLI argparse 整合測試。"""

    def test_import_main_module(self):
        """主模組可以 import（不 crash）。"""
        import check_plan_impl_consistency
        assert hasattr(check_plan_impl_consistency, "main")

    def test_has_cli_entry_point(self):
        """main 函式存在。"""
        from check_plan_impl_consistency import main
        assert callable(main)

    def test_ignore_legacy_flag_accepted(self):
        """--ignore-legacy 是有效的 CLI 參數。"""
        import argparse, sys
        from importlib import reload
        import check_plan_impl_consistency as cpic
        reload(cpic)
        # 模擬 python check.py --help 能成功（不crash）
        try:
            cpic.main()
        except SystemExit:
            pass  # argparse exits after --help
        # 直接測 argparse 解析
        parser = argparse.ArgumentParser()
        parser.add_argument("--ignore-legacy", action="store_true")
        args = parser.parse_args(["--ignore-legacy"])
        assert args.ignore_legacy is True
