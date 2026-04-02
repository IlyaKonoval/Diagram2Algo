import os
import pytest
from app.config import Settings, LLMProvider


class TestSettings:
    def test_default_provider_is_gemini(self):
        s = Settings(gemini_api_key="test-key")
        assert s.llm_provider == LLMProvider.GEMINI

    def test_default_fallback_is_ollama(self):
        s = Settings(gemini_api_key="test-key")
        assert s.llm_fallback_provider == LLMProvider.OLLAMA

    def test_ollama_defaults(self):
        s = Settings(gemini_api_key="test-key")
        assert s.ollama_url == "http://localhost:11434"
        assert s.ollama_model == "qwen2.5-vl:7b"

    def test_gemini_defaults(self):
        s = Settings(gemini_api_key="test-key")
        assert s.gemini_model == "gemini-2.0-flash"

    def test_inference_defaults(self):
        s = Settings(gemini_api_key="test-key")
        assert s.max_tokens == 2048
        assert s.llm_timeout == 180.0

    def test_ocr_default_enabled(self):
        s = Settings(gemini_api_key="test-key")
        assert s.use_ocr is True

    def test_image_dimension_default(self):
        s = Settings(gemini_api_key="test-key")
        assert s.max_image_dimension == 1024

    def test_log_defaults(self):
        s = Settings(gemini_api_key="test-key")
        assert s.log_level == "INFO"
        assert s.log_json is False

    def test_override_from_kwargs(self):
        s = Settings(
            llm_provider=LLMProvider.OLLAMA,
            max_tokens=4096,
            use_ocr=False,
            gemini_api_key="test",
        )
        assert s.llm_provider == LLMProvider.OLLAMA
        assert s.max_tokens == 4096
        assert s.use_ocr is False
