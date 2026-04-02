import logging
from pathlib import Path
from typing import Union

from app.models import FileType

logger = logging.getLogger(__name__)

EXTENSION_MAP = {
    ".png": FileType.IMAGE,
    ".jpg": FileType.IMAGE,
    ".jpeg": FileType.IMAGE,
    ".gif": FileType.IMAGE,
    ".bmp": FileType.IMAGE,
    ".webp": FileType.IMAGE,
    ".tiff": FileType.IMAGE,
    ".tif": FileType.IMAGE,

    ".svg": FileType.SVG,

    ".pdf": FileType.PDF,

    ".drawio": FileType.DRAWIO,
    ".dio": FileType.DRAWIO,
    ".xml": FileType.DRAWIO,

    ".bpmn": FileType.BPMN,

    ".zip": FileType.ARCHIVE,
    ".rar": FileType.ARCHIVE,
    ".7z": FileType.ARCHIVE,
}


def get_file_type(path: Union[str, Path]) -> FileType:
    path = Path(path)
    ext = path.suffix.lower()

    if ext == ".xml":
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")[:1000]
            if "mxfile" in content.lower() or "mxgraph" in content.lower():
                return FileType.DRAWIO
            if "bpmn" in content.lower():
                return FileType.BPMN
        except Exception:
            pass
        return FileType.UNKNOWN

    return EXTENSION_MAP.get(ext, FileType.UNKNOWN)


def get_supported_extensions() -> set[str]:
    return set(EXTENSION_MAP.keys())


def is_supported(path: Union[str, Path]) -> bool:
    return get_file_type(path) != FileType.UNKNOWN


def requires_conversion(file_type: FileType) -> bool:
    return file_type == FileType.ARCHIVE


def requires_text_extraction(file_type: FileType) -> bool:
    return file_type in {FileType.DRAWIO, FileType.BPMN}


def get_handler_name(file_type: FileType) -> str:
    handlers = {
        FileType.IMAGE: "image_inference",
        FileType.SVG: "svg_to_image",
        FileType.PDF: "pdf_to_images",
        FileType.DRAWIO: "drawio_to_text",
        FileType.BPMN: "bpmn_to_text",
        FileType.ARCHIVE: "extract_and_process",
    }
    return handlers.get(file_type, "unknown")
