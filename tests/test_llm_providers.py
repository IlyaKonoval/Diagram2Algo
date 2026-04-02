
import pytest
from PIL import Image

from app.llm.base import LLMProvider as BaseLLMProvider


class MockProvider(BaseLLMProvider):

    def __init__(self, response: str = "mock response", should_fail: bool = False):
        self._response = response
        self._should_fail = should_fail

    def image_inference(self, image, prompt, max_tokens=2048):
        if self._should_fail:
            raise ConnectionError("Provider unavailable")
        return self._response

    def text_inference(self, text, prompt, max_tokens=2048):
        if self._should_fail:
            raise ConnectionError("Provider unavailable")
        return self._response

    def warmup(self):
        return not self._should_fail

    @property
    def name(self):
        return "MockProvider"

    @property
    def model_id(self):
        return "mock-model-1.0"


class TestLLMProviderInterface:
    def test_image_inference(self):
        provider = MockProvider(response='{"steps": []}')
        img = Image.new("RGB", (100, 100))
        result = provider.image_inference(img, "extract steps")
        assert result == '{"steps": []}'

    def test_text_inference(self):
        provider = MockProvider(response='{"steps": []}')
        result = provider.text_inference("A -> B", "extract steps")
        assert result == '{"steps": []}'

    def test_warmup_success(self):
        provider = MockProvider()
        assert provider.warmup() is True

    def test_warmup_failure(self):
        provider = MockProvider(should_fail=True)
        assert provider.warmup() is False

    def test_name_property(self):
        provider = MockProvider()
        assert provider.name == "MockProvider"

    def test_model_id_property(self):
        provider = MockProvider()
        assert provider.model_id == "mock-model-1.0"

    def test_failed_inference_raises(self):
        provider = MockProvider(should_fail=True)
        img = Image.new("RGB", (100, 100))
        with pytest.raises(ConnectionError):
            provider.image_inference(img, "test")


class TestFactoryFallback:
    def test_fallback_on_primary_failure(self):
        import app.llm.factory as factory

        factory._primary = None
        factory._fallback = None

        primary = MockProvider(should_fail=True)
        fallback = MockProvider(response="fallback result")

        factory._primary = primary
        factory._fallback = fallback

        img = Image.new("RGB", (100, 100))
        result = factory.image_inference(img, "test", max_tokens=100)
        assert result == "fallback result"

    def test_no_fallback_raises(self):
        import app.llm.factory as factory

        factory._primary = MockProvider(should_fail=True)
        factory._fallback = None

        img = Image.new("RGB", (100, 100))
        with pytest.raises(Exception):
            factory.image_inference(img, "test", max_tokens=100)


class TestOllamaProvider:
    def test_init_stores_params(self):
        from app.llm.ollama import OllamaProvider
        provider = OllamaProvider(url="http://test:11434", model="test-model", timeout=60.0)
        assert provider.name == "Ollama"
        assert provider.model_id == "test-model"

    def test_image_to_base64(self):
        from app.llm.ollama import OllamaProvider
        img = Image.new("RGB", (10, 10), (255, 0, 0))
        b64 = OllamaProvider._image_to_base64(img)
        assert isinstance(b64, str)
        assert len(b64) > 0
