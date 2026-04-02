from app.models import DiagramStep
from app.plantuml import (
    _plantuml_encode,
    _safe_alias,
    generate_activity_diagram,
    generate_sequence_diagram,
)


class TestSafeAlias:
    def test_simple_name(self):
        assert _safe_alias("User") == "User"

    def test_spaces_replaced(self):
        assert _safe_alias("Web Server") == "Web_Server"

    def test_special_chars_removed(self):
        assert _safe_alias("User (admin)") == "User__admin_"

    def test_cyrillic_preserved(self):
        result = _safe_alias("Пользователь")
        assert "Пользователь" == result


class TestGenerateSequenceDiagram:
    def test_basic_sequence(self):
        steps = [
            DiagramStep(number=1, actor="User", action="Login", target="Server"),
        ]
        result = generate_sequence_diagram(steps)
        assert "@startuml" in result
        assert "@enduml" in result
        assert "User" in result
        assert "Server" in result
        assert "Login" in result

    def test_with_title(self):
        steps = [DiagramStep(number=1, action="Test")]
        result = generate_sequence_diagram(steps, title="My Diagram")
        assert "title My Diagram" in result

    def test_with_note(self):
        steps = [
            DiagramStep(number=1, actor="A", action="Do", target="B", note="Important"),
        ]
        result = generate_sequence_diagram(steps)
        assert "note right: Important" in result

    def test_default_actor_and_target(self):
        steps = [DiagramStep(number=1, action="Process")]
        result = generate_sequence_diagram(steps)
        assert "User" in result
        assert "System" in result

    def test_participants_declared(self):
        steps = [
            DiagramStep(number=1, actor="Client", action="Request", target="API"),
        ]
        result = generate_sequence_diagram(steps)
        assert 'participant "API"' in result
        assert 'participant "Client"' in result


class TestGenerateActivityDiagram:
    def test_basic_activity(self):
        steps = [
            DiagramStep(number=1, action="Start process"),
            DiagramStep(number=2, action="End process"),
        ]
        result = generate_activity_diagram(steps)
        assert "@startuml" in result
        assert "start" in result
        assert "stop" in result
        assert ":Start process;" in result

    def test_with_actor(self):
        steps = [DiagramStep(number=1, actor="Admin", action="Approve")]
        result = generate_activity_diagram(steps)
        assert ":Admin: Approve;" in result

    def test_with_title(self):
        steps = [DiagramStep(number=1, action="Test")]
        result = generate_activity_diagram(steps, title="Flow")
        assert "title Flow" in result


class TestPlantUMLEncode:
    def test_returns_string(self):
        result = _plantuml_encode("@startuml\n@enduml")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_deterministic(self):
        code = "@startuml\nA -> B: test\n@enduml"
        assert _plantuml_encode(code) == _plantuml_encode(code)
