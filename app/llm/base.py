from abc import ABC, abstractmethod

from PIL import Image


class LLMProvider(ABC):

    @abstractmethod
    def image_inference(self, image: Image.Image, prompt: str, max_tokens: int = 2048) -> str: ...

    @abstractmethod
    def text_inference(self, text: str, prompt: str, max_tokens: int = 2048) -> str: ...

    @abstractmethod
    def warmup(self) -> bool: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def model_id(self) -> str: ...
