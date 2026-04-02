import base64
import io
import logging
from typing import Optional

import httpx
from PIL import Image

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):

    def __init__(self, url: str, model: str, timeout: float = 180.0):
        self._url = url
        self._model = model
        self._timeout = timeout
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(base_url=self._url, timeout=self._timeout)
        return self._client

    @staticmethod
    def _image_to_base64(image: Image.Image) -> str:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()

    def _chat(self, prompt: str, images: Optional[list[str]] = None, max_tokens: int = 2048) -> str:
        client = self._get_client()
        message = {"role": "user", "content": prompt}
        if images:
            message["images"] = images

        resp = client.post("/api/chat", json={
            "model": self._model,
            "messages": [message],
            "stream": False,
            "options": {"num_predict": max_tokens},
        })
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()

    def image_inference(self, image: Image.Image, prompt: str, max_tokens: int = 2048) -> str:
        rgb_image = image.convert("RGB") if image.mode != "RGB" else image
        b64 = self._image_to_base64(rgb_image)
        return self._chat(prompt, images=[b64], max_tokens=max_tokens)

    def text_inference(self, text: str, prompt: str, max_tokens: int = 2048) -> str:
        full_prompt = f"{prompt}\n\nContent to analyze:\n{text}"
        return self._chat(full_prompt, max_tokens=max_tokens)

    def warmup(self) -> bool:
        try:
            client = self._get_client()
            resp = client.post("/api/show", json={"model": self._model})
            if resp.status_code == 404:
                logger.info(f"Pulling model {self._model}...")
                pull = client.post(
                    "/api/pull",
                    json={"model": self._model, "stream": False},
                    timeout=600.0,
                )
                pull.raise_for_status()
            logger.info(f"Model {self._model} ready via Ollama")
            return True
        except Exception as e:
            logger.error(f"Ollama warmup failed: {e}")
            return False

    @property
    def name(self) -> str:
        return "Ollama"

    @property
    def model_id(self) -> str:
        return self._model
