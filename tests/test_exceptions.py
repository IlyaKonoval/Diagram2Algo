import pytest

from app.exceptions import (
    CVUMLException,
    ExtractionError,
    FileProcessingError,
    LLMProviderError,
    ParsingError,
    UnsupportedFileError,
)


class TestExceptionHierarchy:
    def test_base_exception(self):
        exc = CVUMLException("test error", detail="details here")
        assert str(exc) == "test error"
        assert exc.message == "test error"
        assert exc.detail == "details here"

    def test_llm_provider_error_is_cvuml(self):
        exc = LLMProviderError("provider down")
        assert isinstance(exc, CVUMLException)

    def test_extraction_error_is_cvuml(self):
        exc = ExtractionError("failed")
        assert isinstance(exc, CVUMLException)

    def test_parsing_error_is_cvuml(self):
        exc = ParsingError("bad json")
        assert isinstance(exc, CVUMLException)

    def test_file_processing_error_is_cvuml(self):
        exc = FileProcessingError("corrupt file")
        assert isinstance(exc, CVUMLException)

    def test_unsupported_file_is_file_processing(self):
        exc = UnsupportedFileError("unknown format")
        assert isinstance(exc, FileProcessingError)
        assert isinstance(exc, CVUMLException)

    def test_default_detail_is_empty(self):
        exc = CVUMLException("msg")
        assert exc.detail == ""

    def test_can_catch_by_base_class(self):
        with pytest.raises(CVUMLException):
            raise LLMProviderError("connection refused")
