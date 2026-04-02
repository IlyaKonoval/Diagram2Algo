from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    llm_provider: LLMProvider = LLMProvider.GEMINI
    llm_fallback_provider: Optional[LLMProvider] = LLMProvider.OLLAMA

    @field_validator("llm_fallback_provider", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.0-flash-exp:free"

    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-vl:7b"

    max_tokens: int = 2048
    llm_timeout: float = 180.0

    max_image_dimension: int = 1024

    use_ocr: bool = True

    log_level: str = "INFO"
    log_json: bool = False


settings = Settings()

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCS_DIR = PROJECT_ROOT / "docs"
DATASET_PART2 = DOCS_DIR / "Диаграммы. 2 часть" / "Диаграммы. 2 часть"
DATASET_MIXED = DOCS_DIR / "Диаграммы" / "Диаграммы"

PICTURES_DIR = DATASET_PART2 / "Picture"

TEST_DIR = DATASET_PART2 / "test"
GT_FILE = TEST_DIR / "test.txt"

EVAL_OUTPUT_DIR = PROJECT_ROOT / "eval_output"

SAMPLE_FILES = {
    "PNG": PICTURES_DIR / "1.png",
    "JPG": DATASET_MIXED / "Телеграм_Диаграммы 2" / "uml" / "class.jpg",
    "DrawIO": DATASET_MIXED / "Notion_Диаграммы" / "BPMN" / "bpmn.drawio",
    "BPMN": DATASET_MIXED / "БиблиотечныйСервис_Диаграммы" / "BPMN" / "Process_Booking.bpmn",
    "SVG": DATASET_MIXED / "АналогUber_Диаграммы" / "C4_Architecture" / "Context.svg",
}
