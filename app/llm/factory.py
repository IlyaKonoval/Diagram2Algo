import logging
from typing import Optional

from PIL import Image

from app.config import LLMProvider as ProviderEnum
from app.config import settings
from app.exceptions import LLMProviderError
from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_primary: Optional[LLMProvider] = None
_fallback: Optional[LLMProvider] = None


def _create_provider(provider_type: ProviderEnum) -> LLMProvider:
    if provider_type == ProviderEnum.GEMINI:
        from app.llm.gemini import GeminiProvider
        return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
    elif provider_type == ProviderEnum.OPENROUTER:
        from app.llm.openrouter import OpenRouterProvider
        return OpenRouterProvider(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            timeout=settings.llm_timeout,
        )
    elif provider_type == ProviderEnum.OLLAMA:
        from app.llm.ollama import OllamaProvider
        return OllamaProvider(
            url=settings.ollama_url,
            model=settings.ollama_model,
            timeout=settings.llm_timeout,
        )
    raise ValueError(f"Unknown provider: {provider_type}")


def get_provider() -> LLMProvider:
    global _primary, _fallback
    if _primary is None:
        fallback_type = settings.llm_fallback_provider
        try:
            _primary = _create_provider(settings.llm_provider)
        except Exception as e:
            logger.warning(f"Failed to create {settings.llm_provider.value} provider: {e}")
            if fallback_type and fallback_type != settings.llm_provider:
                logger.info(f"Falling back to {fallback_type.value}")
                _primary = _create_provider(fallback_type)
                fallback_type = None  # no fallback if primary is already the fallback
            else:
                raise
        if fallback_type and fallback_type != settings.llm_provider:
            try:
                _fallback = _create_provider(fallback_type)
            except Exception as e:
                logger.warning(f"Fallback provider {fallback_type.value} unavailable: {e}")
    return _primary


def image_inference(image: Image.Image, prompt: str, max_tokens: int = settings.max_tokens) -> str:
    provider = get_provider()
    try:
        return provider.image_inference(image, prompt, max_tokens)
    except Exception as e:
        if _fallback:
            logger.warning(f"{provider.name} failed: {e}. Trying {_fallback.name}...")
            return _fallback.image_inference(image, prompt, max_tokens)
        raise LLMProviderError(f"{provider.name} inference failed", detail=str(e)) from e


def text_inference(text: str, prompt: str, max_tokens: int = settings.max_tokens) -> str:
    provider = get_provider()
    try:
        return provider.text_inference(text, prompt, max_tokens)
    except Exception as e:
        if _fallback:
            logger.warning(f"{provider.name} failed: {e}. Trying {_fallback.name}...")
            return _fallback.text_inference(text, prompt, max_tokens)
        raise LLMProviderError(f"{provider.name} inference failed", detail=str(e)) from e


def warmup() -> bool:
    provider = get_provider()
    ok = provider.warmup()
    if _fallback:
        _fallback.warmup()
    return ok
