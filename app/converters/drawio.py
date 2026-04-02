import base64
import logging
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from typing import Optional, Union
from urllib.parse import unquote

logger = logging.getLogger(__name__)


def decode_drawio_data(data: str) -> str:
    try:
        decoded = base64.b64decode(data)
        decompressed = zlib.decompress(decoded, -zlib.MAX_WBITS)
        return unquote(decompressed.decode("utf-8"))
    except Exception:
        return unquote(data)


def parse_drawio(source: Union[str, Path, bytes]) -> Optional[str]:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            logger.error(f"DrawIO file not found: {path}")
            return None
        xml_data = path.read_text(encoding="utf-8")
    else:
        xml_data = source.decode("utf-8")

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        logger.error(f"Failed to parse DrawIO XML: {e}")
        return None

    elements = []
    connections = []

    for diagram in root.iter("diagram"):
        diagram_name = diagram.get("name", "Diagram")
        elements.append(f"Diagram: {diagram_name}")

        compressed_data = diagram.text
        if compressed_data:
            try:
                decompressed = decode_drawio_data(compressed_data.strip())
                inner_root = ET.fromstring(decompressed)
                _extract_cells(inner_root, elements, connections)
            except Exception as e:
                logger.debug(f"Could not decompress diagram data: {e}")

        for mx_cell in diagram.iter("mxCell"):
            _process_cell(mx_cell, elements, connections)

        for mx_graph_model in diagram.iter("mxGraphModel"):
            for mx_cell in mx_graph_model.iter("mxCell"):
                _process_cell(mx_cell, elements, connections)

    result_parts = []
    if elements:
        result_parts.append("Elements:\n" + "\n".join(f"  - {e}" for e in elements))
    if connections:
        result_parts.append("Connections:\n" + "\n".join(f"  - {c}" for c in connections))

    return "\n\n".join(result_parts) if result_parts else None


def _extract_cells(root: ET.Element, elements: list, connections: list):
    for mx_cell in root.iter("mxCell"):
        _process_cell(mx_cell, elements, connections)


def _process_cell(cell: ET.Element, elements: list, connections: list):
    cell_id = cell.get("id", "")
    value = cell.get("value", "")
    source = cell.get("source")
    target = cell.get("target")
    style = cell.get("style", "")

    if source and target:
        label = value if value else "connects to"
        connections.append(f"[{source}] --{label}--> [{target}]")
    elif value and value.strip():
        shape_type = "shape"
        if "ellipse" in style:
            shape_type = "ellipse"
        elif "rhombus" in style:
            shape_type = "decision"
        elif "rounded" in style:
            shape_type = "rounded rect"

        elements.append(f"[{cell_id}] {shape_type}: {value.strip()}")


def extract_drawio_text(source: Union[str, Path, bytes]) -> list[str]:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            return []
        xml_data = path.read_text(encoding="utf-8")
    else:
        xml_data = source.decode("utf-8")

    texts = []
    try:
        root = ET.fromstring(xml_data)
        for elem in root.iter():
            value = elem.get("value", "")
            if value and value.strip():
                import html
                clean = html.unescape(value)
                clean = ET.fromstring(f"<root>{clean}</root>").itertext() if "<" in clean else [clean]
                texts.extend(t.strip() for t in clean if t.strip())
    except Exception as e:
        logger.error(f"Failed to extract DrawIO text: {e}")

    return texts
