import logging

from PIL import Image

from app.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model_id = model

    def image_inference(self, image: Image.Image, prompt: str, max_tokens: int = 2048) -> str:
        from google.genai import types

        response = self._client.models.generate_content(
            model=self._model_id,
            contents=[prompt, image],
            config=types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
        return response.text.strip()

    def text_inference(self, text: str, prompt: str, max_tokens: int = 2048) -> str:
        from google.genai import types

        full_prompt = f"{prompt}\n\nContent to analyze:\n{text}"
        response = self._client.models.generate_content(
            model=self._model_id,
            contents=full_prompt,
            config=types.GenerateContentConfig(max_output_tokens=max_tokens),
        )
        return response.text.strip()

    def warmup(self) -> bool:
        try:
            self._client.models.generate_content(
                model=self._model_id,
                contents="ping",
                config={"max_output_tokens": 5},
            )
            logger.info(f"Gemini model {self._model_id} ready")
            return True
        except Exception as e:
            logger.error(f"Gemini warmup failed: {e}")
            return False

    @property
    def name(self) -> str:
        return "Google Gemini"

    @property
    def model_id(self) -> str:
        return self._model_id
