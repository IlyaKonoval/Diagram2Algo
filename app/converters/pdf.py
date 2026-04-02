import logging
from pathlib import Path
from typing import Union

import fitz
from PIL import Image

logger = logging.getLogger(__name__)


def render_pdf_pages(
    path: Union[str, Path],
    dpi: int = 300,
    max_pages: int = 5,
) -> list[Image.Image]:
    images = []
    try:
        doc = fitz.open(str(path))
        total = min(len(doc), max_pages)
        zoom = dpi / 72
        matrix = fitz.Matrix(zoom, zoom)

        for i in range(total):
            page = doc[i]
            pixmap = page.get_pixmap(matrix=matrix)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            images.append(image)
            logger.info(f"PDF page {i + 1}/{total} rendered: {image.size}")

        doc.close()

        if len(doc) > max_pages:
            logger.warning(f"PDF has {len(doc)} pages, processed only first {max_pages}")

    except Exception as e:
        logger.error(f"Failed to render PDF {path}: {e}")

    return images
