import base64
import io
import logging
import time

import httpx
from PIL import Image

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

VISION_FALLBACKS = [
    "google/gemma-3-27b-it:free",
    "google/gemma-3-12b-it:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "google/gemma-3-4b-it:free",
]


class OpenRouterProvider(LLMProvider):

    def __init__(self, api_key: str, model: str = "google/gemma-3-27b-it:free", timeout: float = 180.0):
        if not api_key:
            raise ValueError("OpenRouter API key is required")
        self._api_key = api_key
        self._model_id = model
        self._timeout = timeout
        self._active_model = model

    def _image_to_base64(self, image: Image.Image) -> str:
        buf = io.BytesIO()
        fmt = "PNG" if image.mode == "RGBA" else "JPEG"
        image.save(buf, format=fmt)
        return base64.b64encode(buf.getvalue()).decode()

    def _call(self, messages: list, max_tokens: int, model: str | None = None) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self._active_model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(OPENROUTER_URL, json=payload, headers=headers)
            if resp.status_code == 429:
                raise RateLimitError(resp.text)
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        if content is None:
            raise ValueError("Model returned empty response")
        return content.strip()

    def _call_with_fallback(self, messages: list, max_tokens: int) -> str:
        models = [self._active_model] + [m for m in VISION_FALLBACKS if m != self._active_model]
        last_error = None

        for model in models:
            try:
                result = self._call(messages, max_tokens, model=model)
                if model != self._active_model:
                    logger.info(f"Switched to {model} (primary was rate-limited)")
                    self._active_model = model
                return result
            except RateLimitError as e:
                logger.warning(f"{model} rate-limited, trying next...")
                last_error = e
                continue
            except Exception as e:
                last_error = e
                logger.warning(f"{model} failed: {e}")
                continue

        raise last_error or RuntimeError("All OpenRouter models failed")

    def image_inference(self, image: Image.Image, prompt: str, max_tokens: int = 2048) -> str:
        b64 = self._image_to_base64(image)
        mime = "image/png" if image.mode == "RGBA" else "image/jpeg"
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ],
        }]
        return self._call_with_fallback(messages, max_tokens)

    def text_inference(self, text: str, prompt: str, max_tokens: int = 2048) -> str:
        messages = [{
            "role": "user",
            "content": f"{prompt}\n\nContent to analyze:\n{text}",
        }]
        return self._call_with_fallback(messages, max_tokens)

    def warmup(self) -> bool:
        try:
            messages = [{"role": "user", "content": "ping"}]
            self._call_with_fallback(messages, max_tokens=5)
            logger.info(f"OpenRouter ready (active model: {self._active_model})")
            return True
        except Exception as e:
            logger.error(f"OpenRouter warmup failed: {e}")
            return False

    @property
    def name(self) -> str:
        return "OpenRouter"

    @property
    def model_id(self) -> str:
        return self._active_model


class RateLimitError(Exception):
    pass
