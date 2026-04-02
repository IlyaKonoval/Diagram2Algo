import base64
import logging
import re
import shutil
import subprocess
import tempfile
import zlib
from pathlib import Path
from typing import Optional

import httpx

from app.models import DiagramStep

logger = logging.getLogger(__name__)


def _safe_alias(name: str) -> str:
    return re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9_]', '_', name.replace(" ", "_"))


def generate_sequence_diagram(steps: list[DiagramStep], title: Optional[str] = None) -> str:
    lines = ["@startuml"]

    if title:
        lines.append(f"title {title}")

    participants = set()
    for step in steps:
        if step.actor:
            participants.add(step.actor)
        if step.target:
            participants.add(step.target)

    for p in sorted(participants):
        lines.append(f'participant "{p}" as {_safe_alias(p)}')

    lines.append("")

    for step in steps:
        actor = step.actor or "User"
        target = step.target or "System"

        lines.append(f"{_safe_alias(actor)} -> {_safe_alias(target)}: {step.action}")

        if step.note:
            lines.append(f"note right: {step.note}")

    lines.append("@enduml")
    return "\n".join(lines)


def generate_activity_diagram(steps: list[DiagramStep], title: Optional[str] = None) -> str:
    lines = ["@startuml"]

    if title:
        lines.append(f"title {title}")

    lines.append("start")

    for step in steps:
        action = step.action
        if step.actor:
            action = f"{step.actor}: {action}"
        lines.append(f":{action};")

    lines.append("stop")
    lines.append("@enduml")
    return "\n".join(lines)


def _plantuml_encode(text: str) -> str:
    compressed = zlib.compress(text.encode("utf-8"))[2:-4]
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    result = []
    for i in range(0, len(compressed), 3):
        chunk = compressed[i:i+3]
        if len(chunk) == 3:
            b0, b1, b2 = chunk
            result.append(alphabet[b0 >> 2])
            result.append(alphabet[((b0 & 0x3) << 4) | (b1 >> 4)])
            result.append(alphabet[((b1 & 0xF) << 2) | (b2 >> 6)])
            result.append(alphabet[b2 & 0x3F])
        elif len(chunk) == 2:
            b0, b1 = chunk
            result.append(alphabet[b0 >> 2])
            result.append(alphabet[((b0 & 0x3) << 4) | (b1 >> 4)])
            result.append(alphabet[(b1 & 0xF) << 2])
        elif len(chunk) == 1:
            b0 = chunk[0]
            result.append(alphabet[b0 >> 2])
            result.append(alphabet[(b0 & 0x3) << 4])
    return "".join(result)


def render_plantuml(code: str) -> Optional[str]:
    try:
        if shutil.which("java"):
            plantuml_jar = Path("plantuml.jar")
            if plantuml_jar.exists():
                with tempfile.NamedTemporaryFile(mode="w", suffix=".puml", delete=False) as f:
                    f.write(code)
                    puml_path = f.name
                subprocess.run(
                    ["java", "-jar", str(plantuml_jar), "-tpng", puml_path],
                    check=True, capture_output=True,
                )
                png_path = Path(puml_path).with_suffix(".png")
                if png_path.exists():
                    with open(png_path, "rb") as f:
                        png_data = f.read()
                    png_path.unlink()
                    Path(puml_path).unlink()
                    return base64.b64encode(png_data).decode()
    except Exception as e:
        logger.warning(f"Local PlantUML failed: {e}")

    try:
        encoded = _plantuml_encode(code)
        resp = httpx.get(f"https://www.plantuml.com/plantuml/png/{encoded}", timeout=15)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
            return base64.b64encode(resp.content).decode()
    except Exception as e:
        logger.error(f"PlantUML server failed: {e}")

    return None
