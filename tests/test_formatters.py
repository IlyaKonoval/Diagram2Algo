import pytest
from app.formatters import format_result_html, format_result_text
from app.models import DiagramStep, ExtractionResult


@pytest.fixture
def sample_result():
    return ExtractionResult(
        source_file="test.png",
        diagram_type="sequence",
        steps=[
            DiagramStep(number=1, actor="User", action="Login", target="Server"),
            DiagramStep(number=2, actor="Server", action="Validate", target="DB"),
        ],
        confidence=0.85,
    )


@pytest.fixture
def error_result():
    return ExtractionResult(
        source_file="bad.png",
        error="Failed to process",
    )


@pytest.fixture
def empty_result():
    return ExtractionResult(
        source_file="empty.png",
        diagram_type="unknown",
        steps=[],
        confidence=0.0,
    )


class TestFormatResultText:
    def test_contains_filename(self, sample_result):
        text = format_result_text(sample_result)
        assert "test.png" in text

    def test_contains_diagram_type(self, sample_result):
        text = format_result_text(sample_result)
        assert "sequence" in text

    def test_contains_steps(self, sample_result):
        text = format_result_text(sample_result)
        assert "Login" in text
        assert "Validate" in text

    def test_contains_actor(self, sample_result):
        text = format_result_text(sample_result)
        assert "[User]" in text

    def test_contains_confidence(self, sample_result):
        text = format_result_text(sample_result)
        assert "85%" in text

    def test_error_result(self, error_result):
        text = format_result_text(error_result)
        assert "ОШИБКА" in text
        assert "Failed to process" in text

    def test_empty_steps(self, empty_result):
        text = format_result_text(empty_result)
        assert "не найдены" in text


class TestFormatResultHtml:
    def test_is_valid_html(self, sample_result):
        html = format_result_html(sample_result)
        assert "<!DOCTYPE html>" in html
        assert "</html>" in html

    def test_contains_steps(self, sample_result):
        html = format_result_html(sample_result)
        assert "Login" in html
        assert "Validate" in html

    def test_error_has_error_class(self, error_result):
        html = format_result_html(error_result)
        assert "error" in html
        assert "Failed to process" in html
