"""Tests for FunctionSigExtractor — Phase 1.4 RED."""
import pytest
from check_plan_impl_consistency import FunctionSigExtractor


class TestFunctionSigExtractorPlan:
    """FunctionSigExtractor 從 plan 文件抽函式簽名。"""

    def test_extracts_def_from_plan(self):
        """Plan 文本含 def upload_file(path: Path, key: str) → 抽出."""
        plan_text = """
        ## L.1.1 函式簽名
        ```python
        def upload_file(path: Path, key: str) -> bool:
        ```
        """
        extractor = FunctionSigExtractor()
        results = extractor.extract(plan_text, source="plan")
        keys = [r.key for r in results]
        assert any("def upload_file" in k for k in keys)


class TestFunctionSigExtractorCode:
    """FunctionSigExtractor 從 code 文件抽函式簽名。"""

    def test_extracts_func_def_from_code(self):
        """Code 文本含 def upload_file(local_path, remote_key, ...) → 抽出."""
        code_text = '''
        def upload_file(local_path, remote_key, bucket=None):
            pass
        '''
        extractor = FunctionSigExtractor()
        results = extractor.extract(code_text, source="code")
        keys = [r.key for r in results]
        assert any("def upload_file" in k for k in keys)

    def test_extracts_async_def_from_code(self):
        """Code 文本含 async def get_prediction → 抽出."""
        code_text = '''
        async def get_prediction(game_id: str) -> dict:
            pass
        '''
        extractor = FunctionSigExtractor()
        results = extractor.extract(code_text, source="code")
        keys = [r.key for r in results]
        assert any("def get_prediction" in k for k in keys)
