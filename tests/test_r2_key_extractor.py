"""Tests for R2KeyExtractor — Phase 1.1 RED."""
import pytest
from check_plan_impl_consistency import R2KeyExtractor


class TestR2KeyExtractorPlan:
    """R2KeyExtractor 從 plan 文件抽 R2 key patterns."""

    def test_extracts_gamelogs_datestring_from_plan(self):
        """Plan 文本含 gamelogs/{season}/{date}.jsonl.gz → 抽出該 key."""
        plan_text = """
        ## L.1.2 上傳路徑
        上傳至 R2: gamelogs/{season}/{date}.jsonl.gz
        """
        extractor = R2KeyExtractor()
        results = extractor.extract(plan_text, source="plan")
        keys = [r.key for r in results]
        assert "gamelogs/{season}/{date}.jsonl.gz" in keys

    def test_extracts_cpbl_full_datestring_from_plan(self):
        """Plan 文本含 gamelogs/cpbl_full_{date}.json → 抽出."""
        plan_text = """
        ## L.1.2 R2 key
        remote_key = f"gamelogs/cpbl_full_{date}.json"
        """
        extractor = R2KeyExtractor()
        results = extractor.extract(plan_text, source="plan")
        keys = [r.key for r in results]
        assert "gamelogs/cpbl_full_{date}.json" in keys


class TestR2KeyExtractorCode:
    """R2KeyExtractor 從 code 文件抽 R2 key patterns."""

    def test_extracts_fstring_r2_key_from_code(self):
        """Code 文本含 f\"gamelogs/cpbl_full_{date_str}.json\" → 抽出."""
        code_text = '''
        remote_key = f"gamelogs/cpbl_full_{date_str}.json"
        '''
        extractor = R2KeyExtractor()
        results = extractor.extract(code_text, source="code")
        keys = [r.key for r in results]
        assert any("gamelogs/cpbl_full" in k for k in keys)

    def test_extracts_plain_r2_key_from_code(self):
        """Code 文本含 remote_key = \"gamelogs/{date}.jsonl.gz\" → 抽出."""
        code_text = '''
        remote_key = "gamelogs/{date}.jsonl.gz"
        '''
        extractor = R2KeyExtractor()
        results = extractor.extract(code_text, source="code")
        keys = [r.key for r in results]
        assert "gamelogs/{date}.jsonl.gz" in keys
