from app.models import ExtractionResult


def format_result_text(result: ExtractionResult) -> str:
    lines = []
    lines.append(f"{'='*50}")
    lines.append(f"Файл: {result.source_file}")
    if result.diagram_type:
        lines.append(f"Тип: {result.diagram_type}")
    lines.append(f"{'='*50}")
    lines.append("")

    if result.error:
        lines.append(f"ОШИБКА: {result.error}")
        return "\n".join(lines)

    if not result.steps:
        lines.append("Шаги не найдены")
        return "\n".join(lines)

    lines.append("АЛГОРИТМ:")
    lines.append("")

    for step in result.steps:
        num = step.number or "•"
        line = f"  {num}. "
        if step.actor:
            line += f"[{step.actor}] "
        line += step.action or "—"
        if step.target and step.target != step.actor:
            line += f" → {step.target}"
        lines.append(line)

    lines.append("")
    lines.append(f"Всего шагов: {len(result.steps)}")
    if result.confidence:
        lines.append(f"Уверенность: {result.confidence:.0%}")

    return "\n".join(lines)


def format_result_html(result: ExtractionResult) -> str:
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{result.source_file} - Diagram2Algo</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 800px; margin: 40px auto; padding: 20px; background: #1a1a2e; color: #eee; }}
        h1 {{ color: #00d4ff; margin-bottom: 5px; }}
        .type {{ color: #888; margin-bottom: 20px; }}
        .steps {{ background: #16213e; padding: 20px; border-radius: 8px; }}
        .step {{ padding: 10px 15px; margin: 8px 0; background: #0f3460; border-radius: 6px;
                 border-left: 3px solid #00d4ff; }}
        .step-num {{ color: #00d4ff; font-weight: bold; margin-right: 10px; }}
        .actor {{ color: #ffaa00; margin-right: 8px; }}
        .action {{ color: #fff; }}
        .target {{ color: #888; margin-left: 8px; }}
        .note {{ color: #666; font-style: italic; margin-top: 5px; font-size: 0.9em; }}
        .summary {{ margin-top: 20px; color: #888; }}
        .error {{ background: #4a1a1a; border-left-color: #ff4444; }}
    </style>
</head>
<body>
    <h1>{result.source_file}</h1>
    <div class="type">{result.diagram_type or 'Тип не определён'}</div>
"""

    if result.error:
        html += f'<div class="step error">Ошибка: {result.error}</div>'
    elif not result.steps:
        html += '<div class="step">Шаги не найдены</div>'
    else:
        html += '<div class="steps">'
        for step in result.steps:
            html += '<div class="step">'
            html += f'<span class="step-num">{step.number or "•"}.</span>'
            if step.actor:
                html += f'<span class="actor">[{step.actor}]</span>'
            html += f'<span class="action">{step.action or "—"}</span>'
            if step.target and step.target != step.actor:
                html += f'<span class="target">→ {step.target}</span>'
            if step.note and step.note != step.action:
                html += f'<div class="note">{step.note}</div>'
            html += '</div>'
        html += '</div>'

        conf_pct = f"{result.confidence:.0%}" if result.confidence else "—"
        html += f'<div class="summary">Шагов: {len(result.steps)} | Уверенность: {conf_pct}</div>'

    html += "</body></html>"
    return html
