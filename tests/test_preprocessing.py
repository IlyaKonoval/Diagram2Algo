import pytest
from PIL import Image

from app.preprocessing import (
    convert_to_rgb,
    enhance_contrast,
    is_dark_background,
    preprocess_image,
    resize_image,
)


@pytest.fixture
def white_image():
    return Image.new("RGB", (100, 100), (255, 255, 255))


@pytest.fixture
def black_image():
    return Image.new("RGB", (100, 100), (0, 0, 0))


@pytest.fixture
def large_image():
    return Image.new("RGB", (2000, 1500), (200, 200, 200))


@pytest.fixture
def small_image():
    return Image.new("RGB", (100, 100), (200, 200, 200))


@pytest.fixture
def rgba_image():
    return Image.new("RGBA", (100, 100), (255, 0, 0, 128))


class TestResizeImage:
    def test_large_image_resized(self, large_image):
        result = resize_image(large_image, max_dim=1280)
        assert max(result.size) <= 1280

    def test_small_image_unchanged(self, small_image):
        result = resize_image(small_image, max_dim=1280, min_dim=50)
        assert result.size == small_image.size

    def test_maintains_aspect_ratio(self, large_image):
        original_ratio = large_image.size[0] / large_image.size[1]
        result = resize_image(large_image, max_dim=1280)
        new_ratio = result.size[0] / result.size[1]
        assert abs(original_ratio - new_ratio) < 0.01


class TestEnhanceContrast:
    def test_returns_image(self, white_image):
        result = enhance_contrast(white_image, factor=1.3)
        assert isinstance(result, Image.Image)
        assert result.size == white_image.size


class TestIsDarkBackground:
    def test_white_not_dark(self, white_image):
        assert is_dark_background(white_image) is False

    def test_black_is_dark(self, black_image):
        assert is_dark_background(black_image) is True


class TestConvertToRgb:
    def test_rgba_to_rgb(self, rgba_image):
        result = convert_to_rgb(rgba_image)
        assert result.mode == "RGB"

    def test_rgb_unchanged(self, white_image):
        result = convert_to_rgb(white_image)
        assert result.mode == "RGB"


class TestPreprocessImage:
    def test_full_pipeline(self, large_image):
        result = preprocess_image(large_image)
        assert result.mode == "RGB"
        assert max(result.size) <= 1280

    def test_skip_resize(self, large_image):
        result = preprocess_image(large_image, resize=False)
        assert result.size == large_image.size

    def test_skip_enhance(self, white_image):
        result = preprocess_image(white_image, enhance=False)
        assert isinstance(result, Image.Image)
