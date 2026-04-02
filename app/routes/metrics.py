from collections import defaultdict
from threading import Lock

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["metrics"])

_lock = Lock()
_counters: dict[str, int] = defaultdict(int)
_histograms: dict[str, list[float]] = defaultdict(list)


def inc_counter(name: str, value: int = 1):
    with _lock:
        _counters[name] += value


def observe_histogram(name: str, value: float):
    with _lock:
        _histograms[name].append(value)


def _format_prometheus() -> str:
    lines = []
    with _lock:
        for name, value in sorted(_counters.items()):
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")

        for name, values in sorted(_histograms.items()):
            if values:
                lines.append(f"# TYPE {name} summary")
                lines.append(f"{name}_count {len(values)}")
                lines.append(f"{name}_sum {sum(values):.3f}")
                avg = sum(values) / len(values)
                lines.append(f"{name}_avg {avg:.3f}")
    return "\n".join(lines) + "\n"


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return _format_prometheus()
