import pytest
from app.postprocessing import (
    extract_json_from_text,
    parse_json_response,
    parse_simple_format,
    parse_llm_response,
    validate_steps,
)
from app.models import DiagramStep


class TestExtractJsonFromText:
    def test_simple_json(self):
        text = '{"steps": []}'
        assert extract_json_from_text(text) == '{"steps": []}'

    def test_json_with_prefix(self):
        text = 'Here is the result: {"steps": [{"action": "test"}]}'
        result = extract_json_from_text(text)
        assert result == '{"steps": [{"action": "test"}]}'

    def test_json_with_suffix(self):
        text = '{"steps": []} Some extra text'
        assert extract_json_from_text(text) == '{"steps": []}'

    def test_nested_json(self):
        text = '{"outer": {"inner": "value"}}'
        assert extract_json_from_text(text) == '{"outer": {"inner": "value"}}'

    def test_no_json(self):
        text = "This is plain text without JSON"
        assert extract_json_from_text(text) is None


class TestParseJsonResponse:
    def test_valid_json(self):
        text = '{"diagram_type": "sequence", "steps": []}'
        result = parse_json_response(text)
        assert result == {"diagram_type": "sequence", "steps": []}

    def test_json_in_text(self):
        text = 'The response is: {"steps": [{"action": "test"}]}'
        result = parse_json_response(text)
        assert result == {"steps": [{"action": "test"}]}

    def test_json_with_trailing_comma(self):
        text = '{"steps": ["a", "b",]}'
        result = parse_json_response(text)
        assert result == {"steps": ["a", "b"]}

    def test_invalid_json(self):
        text = "not json at all"
        assert parse_json_response(text) is None


class TestParseSimpleFormat:
    def test_arrow_format(self):
        text = "1. User -> Clicks button -> System"
        steps = parse_simple_format(text)
        assert len(steps) == 1
        assert steps[0].actor == "User"
        assert steps[0].action == "Clicks button"
        assert steps[0].target == "System"

    def test_simple_format(self):
        text = "1. First action\n2. Second action\n3. Third action"
        steps = parse_simple_format(text)
        assert len(steps) == 3
        assert steps[0].action == "First action"
        assert steps[1].action == "Second action"

    def test_empty_text(self):
        steps = parse_simple_format("")
        assert len(steps) == 0


class TestParseLlmResponse:
    def test_json_response(self):
        text = '{"diagram_type": "BPMN", "steps": [{"number": 1, "action": "Start"}], "confidence": 0.9}'
        result = parse_llm_response(text, "test.png")
        assert result.diagram_type == "BPMN"
        assert len(result.steps) == 1
        assert result.confidence == 0.9

    def test_fallback_to_simple(self):
        text = "1. First step\n2. Second step"
        result = parse_llm_response(text, "test.png")
        assert len(result.steps) == 2
        assert result.confidence == 0.5

    def test_no_steps(self):
        text = "No valid content here"
        result = parse_llm_response(text, "test.png")
        assert len(result.steps) == 0
        assert result.error is not None


class TestValidateSteps:
    def test_removes_empty_actions(self):
        steps = [
            DiagramStep(number=1, action="Valid"),
            DiagramStep(number=2, action=""),
            DiagramStep(number=3, action="  "),
        ]
        result = validate_steps(steps)
        assert len(result) == 1

    def test_normalizes_whitespace(self):
        steps = [DiagramStep(number=1, action="Too   many   spaces")]
        result = validate_steps(steps)
        assert result[0].action == "Too many spaces"

    def test_renumbers_steps(self):
        steps = [
            DiagramStep(number=5, action="First"),
            DiagramStep(number=10, action="Second"),
        ]
        result = validate_steps(steps)
        assert result[0].number == 1
        assert result[1].number == 2
