"""Tests for ApiPathExtractor — Phase 1.3 RED."""
import pytest
from check_plan_impl_consistency import ApiPathExtractor


class TestApiPathExtractorPlan:
    """ApiPathExtractor 從 plan 文件抽 API path。"""

    def test_extracts_health_endpoint_from_plan(self):
        """Plan 文本含 /api/v1/health → 抽出."""
        plan_text = """
        ## L.0.4 最終確認
        驗證 API: GET /api/v1/health
        """
        extractor = ApiPathExtractor()
        results = extractor.extract(plan_text, source="plan")
        keys = [r.key for r in results]
        assert "/api/v1/health" in keys

    def test_extracts_predictions_endpoint_from_plan(self):
        """Plan 文本含 /api/v1/predictions/{game_id} → 抽出."""
        plan_text = """
        ## L.3.2 預測 API
        GET /api/v1/predictions/{game_id}
        """
        extractor = ApiPathExtractor()
        results = extractor.extract(plan_text, source="plan")
        keys = [r.key for r in results]
        assert '"/api/v1/predictions/{game_id}"' in keys or "/api/v1/predictions/{game_id}" in keys


class TestApiPathExtractorCode:
    """ApiPathExtractor 從 code 文件抽 API path。"""

    def test_extracts_api_path_from_fastapi_decorator(self):
        """Code 文本含 @app.get(\"/api/v1/health\") → 抽出."""
        code_text = '''
        @app.get("/api/v1/health")
        async def health():
            return {"status": "ok"}
        '''
        extractor = ApiPathExtractor()
        results = extractor.extract(code_text, source="code")
        keys = [r.key for r in results]
        assert '"/api/v1/health"' in keys or "/api/v1/health" in keys

    def test_extracts_api_path_with_path_param(self):
        """Code 文本含 /api/v1/predictions/{game_id} → 抽出."""
        code_text = '''
        @router.get("/api/v1/predictions/{game_id}")
        def get_prediction(game_id: str):
            pass
        '''
        extractor = ApiPathExtractor()
        results = extractor.extract(code_text, source="code")
        keys = [r.key for r in results]
        assert any("predictions" in k and "game_id" in k for k in keys)
