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


class TestR2KeyExtractorBlindSpots:
    """盲點修復測試：R2KeyExtractor 過寬鬆"""

    def test_r2_key_rejects_api_path(self):
        """R2 key 白名單前綴：/api/v1/health 不是 R2 key，應被排除"""
        extractor = R2KeyExtractor()
        text = "API endpoint: /api/v1/health"
        results = extractor.extract(text, source="plan")
        keys = [r.key for r in results]
        assert "/api/v1/health" not in keys, f"/api/v1/health 不應被當 R2 key，實際抓到: {keys}"

    def test_r2_key_rejects_player_account(self):
        """R2 key 白名單前綴：/players/DUBA01 不是 R2 key，應被排除"""
        extractor = R2KeyExtractor()
        text = "Player account: /players/DUBA01"
        results = extractor.extract(text, source="plan")
        keys = [r.key for r in results]
        assert "/players/DUBA01" not in keys, f"/players/DUBA01 不應被當 R2 key，實際抓到: {keys}"

    def test_r2_key_rejects_conceptual_text(self):
        """R2 key 白名單前綴：/Read/Write、DELETE/TRUNCATE 等敘述不應被當 R2 key"""
        extractor = R2KeyExtractor()
        text = "Operations: Read/Write, DELETE/TRUNCATE"
        results = extractor.extract(text, source="plan")
        keys = [r.key for r in results]
        # Read/Write 這種不應被識別為 R2 key
        for key in keys:
            assert " " not in key, f"'{key}' 含空白不應為 R2 key"
            first_segment = key.split("/")[0]
            valid_prefixes = {"gamelogs", "pbp", "models", "odds", "advanced", "splits", "weather"}
            assert first_segment in valid_prefixes or key.startswith("gamelogs"), \
                f"'{key}' 不是有效 R2 key"

    def test_r2_key_accepts_valid_prefix_gamelogs(self):
        """gamelogs/ 前綴要接受"""
        extractor = R2KeyExtractor()
        text = "Path: gamelogs/cpbl_full_2026-06-04.json"
        results = extractor.extract(text, source="plan")
        keys = [r.key for r in results]
        assert any("gamelogs/cpbl_full_2026-06-04.json" in k for k in keys), \
            f"gamelogs/ 前綴 R2 key 應被接受，實際抓到: {keys}"

    def test_r2_key_accepts_valid_prefix_pbp(self):
        """pbp/ 前綴要接受"""
        extractor = R2KeyExtractor()
        text = "Path: pbp/games_2026.jsonl.gz"
        results = extractor.extract(text, source="plan")
        keys = [r.key for r in results]
        assert any("pbp/games_2026.jsonl.gz" in k for k in keys), \
            f"pbp/ 前綴 R2 key 應被接受，實際抓到: {keys}"

    def test_r2_key_accepts_valid_prefix_models(self):
        """models/ 前綴要接受"""
        extractor = R2KeyExtractor()
        text = "Model path: models/prophet_v1.pkl"
        results = extractor.extract(text, source="plan")
        keys = [r.key for r in results]
        assert any("models/prophet_v1.pkl" in k for k in keys), \
            f"models/ 前綴 R2 key 應被接受，實際抓到: {keys}"
