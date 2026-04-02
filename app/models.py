from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class FileType(str, Enum):
    IMAGE = "image"
    SVG = "svg"
    PDF = "pdf"
    DRAWIO = "drawio"
    BPMN = "bpmn"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"


class DiagramStep(BaseModel):
    number: int = Field(...)
    actor: Optional[str] = Field(None)
    action: str = Field(...)
    target: Optional[str] = Field(None)
    note: Optional[str] = Field(None)


class ExtractionResult(BaseModel):
    source_file: str = Field(...)
    page_or_slide: Optional[int] = Field(None)
    diagram_type: Optional[str] = Field(None)
    steps: list[DiagramStep] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    error: Optional[str] = Field(None)


class FileInput(BaseModel):
    path: Path = Field(...)
    file_type: FileType = Field(...)
    parent_archive: Optional[str] = Field(None)


class BatchResult(BaseModel):
    total_files: int = Field(...)
    successful: int = Field(...)
    failed: int = Field(...)
    results: list[ExtractionResult] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    steps: list[DiagramStep] = Field(...)
    diagram_type: str = Field("sequence")
    title: Optional[str] = Field(None)


class GenerateResponse(BaseModel):
    plantuml_code: str = Field(...)
    png_base64: Optional[str] = Field(None)
    error: Optional[str] = Field(None)
