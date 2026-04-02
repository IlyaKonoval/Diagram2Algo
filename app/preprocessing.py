import logging
from typing import Optional

from PIL import Image, ImageEnhance, ImageOps

from app.config import settings

logger = logging.getLogger(__name__)

MAX_DIMENSION = settings.max_image_dimension
MIN_DIMENSION = 224
MAX_DIMENSION_HIRES = min(settings.max_image_dimension + 256, 1280)


def resize_image(
    image: Image.Image,
    max_dim: int = MAX_DIMENSION,
    min_dim: int = MIN_DIMENSION,
) -> Image.Image:
    width, height = image.size
    max_current = max(width, height)
    min_current = min(width, height)

    if max_current <= max_dim and min_current >= min_dim:
        return image

    if max_current > max_dim:
        scale = max_dim / max_current
    elif min_current < min_dim:
        scale = min_dim / min_current
    else:
        return image

    new_width = int(width * scale)
    new_height = int(height * scale)

    logger.debug(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def enhance_contrast(image: Image.Image, factor: float = 1.3) -> Image.Image:
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def enhance_sharpness(image: Image.Image, factor: float = 1.2) -> Image.Image:
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(factor)


def is_dark_background(image: Image.Image, threshold: float = 0.4) -> bool:
    gray = image.convert("L")
    width, height = gray.size
    samples = []

    margin_x = int(width * 0.1)
    margin_y = int(height * 0.1)

    corners = [
        (margin_x, margin_y),
        (width - margin_x, margin_y),
        (margin_x, height - margin_y),
        (width - margin_x, height - margin_y),
    ]

    for x, y in corners:
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        samples.append(gray.getpixel((x, y)))

    avg_brightness = sum(samples) / len(samples) / 255.0
    return avg_brightness < threshold


def invert_dark_background(image: Image.Image) -> Image.Image:
    if is_dark_background(image):
        logger.debug("Dark background detected, inverting image")
        if image.mode == "RGBA":
            r, g, b, a = image.split()
            rgb = Image.merge("RGB", (r, g, b))
            rgb_inverted = ImageOps.invert(rgb)
            r, g, b = rgb_inverted.split()
            return Image.merge("RGBA", (r, g, b, a))
        elif image.mode == "RGB":
            return ImageOps.invert(image)
        else:
            rgb = image.convert("RGB")
            inverted = ImageOps.invert(rgb)
            return inverted.convert(image.mode)
    return image


def convert_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        return background
    elif image.mode != "RGB":
        return image.convert("RGB")
    return image


def preprocess_image(
    image: Image.Image,
    resize: bool = True,
    enhance: bool = True,
    handle_dark: bool = True,
    max_dim: int = MAX_DIMENSION,
) -> Image.Image:
    result = image.copy()

    if handle_dark:
        result = invert_dark_background(result)

    result = convert_to_rgb(result)

    if resize:
        result = resize_image(result, max_dim=max_dim)

    if enhance:
        result = enhance_contrast(result, factor=1.2)
        result = enhance_sharpness(result, factor=1.1)

    return result


def preprocess_rendered(image: Image.Image) -> Image.Image:
    result = convert_to_rgb(image)
    result = resize_image(result, max_dim=MAX_DIMENSION_HIRES)
    return result


def load_and_preprocess(
    path: str,
    **kwargs,
) -> Optional[Image.Image]:
    try:
        image = Image.open(path)
        return preprocess_image(image, **kwargs)
    except Exception as e:
        logger.error(f"Failed to load/preprocess image {path}: {e}")
        return None
