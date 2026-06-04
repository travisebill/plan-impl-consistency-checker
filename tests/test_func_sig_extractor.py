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


class TestFuncSigExtractorBlindSpots:
    """盲點修復測試：FunctionSigExtractor 只比對函式名"""

    def test_func_sig_key_is_function_name_only(self):
        """extract() 的 key 應只含函式名，不含參數，這樣比對時不因型別差異誤報"""
        extractor = FunctionSigExtractor()
        text = "def upload_file(path: Path, key: str)"
        results = extractor.extract(text, source="plan")
        # key 應該是 "def upload_file"，不是整個 signature
        assert len(results) == 1, f"應抓到 1 個，實際: {len(results)}"
        assert results[0].key == "def upload_file", \
            f"key 應為 'def upload_file'，實際為 '{results[0].key}'"

    def test_func_sig_same_name_different_params_no_warning(self):
        """Plan def foo(x: int), Code def foo(x) → ConsistencyChecker 不應報 warning"""
        from check_plan_impl_consistency import ConsistencyChecker, FunctionSigExtractor
        extractor = FunctionSigExtractor()
        plan_text = "def upload_file(path: Path, key: str)"
        code_text = "def upload_file(local_path, remote_key)"
        plan_keys = extractor.extract(plan_text, source="plan")
        code_keys = extractor.extract(code_text, source="code")
        checker = ConsistencyChecker(plan_keys, code_keys)
        warnings = checker.check()
        assert len(warnings) == 0, \
            f"同函式名不應報 warning，實際: {[w.message for w in warnings]}"

    def test_func_sig_rejects_totally_different_functions(self):
        """Plan def foo, Code def bar → ConsistencyChecker 應報 warning"""
        from check_plan_impl_consistency import ConsistencyChecker
        extractor = FunctionSigExtractor()
        plan_text = "def foo(a, b)"
        code_text = "def bar(x, y)"
        plan_keys = extractor.extract(plan_text, source="plan")
        code_keys = extractor.extract(code_text, source="code")
        checker = ConsistencyChecker(plan_keys, code_keys)
        warnings = checker.check()
        assert len(warnings) == 2, \
            f"不同函式名應各報 1 個 warning，實際: {[w.message for w in warnings]}"
