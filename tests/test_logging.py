import json
import logging
import pytest
from app.logging_config import JSONFormatter, request_id_var, setup_logging


class TestJSONFormatter:
    def test_formats_as_json(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert data["level"] == "INFO"
        assert data["message"] == "test message"
        assert data["logger"] == "test"
        assert "timestamp" in data

    def test_includes_request_id(self):
        formatter = JSONFormatter()
        token = request_id_var.set("abc123")
        try:
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="", lineno=0,
                msg="test", args=(), exc_info=None,
            )
            output = formatter.format(record)
            data = json.loads(output)
            assert data["request_id"] == "abc123"
        finally:
            request_id_var.reset(token)

    def test_no_request_id_when_not_set(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test", args=(), exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)
        assert "request_id" not in data


class TestSetupLogging:
    def test_setup_with_text_format(self):
        setup_logging(json_format=False, level="DEBUG")
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert len(root.handlers) == 1

    def test_setup_with_json_format(self):
        setup_logging(json_format=True, level="INFO")
        root = logging.getLogger()
        assert isinstance(root.handlers[0].formatter, JSONFormatter)
