import logging
from pathlib import Path
from typing import Optional, Union

import fitz
from PIL import Image

logger = logging.getLogger(__name__)


def render_svg(path: Union[str, Path], dpi: int = 300) -> Optional[Image.Image]:
    try:
        doc = fitz.open(str(path))
        page = doc[0]

        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix)

        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)

        doc.close()
        logger.info(f"SVG rendered: {Path(path).name} -> {image.size}")
        return image

    except Exception as e:
        logger.error(f"Failed to render SVG {path}: {e}")
        return None
