"""Tests for ErrorCodeExtractor — Phase 1.5 RED."""
import pytest
from check_plan_impl_consistency import ErrorCodeExtractor


class TestErrorCodeExtractorPlan:
    """ErrorCodeExtractor 從 plan 文件抽錯誤碼常量。"""

    def test_extracts_r2_upload_failed_from_plan(self):
        """Plan 文本含 R2_UPLOAD_FAILED → 抽出."""
        plan_text = """
        ## L.1.1 錯誤處理
        錯誤碼：R2_UPLOAD_FAILED, R2_HEAD_FAILED, R2_CREDENTIALS_MISSING
        """
        extractor = ErrorCodeExtractor()
        results = extractor.extract(plan_text, source="plan")
        keys = [r.key for r in results]
        assert "R2_UPLOAD_FAILED" in keys
        assert "R2_HEAD_FAILED" in keys


class TestErrorCodeExtractorCode:
    """ErrorCodeExtractor 從 code 文件抽錯誤碼常量。"""

    def test_extracts_error_constant_from_code(self):
        """Code 文本含 R2_UPLOAD_FAILED → 抽出."""
        code_text = '''
        R2_UPLOAD_FAILED = "R2 upload failed"
        '''
        extractor = ErrorCodeExtractor()
        results = extractor.extract(code_text, source="code")
        keys = [r.key for r in results]
        assert "R2_UPLOAD_FAILED" in keys

    def test_extracts_network_error_from_code(self):
        """Code 文本含 NETWORK_TIMEOUT_ERROR → 抽出."""
        code_text = '''
        except NetworkTimeoutError:
            raise NETWORK_TIMEOUT_ERROR
        '''
        extractor = ErrorCodeExtractor()
        results = extractor.extract(code_text, source="code")
        keys = [r.key for r in results]
        assert "NETWORK_TIMEOUT_ERROR" in keys
