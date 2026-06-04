"""Tests for ConsistencyChecker — Phase 2 RED."""
import pytest
from check_plan_impl_consistency import (
    ConsistencyChecker,
    ConsistencyWarning,
    IgnoreEntry,
    KeywordMatch,
)


class TestConsistencyCheckerBasic:
    """基本比對邏輯。"""

    def test_detects_r2_key_mismatch(self):
        """Plan: gamelogs/{date}.jsonl.gz, Code: gamelogs/cpbl_full_{date}.json → 1 mismatch."""
        plan_keys = [
            KeywordMatch(key="gamelogs/{date}.jsonl.gz", line_no=10, source="plan"),
        ]
        code_keys = [
            KeywordMatch(key="gamelogs/cpbl_full_{date}.json", line_no=20, source="code"),
        ]
        checker = ConsistencyChecker(plan_keys, code_keys)
        warnings = checker.check()
        assert len(warnings) == 2  # plan→code 1, code→plan 1

    def test_no_warnings_when_keys_match(self):
        """Plan 和 Code 有相同的 key → 0 warnings."""
        plan_keys = [
            KeywordMatch(key="gamelogs/{date}.jsonl.gz", line_no=10, source="plan"),
        ]
        code_keys = [
            KeywordMatch(key="gamelogs/{date}.jsonl.gz", line_no=20, source="code"),
        ]
        checker = ConsistencyChecker(plan_keys, code_keys)
        warnings = checker.check()
        assert len(warnings) == 0

    def test_multiple_mismatches(self):
        """多個 key 差異 → 多個 warnings。"""
        plan_keys = [
            KeywordMatch(key="R2_ACCOUNT_ID", line_no=1, source="plan"),
            KeywordMatch(key="gamelogs/{date}.jsonl.gz", line_no=2, source="plan"),
        ]
        code_keys = [
            KeywordMatch(key="R2_ACCESS_KEY_ID", line_no=3, source="code"),
            KeywordMatch(key="gamelogs/cpbl_full_{date}.json", line_no=4, source="code"),
        ]
        checker = ConsistencyChecker(plan_keys, code_keys)
        warnings = checker.check()
        assert len(warnings) == 4


class TestConsistencyCheckerIgnore:
    """豁免機制。"""

    def test_ignored_key_no_warning(self):
        """ignore 清單有的 key → 不產生 warning。"""
        plan_keys = [
            KeywordMatch(key="gamelogs/cpbl_full_{date}.json", line_no=10, source="plan"),
        ]
        code_keys = [
            KeywordMatch(key="gamelogs/cpbl_full_{date}.json", line_no=20, source="code"),
        ]
        ignore_entries = [
            IgnoreEntry(key="gamelogs/cpbl_full_{date}.json", reason="known diff", expires="never"),
        ]
        checker = ConsistencyChecker(plan_keys, code_keys, ignore_entries=ignore_entries)
        warnings = checker.check()
        assert len(warnings) == 0

    def test_unignored_key_still_warns(self):
        """ignore 清單只有部分 key → 其他仍 warn。"""
        plan_keys = [
            KeywordMatch(key="gamelogs/cpbl_full_{date}.json", line_no=10, source="plan"),
            KeywordMatch(key="R2_ACCOUNT_ID", line_no=11, source="plan"),
        ]
        code_keys = [
            KeywordMatch(key="gamelogs/cpbl_full_{date}.json", line_no=20, source="code"),
            KeywordMatch(key="R2_ACCESS_KEY_ID", line_no=21, source="code"),
        ]
        ignore_entries = [
            IgnoreEntry(key="gamelogs/cpbl_full_{date}.json", reason="known diff", expires="never"),
        ]
        checker = ConsistencyChecker(plan_keys, code_keys, ignore_entries=ignore_entries)
        warnings = checker.check()
        assert len(warnings) == 2  # R2_ACCOUNT_ID and R2_ACCESS_KEY_ID


class TestConsistencyCheckerReport:
    """報告產出。"""

    def test_report_contains_plan_mention(self):
        """報告包含「Plan mentions X but not in code」訊息。"""
        plan_keys = [
            KeywordMatch(key="gamelogs/{date}.jsonl.gz", line_no=10, source="plan"),
        ]
        code_keys = []  # code 沒有這個 key
        checker = ConsistencyChecker(plan_keys, code_keys)
        checker.check()
        report = checker.get_report()
        assert "Plan" in report or "gamelogs" in report

    def test_report_contains_code_usage(self):
        """報告包含「Code uses Y but not in plan」訊息。"""
        plan_keys = []  # plan 沒有
        code_keys = [
            KeywordMatch(key="gamelogs/cpbl_full_{date}.json", line_no=20, source="code"),
        ]
        checker = ConsistencyChecker(plan_keys, code_keys)
        checker.check()
        report = checker.get_report()
        assert "Code" in report or "gamelogs" in report

    def test_report_no_warnings(self):
        """0 warnings → 報告顯示「一致」或「0 warnings」。"""
        plan_keys = [
            KeywordMatch(key="R2_ACCOUNT_ID", line_no=1, source="plan"),
        ]
        code_keys = [
            KeywordMatch(key="R2_ACCOUNT_ID", line_no=2, source="code"),
        ]
        checker = ConsistencyChecker(plan_keys, code_keys)
        checker.check()
        report = checker.get_report()
        assert "0" in report or "一致" in report or "✅" in report
