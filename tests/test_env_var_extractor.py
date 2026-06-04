"""Tests for EnvVarExtractor — Phase 1.2 RED."""
import pytest
from check_plan_impl_consistency import EnvVarExtractor


class TestEnvVarExtractorPlan:
    """EnvVarExtractor 從 plan 文件抽環境變數名稱。"""

    def test_extracts_r2_account_id_from_plan(self):
        """Plan 文本含 `R2_ACCOUNT_ID` → 抽出."""
        plan_text = """
        ## L.1.1 R2 上傳 client
        環境變數：R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY
        """
        extractor = EnvVarExtractor()
        results = extractor.extract(plan_text, source="plan")
        keys = [r.key for r in results]
        assert "R2_ACCOUNT_ID" in keys
        assert "R2_ACCESS_KEY_ID" in keys

    def test_extracts_database_url_from_plan(self):
        """Plan 文本含 `DATABASE_URL` → 抽出."""
        plan_text = """
        ## L.1.4 Supabase 直寫
        需設定：DATABASE_URL, SUPABASE_SERVICE_ROLE_KEY
        """
        extractor = EnvVarExtractor()
        results = extractor.extract(plan_text, source="plan")
        keys = [r.key for r in results]
        assert "DATABASE_URL" in keys


class TestEnvVarExtractorCode:
    """EnvVarExtractor 從 code 文件抽環境變數名稱。"""

    def test_extracts_os_environ_from_code(self):
        """Code 文本含 os.environ[\"R2_BUCKET_NAME\"] → 抽出."""
        code_text = '''
        bucket = os.environ["R2_BUCKET_NAME"]
        '''
        extractor = EnvVarExtractor()
        results = extractor.extract(code_text, source="code")
        keys = [r.key for r in results]
        assert "R2_BUCKET_NAME" in keys

    def test_extracts_os_getenv_from_code(self):
        """Code 文本含 os.getenv(\"DATABASE_URL\") → 抽出."""
        code_text = '''
        url = os.getenv("DATABASE_URL")
        '''
        extractor = EnvVarExtractor()
        results = extractor.extract(code_text, source="code")
        keys = [r.key for r in results]
        assert "DATABASE_URL" in keys
