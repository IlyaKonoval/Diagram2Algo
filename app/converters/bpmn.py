import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

BPMN_NAMESPACES = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmn2": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
}


def parse_bpmn(source: Union[str, Path, bytes]) -> Optional[str]:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            logger.error(f"BPMN file not found: {path}")
            return None
        xml_data = path.read_bytes()
    else:
        xml_data = source

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        logger.error(f"Failed to parse BPMN XML: {e}")
        return None

    ns = _detect_namespace(root)

    participants = []
    events = []
    tasks = []
    gateways = []
    flows = []

    for elem in root.iter():
        tag = _local_name(elem.tag)
        name = elem.get("name", "")
        elem_id = elem.get("id", "")

        if tag == "participant":
            participants.append(f"Participant: {name or elem_id}")
        elif tag in ("startEvent", "endEvent", "intermediateThrowEvent", "intermediateCatchEvent"):
            event_type = tag.replace("Event", " Event")
            events.append(f"{event_type}: {name or elem_id}")
        elif tag in ("task", "userTask", "serviceTask", "scriptTask", "manualTask", "sendTask", "receiveTask"):
            task_type = tag.replace("Task", " Task") if "Task" in tag else "Task"
            tasks.append(f"{task_type}: {name or elem_id}")
        elif tag in ("exclusiveGateway", "parallelGateway", "inclusiveGateway", "eventBasedGateway"):
            gw_type = tag.replace("Gateway", " Gateway")
            gateways.append(f"{gw_type}: {name or elem_id}")
        elif tag == "sequenceFlow":
            source_ref = elem.get("sourceRef", "?")
            target_ref = elem.get("targetRef", "?")
            flow_name = f" ({name})" if name else ""
            flows.append(f"{source_ref} --> {target_ref}{flow_name}")

    result_parts = []

    if participants:
        result_parts.append("Participants:\n" + "\n".join(f"  - {p}" for p in participants))
    if events:
        result_parts.append("Events:\n" + "\n".join(f"  - {e}" for e in events))
    if tasks:
        result_parts.append("Tasks:\n" + "\n".join(f"  - {t}" for t in tasks))
    if gateways:
        result_parts.append("Gateways:\n" + "\n".join(f"  - {g}" for g in gateways))
    if flows:
        result_parts.append("Sequence Flows:\n" + "\n".join(f"  - {f}" for f in flows))

    return "\n\n".join(result_parts) if result_parts else None


def _detect_namespace(root: ET.Element) -> dict:
    tag = root.tag
    if tag.startswith("{"):
        ns_uri = tag[1:tag.index("}")]
        return {"bpmn": ns_uri}
    return BPMN_NAMESPACES


def _local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag[tag.index("}") + 1:]
    return tag


def extract_bpmn_elements(source: Union[str, Path, bytes]) -> dict:
    if isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            return {}
        xml_data = path.read_bytes()
    else:
        xml_data = source

    result = {
        "participants": [],
        "tasks": [],
        "events": [],
        "gateways": [],
        "flows": [],
    }

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError:
        return result

    for elem in root.iter():
        tag = _local_name(elem.tag)
        name = elem.get("name", "")
        elem_id = elem.get("id", "")

        if tag == "participant":
            result["participants"].append({"id": elem_id, "name": name})
        elif "Event" in tag:
            result["events"].append({"id": elem_id, "name": name, "type": tag})
        elif "Task" in tag or tag == "task":
            result["tasks"].append({"id": elem_id, "name": name, "type": tag})
        elif "Gateway" in tag:
            result["gateways"].append({"id": elem_id, "name": name, "type": tag})
        elif tag == "sequenceFlow":
            result["flows"].append({
                "id": elem_id,
                "source": elem.get("sourceRef"),
                "target": elem.get("targetRef"),
                "name": name,
            })

    return result
