import json
import logging
import re
from typing import Optional

from app.models import DiagramStep, ExtractionResult

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> Optional[str]:
    brace_count = 0
    start_idx = None
    end_idx = None

    for i, char in enumerate(text):
        if char == "{":
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0 and start_idx is not None:
                end_idx = i + 1
                break

    if start_idx is not None and end_idx is not None:
        return text[start_idx:end_idx]

    return None


def parse_json_response(text: str) -> Optional[dict]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    json_str = extract_json_from_text(text)
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    fixed = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    json_str = extract_json_from_text(fixed)
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    logger.warning("Failed to parse JSON from response")
    return None


def is_invalid_action(action: str) -> bool:
    action = action.strip()
    if re.match(r"^[\d\.\-]+$", action):
        return True
    if re.match(r"^\d+[-–]\d+(\.\d+)?$", action):
        return True
    if len(action) < 3:
        return True
    return False


def parse_simple_format(text: str) -> list[DiagramStep]:
    steps = []

    arrow_pattern = r"(\d+)\.\s*([^->]+?)\s*->\s*(.+?)\s*->\s*([^->]+?)(?:\n|$)"
    simple_pattern = r"(\d+)\.\s*(.+?)(?:\n|$)"

    arrow_matches = re.findall(arrow_pattern, text)
    if arrow_matches:
        for match in arrow_matches:
            num, actor, action, target = match
            if is_invalid_action(action):
                continue
            actor = actor.strip() if actor.strip() != "?" else None
            target = target.strip() if target.strip() != "?" else None
            steps.append(
                DiagramStep(
                    number=int(num),
                    actor=actor,
                    action=action.strip(),
                    target=target,
                )
            )
        return steps

    simple_matches = re.findall(simple_pattern, text)
    for match in simple_matches:
        num, action = match
        if is_invalid_action(action):
            continue
        steps.append(
            DiagramStep(
                number=int(num),
                action=action.strip(),
            )
        )

    return steps


def parse_llm_response(
    text: str,
    source_file: str,
    page_or_slide: Optional[int] = None,
) -> ExtractionResult:
    data = parse_json_response(text)

    if data and isinstance(data, dict):
        steps = []
        for i, step_data in enumerate(data.get("steps", [])):
            if isinstance(step_data, dict):
                action = step_data.get("action", "Unknown")
                if is_invalid_action(action):
                    continue
                steps.append(
                    DiagramStep(
                        number=step_data.get("number", i + 1),
                        actor=step_data.get("actor"),
                        action=action,
                        target=step_data.get("target"),
                        note=step_data.get("note"),
                    )
                )

        return ExtractionResult(
            source_file=source_file,
            page_or_slide=page_or_slide,
            diagram_type=data.get("diagram_type"),
            steps=steps,
            confidence=float(data.get("confidence", 0.8)),
        )

    logger.info("Falling back to simple format parsing")
    steps = parse_simple_format(text)

    if steps:
        return ExtractionResult(
            source_file=source_file,
            page_or_slide=page_or_slide,
            steps=steps,
            confidence=0.5,
        )

    return ExtractionResult(
        source_file=source_file,
        page_or_slide=page_or_slide,
        steps=[],
        confidence=0.0,
        error="Failed to parse any steps from LLM response",
    )


def validate_steps(steps: list[DiagramStep]) -> list[DiagramStep]:
    valid_steps = []

    for step in steps:
        if not step.action or not step.action.strip():
            continue

        action = step.action.strip()
        action = re.sub(r"\s+", " ", action)

        if is_invalid_action(action):
            continue

        valid_steps.append(
            DiagramStep(
                number=step.number,
                actor=step.actor.strip() if step.actor else None,
                action=action,
                target=step.target.strip() if step.target else None,
                note=step.note.strip() if step.note else None,
            )
        )

    for i, step in enumerate(valid_steps):
        step.number = i + 1

    return valid_steps


def merge_results(results: list[ExtractionResult]) -> ExtractionResult:
    if not results:
        return ExtractionResult(
            source_file="",
            steps=[],
            error="No results to merge",
        )

    if len(results) == 1:
        return results[0]

    all_steps = []
    for result in results:
        all_steps.extend(result.steps)

    for i, step in enumerate(all_steps):
        step.number = i + 1

    first = results[0]

    return ExtractionResult(
        source_file=first.source_file,
        diagram_type=first.diagram_type,
        steps=all_steps,
        confidence=sum(r.confidence for r in results) / len(results),
    )
